"""Convert the four cached open MOABB collections, without further downloads.

Native recordings -> per-recording compressed NPZ intermediates -> exact float64
.ts files and ordered case/sensor/provenance sidecars. Output folders are staged
and published only after validation. Original data are never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import warnings
import zipfile
import zlib

import numpy as np
from scipy.io import loadmat

from tools.prepare_moabb import dump as _dump, sha
from tools.prepare_small_moabb import header, validate, overlapping_intervals, smoke
from tools.prepare_wang import digest_case, format_case

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'
SPECS = {
    'rodrigues': dict(name='RestingEyeState', source='Rodrigues2017 / Alpha Waves',
        cache='Rodrigues2017', hz=512, points=5120, classes=2, train_subjects=14,
        labels={'1':'eyes_closed','2':'eyes_open'}, doi='10.5281/zenodo.2605110',
        paper='Cattan, Rodrigues and Congedo, EEG Alpha Waves Dataset, HAL hal-02086581',
        note='Native MAT microvolt values unchanged. Source header names/order retained. Original loader excludes participant 07; native 10-second windows for 07 also overlap opposite-state onsets. Right-earlobe reference and AFz ground are documented, not file-header fields.'),
    'brainform': dict(name='GameTargets', source='RomaniBF2025ERP / BrainForm calibration',
        cache='RomaniBF2025ERP', hz=250, points=225, classes=2, train_subjects=17,
        labels={'1':'calibration_target_T1','2':'calibration_nontarget_T2_to_T10'}, doi='10.5281/zenodo.17225966',
        paper='Romani et al., BrainForm: a Serious Game for BCI Training and Data Collection, arXiv:2510.10169',
        note='First 600 calibration flashes of each of two main recordings only. T1 -> target, T2-T10 -> nontarget follows pinned MOABB mapping; native events identify stimulus, not an explicit attended-target field. Only participants with both main recordings included. EDF calibrated volts multiplied by 1e6; no other numerical processing. Optional Extra and inference phases excluded. BIDS session labels are conditions within one visit, not separate-day visits.'),
    'castillos': dict(name='CodedFlickerTargets', source='Castillos2023 four-condition target classification',
        cache='Castillos2023', hz=500, points=1100, classes=4, train_subjects=9,
        labels={str(i):f'attended_target_{i}' for i in range(1,5)}, doi='10.5281/zenodo.8255618',
        paper='Cabrera Castillos et al. (2023), NeuroImage, DOI 10.1016/j.neuroimage.2023.120446',
        note='All four separately recorded code/contrast conditions combined. Full 2.2-second target epochs, not binary bit epochs. Native float32 FDT microvolt values cast to float64. The 28 named electrodes shared by two native 32-channel layouts are explicitly selected/reordered by matching native labels; layout-only electrodes excluded. SET internal FDT names may be stale; pair by actual archive directory/stem and require exact byte length. Native reference field retained; source acquisition documents FCz. No demeaning or MOABB baseline correction.'),
    'kumar': dict(name='ImaginedHandTraining', source='Kumar2024 longitudinal bar-feedback motor imagination',
        cache='Kumar2024', hz=512, points=2560, classes=2, train_subjects=14,
        labels={'1':'imagined_left_hand','2':'imagined_right_hand'}, doi='10.5281/zenodo.10694880',
        paper='Kumar et al. (2024), Transfer learning promotes acquisition of individual BCI skills, DOI 10.1093/pnasnexus/pgae076',
        note='Offline and Online bar-feedback GDF recordings; Race excluded. Native GDF annotation 769/770 starts 5-second windows. Keep actual source IDs (01-09,11-19), native uppercase sensor names and order. Header unit multipliers are 1 with malformed +/-float32-max physical/digital limits; numerical EEG values are interpreted as microvolts following pinned loader/source documentation, not multiplied by 1e6. Native header/calibration evidence retained. No filtering/resampling/reference change.'),
}
SHARED = 'Fp1 Fz F3 F7 FC5 FC1 C3 T7 CP5 CP1 Pz P3 P7 O1 Oz O2 P8 P4 CP2 CP6 T8 C4 Cz FC2 FC6 F8 F4 Fp2'.split()


def native_json(value):
    """Convert recovered NumPy header fields to JSON; missing coordinates -> null."""
    if isinstance(value,np.ndarray):return native_json(value.tolist())
    if isinstance(value,np.generic):return native_json(value.item())
    if isinstance(value,dict):return {str(k):native_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [native_json(v) for v in value]
    if isinstance(value,float) and not np.isfinite(value):return None
    return value


def dump(path,value):
    _dump(path,native_json(value))


def training_people(key,people,count):
    if key=='kumar':
        gr=sorted(p for p in people if int(p)<=9)
        par=sorted(p for p in people if int(p)>9)
        if len(gr)!=9 or len(par)!=9:raise ValueError('Kumar group membership differs from source protocol')
        return set(gr[:7]+par[:7])
    return set(sorted(people)[:count])

def case_partition(spec,row,training_subjects):
    split=spec['case_splitter'](row) if spec.get('case_splitter') else 'TRAIN' if row['participant_id'] in training_subjects else 'TEST'
    if split not in ['TRAIN','TEST']:raise ValueError('Archive has only TRAIN and TEST partitions')
    return split

def partition_people(spec,key,people,chunks):
    if spec.get('case_splitter'):
        groups={'TRAIN':set(),'TEST':set()}
        for _,rows in chunks:
            for row in rows:groups[case_partition(spec,row,set())].add(row['participant_id'])
        return groups['TRAIN'],groups['TEST']
    train=spec['splitter'](people,chunks) if spec.get('splitter') else training_people(key,people,spec['train_subjects'])
    return train,set(people)-train


def table(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def extract_selected(archive, root, select):
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if item.is_dir() or not select(item.filename): continue
            target = (root / item.filename).resolve()
            if not target.is_relative_to(root): raise ValueError('Unsafe archive member')
            if target.is_file() and target.stat().st_size == item.file_size:
                crc=0
                with target.open('rb') as cached:
                    for block in iter(lambda:cached.read(1024*1024),b''):crc=zlib.crc32(block,crc)
                if crc==item.CRC:continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as src, target.open('wb') as dst: shutil.copyfileobj(src,dst,1024*1024)
    return root


def crop(data, start, points):
    start = int(start); end = start + points
    if start < 0 or end > data.shape[1]: raise ValueError('Incomplete source epoch')
    x = np.ascontiguousarray(data[:,start:end], dtype='<f8')
    if not np.isfinite(x).all(): raise ValueError('Nonfinite source data')
    return x


def pulse_onsets(values):
    values = np.asarray(values)
    return np.flatnonzero((values>0) & np.r_[True, values[1:]!=values[:-1]])


def gdf_files(root):
    return sorted({p.resolve() for p in Path(root).rglob('*') if p.is_file() and p.suffix.lower()=='.gdf'})

def store_intermediate(path,x):
    """Reuse an NPZ only after exact comparison with freshly decoded source cases."""
    path=Path(path)
    if path.exists():
        try:
            with np.load(path,allow_pickle=False) as saved:
                if saved.files==['X']:
                    previous=saved['X']
                    if previous.shape==x.shape and previous.dtype==x.dtype and np.array_equal(np.ascontiguousarray(previous).view('u1'),np.ascontiguousarray(x).view('u1')):return
        except (OSError,ValueError,zipfile.BadZipFile):pass
    np.savez_compressed(path,X=x)


def base_row(person, session, run, file, event, start, points, hz, original, encoded):
    rid = file.replace('\\','/')
    return dict(participant_id=person, session_id=session, run_id=run, recording_id=rid,
        source_file=rid, source_epoch_index=event, event_index=event,
        start_sample=int(start), end_sample=int(start)+points,
        start_time_seconds=int(start)/hz, end_time_seconds=(int(start)+points)/hz,
        source_event_sample=int(start), source_event_sample_1based='',
        sample_reference='Native recording samples, zero-based, end exclusive',
        source_label=str(original), label=str(encoded), original_partition='unsplit')


def rod_records(cache, spec):
    names = loadmat(cache/'header.mat', squeeze_me=True)['Header'].tolist()
    if len(names)!=19 or names[0]!='Time' or names[-2:]!=['EyesClosed','EyesOpened']:
        raise ValueError('Unexpected native Alpha Waves header')
    demographic = loadmat(cache/'demographic.mat', squeeze_me=True)
    demo = {k:np.asarray(v).tolist() for k,v in demographic.items() if not k.startswith('__')}
    for person in [i for i in range(1,21) if i!=7]:
        path=cache/f'subject_{person:02d}.mat'; a=loadmat(path)['SIGNAL']
        if a.ndim!=2 or a.shape[1]!=19: raise ValueError('Native Alpha Waves columns changed')
        events=a[:,17]+2*a[:,18]; starts=pulse_onsets(events)
        if len(starts)!=10 or Counter(events[starts])!={1:5,2:5}: raise ValueError('Alpha Waves marker protocol mismatch')
        if (np.diff(starts)<spec['points']).any(): raise ValueError('Eye-state windows cross another condition onset')
        data=a[:,1:17].T; rows=[]; values=[]
        for event,start in enumerate(starts):
            label=int(events[start]); row=base_row(f'{person:02d}','0','0',path.name,event,start,spec['points'],spec['hz'],label,label)
            row.update(source_timestamp_start=float(a[start,0]),source_timestamp_end=float(a[start+spec['points']-1,0]),
                       source_array_index=f'SIGNAL[{start}:{start+spec["points"]},1:17].T', event_evidence='Native EyesClosed/EyesOpened marker columns')
            rows.append(row);values.append(crop(data,start,spec['points']))
        info=dict(source_file=path.name,participant_id=f'{person:02d}',session_id='0',run_id='0',
            native_shape=list(a.shape),native_channel_names=names[1:17],source_column_indices=list(range(1,17)),
            sensor_types=['EEG']*16,source_file_sha256=sha(path),native_demographic_table=demo)
        yield np.stack(values),rows,names[1:17],info


def mne_info(raw):
    extra=raw._raw_extras[0]
    return dict(native_channel_names=raw.ch_names,native_channel_types=raw.get_channel_types(),
        mne_version=__import__('mne').__version__,sampling_frequency_hz=raw.info['sfreq'],
        native_samples=raw.n_times,original_units=raw._orig_units,
        unit_multipliers=np.asarray(extra.get('units',[])).tolist(),
        physical_min=np.asarray(extra.get('physical_min',[])).tolist(),
        physical_max=np.asarray(extra.get('physical_max',[])).tolist(),
        digital_min=np.asarray(extra.get('digital_min',[])).tolist(),
        digital_max=np.asarray(extra.get('digital_max',[])).tolist(),
        annotations=[dict(onset=float(o),duration=float(d),description=str(s)) for o,d,s in zip(raw.annotations.onset,raw.annotations.duration,raw.annotations.description)])


def main_brain_files(root):
    groups={}
    for path in sorted(root.rglob('*_eeg.edf')):
        person=path.parts[-4][4:];session=path.parts[-3][4:]
        if 'Extra' in session or 'Failed' in session: continue
        groups.setdefault(person,[]).append((session,path))
    complete={p:fs for p,fs in groups.items() if len(fs)==2 and {s[0] for s,_ in fs}=={'0','1'}}
    return complete,sorted(set(groups)-set(complete))


def brain_records(cache,spec):
    import mne
    root=extract_selected(cache/'BIDS.zip',cache/'extracted',lambda n:n.startswith('BIDS/'))/'BIDS'
    groups,excluded=main_brain_files(root)
    if len(groups)!=22: raise ValueError('Expected 22 participants with both main sessions')
    for person, files in sorted(groups.items()):
        for session,path in sorted(files):
            prefix=path.with_name(path.name[:-8]); events=table(str(prefix)+'_events.tsv'); channels=table(str(prefix)+'_channels.tsv')
            props=json.loads(Path(str(prefix)+'_eeg.json').read_text(encoding='utf-8-sig'))
            if len(events)<600: raise ValueError('Incomplete calibration')
            selected=events[:600]
            if Counter(e['trial_type'] for e in selected)!={f'T{i}':60 for i in range(1,11)}: raise ValueError('Calibration source codes changed')
            raw=mne.io.read_raw_edf(path,preload=True,verbose=False)
            idx=[i for i,c in enumerate(channels) if c['type']=='EEG'];names=[channels[i]['name'] for i in idx]
            if raw.ch_names!=[c['name'] for c in channels] or len(idx)!=8 or raw.info['sfreq']!=250:
                raise ValueError('BrainForm header/channel table mismatch')
            data=raw.get_data(picks=idx).astype(np.float64)*1e6
            rows=[];values=[]
            for event,e in enumerate(selected):
                start=int(e['sample']);onset=float(e['onset'])
                if abs(start-onset*250)>0.501: raise ValueError('Native event onset/sample disagree')
                for o,d,s in zip(raw.annotations.onset,raw.annotations.duration,raw.annotations.description):
                    if s.startswith('BAD') and start/250<o+d and (start+225)/250>o: raise ValueError('Calibration overlaps bad acquisition interval')
                label=1 if e['trial_type']=='T1' else 2
                row=base_row(person,session,'calibration',path.relative_to(root).as_posix(),event,start,225,250,e['trial_type'],label)
                row.update(native_event_code=e['value'],source_trial_type=e['trial_type'],source_event_onset=onset,
                    source_array_index=f'EDF EEG samples [{start}:{start+225}]',
                    event_evidence='Native BIDS event sample; binary target mapping follows pinned MOABB, not an explicit attended-target field',
                    visual_texture='grain' if 'grain' in session else 'checkerboard')
                rows.append(row);values.append(crop(data,start,225))
            positions=Path(str(prefix)+'_space-CapTrak_electrodes.tsv')
            # Actual BIDS electrode sidecars are named without task suffix.
            electrodes=list(path.parent.glob('*_electrodes.tsv'))
            coords=list(path.parent.glob('*_coordsystem.json'))
            info=dict(mne_info(raw),source_file=path.relative_to(root).as_posix(),participant_id=person,session_id=session,run_id='calibration',
                source_eeg_indices=idx,source_file_sha256=sha(path),bids_eeg=props,
                native_channels=channels, native_electrodes=table(electrodes[0]) if electrodes else [],
                native_coordinate_system=json.loads(coords[0].read_text()) if coords else None,
                excluded_partial_participants=excluded,excluded_extra_inference=True)
            yield np.stack(values),rows,names,info


def harmonise_castillos(names):
    if len(names)!=len(set(names)) or len(names)!=32: raise ValueError('Invalid Castillos sensor labels')
    extra=set(names)-set(SHARED)
    if extra not in [set('F9 P9 P10 F10'.split()),set('FT9 TP9 TP10 FT10'.split())]:
        raise ValueError('Unknown Castillos native sensor layout')
    return [names.index(n) for n in SHARED]


def cast_records(cache,spec):
    with zipfile.ZipFile(cache/'4Class-CVEP.zip') as z:
        files=[n for n in z.namelist() if n.endswith('.set')]
        files.sort(key=lambda n:(int(re.search(r'/P(\d+)/',n)[1]),Path(n).stem))
        if len(files)!=48: raise ValueError('Expected 48 Castillos recordings')
        for file in files:
            eeg=loadmat(io.BytesIO(z.read(file)),simplify_cells=True)
            eeg=eeg.get('EEG',eeg)  # Both top-level and EEG-struct SET variants are distributed.
            names=[c['labels'] for c in eeg['chanlocs']];keep=harmonise_castillos(names)
            partner=str(Path(file).with_suffix('.fdt')).replace('\\','/')
            source=np.frombuffer(z.read(partner),dtype='<f4')
            if source.size!=eeg['nbchan']*eeg['pnts'] or eeg['srate']!=500 or eeg['trials']!=1:raise ValueError('Castillos SET/FDT mismatch')
            data=source.reshape(int(eeg['pnts']),32).T[keep]
            person=f'{int(re.search(r"/P(\d+)/",file)[1]):02d}';condition=Path(file).stem.split('_',1)[1]
            rows=[];values=[]
            for event,e in enumerate(eeg['event']):
                description=str(e['type']);match=re.search(r'_([1-4])$',description)
                if not match:raise ValueError('Unexpected Castillos event; cannot infer target')
                latency=float(e['latency']);start=int(np.rint(latency))-1;label=match[1]
                row=base_row(person,'0',condition,file,event,start,1100,500,label,label)
                row.update(source_event_sample_1based=latency,native_event_description=description,
                    source_participant_id_token=Path(file).parts[-2],
                    source_fdt_file=partner,condition=condition,code_type='burst' if condition.startswith('burst') else 'm_sequence',
                    contrast_percent=40 if condition.endswith('40') else 100,
                    source_array_index=f'FDT native axes {keep}, samples [{start}:{start+1100}]',
                    event_evidence='Native EEGLAB event target suffix, one-based latency converted to zero-based')
                rows.append(row);values.append(crop(data,start,1100))
            if len(rows)!=60 or Counter(r['label'] for r in rows)!={str(i):15 for i in range(1,5)}:raise ValueError('Castillos target counts changed')
            def clean(v):
                if isinstance(v,np.ndarray):return v.tolist()
                if isinstance(v,np.generic):return v.item()
                if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
                if isinstance(v,list):return [clean(x) for x in v]
                return v
            info=dict(source_file=file,participant_id=person,session_id='0',run_id=condition,
                native_channel_names=names,source_eeg_indices=keep,excluded_layout_only=[n for n in names if n not in SHARED],
                native_chanlocs=clean(eeg['chanlocs']),native_reference=clean(eeg['ref']),
                native_fdt_reference=str(eeg['data']),actual_paired_fdt=partner,
                native_fdt_reference_differs=Path(str(eeg['data'])).name!=Path(partner).name,
                set_sha256=__import__('hashlib').sha256(z.read(file)).hexdigest(),
                fdt_sha256=__import__('hashlib').sha256(z.read(partner)).hexdigest())
            yield np.stack(values),rows,SHARED,info


def kumar_records(cache,spec):
    import mne
    root=extract_selected(cache/'Online_Offline_Race.zip',cache/'extracted',lambda n:n.startswith(('Offline/','Online/')) and n.lower().endswith('.gdf'))
    # Windows glob is case-insensitive; combining *.gdf and *.GDF duplicates files.
    files=gdf_files(root)
    if len(files)!=360:raise ValueError(f'Expected 360 distinct Kumar bar recordings, got {len(files)}')
    def identity(path):
        m=re.search(r'Subject_0*(\d+).*_s(\d+)_r(\d+)_',path.name,re.I)
        if not m:raise ValueError(f'Unknown Kumar file identity {path}')
        return int(m[1]),int(m[2]),int(m[3]),path.as_posix()
    files.sort(key=identity)
    for path in files:
        person,session,run,_=identity(path)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw=mne.io.read_raw_gdf(path,preload=True,verbose=False)
        if raw.info['sfreq']!=512 or len(raw.ch_names)!=26:raise ValueError('Kumar native schema mismatch')
        names=raw.ch_names[:22]
        if raw.ch_names[22:]!=['sens1','sens2','sens3','Status']:raise ValueError('Kumar auxiliary schema changed')
        # Preserve decoded float32 native numerical microvolts, avoiding a V roundtrip.
        extra=raw._raw_extras[0]
        if not np.all(np.asarray(extra['units'])[:22]==1):raise ValueError('Kumar GDF units changed; review scaling')
        if not np.all(np.asarray(extra['physical_max'])[:22]>1e30):raise ValueError('Kumar GDF header no longer matches reviewed malformed limits')
        data=raw.get_data(picks=list(range(22)))
        rows=[];values=[]
        for event,(onset,description) in enumerate(zip(raw.annotations.onset,raw.annotations.description)):
            if description not in ['769','770']:continue
            start=int(raw.time_as_index([onset],use_rounding=True)[0]);label='1' if description=='769' else '2'
            row=base_row(f'{person:02d}',f'{session:03d}',f'{run:03d}',path.relative_to(root).as_posix(),event,start,2560,512,description,label)
            row.update(source_event_onset=float(onset),source_array_index=f'GDF channels[0:22], samples[{start}:{start+2560}]',
                source_participant_id_token=re.search(r'Subject_(\d+)',path.name)[1],
                source_session_id_token=re.search(r'_s(\d+)_',path.name)[1],
                group='GR' if person<=9 else 'PAR',phase='Offline' if session==1 else 'Online',
                event_evidence='Native GDF annotation 769/770; no relabeling of feedback sub-events')
            rows.append(row)
        if len(rows)!=20 or Counter(r['label'] for r in rows)!={'1':10,'2':10}:raise ValueError(f'Kumar unexpected run trials: {path}, {len(rows)}')
        excluded=[dict(r,reason='Recording ends before complete 5-second source-event window',available_samples=raw.n_times-r['start_sample']) for r in rows if r['end_sample']>raw.n_times]
        rows=[r for r in rows if r['end_sample']<=raw.n_times]
        if not rows:raise ValueError('No complete Kumar trials in source recording')
        values=[crop(data,r['start_sample'],2560) for r in rows]
        info=dict(mne_info(raw),source_file=path.relative_to(root).as_posix(),source_file_sha256=sha(path),
            participant_id=f'{person:02d}',session_id=f'{session:03d}',run_id=f'{run:03d}',source_eeg_indices=list(range(22)),
            auxiliary_channel_types_documented={'sens1':'EOG','sens2':'EOG','sens3':'EOG','Status':'stim'},
            source_trial_count=20,excluded_incomplete_cases=excluded,
            units_interpretation='Native numerical EEG microvolts; malformed GDF calibration retained as evidence; follows pinned loader correction')
        yield np.stack(values),rows,names,info


READERS={'rodrigues':rod_records,'brainform':brain_records,'castillos':cast_records,'kumar':kumar_records}


def preflight_case_hashes(x,rows,seen):
    """Fail on exact source-case copies before writing a potentially large export."""
    for case,row in zip(x,rows,strict=True):
        identity=(row.get('source_file'),row.get('event_index'),row.get('label'))
        digest=digest_case(case)
        if digest in seen:raise ValueError(f'Duplicate source case before export: {seen[digest]} and {identity}; source-specific review required')
        seen[digest]=identity


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG')):
    spec=dict(SPECS[key]);cache=Path(cache_root)/spec['cache'];output=Path(output);final=output/spec['name']
    if final.exists():raise FileExistsError(final)
    receipt=json.loads((cache/'download-receipt.json').read_text())
    if receipt['licence']!=spec.get('licence','CC-BY-4.0'):raise ValueError('Unexpected data licence')
    for f in receipt['files']:
        p=cache/f['name']
        if p.stat().st_size!=f['bytes'] or sha(p)!=f['sha256']:raise ValueError('Cached source changed')
    intermediates=cache/spec.get('intermediate_directory','classification-intermediate');intermediates.mkdir(exist_ok=True)
    chunks=[];channels=None;recordings=[];flat=None;tiny=None;case_count=0;source_case_hashes={}
    for idx,(x,rows,names,info) in enumerate(READERS[key](cache,spec)):
        if channels is None:channels=list(names);flat=np.zeros(len(names),dtype=int);tiny=flat.copy()
        if list(names)!=channels:raise ValueError('Unharmonised channel order difference')
        if x.shape!=(len(rows),len(channels),spec['points']) or not np.isfinite(x).all():raise ValueError('Invalid native case shape/values')
        preflight_case_hashes(x,rows,source_case_hashes)
        flat+=(np.ptp(x,axis=2)==0).sum(axis=0);tiny+=(x.std(axis=2)<=1e-7).sum(axis=0)
        chunk=intermediates/f'recording-{idx:04d}.npz'
        store_intermediate(chunk,x)
        chunks.append((chunk,rows));recordings.append(info);case_count+=len(rows)
        if (idx+1)%10==0:print(f'{spec["name"]}: {idx+1} recordings / {case_count} cases inspected',flush=True)
    del source_case_hashes
    if not chunks:raise ValueError('No cases')
    removed=np.flatnonzero(tiny>0).tolist();keep=[i for i in range(len(channels)) if i not in removed]
    if not keep:raise ValueError('All sensors constant/effectively flat in some cases; source review required')
    people=sorted({r['participant_id'] for _,rows in chunks for r in rows})
    train,test=partition_people(spec,key,people,chunks)
    if not train or not test:raise ValueError('Empty subject partition')
    spec['channels']=len(keep);names=[channels[i] for i in keep]
    quality=dict(threshold_std_uV=1e-7,constant_case_counts=flat.tolist(),effectively_flat_case_counts=tiny.tolist(),
        source_channel_names=channels,removed_indices=removed,policy='Remove sensor globally if any retained trial has std <= 1e-7 uV')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.'+spec['name']+'-',dir=output) as tmp:
        stage=Path(tmp);handles={};tables={};writers={};counts=Counter()
        fields=sorted(set().union(*(set(r) for _,rows in chunks for r in rows))|{'split','row','example_id','signal_sha256','signal_hash_dtype','label_description'})
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{spec["name"]}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header(spec))
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',encoding='utf-8',newline='')
                writers[split]=csv.DictWriter(tables[split],fields,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for chunk,rows in chunks:
                with np.load(chunk,allow_pickle=False) as saved:x=saved['X']
                for xcase,row in zip(x,rows,strict=True):
                    xcase=np.ascontiguousarray(xcase[keep],dtype='<f8');split=case_partition(spec,row,train)
                    row.update(split=split,row=counts[split],example_id=f'{spec["name"]}/{row["recording_id"]}/{row["event_index"]}',
                        signal_sha256=digest_case(xcase),signal_hash_dtype='<f8',label_description=spec['labels'][row['label']])
                    writers[split].writerow(row);handles[split].write(format_case(xcase)+':'+row['label']+'\n');counts[split]+=1
                print(f'{spec["name"]}: exported {sum(counts.values())}/{case_count}',flush=True)
        finally:
            for h in [*handles.values(),*tables.values()]:h.close()
        reports={};hashes={};intervals={}
        for split in ['TRAIN','TEST']:
            reports[split],hashes[split],intervals[split]=validate(stage,spec,split)
            print(f'{spec["name"]}: {split} exact readback passed',flush=True)
        duplicates=len(hashes['TRAIN']&hashes['TEST']);overlaps=overlapping_intervals(intervals['TRAIN'],intervals['TEST'])
        if train&test and spec.get('allow_subject_overlap') and not spec.get('subject_overlap_reason'):raise ValueError('Shared-subject protocol requires a documented reason')
        if duplicates or overlaps or (train&test and not spec.get('allow_subject_overlap',False)) or any(r['within_split_duplicate_cases'] for r in reports.values()):raise ValueError('Duplicate cases or partition leakage')
        validation=dict(partitions=reports,shared_subjects=sorted(train&test),cross_split_duplicate_cases=duplicates,
            cross_split_overlapping_intervals=overlaps,aeon=smoke(stage,spec),
            aeon_scope='All cases exact .ts readback; aeon load/variance/fit/predict on 3 cases per class per partition',
            channel_order_verified_all_recordings=True,source_sensor_identity='Native MAT header, BIDS/EDF or SET/GDF labels; Castillos explicit named intersection')
        validation.update(spec.get('validation_updates',{}))
        if train&test:validation['subject_overlap_reason']=spec['subject_overlap_reason']
        sensors=[dict(array_index=i,name=channels[old],type='EEG',units='uV',pre_flat_removal_array_index=old,
                      identity_evidence='Native source labels; see per-recording source index mapping') for i,old in enumerate(keep)]
        sessions={p:sorted({r['session_id'] for _,rows in chunks for r in rows if r['participant_id']==p}) for p in people}
        metadata=dict(name=spec['name'],source_dataset=spec['source'],source_doi=spec['doi'],reference=spec['paper'],
            licence=receipt['licence'],moabb_revision=spec.get('moabb_revision',REVISION),source_revision=receipt.get('source_revision',f'Zenodo record {receipt["source_record_id"]}'),
            shapes={s.lower():r['shape'] for s,r in reports.items()},subjects=len(people),actual_subjects=dict(train=sorted(train),test=sorted(test)),
            sessions_per_subject={p:len(s) for p,s in sessions.items()},session_ids=sessions,recording_count=len(recordings),
            channel_names=names,channel_count=len(names),sensors=sensors,channel_quality=quality,
            removed_channels=[dict(name=channels[i],pre_flat_removal_array_index=i,reason='At least one constant/effectively flat case; authorised global sensor removal') for i in removed],
            sampling_frequency_hz=spec['hz'],original_sampling_frequency_hz=spec['hz'],dtype='float64',units='uV',
            window_samples=spec['points'],window_seconds=spec['points']/spec['hz'],window_bounds='Start inclusive, end exclusive',
            label_mapping=spec['labels'],class_distributions={s.lower():r['class_counts'] for s,r in reports.items()},
            split_definition=('First seven original IDs within each GR/PAR group train, remaining two per group test; no shared subjects' if key=='kumar' else f'Original IDs in sorted order: first {len(train)} participants train, remaining {len(test)} test; explicit memberships retained'),
            original_partition='unsplit',validation_partition=None,case_order='Native file order as documented by adapter, source event order; never shuffled',
            preprocessing='Native EEG selection, source-event crops, float64 microvolt scale; no additional filter, baseline, resampling or rereference',
            source_and_conversion_notes=spec['note'],recordings=recordings,
            intermediate_format='Per-recording numpy.savez_compressed X float64 (case,channel,time), allow_pickle=False, kept under source cache; no validation partition',
            metadata_evidence=dict(direct='Native numeric arrays, event/sample/file IDs, embedded sensor labels and available headers',
                assigned='Encoded labels, subject split; inferred IDs identified by adapter',documented='Acquisition protocol, reference and unit interpretation where not embedded'),
            missing_or_inconsistent_metadata=['Original source partition absent; archive defines subject split',
                'Individual sensor positions/reference unavailable where native fields are empty; no individual geometry invented',spec['note']])
        metadata.update(spec.get('metadata_updates',{}))
        dump(stage/f'{spec["name"]}_metadata.json',metadata);dump(stage/f'{spec["name"]}_validation.json',validation)
        dump(stage/'metadata-completeness.json',dict(evidence=metadata['metadata_evidence'],missing_or_inconsistent=metadata['missing_or_inconsistent_metadata']))
        with (stage/'channels.tsv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,list(sensors[0]),delimiter='\t');writer.writeheader();writer.writerows(sensors)
        (stage/'channels.txt').write_text(', '.join(names)+'\n',encoding='utf-8')
        evidence=stage/'source_metadata';evidence.mkdir()
        for file in ['download-receipt.json','source-record.json']:shutil.copy2(cache/file,evidence/file)
        for file in spec.get('evidence_files',['open-moabb-download-source-lock.json','open-moabb-source-inspection.json']):shutil.copy2(ROOT/'docs'/file,evidence/file)
        for file in spec.get('cache_evidence_files',[]):
            destination=evidence/file;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(cache/file,destination)
        if key=='rodrigues':
            for f in cache.glob('*header*'):shutil.copy2(f,evidence/f.name)
            shutil.copy2(cache/'demographic.mat',evidence/'demographic.mat')
        if key=='brainform':
            bids=cache/'extracted/BIDS'
            for p in bids.rglob('*'):
                if p.is_file() and p.suffix!='.edf':
                    dest=evidence/'BIDS'/p.relative_to(bids);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        code=stage/'conversion_code';code.mkdir()
        for f in ['prepare_open_moabb.py','prepare_small_moabb.py','prepare_wang.py','prepare_moabb.py','requirements-moabb.txt']+spec.get('conversion_files',[]):shutil.copy2(Path(__file__).with_name(f),code/f)
        (stage/'ATTRIBUTION.txt').write_text(f'{spec["source"]}. Original data DOI {spec["doi"]}. {spec["paper"]}. {receipt["licence"]} {spec.get("licence_url","https://creativecommons.org/licenses/by/4.0/")}\nChanges: EEG selection/harmonisation, source-event epoching, subject split, microvolt float64 export; see metadata for details.\n',encoding='utf-8')
        (stage/f'README_{spec["name"]}.md').write_text(f'# {spec["name"]}\n\n{spec["source"]}. {spec["classes"]} classes, {len(names)} EEG channels, {spec["points"]} samples at {spec["hz"]} Hz. Float64 microvolts.\n\n{spec["note"]}\n\nCase TSV row order exactly matches .ts cases. Read IDs as strings. All participant memberships, labels and missing metadata are in the metadata JSON. No archived validation partition. Source files remain in a separate cache.\n',encoding='utf-8')
        dump(stage/f'{spec["name"]}_manifest.json',dict(name=spec['name'],source_revision=receipt.get('source_revision',receipt['source_record_id']),source_doi=spec['doi'],
            licence=receipt['licence'],moabb_revision=spec.get('moabb_revision',REVISION),source_files=receipt['files'],split=metadata['actual_subjects'],conversion_notes=spec['note'],
            artifacts={p.relative_to(stage).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(final)
    result=dict(dataset=spec['name'],source_key=key,path=str(final),train_cases=counts['TRAIN'],test_cases=counts['TEST'],subjects=len(people),
        channels=len(names),timepoints=spec['points'],classes=spec['classes'],frequency=spec['hz'],
        size_GB=sum(p.stat().st_size for p in final.rglob('*') if p.is_file())/1e9,licence=receipt['licence'],validation=validation,channel_quality=quality)
    path=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(path.read_text()) if path.exists() else {}
    results[key]=result;dump(path,results)
    print(json.dumps({k:v for k,v in result.items() if k not in ['validation','channel_quality']},indent=2),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--datasets',nargs='+',choices=list(SPECS),default=list(SPECS));p.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args()
    for key in a.datasets:prepare(key,a.cache,a.output)
