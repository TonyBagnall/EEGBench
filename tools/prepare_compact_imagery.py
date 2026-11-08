"""Native compact motor imagery sources to exact float64 .ts and sidecars."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import shutil
import warnings
from xml.etree import ElementTree as ET

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.update_dataset_sidecars import finish
from tools import read_bci2000_native as bci

ROOT=Path(__file__).resolve().parents[1]
SCENARIOS={'Left Hand Up-Down Imagine':'1','Right Hand Up-Down Imagine':'2','Stand Up-Down Imagine':'3'}
MIMED_CHANNELS='AF3 F7 F3 FC5 T7 P7 O1 O2 P8 T8 FC6 F4 F8 AF4'.split()
MOVING_CHANNELS='P7 P4 Cz Pz P3 P8 O1 O2 T8 F8 C4 F4 Fp2 Fz C3 F3 Fp1 T7 F7 Oz PO4 FC6 FC2 AF4 CP6 CP2 CP1 CP5 FC1 FC5 AF3 PO3'.split()
MOVING_MAP={'Trigger#1':'1','Trigger#7':'1','Trigger#13':'1','Trigger#3':'2','Trigger#9':'3','Trigger#15':'4'}


def extract_rar(cache,filename,patterns=None):
    dest=cache/'extracted'
    # 7-Zip protects archive paths; extraction stays in the named source cache.
    cmd=['C:/Program Files/7-Zip/7z.exe','x',str(cache/filename),'-o'+str(dest),'-y','-bso0']
    subprocess.run(cmd+(patterns or []),check=True)
    return dest


def mimed_block(d,index):
    names=[str(c).strip() for c in np.asarray(d['channel']).ravel()]
    if names!=MIMED_CHANNELS or int(d['Fs'])!=128:raise ValueError('Changed native MIMED channel order/rate')
    block=np.asarray(d['joined_data'][index])
    if block.ndim!=2 or block.shape[1]!=14 or len(block)<896:raise ValueError('Incomplete MIMED block')
    return np.ascontiguousarray(block[384:896].T,dtype='<f8'),names,block


def mimed_records(cache,spec):
    root=core.extract_selected(cache/'Motor Imagery.zip',cache/'extracted',lambda n:n.endswith('.mat'))
    for person in [f'P{i:02}' for i in range(1,31)]:
        if spec.get('subjects') and person not in spec['subjects']:continue
        for scenario,label in SCENARIOS.items():
            path=root/'Motor Imagery'/scenario/(person+'.mat');d=loadmat(path,simplify_cells=True)
            if str(d['subject']).strip()!=person or len(d['joined_data'])!=4:raise ValueError('Native participant/block mismatch')
            source=path.relative_to(cache).as_posix()
            for i in range(4):
                x,names,block=mimed_block(d,i)
                row=core.base_row(person,'day'+str(i//2+1),'scenario'+str(i%2+1),source+'#block'+str(i),i,384,512,128,scenario,label)
                row.update(source_file=source,source_array_index=f'joined_data[{i}][384:896,:].T',source_block_index=i,
                    sample_reference='Native epoch-local samples; original continuous offsets unavailable',
                    source_event_sample='',original_continuous_start_sample='',original_continuous_end_sample='',
                    epoch_onset_evidence='Assigned 3-second offset after documented baseline; no recorded cue timestamps',
                    session_id_evidence='Published four-cell mapping: first two day1, last two day2; dates absent',
                    original_label_evidence='Native scenario folder; raising/lowering directions not individually labelled')
                info=dict(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id=row['session_id'],run_id=row['run_id'],
                    source_block_index=i,native_subject=str(d['subject']).strip(),native_channel_names=names,native_channel_types=['EEG']*14,
                    native_sampling_frequency_hz=int(d['Fs']),native_block_shape=list(block.shape),native_dtype=str(block.dtype),
                    selected_native_sample_slice=[384,896],source_case_count=1,units_evidence='Original Emotiv EDF-derived numeric values interpreted as microvolts; native MAT has no physical unit field',
                    continuous_offsets=None)
                yield x[None], [row], names, info


def moving_events(raw):
    selected=[]
    for i,(o,d,s) in enumerate(zip(raw.annotations.onset,raw.annotations.duration,raw.annotations.description)):
        if s not in MOVING_MAP:continue
        start=int(raw.time_as_index(float(o)-raw.first_time,use_rounding=True)[0])
        if start<0 or start+3000>raw.n_times:raise ValueError('Incomplete MOVING task interval')
        selected.append((i,start,str(s),MOVING_MAP[s]))
    if not selected:raise ValueError('No native MOVING imagery/rest markers')
    return selected


def moving_records(cache,spec):
    import mne
    root=cache/'extracted'
    if len(list(root.rglob('*.edf')))!=11:root=extract_rar(cache,'edf.rar')
    files=sorted(root.rglob('*.edf'),key=lambda p:int(re.search(r'Subj_(\d+)_',p.name)[1]))
    for path in files:
        person=re.search(r'Subj_(\d+)_',path.name)[1]
        if spec.get('subjects') and person not in spec['subjects']:continue
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_edf(path,preload=False,verbose=False)
        if raw.ch_names!=MOVING_CHANNELS+['X','Y','Z'] or raw.info['sfreq']!=500:raise ValueError('Changed native MOVING order/rate')
        if not np.all(np.asarray(raw._raw_extras[0]['units'])[:32]==1e-6):raise ValueError('Unexpected EDF physical units')
        source=path.relative_to(cache).as_posix();values=[];rows=[]
        for i,start,code,label in moving_events(raw):
            x=np.asarray(raw.get_data(picks=list(range(32)),start=start,stop=start+3000),dtype='<f8')*1e6
            values.append(x)
            row=core.base_row(person,'recording1','recording1',source,i,start,3000,500,code,label)
            row.update(source_annotation_index=i,native_annotation_onset_seconds=float(raw.annotations.onset[i]),
                source_annotation_duration_seconds=float(raw.annotations.duration[i]),source_event_sample=start,
                source_epoch_index='',session_id_evidence='Assigned sole recording per subject; no visit number embedded',
                native_recording_date=raw.info['meas_date'].isoformat() if raw.info['meas_date'] else '',
                timestamp_evidence='MNE representation of EDF local header; original timezone unavailable')
            rows.append(row)
        info=core.mne_info(raw);info.update(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id='recording1',run_id='recording1',
            source_eeg_indices=list(range(32)),channel_types_recovered=['EEG']*32+['accelerometer']*3,
            excluded_native_channels=['X','Y','Z'],native_recording_date=raw.info['meas_date'].isoformat() if raw.info['meas_date'] else None,
            edf_calibration=raw._raw_extras[0]['cal'],edf_offsets=raw._raw_extras[0]['offsets'],source_case_count=len(rows),
            unit_conversion='MNE calibrated volts cast float64 then multiplied by 1e6; native EDF EEG physical dimensions microvolts')
        yield np.stack(values),rows,list(MOVING_CHANNELS),info


ZHANG_CAPTIONS=['Rest','elbow','drawer','spoon','weight','door','plate','comb','pizza','pick_and_place']


def zhang_participants(path):
    tree=ET.fromstring(Path(path).read_bytes())
    table=next(e for e in tree.iter('table-wrap') if e.get('id')=='pone.0188293.t002')
    people=[]
    for row in table.iter('tr'):
        cells=[''.join(c.itertext()).strip() for c in row.findall('td')]
        if not cells:continue
        paper_id,sex,age,hand=cells
        if not re.fullmatch(r'H\d{2}',paper_id) or sex not in ['M','F'] or hand not in ['Right','Left']:raise ValueError('Changed original participant table')
        people.append(dict(participant_id='H'+str(int(paper_id[1:])),published_participant_id=paper_id,age_years=int(age),sex=sex,dominant_hand=hand,
            evidence='Original article Table2; numeric H identifier joins archive H1 to publication H01; strings preserved'))
    if {p['participant_id'] for p in people}!={'H'+str(i) for i in range(1,13)}:raise ValueError('Incomplete published cohort')
    return people


def zhang_intervals(values):
    kept=[];excluded=[]
    for ordinal,(start,stop,code) in enumerate(bci.intervals(values)):
        if not 1<=code<=10:raise ValueError('Unknown native stimulus code')
        if stop-start<3960:
            if start==0 and stop==40:
                excluded.append(dict(interval_index=ordinal,start=start,stop=stop,code=code,reason='40sample left-censored nonzero state at file boundary; not a complete stimulus'))
                continue
            raise ValueError('Unexpected short native stimulus')
        kept.append((ordinal,start,stop,code))
    return kept,excluded


def zhang_records(cache,spec):
    root=cache/'extracted'
    if len(list(root.rglob('*.dat')))!=180:root=extract_rar(cache,'KI.rar')
    files=sorted(root.rglob('*.dat'),key=lambda p:(int(p.parent.name[1:]),int(re.search(r'R(\d+)\.dat',p.name)[1])))
    for path in files:
        person=path.parent.name
        if spec.get('subjects') and person not in spec['subjects']:continue
        r=bci.read(path);params=r['parameters'];source=path.relative_to(cache).as_posix()
        if r['n_channels']!=17 or r['frequency']!=1000:raise ValueError('Changed native Zhang schema')
        native_names=bci.parameter_list(params,'ChannelNames')
        if native_names:raise ValueError('Source now has channel identities; review and recover them')
        # The source column is recoverable; its anatomical electrode is not.
        names=[f'source_column_{i:02d}' for i in range(17)]
        stimuli=params['Stimuli'];captions=stimuli.split('}',2)[2].split()[:10]
        if captions!=ZHANG_CAPTIONS:raise ValueError('Changed native stimulus caption order')
        events,excluded=zhang_intervals(bci.state(r,'StimulusCode'));values=[];rows=[]
        for i,start,stop,code in events:
            values.append(bci.calibrated(r,start,start+3960))
            row=core.base_row(person,params['SubjectSession'].split()[0],params['SubjectRun'].split()[0],source,i,start,3960,1000,str(code),str(code))
            row.update(source_epoch_index='',native_stimulus_caption=captions[code-1],native_stimulus_end_sample=stop,
                native_stimulus_duration_samples=stop-start,native_header_subject_name=params['SubjectName'].split()[0],
                participant_id_evidence='Original H1..H12 archive directory; header SubjectName is nonunique H',
                native_storage_time=params['StorageTime'].split()[0],native_stimulus_index=i,
                channel_identity_status='Unknown anatomical names; source ordinal columns preserved without guessed EGI/10-20 mapping')
            rows.append(row)
        info=dict(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id=rows[0]['session_id'],run_id=rows[0]['run_id'],
            native_channel_names=[],array_channel_identifiers=names,native_channel_types_documented=['EEG']*17,native_sampling_frequency_hz=1000,
            native_source_columns=17,native_data_format='float32',native_samples=len(r['data']),native_gain_uV_per_AD_unit=r['gains'],native_offsets_AD_units=r['offsets'],
            native_storage_time=params['StorageTime'].split()[0],native_subject_name=params['SubjectName'].split()[0],
            native_stimulus_matrix=stimuli,native_sequence=params['Sequence'],native_state_definitions=r['states'],
            native_stimulus_intervals=events,excluded_native_intervals=excluded,source_case_count=len(rows),
            sensor_identity_evidence='ChannelNames empty; 17 source columns retained. No inferred EGI sensor indices or anatomical positions applied')
        yield np.stack(values),rows,names,info


SPECS={
 'mimed':dict(name='ImaginedHandsTrunk',source='MIMED2024 imagery-only',cache='MIMED2024',hz=128,points=512,classes=3,train_subjects=23,
    labels={'1':'imagined_left_hand_raising_lowering','2':'imagined_right_hand_raising_lowering','3':'imagined_standing_sitting'},doi='10.17632/zs25xxjkm9.3',
    paper='Wirawan et al.(2024), Acquisition and processing of Motor Imagery and Motor Execution Dataset (MIMED) for six movement activities; 10.1016/j.dib.2024.110833',
    note='Original joined_data numbers cast float64 without rescaling. Native channel/Fs/subject fields checked. Three folder-level imagined activity families; no guessed up/down labels. Four-second archive crop at native block384:896 after documented3second baseline. Native blocks are9 or19seconds, not continuous recordings; original source offsets absent. Two-day cell mapping documented by original article. First23 original participant IDs train, remaining7 test; no extra filtering, resampling or reference change.',
    metadata_updates=dict(reference='Emotiv reference not explicitly recovered from MAT; device CMS/DRL convention is not a measured source reference',
      original_source_url='https://data.mendeley.com/datasets/zs25xxjkm9/3',unit_evidence='Presumed microvolt numeric scale from Emotiv-derived data; explicit native MAT unit missing; multiplier1',
      session_count_evidence='Article describes cells0/1 as scenarios1/2 day1 and cells2/3 day2; no original dates',
      missing_or_inconsistent_metadata=['Continuous source offsets and actual cue timestamps unavailable; 3second baseline offset and four-second crop are documented/assigned, not recorded events',
      'MAT has native channel order, Fs, subject and four cell blocks; individual up/down labels absent',
      'Physical unit absent in MAT; presumed microvolt values unchanged, including large DC offsets','No measured individual coordinates, native reference field or dates recovered'])),
 'moving':dict(name='ImaginedHandGestures',source='MOVING2024 imagery plus shared rest',cache='MOVING2024',hz=500,points=3000,classes=4,train_subjects=8,
    labels={'1':'rest','2':'imagined_right_hand_open_close','3':'imagined_right_wrist_rotation','4':'imagined_right_finger_tapping'},doi='10.5281/zenodo.12804784',
    paper='Mattei et al.(2024), MOVING: A Multi-Modal Dataset of EEG Signals and Virtual Glove Hand Tracking; 10.3390/s24165207',
    note='Native EDF order and physical calibration retained; exclude X/Y/Z accelerometers. Select Trigger#1/7/13 rest and3/9/15 imagined movements only; no execution windows. Six seconds at native onset, calibrated MNE volts converted float64 to microvolts. Fixed task order is a source confound. Shared rest segments mean an execution view would not be a wholly independent recording set. First8 native participant IDs train, remaining3 test.',
    metadata_updates=dict(original_source_url='https://zenodo.org/records/12804784',reference='Not recovered from original EDF header; no rereference applied',
      missing_or_inconsistent_metadata=['Fixed movement order confounds task with position in block',
      'Individual montage geometry and reference not recovered; anatomical sensor names are native EDF labels',
      'EDF measurement date has no independently established timezone; displayed UTC is MNE representation',
      'Session/run recording1 identifiers assigned for sole native file per participant']))
}
SPECS['zhang']=dict(name='ImaginedArmTasks',source='Zhang2017 / elbow-centred kinesthetic motor imagery',cache='Zhang2017',hz=1000,points=3960,classes=10,train_subjects=9,
    splitter=lambda people,chunks:set(sorted(people,key=lambda p:int(p[1:]))[:9]),
    labels={str(i+1):label for i,label in enumerate(['rest','imagined_elbow_flexion_extension','imagined_drawer_open_close','imagined_spoon_feeding','imagined_weight_lifting','imagined_door_open_close','imagined_plate_cleaning','imagined_hair_combing','imagined_pizza_cutting','imagined_pick_and_place'])},
    doi='10.6084/m9.figshare.5579461.v1',paper='Zhang, Yong and Menon(2017), Evaluating the versatility of EEG models generated from motor imagery tasks; 10.1371/journal.pone.0188293',
    note='Native BCI2000 samples calibrated float64 as(raw-SourceChOffset)*SourceChGain in microvolts. Native StimulusCode/caption matrix defines ten classes. First3.96seconds of each complete stimulus interval: three native cues are3960samples, others4000. Exclude40sample left-censored H6run01 initial state fragment. Preserve source17-column order, with no hemisphere flipping or rereferencing. ANATOMICAL CHANNEL NAMES UNKNOWN: source_column_00..16 are ordinal identifiers, not recovered electrode names; no inferred EGI mapping. H1..H9 train,H10..H12 test.',
    validation_updates=dict(channel_order_verified_all_recordings=False,source_column_order_preserved_all_recordings=True,
        anatomical_channel_order_consistency=None,source_sensor_identity='Unresolved: native ChannelNames empty. Every file has17 source columns, preserved as ordinals; no anatomical order verified'),
    metadata_updates=dict(original_source_url='https://doi.org/10.6084/m9.figshare.5579461.v1',reference='Cz, documented in original paper; no rereference applied',ground='COM, documented in original paper',
        metadata_status='FLAGGED: anatomical channel identities and their consistency across files unresolved',
        channel_names_kind='Opaque zero-based source column identifiers; original electrode names unavailable',anatomical_channel_names=[None]*17,
        split_definition='Original archive directory IDs H1-H9 TRAIN,H10-H12 TEST; numeric sort; whole participants; no original official split',
        case_order='Native participant directory numeric order, run numeric order, StimulusCode interval onset order',
        unit_evidence='Explicit native per-column BCI2000 SourceChGain/SourceChOffset; official calibration(raw-offset)*gain yields microvolts',
        preprocessing='Source paper documents0.1-40Hz acquisition filtering, not independently recovered as applied raw-data processing. Archive only native calibration, first3.96second cue crop, float64 and global flat policy; no hemisphere flip/filter/resample/rereference.',
        missing_or_inconsistent_metadata=['Anatomical channel identities absent in original header; inferred loader EGI1-16/E28 mapping not accepted as recovered names',
            'Same anatomical order across recordings cannot be established; original source column order preserved without reordering',
            'No source montage coordinates applied because channel-to-electrode mapping unresolved',
            'H1..H12 are directory participant IDs; native SubjectName H is nonunique; actual calendar timezone unknown',
            'Published nominal trial arithmetic is inconsistent; actual StimulusCode intervals determine retained counts']))


def finish_sidecars(result,key):
    spec=SPECS[key];folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    for s in m['sensors']:
        s['native_channel_index']=s['pre_flat_removal_array_index'];s['identity_evidence']='Native MAT channel field in column order' if key=='mimed' else 'Native EDF labels in source signal order'
        if key=='zhang':s.update(anatomical_name=None,identity_evidence='Opaque source column ordinal only; anatomical name unknown')
        s['position']=None;s['position_evidence']='Individual coordinates not distributed; no template invented'
    m['aliases']=[spec['cache']];m['source_case_count']=sum(r['source_case_count'] for r in m['recordings'])
    for recording in m['recordings']:recording['exported_native_channel_indices']=[s['native_channel_index'] for s in m['sensors']]
    m['native_source_files']=len({r['source_file'] for r in m['recordings']})
    m['recording_count_evidence']='One exporter chunk per native block' if key=='mimed' else 'One native continuous source file per exporter chunk'
    m['metadata_evidence']=dict(direct='Native numeric arrays, channel labels/order, source IDs and calibration/annotations where available',
        documented='Original paper acquisition protocol and MIMED cell/day interpretation',assigned='Archive split, encoded classes, fixed crop lengths; MIMED cue offset assigned after documented baseline',
        inferred='MIMED microvolt numeric interpretation; no inferred anatomical names or individual geometry')
    if key=='zhang':
        m['metadata_evidence'].update(direct='Native float32 source columns, gain/offset, state definitions and stimulus captions; ChannelNames explicitly empty',inferred='No inferred anatomical channel names/positions used; only original source-column ordinals')
        m['participants']=zhang_participants(ROOT/'docs/source-evidence/motor-imagery-survey/zhang-article.xml')
        m['published_demographic_scope']='All12 published participants; pilot/retained memberships are separately explicit in actual_subjects'
    m['metadata_evidence']['availability']=dict(participant_id=True,session_id=True,run_or_block_id=True,original_trial_or_epoch_id=True,
        continuous_recording_samples=key!='mimed',native_channel_names=key!='zhang',anatomical_channel_order_confirmed=key!='zhang',
        measured_individual_positions=False,physical_units_explicit=key!='mimed',native_labels=True,source_file=True,
        original_partition=False,original_reference_documented=key=='zhang')
    evidence_name='original-release.html' if key=='mimed' else 'original-record.json'
    evidence=Path(result.get('source_cache',str(Path('D:/Data/EEGSources')/spec['cache'])))/evidence_name
    # Keep original-host licence evidence with the archive, not only in the repo.
    if evidence.exists():
        destination=folder/'source_metadata'/evidence_name;shutil.copy2(evidence,destination)
        manifest_path=folder/(name+'_manifest.json');manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['artifacts']['source_metadata/'+evidence_name]=dict(bytes=destination.stat().st_size,sha256=core.sha(destination))
        core.dump(manifest_path,manifest)
    docs=[key+'-imagery-source-lock.json','compact-imagery-preparation.md']
    if key=='zhang':docs+=['source-evidence/motor-imagery-survey/zhang-article.xml']
    return finish(result,m,docs,
        ['prepare_compact_imagery.py','download_compact_imagery.py','read_bci2000_native.py','requirements-moabb.txt'],dict(original_source_url=m['original_source_url'],label_mapping=spec['labels'],licence_url='https://creativecommons.org/licenses/by/4.0/',metadata_status=m.get('metadata_status','Native names recovered')))


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPECS[key])
    if pilot:
        spec.update(name=spec['name']+'Pilot',subjects={'mimed':['P01','P30'],'moving':['01','11'],'zhang':['H1','H12']}[key],train_subjects=1,intermediate_directory='pilot-classification-intermediate'+('-3960' if key=='zhang' else ''))
        if key=='zhang':spec['splitter']=lambda people,chunks:{'H1'}
    spec['evidence_files']=[key+'-imagery-source-lock.json','compact-imagery-preparation.md']
    spec['cache_evidence_files']=['original-release.html' if key=='mimed' else 'original-record.json']
    spec['conversion_files']=['prepare_compact_imagery.py','download_compact_imagery.py','update_dataset_sidecars.py','read_bci2000_native.py']
    core.SPECS[key]=spec;core.READERS[key]={'mimed':mimed_records,'moving':moving_records,'zhang':zhang_records}[key]
    result=core.prepare(key,cache_root,output)
    result['source_cache']=str(Path(cache_root)/spec['cache'])
    return finish_sidecars(result,key)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=list(SPECS));p.add_argument('--pilot',action='store_true');p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));a=p.parse_args();prepare(a.dataset,a.cache_root,a.output,a.pilot)
