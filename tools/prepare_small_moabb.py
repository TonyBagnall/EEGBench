"""Five compact MOABB source collections -> .ts with exact float64 sidecars.

Reads native MATLAB arrays or the pinned Zhou BIDS release directly. Does not
execute MOABB's default filters, synthetic timelines, demeaning or epoch rejection.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
import shutil
import ssl
import tempfile
import time
import urllib.request
import zipfile

import certifi
import numpy as np
from scipy.io import loadmat

from tools.prepare_moabb import MOABB_REVISION, dump, lines, sha
from tools.prepare_wang import format_case, digest_case

ROOT = Path('D:/Data/EEGSources/SmallMOABB')
NAKA_REVISION = '2d4e281a430b4676f75c9270db839e963f172da5'
BNCI = 'https://lampx.tugraz.at/~bci/database/'
SPECS = {
    'nakanishi': dict(name='FlickerTargets',source='Nakanishi2015',subjects=10,channels=8,points=1114,hz=256,classes=12,mode='subject',train=8,licence='Unspecified original data licence; public author release',doi='10.1371/journal.pone.0140703'),
    'bci2b': dict(name='ImaginedHandSides',source='BCI Competition IV 2b / BNCI2014_004',subjects=9,channels=3,points=1125,hz=250,classes=2,mode='official',licence='CC-BY-ND-4.0',doi='10.1109/TNSRE.2007.906956'),
    'speller': dict(name='SpellerFlashes',source='BNCI2015_003 / Guger2009',subjects=10,channels=8,points=205,hz=256,classes=2,mode='official',licence='CC-BY-NC-ND-4.0',doi='10.1016/j.neulet.2009.06.045'),
    'zhou': dict(name='ImaginedHandsFeet',source='Zhou2016 / Zenodo 16534752',subjects=4,channels=13,source_channels=14,remove_channels=[1],points=1250,hz=250,classes=3,mode='subject',train=3,licence='CC-BY-4.0 (pinned BIDS release)',doi='10.1371/journal.pone.0162657'),
    'als': dict(name='ALSAttention',source='BNCI2014_008 / Riccio2013',subjects=8,channels=8,points=256,hz=256,classes=2,mode='official',licence='CC-BY-NC-ND-4.0',doi='10.3389/fnhum.2013.00732'),
    'mamem3': dict(name='WirelessFlicker',source='MAMEM3 / MAMEM EEG SSVEP Dataset III',subjects=11,channels=14,points=640,hz=128,classes=5,mode='subject',train=8,licence='CC-BY-4.0',doi='10.6084/m9.figshare.3413851.v3'),
}
LABELS = {
    'nakanishi': {str(i+1):f'attended_{f:g}_Hz' for i,f in enumerate([9.25,11.25,13.25,9.75,11.75,13.75,10.25,12.25,14.25,10.75,12.75,14.75])},
    'bci2b': {'1':'imagined_left_hand','2':'imagined_right_hand'},
    'speller': {'1':'NonTarget','2':'Target'},
    'zhou': {'1':'feet','2':'left_hand','3':'right_hand'},
    'als': {'1':'NonTarget','2':'Target'},
    'mamem3': {'1':'12.00_Hz','2':'10.00_Hz','3':'8.57_Hz','4':'7.50_Hz','5':'6.66_Hz'},
}
FIELDS = ['split','row','example_id','participant_id','session_id','run_id','recording_id','source_file','source_array_index',
          'source_epoch_index','event_index','source_event_sample','source_event_sample_1based','start_sample','end_sample',
          'start_time_seconds','end_time_seconds','sample_reference','source_label','label','label_description','original_partition',
          'source_trial_start_sample_1based','source_character_selection_index','source_flash_code','source_flash_description',
          'source_artifact_flag','signal_sha256','signal_hash_dtype']


def fetch(url, path, checksum=None, size=None):
    """Atomic verified transfer; all caller-supplied source paths are fixed."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    def valid(p):
        if not p.is_file() or (size is not None and p.stat().st_size!=size):return False
        if checksum:
            algorithm,value=checksum.split(':',1)
            if algorithm=='gitblob':
                raw=p.read_bytes();return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==value
            return sha(p,algorithm)==value
        return True
    if valid(path):return path
    ctx=ssl.create_default_context(cafile=certifi.where())
    for attempt in range(5):
        try:
            part=path.with_name(path.name+'.part')
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EEGBench source preparation'}),context=ctx,timeout=90) as r,part.open('wb') as out:
                shutil.copyfileobj(r,out,1024*1024)
            if not valid(part):raise ValueError('Source checksum/size mismatch')
            part.replace(path);return path
        except Exception:
            if attempt==4:raise
            time.sleep(min(2**attempt,10))


def pulse_onsets(values):
    """One event per positive pulse, including adjacent changed positive codes."""
    values=np.asarray(values).ravel()
    return np.flatnonzero((values>0)&np.r_[True,values[1:]!=values[:-1]])


def slice_window(data, event, offset, points):
    start=int(event)+offset;end=start+points
    if start<0 or end>data.shape[0]:raise ValueError('Incomplete source epoch')
    x=np.ascontiguousarray(data[start:end].T,dtype='<f8')
    if not np.isfinite(x).all():raise ValueError('Nonfinite source epoch')
    return x,start,end


def select_channels(data,names,drop):
    if len(names)!=len(data) or any(i<0 or i>=len(names) for i in drop):raise ValueError('Invalid source channel selection')
    keep=[i for i in range(len(names)) if i not in drop]
    if not keep:raise ValueError('No retained channels')
    return data[keep],[names[i] for i in keep],keep


def rows(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter='\t'))


def bootstrap(cache,download):
    """Small source evidence needed to reproduce a conversion from an empty cache."""
    urls={
        'Nakanishi2015/tree.json':f'https://api.github.com/repos/mnakanishi/12JFPM_SSVEP/git/trees/{NAKA_REVISION}?recursive=1',
        'Nakanishi2015/README.md':f'https://raw.githubusercontent.com/mnakanishi/12JFPM_SSVEP/{NAKA_REVISION}/README.md',
        'zhou-record.json':'https://zenodo.org/api/records/16534752',
        'bnci-source.html':'https://bnci-horizon-2020.eu/database/data-sets',
        'bci2b-description.pdf':'https://bnci-horizon-2020.eu/database/data-sets/004-2014/description.pdf',
        'als-description.pdf':'https://bnci-horizon-2020.eu/database/data-sets/008-2014/description.pdf',
        'mamem3-record-v3.json':'https://api.figshare.com/v2/articles/3413851/versions/3',
    }
    for name,path in [('moabb_nakanishi.py','ssvep_nakanishi.py'),('moabb_bnci2014.py','bnci/bnci_2014.py'),
                      ('moabb_bnci2015.py','bnci/bnci_2015.py'),('moabb_bnci_base.py','bnci/base.py'),('moabb_zhou.py','Zhou2016.py'),('moabb_mamem.py','ssvep_mamem.py')]:
        urls[name]=f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/{path}'
    for name,url in urls.items():
        if download:fetch(url,cache/name)
        if not (cache/name).is_file():raise FileNotFoundError(name)


def ensure_sources(key,cache,subjects,download=True):
    """Freeze unversioned publisher files in a receipt; verify it on every reuse."""
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);bootstrap(cache,download);items=[]
    if key=='nakanishi':
        tree=json.loads((cache/'Nakanishi2015/tree.json').read_text());blobs={x['path']:x for x in tree['tree']}
        for subject in subjects:
            name=f'data/s{subject}.mat';f=blobs[name]
            items.append((f'Nakanishi2015/s{subject}.mat',f'https://raw.githubusercontent.com/mnakanishi/12JFPM_SSVEP/{NAKA_REVISION}/{name}','gitblob:'+f['sha'],f['size']))
    elif key=='mamem3':
        record=json.loads((cache/'mamem3-record-v3.json').read_text())
        if record['version']!=3 or record['license']['name']!='CC BY 4.0':raise ValueError('MAMEM3 version/licence changed')
        for f in record['files']:
            match=re.fullmatch(r'U(\d{3})([a-e])(ii|i)\.mat',f['name'])
            if match and int(match[1]) in subjects or f['name'].endswith('.pdf'):
                items.append(('MAMEM3/'+f['name'],f['download_url'],'md5:'+f['computed_md5'],f['size']))
    elif key=='zhou':
        record=json.loads((cache/'zhou-record.json').read_text())
        if record['id']!=16534752 or record['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Zhou revision/licence changed')
        for f in record['files']:
            if f['key'].startswith('sub-') and int(f['key'][4:-4]) not in subjects:continue
            items.append(('Zhou2016/'+f['key'],f['links']['self'],f['checksum'],f['size']))
    else:
        for subject in subjects:
            if key=='bci2b':
                for phase in ['T','E']:items.append((f'BCIIV2b/B{subject:02d}{phase}.mat',BNCI+f'004-2014/B{subject:02d}{phase}.mat',None,None))
            elif key=='speller':items.append((f'Speller/s{subject}.mat',BNCI+f'003-2015/s{subject}.mat',None,None))
            else:items.append((f'ALS/A{subject:02d}.mat',BNCI+f'008-2014/A{subject:02d}.mat',None,None))
    receipt=cache/f'{key}-source-receipt.json';old=json.loads(receipt.read_text()) if receipt.exists() else {}
    lock=Path(__file__).parents[1]/'docs/small-moabb-source-lock.json'
    locked=json.loads(lock.read_text()).get(key,{}) if lock.is_file() else {}
    for name,entry in locked.items():
        if name in old and old[name]['sha256']!=entry['sha256']:raise ValueError('Cache receipt disagrees with pinned source lock')
    old={**locked,**old}
    def ensure(item):
        name,url,checksum,size=item
        if name in old:checksum='sha256:'+old[name]['sha256'];size=old[name]['bytes']
        p=cache/name
        if download:fetch(url,p,checksum,size)
        if not p.is_file():raise FileNotFoundError(p)
        if size is not None and p.stat().st_size!=size:raise ValueError('Source size changed')
        if checksum:
            algorithm,value=checksum.split(':',1)
            if algorithm=='gitblob':
                raw=p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            else:actual=sha(p,algorithm)
            if actual!=value:raise ValueError('Pinned source checksum changed')
        record=dict(path=name,url=url,sha256=sha(p),bytes=p.stat().st_size,publisher_checksum=item[2])
        if name in old and record['sha256']!=old[name]['sha256']:raise ValueError('Frozen source changed')
        return record
    with ThreadPoolExecutor(max_workers=4) as pool:inventory=list(pool.map(ensure,items))
    old.update({x['path']:x for x in inventory});dump(receipt,old)
    return inventory


def case_row(spec,subject,session,run,source,event_index,label,original_partition):
    return dict(participant_id=f'{subject:02d}',session_id=str(session),run_id=str(run),recording_id=f'{subject:02d}/{session}/{run}',
                source_file=source,event_index=event_index,source_epoch_index=event_index,label=str(label),
                label_description=LABELS[spec][str(label)],original_partition=original_partition)


def mamem_trials(eeg,events):
    """Decode exact native label/start/stop rows; sample positions are MATLAB-based."""
    label=None;start=None;label_index=None;start_index=None
    for index,event in enumerate(events):
        code=int(event[1]);sample=int(event[2])-1
        if sample<0 or sample>=eeg.shape[1] or int(np.rint(eeg[-1,sample]))!=code:raise ValueError('MAMEM event matrix/status indexing mismatch')
        if 33025<=code<=33029:
            if label is not None:raise ValueError('Unclosed MAMEM trial')
            label=code;label_index=index
        elif code==32779:
            if label is None or start is not None:raise ValueError('Missing MAMEM target/start')
            start=sample;start_index=index
        elif code==32780:
            if start is None or sample-start!=640:raise ValueError('MAMEM trial is not exactly five seconds')
            yield label,start,sample,label_index,start_index,index
            label=None;start=None
    if label is not None or start is not None:raise ValueError('Incomplete final MAMEM trial')


def native_cases(key,cache,subject,recordings):
    """Yield (float64 channels×time, metadata, ordered sensors) in source order."""
    spec=SPECS[key];cache=Path(cache)
    if key=='nakanishi':
        source=f'Nakanishi2015/s{subject}.mat';mat=loadmat(cache/source);data=mat['eeg']
        if data.shape!=(12,8,1114,15):raise ValueError('Nakanishi source axes changed')
        names=['PO7','PO3','POz','PO4','PO8','O1','Oz','O2']
        recordings.append(dict(participant_id=f'{subject:02d}',source_file=source,session_id='0',run_id='0',
            source_shape=list(data.shape),source_sub_i=mat.get('sub_i',np.array([])).tolist(),source_list_sub=mat.get('list_sub',np.array([])).tolist(),
            note='One documented session; no original date, continuous offsets or embedded sensor names. Auxiliary train/ans fields are not the published eeg tensor.'))
        for target in range(12):
            for trial in range(15):
                row=case_row(key,subject,'0','0',source,target*15+trial,target+1,'No fixed partition; original block cross-validation')
                row.update(source_label=target+1,source_array_index=f'eeg[{target},:,:,{trial}]',source_epoch_index=trial,
                           sample_reference='Native epoch-local samples; original continuous offsets unavailable',start_sample=0,end_sample=1114,
                           start_time_seconds=-38/256,end_time_seconds=(1114-38)/256)
                yield np.ascontiguousarray(data[target,:,:,trial],dtype='<f8'),row,names
    elif key=='mamem3':
        for path in sorted((cache/'MAMEM3').glob(f'U{subject:03d}[a-e]i*.mat')):
            match=re.fullmatch(r'U(\d{3})([a-e])(ii|i)\.mat',path.name)
            if not match:continue
            mat=loadmat(path,struct_as_record=False,squeeze_me=True);info=mat['info'];eeg=mat['eeg'];events=mat['events']
            names=list(map(str,info.label));units=list(map(str,info.units))
            if len(names)!=15 or names[-1]!='Status' or eeg.shape[0]!=15 or any(u!='uV' for u in units[:-1]):raise ValueError('MAMEM native sensor names/types/units changed')
            if not np.all(np.asarray(info.samples)[:-1]/float(info.duration)==128):raise ValueError('MAMEM sampling rate changed')
            session,run=match[2],match[3];source=path.relative_to(cache).as_posix();sid=f'{subject:03d}'
            recordings.append(dict(participant_id=sid,source_participant_id=f'U{sid}',session_id=session,run_id=run,source_file=source,
                channel_names=names,channel_types=['EEG']*14+['stim'],units=units,header_startdate=str(info.startdate),header_starttime=str(info.starttime),
                physical_min=np.asarray(info.physicalMin).tolist(),physical_max=np.asarray(info.physicalMax).tolist(),
                source_prefilter=list(map(str,info.prefilter)),source_event_matrix=events.tolist(),source_shape=list(eeg.shape),
                session_definition='Source a–e subsessions/blocks, each split i/ii; MOABB groups these into one session. Header timestamps retained without asserting original visit dates.'))
            for trial,(code,start,end,label_index,start_index,stop_index) in enumerate(mamem_trials(eeg,events)):
                row=case_row(key,subject,session,run,source,trial,code-33024,'Main experiment; adaptation x excluded')
                row.update(participant_id=sid,recording_id=path.stem,source_label=code,source_array_index=f'eeg[0:14,{start}:{end}]',
                    source_epoch_index=trial,event_index=start_index,source_event_sample=start,source_event_sample_1based=start+1,
                    start_sample=start,end_sample=end,start_time_seconds=start/128,end_time_seconds=end/128,
                    sample_reference='Samples within native MAT waveform; event matrix is one-based',source_flash_code=code,
                    source_flash_description=f'Label event row {label_index}, start row {start_index}, stop row {stop_index}')
                yield np.ascontiguousarray(eeg[:-1,start:end],dtype='<f8'),row,names[:-1]
    elif key=='bci2b':
        for phase in ['T','E']:
            source=f'BCIIV2b/B{subject:02d}{phase}.mat';data=np.atleast_1d(loadmat(cache/source,struct_as_record=False,squeeze_me=True)['data'])
            for index,run in enumerate(data):
                session=f'{index+1 if phase=="T" else index+4:02d}{phase}';names=['C3','Cz','C4'];x=np.asarray(run.X,dtype=np.float64)
                if x.shape[1]!=6 or int(run.fs)!=250:raise ValueError('BCI IV2b sensor/rate changed')
                artifacts=np.asarray(run.artifacts).ravel();events=np.asarray(run.trial).ravel();labels=np.asarray(run.y).ravel()
                if len(events)!=len(labels) or len(events)!=len(artifacts):raise ValueError('BCI metadata length mismatch')
                recordings.append(dict(participant_id=f'{subject:02d}',session_id=session,source_file=source,mat_array_index=index,
                    age=getattr(run,'age',None),gender=getattr(run,'gender',None),source_classes=list(run.classes),
                    source_sensors=['C3','Cz','C4','EOG1','EOG2','EOG3'],source_types=['EEG']*3+['EOG']*3,
                    reference='Bipolar EEG derivations; EOG left-mastoid reference; ground Fz per source PDF',source_points=len(x)))
                for i,(event,label) in enumerate(zip(events,labels)):
                    event=int(event)-1;case,start,end=slice_window(x[:,:3],event,750,1125)
                    row=case_row(key,subject,session,'0',source,i,int(label),'train' if phase=='T' else 'evaluation')
                    row.update(split='TRAIN' if phase=='T' else 'TEST',source_label=int(label),source_array_index=f'data[{index}].X[{start}:{end},0:3]',
                        source_event_sample=event,source_event_sample_1based=event+1,start_sample=start,end_sample=end,
                        start_time_seconds=start/250,end_time_seconds=end/250,sample_reference='Samples within original MAT session recording',source_artifact_flag=int(artifacts[i]))
                    yield case,row,names
    elif key=='speller':
        source=f'Speller/s{subject}.mat';data=loadmat(cache/source,struct_as_record=False,squeeze_me=True)[f's{subject}']
        names=['Fz','Cz','P3','Pz','P4','PO7','Oz','PO8']
        for run_name in ['train','test']:
            x=np.asarray(getattr(data,run_name),dtype=np.float64)
            if x.shape[0]!=11 or not np.allclose(np.diff(x[0]),1/256):raise ValueError('Speller source axis/time changed')
            events=pulse_onsets(x[9]);codes=sorted(set(map(int,x[9,events])))
            recordings.append(dict(participant_id=f'{subject:02d}',session_id='0',run_id=run_name,source_file=source,
                source_shape=list(x.shape),flash_codes=codes,flash_mode='individual_character' if len(codes)==36 else 'row_column',
                source_channel_order='Time, eight EEG, Flash, Target',source_eeg_names_evidence='Pinned source loader and publisher description; not embedded in signal matrix'))
            for i,event in enumerate(events):
                raw_label=int(x[10,event]);label=raw_label+1
                if raw_label not in [0,1]:raise ValueError('Speller target encoding changed')
                case,start,end=slice_window(x[1:9].T,event,0,205)
                row=case_row(key,subject,'0',run_name,source,i,label,run_name)
                row.update(split=run_name.upper(),source_label=raw_label,source_flash_code=int(x[9,event]),source_array_index=f'{run_name}[1:9,{start}:{end}]',
                    source_event_sample=int(event),start_sample=start,end_sample=end,start_time_seconds=start/256,end_time_seconds=end/256,
                    sample_reference='Samples within native train/test recording matrix; time column retained in source',source_flash_description='Native stimulus code; exact character/row-column mapping retained as code')
                yield case,row,names
    elif key=='als':
        source=f'ALS/A{subject:02d}.mat';data=loadmat(cache/source,struct_as_record=False,squeeze_me=True)['data'];names=list(map(str,data.channels))
        x=np.asarray(data.X,dtype=np.float64);events=pulse_onsets(data.y_stim);starts=np.asarray(data.trial,dtype=int).ravel()-1
        if len(names)!=8 or len(starts)!=35:raise ValueError('ALS source structure changed')
        recordings.append(dict(participant_id=f'{subject:02d}',session_id='0',run_id='0',source_file=source,
            channels=names,gender=str(data.gender),age=str(data.age),ALSfrs=str(data.ALSfrs),onsetALS=str(data.onsetALS),
            source_classes=list(map(str,data.classes)),source_stimulus_classes=list(map(str,data.classes_stim)),character_trial_start_samples_1based=data.trial.tolist(),
            demographic_note='Values recovered from MAT; original publication PDF demographics are retained separately and can differ'))
        selection=np.searchsorted(starts,events,side='right')-1
        if np.any(selection<0) or not np.all(np.bincount(selection,minlength=35)==120):raise ValueError('ALS character/flash alignment changed')
        for i,(event,trial) in enumerate(zip(events,selection)):
            label=int(data.y[event]);code=int(data.y_stim[event]);case,start,end=slice_window(x,event,0,256)
            if label not in [1,2]:raise ValueError('ALS label changed')
            phase='calibration' if trial<15 else 'feedback'
            row=case_row(key,subject,'0','0',source,i,label,phase)
            row.update(split='TRAIN' if trial<15 else 'TEST',source_label=label,source_character_selection_index=int(trial),source_trial_start_sample_1based=int(starts[trial])+1,
                source_flash_code=code,source_flash_description=str(data.classes_stim[code-1]),source_array_index=f'X[{start}:{end},:]',source_event_sample=int(event),
                start_sample=start,end_sample=end,start_time_seconds=start/256,end_time_seconds=end/256,sample_reference='Samples within original continuous MAT recording')
            yield case,row,names
    else:
        import mne
        archive=cache/f'Zhou2016/sub-{subject}.zip';directory=cache/f'Zhou2016/extracted/sub-{subject}'
        if not directory.exists():
            target=directory.parent.resolve();target.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(archive) as z:
                for item in z.infolist():
                    dest=(target/item.filename).resolve()
                    if not dest.is_relative_to(target):raise ValueError('Unsafe source archive path')
                z.extractall(target)
        for path in sorted(directory.rglob('*_eeg.edf')):
            prefix=str(path)[:-8];source=path.relative_to(cache).as_posix();channels=rows(prefix+'_channels.tsv');names=[r['name'] for r in channels]
            if len(channels)!=14 or any(r['type']!='EEG' for r in channels):raise ValueError('Zhou channel type/count changed')
            with mne.io.read_raw_edf(path,preload=False,verbose='ERROR') as raw:
                if raw.ch_names!=names or raw.info['sfreq']!=250:raise ValueError('EDF channels disagree with source table')
                x=raw.get_data().T.astype(np.float64)*1e6
            match=re.search(r'_ses-([^_]+)_task-[^_]+_run-([^_]+)_',path.name);session,run=match.groups()
            eegmeta=json.loads(Path(prefix+'_eeg.json').read_text());event_rows=rows(prefix+'_events.tsv')
            recordings.append(dict(participant_id=f'{subject:02d}',session_id=session,run_id=run,source_file=source,channels=channels,
                source_eeg_metadata=eegmeta,source_shape=list(x.shape),source_events=len(event_rows),
                source_electrodes=[dict(file=p.name,rows=rows(p)) for p in sorted(path.parent.glob('*_electrodes.tsv'))],
                source_coordinate_systems=[dict(file=p.name,metadata=json.loads(p.read_text())) for p in sorted(path.parent.glob('*_coordsystem.json'))],
                timing_note='BIDS/EDF derivative offsets retained; scans.tsv dates may describe conversion and are not asserted as original acquisition dates'))
            for i,event in enumerate(event_rows):
                label=int(event['value']);sample=int(event['sample'])
                if event['trial_type']!=LABELS[key][str(label)] or abs(float(event['onset'])*250-sample)>0.01:raise ValueError('Zhou event mapping/sample mismatch')
                if float(event['duration'])!=5:raise ValueError('Zhou source event duration changed')
                case,start,end=slice_window(x,sample,0,1250)
                row=case_row(key,subject,session,run,source,i,label,'No fixed source partition')
                row.update(source_label=label,source_array_index=f'EDF[:,{start}:{end}]',source_event_sample=sample,start_sample=start,end_sample=end,
                           start_time_seconds=start/250,end_time_seconds=end/250,sample_reference='Samples within pinned distributed EDF; original acquisition offsets unverified')
                yield case,row,names


def header(spec):
    return (f'# {spec["source"]}; float64 microvolt numeric scale; see sidecars.\n@problemName {spec["name"]}\n'
            '@timestamps false\n@missing false\n@univariate false\n'+f'@dimensions {spec["channels"]}\n@equalLength true\n@seriesLength {spec["points"]}\n@classLabel true '+
            ' '.join(map(str,range(1,spec['classes']+1)))+'\n@data\n')


def validate(folder,spec,split):
    counts=Counter();people=set();hashes=set();duplicates=flat=tiny=0;intervals=defaultdict(list)
    with (folder/f'cases_{split.lower()}.tsv').open(newline='',encoding='utf-8') as f:
        metadata=csv.DictReader(f,delimiter='\t')
        for i,(line,row) in enumerate(itertools.zip_longest(lines(folder/f'{spec["name"]}_{split}.ts'),metadata)):
            if line is None or row is None:raise ValueError('Case/metadata count mismatch')
            body,label=line.strip().rsplit(':',1);x=np.stack([np.fromstring(ch,sep=',',dtype=np.float64) for ch in body.split(':')])
            if x.shape!=(spec['channels'],spec['points']) or not np.isfinite(x).all():raise ValueError('Invalid converted case')
            h=digest_case(x)
            if h!=row['signal_sha256'] or label!=row['label'] or int(row['row'])!=i or row['split']!=split:raise ValueError('Exact case/hash/row/label mismatch')
            duplicates+=h in hashes;hashes.add(h);counts[label]+=1;people.add(row['participant_id'])
            if row['sample_reference']!='Native epoch-local samples; original continuous offsets unavailable':intervals[row['recording_id']].append((int(row['start_sample']),int(row['end_sample'])))
            sd=x.std(axis=1);span=np.ptp(x,axis=1);flat+=int((span==0).sum());tiny+=int(((sd<=1e-7)&(span!=0)).sum())
    if set(counts)!=set(map(str,range(1,spec['classes']+1))):raise ValueError('Missing classes')
    if flat or tiny:raise ValueError(f'Channel quality review required: {flat} constant / {tiny} tiny pairs')
    return dict(cases=sum(counts.values()),shape=[sum(counts.values()),spec['channels'],spec['points']],class_counts=dict(counts),subjects=sorted(people),
                exact_float64_roundtrip=True,metadata_rows_verified=True,finite=True,exact_constant_pairs=flat,aeon_tiny_nonconstant_pairs=tiny,within_split_duplicate_cases=duplicates),hashes,intervals


def overlapping_intervals(train,test):
    total=0
    for recording in set(train)&set(test):
        a=sorted(train[recording]);b=sorted(test[recording]);j=0
        for start,end in a:
            while j<len(b) and b[j][1]<=start:j+=1
            k=j
            while k<len(b) and b[k][0]<end:
                if b[k][1]>start:total+=1
                k+=1
    return total


def smoke(folder,spec):
    from aeon.classification.feature_based import SummaryClassifier
    from aeon.datasets import load_from_ts_file
    from aeon.utils.validation.collection import check_collection_variance
    arrays=[]
    with tempfile.TemporaryDirectory() as tmp:
        for split in ['TRAIN','TEST']:
            p=Path(tmp)/f'{split}.ts';counts=Counter()
            with p.open('w') as f:
                f.write(header(spec))
                for line in lines(folder/f'{spec["name"]}_{split}.ts'):
                    label=line.strip().rsplit(':',1)[1]
                    if counts[label]<3:f.write(line);counts[label]+=1
                    if len(counts)==spec['classes'] and min(counts.values())==3:break
            x,y=load_from_ts_file(p);check_collection_variance(x);arrays.append((x,y))
        clf=SummaryClassifier(random_state=0,n_jobs=1);clf.fit(*arrays[0]);pred=clf.predict(arrays[1][0])
        if len(pred)!=len(arrays[1][1]):raise ValueError('aeon smoke predictions')
    return dict(load_fit_predict=True,train_cases=len(arrays[0][1]),test_cases=len(arrays[1][1]))


def enrich_metadata(metadata,key,cache):
    notes=json.loads(Path(__file__).with_name('small_moabb_source_notes.json').read_text(encoding='utf-8'))[key]
    metadata['documented_source_properties']=notes
    sessions=defaultdict(set);checksums={}
    for recording in metadata['recordings']:
        sessions[recording['participant_id']].add(recording.get('session_id','0'))
        name=recording['source_file'];path=Path(cache)/name
        if path.is_file():
            if name not in checksums:checksums[name]=sha(path)
            recording['source_file_sha256']=checksums[name]
    metadata['sessions_per_subject']={k:len(v) for k,v in sorted(sessions.items())}
    metadata['recording_group_count']=len(metadata['recordings'])
    metadata['recording_group_definition']='Native continuous matrices/EDF recordings; Nakanishi groups are epoched tensors and do not establish original continuous recording counts'
    metadata['window_overlap_policy']='Overlapping P300 windows can occur within a partition; exact recording intervals were checked to exclude cross-partition overlap'
    metadata['source_indexing_note']='Array expressions and start/end sample indices are zero-based with exclusive end; explicitly suffixed _1based fields retain MATLAB marker values'
    return metadata


def convert(key,cache=ROOT,output=Path('D:/Data/EEG'),subjects=None,train_subjects=None,download=True):
    spec=SPECS[key];cache=Path(cache);output=Path(output);folder=output/spec['name']
    if folder.exists():raise FileExistsError(folder)
    subjects=tuple(subjects or range(1,spec['subjects']+1));train=set(train_subjects or range(1,spec.get('train',spec['subjects'])+1))
    if not set(subjects)<=set(range(1,spec['subjects']+1)) or len(set(subjects))!=len(subjects):raise ValueError('Invalid subjects')
    inventory=ensure_sources(key,cache,subjects,download);output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{spec["name"]}-',dir=output) as tmp:
        stage=Path(tmp);counts=Counter();recordings=[];channels=None;source_names=None;keep=None;handles={};tables={};writers={}
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{spec["name"]}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header(spec))
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',encoding='utf-8',newline='');writers[split]=csv.DictWriter(tables[split],FIELDS,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for subject in sorted(subjects):
                for x,row,names in native_cases(key,cache,subject,recordings):
                    if source_names is None:source_names=list(names)
                    if names!=source_names:raise ValueError('Original channel order differs between recordings')
                    if len(names)!=spec.get('source_channels',spec['channels']):raise ValueError('Original source sensor count changed')
                    x,names,keep=select_channels(x,names,spec.get('remove_channels',[]))
                    if spec.get('remove_channels'):row['source_array_index']+='; retained source channel indices '+str(keep)
                    if channels is None:channels=names
                    if names!=channels:raise ValueError('Source channel order differs between recordings; no silent reordering')
                    if x.shape!=(spec['channels'],spec['points']) or not np.isfinite(x).all():raise ValueError('Source dimensions/values changed')
                    split=('TRAIN' if subject in train else 'TEST') if spec['mode']=='subject' else row['split']
                    row.update(split=split,row=counts[split],example_id=f'{spec["name"]}/{row["recording_id"]}/{row["event_index"]}',signal_sha256=digest_case(x),signal_hash_dtype='<f8')
                    writers[split].writerow(row);handles[split].write(format_case(x)+':'+row['label']+'\n');counts[split]+=1
                print(f'{spec["name"]}: participant {subject:02d}, cases {dict(counts)}',flush=True)
        finally:
            for h in [*handles.values(),*tables.values()]:h.close()
        reports={};hashes={};intervals={}
        for split in ['TRAIN','TEST']:
            reports[split],hashes[split],intervals[split]=validate(stage,spec,split);print(f'{spec["name"]} {split}: full float64 readback passed',flush=True)
        duplicates=len(hashes['TRAIN']&hashes['TEST']);overlaps=overlapping_intervals(intervals['TRAIN'],intervals['TEST']);shared=set(reports['TRAIN']['subjects'])&set(reports['TEST']['subjects'])
        if duplicates or overlaps or (shared and spec['mode']=='subject'):raise ValueError(f'Cross-split leakage: duplicates={duplicates}, overlapping windows={overlaps}, shared subjects={shared}')
        validation=dict(partitions=reports,cross_split_duplicate_cases=duplicates,cross_split_overlapping_intervals=overlaps,shared_subjects=sorted(shared),
            shared_subjects_intentional=bool(shared),split_unit=spec['mode'],channel_names_and_order_verified_for_all_recordings=True,aeon=smoke(stage,spec))
        split_note={'nakanishi':'Fixed subject split: 01–08 TRAIN, 09–10 TEST; no official fixed source split',
                    'zhou':'Fixed subject split: 01–03 TRAIN, 04 TEST; no official fixed source split',
                    'bci2b':'Original T/E protocol: first three sessions TRAIN, last two TEST; subjects intentionally shared',
                    'speller':'Original train/test recording runs; subjects intentionally shared',
                    'als':'Original calibration/feedback: first 15 character selections TRAIN, remaining 20 TEST; subjects intentionally shared',
                    'mamem3':'Fixed subject split: 001–008 TRAIN, 009–011 TEST; five source subsessions with both halves retained, adaptation x excluded'}[key]
        unknown=['No original acquisition dates verified; distributed demographics/timestamps are preserved as source evidence',
                 'Montage coordinates are unavailable or template-derived unless explicitly identified otherwise']
        if key=='nakanishi':unknown+=['Original continuous recording offsets and independently embedded channel names unavailable','No explicit original data redistribution licence found']
        if key=='speller':unknown+=['Exact character-selection boundaries not recovered; event and flash codes retained','EEG channel names recovered from documented loader/source, not embedded in matrix']
        if key=='zhou':unknown+=['EDF is a distributed BIDS derivative; original pre-conversion precision and raw-file sample correspondence are not established','Distributed scan dates may be conversion timestamps; coordinates may be template-derived']
        local_processing='No filtering, demeaning, reference change or resampling. EEG selection and fixed half-open sample windows; exact float64 shortest-roundtrip decimal output.'
        if key=='zhou':local_processing+=' MNE-calibrated volts multiplied by 1e6 to microvolts using float64.'
        if spec.get('remove_channels'):local_processing+=' Remove Fp2 (original axis 1) globally: three complete source windows are flat at EDF saturation limits; all cases retained.'
        sensors=[dict(array_index=i,name=n,type='EEG',units='uV',source_array_index=keep[i]+1 if key=='speller' else keep[i],
            identity_evidence='Native channels.tsv and EDF header' if key=='zhou' else 'Native MAT info.label field' if key=='mamem3' else 'Native MAT channels field' if key=='als' else 'Source description / pinned loader channel order; no sensor names embedded in MAT signal array',
            derivation='Bipolar' if key=='bci2b' else None) for i,n in enumerate(channels)]
        metadata=dict(name=spec['name'],source_dataset=spec['source'],source_doi=spec['doi'],licence=spec['licence'],release_status='Local research preparation; public redistribution not approved by this conversion',
            shapes={s.lower():reports[s]['shape'] for s in reports},subjects=len(subjects),channel_count=spec['channels'],channel_names=channels,sensors=sensors,
            source_channel_names=source_names,source_channel_count=len(source_names),kept_source_channel_indices=keep,
            removed_channels=[dict(source_array_index=i,name=source_names[i],reason='Three constant test windows at the original EDF physical limits; global removal under authorised constant-channel cleanup',evidence='source_metadata/zhou-flat-channel-source-report.json') for i in spec.get('remove_channels',[])],
            dtype='float64',units='uV',sampling_frequency_hz=spec['hz'],window_samples=spec['points'],window_seconds=spec['points']/spec['hz'],
            original_sampling_frequency_hz_documented=2048 if key=='nakanishi' else spec['hz'],
            original_frequency_evidence='Source paper/loader acquisition description; native release is already 256 Hz' if key=='nakanishi' else 'Native source header/rate or documented acquisition rate; no local resampling',
            montage_positions='Source geometry/coordinate sidecars retained; Zhou coordinates embedded in recording snapshots. No invented individual coordinates or standard-name substitution.',
            label_mapping=LABELS[key],source_label_note='SpellerFlashes raw labels 0/1 encode to 1/2. WirelessFlicker codes 33025–33029 encode to 1–5. Original codes retained in source_label; other source codes unchanged.',
            class_distributions={s.lower():reports[s]['class_counts'] for s in reports},split_definition=split_note,validation_partition=None,
            actual_subjects={'train':reports['TRAIN']['subjects'],'test':reports['TEST']['subjects']},preprocessing=local_processing,
            window_offsets_from_event_samples=750 if key=='bci2b' else 0,window_bounds='Start inclusive, end exclusive',
            reference_evidence='Source recording snapshots and original descriptions retained; missing reference information is not inferred as directly recovered',
            units_evidence='Native numerical microvolt scale as interpreted by pinned source loaders; Zhou uses explicit MNE V→uV conversion',
            unknown_or_inconsistent_metadata=unknown,recordings=recordings,
            metadata_evidence=dict(direct='Array shapes, numerical samples, indices, event codes, stimulus codes, artifact flags and available native demographic/channel fields',
                                   documented='Task timing, non-embedded sensor labels, reference and original acquisition properties; see source_metadata'))
        enrich_metadata(metadata,key,cache)
        dump(stage/f'{spec["name"]}_metadata.json',metadata);dump(stage/f'{spec["name"]}_validation.json',validation)
        dump(stage/'metadata-completeness.json',dict(available=metadata['metadata_evidence'],missing_or_inconsistent=unknown))
        (stage/'channels.txt').write_text(', '.join(channels)+'\n')
        with (stage/'channels.tsv').open('w',newline='') as f:
            w=csv.DictWriter(f,list(sensors[0]),delimiter='\t');w.writeheader();w.writerows(sensors)
        evidence=stage/'source_metadata';evidence.mkdir()
        flat_report=Path(__file__).parents[1]/'docs/zhou-flat-channel-source-report.json'
        if key=='zhou' and flat_report.is_file():shutil.copy2(flat_report,evidence/flat_report.name)
        for p in cache.iterdir():
            if p.is_file():shutil.copy2(p,evidence/p.name)
        if key=='nakanishi':
            for name in ['README.md','tree.json']:shutil.copy2(cache/'Nakanishi2015'/name,evidence/('nakanishi-'+name))
        if key=='mamem3':
            for p in (cache/'MAMEM3').glob('*.pdf'):shutil.copy2(p,evidence/p.name)
        if key=='zhou':
            for p in (cache/'Zhou2016').iterdir():
                if p.is_file() and p.suffix!='.zip':shutil.copy2(p,evidence/p.name)
            for subject in subjects:
                for p in (cache/f'Zhou2016/extracted/sub-{subject}').rglob('*'):
                    if p.is_file() and p.suffix!='.edf':
                        dest=evidence/p.relative_to(cache/'Zhou2016/extracted');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        (stage/'ATTRIBUTION.txt').write_text(f'{spec["source"]}. Paper DOI: {spec["doi"]}. Data terms: {spec["licence"]}. Original descriptions and licence evidence retained under source_metadata/.\nChanges: {local_processing}\n{split_note}. No archived validation split.\n')
        (stage/f'README_{spec["name"]}.md').write_text(f'# {spec["name"]}\n\n{spec["source"]}: {spec["classes"]} classes, {spec["channels"]} EEG channels, {spec["points"]} points at {spec["hz"]} Hz. Values in microvolt numeric scale; exact float64 decimal export.\n\n{split_note}. See metadata for actual membership/counts. Case TSV order exactly matches the .ts rows. Read IDs as strings. Source sample offsets and original labels/partitions are retained where available. No synthetic Raw timelines are exported.\n\n{local_processing}\n\nP300 windows can overlap within a recording; no signal duplicates or overlapping recording intervals cross TRAIN/TEST. Source cohorts/protocols, auxiliary sensors, artifact flags, sensor positions and missing metadata are documented in the metadata. Source data remain subject to their original terms. Public redistribution is not approved by this conversion.\n')
        code=stage/'conversion_code';code.mkdir()
        for name in ['prepare_small_moabb.py','prepare_wang.py','prepare_moabb.py','requirements-moabb.txt','small_moabb_source_notes.json']:shutil.copy2(Path(__file__).with_name(name),code/name)
        lock=Path(__file__).parents[1]/'docs/small-moabb-source-lock.json'
        if lock.is_file():shutil.copy2(lock,evidence/lock.name)
        dump(stage/f'{spec["name"]}_manifest.json',dict(name=spec['name'],moabb_revision=MOABB_REVISION,source_revision=NAKA_REVISION if key=='nakanishi' else 'Zenodo 16534752' if key=='zhou' else 'Figshare 3413851 version 3' if key=='mamem3' else 'Publisher snapshot pinned by per-file SHA256 receipt',
            source_files=inventory,licence=spec['licence'],split=split_note,conversion=local_processing,validation=validation,
            artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(folder)
    return dict(dataset=spec['name'],source_key=key,train_cases=counts['TRAIN'],test_cases=counts['TEST'],subjects=len(subjects),channels=spec['channels'],
        timepoints=spec['points'],classes=spec['classes'],frequency=spec['hz'],size_GB=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9,licence=spec['licence'],validation=validation)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--datasets',nargs='+',choices=list(SPECS),default=list(SPECS));p.add_argument('--cache',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--offline',action='store_true')
    a=p.parse_args();results=[]
    for key in a.datasets:
        result=convert(key,a.cache,a.output,download=not a.offline);results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='validation'}),flush=True)
        dump(Path(__file__).parents[1]/'docs/small-moabb-local-results.json',results)


if __name__=='__main__':main()
