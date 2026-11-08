"""Native Batista, Polo and Leeuwis EEG -> independently validated .ts problems."""
import argparse
import copy
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import warnings
import zipfile

import numpy as np
import pandas as pd
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.prepare_kueper import read_markers
from tools.prepare_vagaja import EEG,header as brainvision_header
from tools.download_mi_next import CONFIG,leeuwis_map
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
LEE_CHANNELS='F3 Fz F4 FC5 FC1 FC2 FC6 T7 C3 C4 Cz T8 CP5 CP1 CP2 CP6'.split()
POLO_CHANNELS='AF3 F3 FZ FC3 FC1 FCZ C5 C3 C1 CZ CP3 CP1 CPZ P3 PZ PO3 AF4 F4 FC2 FC4 C2 C4 C6 CP2 CP4 P4 POZ PO4'.split()
BATISTA_TRAIN={f'{n:02d}' for n in list(range(1,10))+list(range(12,16))}|{'p01','p02'}
BATISTA_CONDITIONS={'MI','MIMO','MIMOHP','MIMOVR','MIMOVRHP'}
BATISTA_AUX_SCHEMAS=[['Aux1','Aux2','Aux3','x_dir','y_dir','z_dir'],['PPG','ECG','Resp','x_dir','y_dir','z_dir']]
LOCAL_TIMES='Native epoch-local samples; original continuous offsets unavailable'


def subject_split(people,chunks):return set(people)&BATISTA_TRAIN


def polo_split(people,chunks):return set(people)&{'B01','B02','B03','B04'}


def csv_epochs(frame):
    """Find actual t=0 in each native trial; never assume an offset of750."""
    if list(frame.columns)!=['TimeStamp']+LEE_CHANNELS+['trial','class']:raise ValueError('Changed native CSV names/order')
    trial=frame['trial'].to_numpy();starts=np.r_[0,np.flatnonzero(np.diff(trial)!=0)+1];ends=np.r_[starts[1:],len(frame)]
    if len(starts)!=40 or trial[starts].tolist()!=list(range(1,41)):raise ValueError('Non-native trial order/membership')
    values=[];info=[]
    for start,end in zip(starts,ends):
        part=frame.iloc[start:end];t=part.TimeStamp.to_numpy(dtype=float);label=part['class'].to_numpy()
        if len(part)!=2000 or not np.allclose(np.diff(t),1/250,rtol=0,atol=1e-10):raise ValueError('Native time axis not2000uniform samples')
        zero=np.flatnonzero(np.isclose(t,0,rtol=0,atol=1e-10))
        if len(zero)!=1 or len(set(label))!=1 or label[0] not in [-1,1]:raise ValueError('Missing zero-time or inconsistent original class')
        cue=int(zero[0]);stop=cue+1250
        if stop>len(part) or not np.allclose(t[cue:stop],np.arange(1250)/250,rtol=0,atol=1e-10):raise ValueError('Incomplete native MI interval')
        values.append(np.ascontiguousarray(part.iloc[cue:stop][LEE_CHANNELS].to_numpy(dtype='<f8').T))
        info.append(dict(trial_id=str(int(trial[start])),source_label=str(int(label[0])),csv_trial_start_row=int(start),csv_trial_end_row=int(end),cue_local=cue,csv_start_row=int(start+cue),csv_end_row=int(start+stop),native_time_bounds=[float(t[0]),float(t[-1])]))
    if Counter(i['source_label'] for i in info)!=Counter({'-1':20,'1':20}):raise ValueError('Changed per-run class balance')
    return np.asarray(values,dtype='<f8'),info


def leeuwis_records(cache,spec):
    mapping=leeuwis_map(cache/'moabb-leeuwis2021.py');receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    by_id={f['datafile_id']:f for f in receipt['files']};selected=set(spec.get('subjects',[str(n) for n in mapping]))
    with (cache/'Questionnaires.csv').open(encoding='utf-8-sig',newline='') as f:demographics=list(csv.DictReader(f))
    if len({r['ppnr'] for r in demographics})!=len(demographics):raise ValueError('Duplicate questionnaire participant IDs')
    demos={r['ppnr']:r for r in demographics}
    for number,ids in mapping.items():
        person=str(number)
        if person not in selected:continue
        if person not in demos:raise ValueError('Missing native subject questionnaire record')
        for index,file_id in enumerate(ids):
            f=by_id[file_id];path=cache/f['name'];run=['calibration','feedback_1','feedback_2','feedback_3'][index]
            native_person=re.search(r'(?:Subject|S)(\d+)_',path.name)
            if not native_person or native_person[1]!=person:raise ValueError('Pinned file mapping disagrees with native filename participant')
            frame=pd.read_csv(path,float_precision='round_trip');x,epochs=csv_epochs(frame);rows=[]
            for i,e in enumerate(epochs):
                label='1' if e['source_label']=='-1' else '2'
                row=core.base_row(person,'single_visit',run,f['name'],i,e['cue_local'],1250,250,e['source_label'],label)
                row.update(source_epoch_index=i,original_trial_id=e['trial_id'],sample_reference=LOCAL_TIMES,original_partition=run,
                    native_epoch_samples=2000,native_epoch_time_start=e['native_time_bounds'][0],native_epoch_time_end=e['native_time_bounds'][1],native_cue_sample_within_epoch=e['cue_local'],
                    csv_trial_start_row=e['csv_trial_start_row'],csv_trial_end_row=e['csv_trial_end_row'],csv_start_row=e['csv_start_row'],csv_end_row=e['csv_end_row'],csv_row_reference='Zero-based data rows, header excluded, end exclusive',
                    native_imagery_start_seconds=0,native_imagery_end_exclusive_seconds=5,source_array_index=f'Native CSV data rows[{e["csv_start_row"]}:{e["csv_end_row"]}], EEG columns1:17, transposed; float64 decimal parsing',
                    native_datafile_id=str(file_id),original_session_id='unknown',session_id_evidence='One visit per participant documented in original data report; no native visit/date field',
                    run_id_evidence='Pinned source file-ID order linked to calibration/feedback labels; original filename retained, including irregular Subject40 names; independent wall-clock order unavailable',
                    gender=demos[person]['Gender'],age=demos[person]['Age'],handedness=demos[person]['Righthanded'],source_questionnaire_id=person)
                rows.append(row)
            info=dict(source_file=f['name'],source_file_sha256=core.sha(path),participant_id=person,session_id='single_visit',run_id=run,native_datafile_id=str(file_id),
                native_channel_names=LEE_CHANNELS,native_channel_types=['EEG']*16,source_eeg_indices=list(range(16)),native_csv_columns=list(frame.columns),
                source_case_count=40,native_stored_rows=len(frame),native_trials=epochs,participant_metadata=demos[person],
                native_sampling_frequency_hz=250,sampling_frequency_evidence='Original readme250Hz and directly checked per-trial TimeStamp increment',
                native_units='Not explicit in CSV/report; numeric values unchanged, microvolt interpretation inferred',
                source_filter_evidence='Paper10.3389/fnhum.2021.634748 describes0.5-30Hz bandpass and48-52Hz notch; exact filtering history of distributed CSV not explicitly identified')
            yield x,rows,LEE_CHANNELS,info


def phase_intervals(task):
    task=np.asarray(task).ravel();starts=np.r_[0,np.flatnonzero(np.diff(task)!=0)+1];ends=np.r_[starts[1:],len(task)]
    return [(int(task[s]),int(s),int(e)) for s,e in zip(starts,ends)]


def polo_epochs(d,condition):
    raw=np.asarray(d['data_EEG']);acq=d['conf']['acquisition'];device=acq['device']['devices_EEG']
    names=list(device['electrodes_names_selected'])
    if names!=POLO_CHANNELS+['VU','VD','HR','HL','AX','AY','AZ'] or raw.shape[0]!=35 or device['fm']!=250:raise ValueError('Changed native Polo sensor names/order/frequency')
    if list(np.asarray(acq['EEG_index']).ravel())!=list(range(1,29)):raise ValueError('Changed native EEG index selection')
    task=np.asarray(d['task_EEG']).ravel()
    if len(task)!=raw.shape[1]:raise ValueError('Task/data alignment mismatch')
    rest,mi=(211,311) if condition=='STATIC' else (221,321)
    intervals=phase_intervals(task);selected=[(c,s,e) for c,s,e in intervals if c in [rest,mi]]
    if Counter(c for c,_,_ in selected)!=Counter({rest:2,mi:1}):raise ValueError('Unexpected native relaxation/MI phases')
    if any(e-s<1000 for _,s,e in selected):raise ValueError('Incomplete4second phase')
    x=np.asarray([np.ascontiguousarray(raw[:28,s:s+1000],dtype='<f8') for c,s,e in selected],dtype='<f8')
    return x,selected,names,device


def polo_records(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));extracted=cache/'extracted';selected=set(spec.get('subjects',[f'B{n:02d}' for n in range(1,7)]))
    aliases={}
    for f in sorted(receipt['files'],key=lambda f:(f['name'][:3],0 if 'STATIC' in f['name'] else 1)):
        match=re.fullmatch(r'(B\d{2})_S1_(STATIC|MOTION)\.zip',f['name'])
        if not match:raise ValueError('Unknown native release file')
        person,condition=match.groups()
        if person not in selected:continue
        core.extract_selected(cache/f['name'],extracted,lambda n:n.endswith('.mat'))
        paths=sorted((extracted/f['name'][:-4]).glob('*.mat'))
        if len(paths)!=11:raise ValueError('Expected11native repetitions per source condition')
        for path in paths:
            identity=re.fullmatch(r'(B\d{2})_(\d{8})_openloop_(\d{2})\.mat',path.name)
            if not identity:raise ValueError('Unknown native repetition filename')
            native_person,date,repetition=identity.groups();d=loadmat(path,simplify_cells=True)['session'];x,phases,names,device=polo_epochs(d,condition)
            acq=d['conf']['acquisition']
            if acq['user_code']!=native_person or str(acq['mode']).upper()!=condition:raise ValueError('Native internal ID/condition mismatch')
            aliases.setdefault(person,set()).add(native_person)
            if len(aliases[person])!=1 or any(native_person in ids for p,ids in aliases.items() if p!=person):raise ValueError('Non-bijective release/native participant relationship')
            source=path.relative_to(extracted).as_posix();rows=[]
            for index,(code,start,end) in enumerate(phases):
                label='1' if code in [211,221] else '2';row=core.base_row(person,'S1',condition+'/'+repetition,source,index,start,1000,250,code,label)
                row.update(original_partition='unsplit',source_epoch_index='',source_repetition_id=repetition,native_participant_id=native_person,release_participant_id=person,
                    source_condition=condition,source_recording_date=date,native_phase_start_sample=start,native_phase_end_sample=end,native_phase_length_samples=end-start,
                    source_acquisition_file_name=acq['file_name'],source_array_index=f'Native session.data_EEG[0:28,{start}:{start+1000}], native float64 scale unchanged',
                    task_index_at_start=str(np.asarray(d['task_index_EEG']).ravel()[start]),task_order_at_start=str(np.asarray(d['task_order_EEG']).ravel()[start]),
                    event_at_start=str(np.asarray(d['event_EEG']).ravel()[start]),
                    trigger_eeg_selected_window_sha256=hashlib.sha256(np.ascontiguousarray(d['trigger_EEG'][:,start:start+1000],dtype='<f8').tobytes()).hexdigest(),
                    session_id_evidence='Original release S1 and one-session protocol; STATIC/MOTION are conditions, not separate visits')
                rows.append(row)
            info=dict(source_file=source,source_file_sha256=core.sha(path),source_zip=f['name'],participant_id=person,native_participant_id=native_person,session_id='S1',run_id=condition+'/'+repetition,
                source_condition=condition,native_recording_date=date,native_channel_names=names,native_channel_types=['EEG']*28+['EOG']*4+['inertial']*3,source_eeg_indices=list(range(28)),
                native_electrode_positions_x=device['electrode_positions_x'],native_electrode_positions_y=device['electrode_positions_y'],
                native_coordinate_evidence='Original configured2D layout, units/frame and individual measurement status unspecified',native_sampling_frequency_hz=int(device['fm']),
                native_acquisition_shift_samples=int(device['shift']),native_source_shape=list(d['data_EEG'].shape),native_source_dtype=str(d['data_EEG'].dtype),
                native_task_intervals=[dict(code=c,start=s,end=e) for c,s,e in phase_intervals(d['task_EEG'])],native_acquisition_task={k:acq['task'][k] for k in ['sequence_tasks','sequence_times','time_multiplier']},
                native_acquisition_file_name=acq['file_name'],native_preprocessing_step_table=d['conf']['info']['preprocessingSteps'],
                native_trigger_eeg_shape=list(d['trigger_EEG'].shape),native_trigger_eeg_range_per_row=[dict(min=float(np.min(v)),max=float(np.max(v))) for v in d['trigger_EEG']],
                source_case_count=len(rows),raw_selection='session.data_EEG only; supplied data_preprocessed_EEG/filter state and classifier outputs not used',
                metadata_caveats='Some descriptive MATLAB string objects are opaque to SciPy; original MAT retained, no guessed decoding or physical units')
            yield x,rows,names[:28],info


def condition_name(path):
    token=Path(path).stem.split('task-')[-1]
    for prefix in ['graz','neurow']:
        if token.startswith(prefix):return token[len(prefix):]
    raise ValueError('Unknown original task prefix')


def batista_header(data):
    text=data.decode('utf-8-sig');section=text.split('[Channel Infos]')[1].split('[Coordinates]')[0]
    names=[match[2].split(',')[0] for line in section.splitlines() if (match:=re.fullmatch(r'Ch(\d+)=(.*)',line))]
    if names[32:] not in BATISTA_AUX_SCHEMAS:raise ValueError('Unknown native auxiliary schema')
    # Only excluded auxiliary labels vary. EEG identity/order is checked by the
    # common native header decoder and is never inferred or rearranged.
    return brainvision_header(data,aux_names=names[32:],require_coordinates=False)


def batista_paths(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));selected=set(spec.get('subjects',[f['name'][4:-4] for f in receipt['files']]))
    extracted=cache/'extracted'
    for f in receipt['files']:
        if f['name'][4:-4] not in selected:continue
        core.extract_selected(cache/f['name'],extracted,lambda n:Path(n).suffix.lower() in ['.vhdr','.vmrk'] or (n.endswith('.eeg') and condition_name(n)!='ME'))
    out=[]
    for p in extracted.rglob('*.vhdr'):
        person=p.relative_to(extracted).parts[0].removeprefix('sub-')
        if person not in selected or condition_name(p)=='ME':continue
        if condition_name(p) not in BATISTA_CONDITIONS:raise ValueError('Undocumented imagery condition')
        events=read_markers(p.with_suffix('.vmrk').read_text(encoding='utf-8-sig'));segments=[e for e in events if e['type']=='New Segment']
        if not segments or not re.fullmatch(r'\d{20}',segments[0]['timestamp']):raise ValueError('Missing native recording timestamp')
        out.append((person,segments[0]['timestamp'],p,events))
    return sorted(out,key=lambda r:(r[0],r[1],r[2].as_posix()))


def batista_trials(events,n_samples=None):
    cues=[e for e in events if e['type']=='Stimulus' and e['code'] in ['S7','S8']];retained=[];excluded=[]
    for i,event in enumerate(cues):
        start=event['position_1based']-1;next_start=cues[i+1]['position_1based']-1 if i+1<len(cues) else (n_samples if n_samples is not None else 10**12)
        ends=[e for e in events if e['code']=='S10' and start<e['position_1based']-1<next_start]
        if len(ends)!=1:
            excluded.append(dict(trial_index=i,event=event,reason='Missing or ambiguous native S10 end'));continue
        end=ends[0]['position_1based']-1;gaps=[e for e in events if e['type']=='New Segment' and start<e['position_1based']-1<end]
        item=dict(trial_index=i,event=event,start=start,native_end=end,native_duration=end-start,end_event=ends[0])
        if gaps or (n_samples is not None and end>n_samples):excluded.append(dict(item,reason='Native lost samples/discontinuity or incomplete source interval',segment_markers=gaps))
        else:retained.append(item)
    return retained,excluded


def eeg_record_hash(digital,resolutions):
    h=hashlib.sha256();h.update(json.dumps(dict(channels=EEG,hz=500,samples=len(digital)),sort_keys=True).encode())
    for start in range(0,len(digital),32768):
        block=np.ascontiguousarray(digital[start:start+32768,:32],dtype='<f8')*np.asarray(resolutions,dtype='<f8')[None,:]
        h.update(block.tobytes())
    return h.hexdigest()


def vagaja_identity(cache_root,metadata_path=None):
    """Content comparison excludes auxiliaries and uses native EEG calibration."""
    metadata_path=Path(metadata_path) if metadata_path else Path('D:/Data/EEG/ImaginedHandsEmbodiment/ImaginedHandsEmbodiment_metadata.json')
    meta=json.loads(metadata_path.read_text(encoding='utf-8'))
    records=[];fingerprints=set()
    for r in meta['recordings']:
        path=Path(cache_root)/'Vagaja2023/extracted'/r['source_file'];binary=path.with_suffix('.eeg')
        if core.sha(binary)!=r['native_binary_sha256']:raise ValueError('Existing Vagaja source changed')
        digital=np.memmap(binary,dtype='<f4',mode='r',shape=(r['native_samples'],38));res=np.array([c['resolution'] for c in r['native_channels'][:32]],dtype='<f8')
        records.append(dict(source_file=r['source_file'],recording_date=r['native_recording_timestamp'][:8],eeg_only_sha256=eeg_record_hash(digital,res)))
        for event in r['native_markers']:
            if event['type']!='Stimulus' or event['code'] not in ['S7','S8']:continue
            start=event['position_1based']-1
            if start+1000<=len(digital):fingerprints.add(core.digest_case(np.ascontiguousarray(digital[start:start+1000,:32].T,dtype='<f8')*res[:,None]))
    return records,fingerprints


def batista_records(cache,spec):
    import mne
    baseline,fingerprints=vagaja_identity(cache.parent,spec.get('identity_reference_metadata'));reference_hashes={r['eeg_only_sha256'] for r in baseline};comparison=[]
    for person,timestamp,path,events in batista_paths(cache,spec):
        channels,coordinates,common,text=batista_header(path.read_bytes())
        binary=path.with_suffix('.eeg');res=np.array([c['resolution'] for c in channels[:32]],dtype='<f8')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_brainvision(path,preload=False,verbose=False,overrides=dict(data_fname=binary.name,marker_fname=path.with_suffix('.vmrk').name))
        if raw.ch_names!=[c['name'] for c in channels] or raw.info['sfreq']!=500 or binary.stat().st_size!=raw.n_times*38*4:raise ValueError('Native BrainVision format disagrees with MNE')
        digital=np.memmap(binary,dtype='<f4',mode='r',shape=(raw.n_times,38))
        if not np.array_equal(raw.get_data(picks=list(range(32)),start=0,stop=64),np.asarray(digital[:64,:32].T,dtype='<f8')*(res*1e-6)[:,None]):raise ValueError('Native/MNE calibration disagreement')
        record_hash=eeg_record_hash(digital,res)
        if record_hash in reference_hashes:raise ValueError('Recording EEG copied from Vagaja2023')
        retained,excluded=batista_trials(events,raw.n_times);x=[];rows=[];source=path.relative_to(cache/'extracted').as_posix();condition=condition_name(path);session=path.relative_to(cache/'extracted').parts[1].removeprefix('ses-')
        for item in retained:
            start=item['start'];event=item['event'];stop=start+spec['points']
            if stop>item['native_end']:raise ValueError('Common crop crosses original MI end')
            prefix=core.digest_case(np.ascontiguousarray(digital[start:start+1000,:32].T,dtype='<f8')*res[:,None])
            if prefix in fingerprints:raise ValueError('Cue-locked EEG segment copied from Vagaja2023')
            value=np.ascontiguousarray(digital[start:stop,:32].T,dtype='<f8')*res[:,None];x.append(value)
            row=core.base_row(person,session,condition,source,event['marker_ordinal'],start,spec['points'],500,event['description'],'1' if event['code']=='S7' else '2')
            row.update(source_epoch_index='',source_trial_ordinal=item['trial_index'],source_participant_folder='sub-'+person,native_filename_participant=path.name.split('_')[0],
                native_recording_timestamp=timestamp,native_recording_date=timestamp[:8],native_recording_timezone='unknown',source_condition=condition,
                native_marker_key=event['marker_key'],native_marker_ordinal=event['marker_ordinal'],native_marker_line_number_1based=event['marker_line_number_1based'],
                source_event_sample_1based=event['position_1based'],native_trial_end_sample_1based=item['end_event']['position_1based'],native_imagery_duration_samples=item['native_duration'],
                source_array_index=f'Native float32 samples[{start}:{stop}], EEG[0:32], transposed and calibrated in float64 microvolts',
                cue_first_two_seconds_eeg_sha256=prefix,participant_cohort='pilot' if person.startswith('p') else 'main')
            rows.append(row)
        comparison.append(dict(source_file=source,recording_date=timestamp[:8],eeg_only_sha256=record_hash,cue_segments_compared=len(rows)))
        info=dict(source_file=source,source_file_sha256=core.sha(path),native_binary_sha256=core.sha(binary),native_marker_sha256=core.sha(path.with_suffix('.vmrk')),
            participant_id=person,session_id=session,run_id=condition,native_recording_timestamp=timestamp,native_channel_names=[c['name'] for c in channels],
            native_channel_types_documented=['EEG']*32+[{'PPG':'PPG','ECG':'ECG','Resp':'respiration','x_dir':'accelerometer','y_dir':'accelerometer','z_dir':'accelerometer'}.get(c['name'],'misc') for c in channels[32:]],source_eeg_indices=list(range(32)),native_channels=channels,
            auxiliary_type_evidence='Native named PPG/ECG/Resp roles retained; generic Aux1-Aux3 remain misc because per-index modality assignment is not established by original distributed files. No forced MOABB auxiliary renaming.',
            native_coordinates=coordinates,native_header_text=text,native_markers=events,native_samples=raw.n_times,sampling_frequency_hz=500,source_case_count=len(retained)+len(excluded),excluded_cases=excluded,
            eeg_only_sha256=record_hash,header_filename_references=dict(declared_data=common['DataFile'],declared_marker=common['MarkerFile'],actual_data=binary.name,actual_marker=path.with_suffix('.vmrk').name),
            source_filter_evidence='Available native hardware/software filter tables preserved in header text; absent tables remain unknown',position_evidence='Embedded CLA-32 template coordinates; not individual measured geometry' if coordinates else 'Native coordinate table absent; no generated montage substituted')
        yield np.asarray(x,dtype='<f8'),rows,EEG,info
    report=dict(batista_recordings=comparison,vagaja_recordings=baseline,exact_eeg_recording_matches=0,exact_cue_first_two_second_matches=0,
        scope='All selected Batista recording EEG-only hashes and retained cue-locked2second32EEG fingerprints compared against26VagajaMIrecordings and all source cue prefixes. Different timestamps support distinct acquisition. Does not establish participant identity across studies.',
        overlapping_recording_dates=sorted({r['recording_date'] for r in comparison}&{r['recording_date'] for r in baseline}))
    core.dump(ROOT/'docs'/('batista-vagaja-'+('pilot' if spec.get('subjects') else 'full')+'-identity.json'),report)


COMMON=dict(classes=2,evidence_files=['mi-next-three-preparation.md'],conversion_files=['prepare_mi_next.py','download_mi_next.py','prepare_vagaja.py','prepare_kueper.py'],
    note='Native EEG only, exact names/order and source IDs retained; float64 microvolt representation with explicit unit evidence/inference. No added filtering, resampling, baseline or reference. Whole-subject split, no validation archive. Original source metadata and any quality exclusions retained.')
SPECS={
 'batista':dict(COMMON,name='ImaginedHandsHaptics',source='Batista2022 / NeuRow VR and haptics',cache='Batista2022',hz=500,points=2500,train_subjects=15,splitter=subject_split,
     validation_updates=dict(source_sensor_identity='Every native BrainVision header EEG name/order/calibration checked, with independent MNE/direct binary decoding; only excluded auxiliary labels vary'),
     labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.5281/zenodo.7664069',paper='Batista,Caetano,Fleury,Figueiredo,Vourvopoulos(2022), original Zenodo data; related NeuRow reference, separate paper DOI not established',
     cache_evidence_files=['original-source-record.json','moabb-batista2022.py'],
     metadata_updates=dict(reference='Unknown, native reference fields empty',ground='Unknown',original_source_url='https://zenodo.org/records/7664069',
         cohort_demographics_documented=dict(reported_subjects=20,health_status='healthy',mean_age_years=24.79,age_sd_years=3.54,male_percent=68,female_percent=32,individual_mapping=None,evidence='Original Zenodo description; reported percentages retained, not converted into guessed integer counts'),
         case_order='Original participant folder IDs sorted; native first New Segment timestamp then filename order; original class-marker order within recording',
         split_definition='Whole-subject:main01-09,12-15 and pilotp01/p02 TRAIN; main16-19 and pilotp03 TEST. Original IDs preserved, no official benchmark split.',
         unit_evidence='Explicit native EEG microvolt resolutions; float32 digital samples cast to float64 before per-channel physical calibration',
         time_reference='Stored native file indices; seconds=index/500, not reconstructed wall-clock time across lost-sample gaps',
         metadata_evidence=dict(direct='Native subject/session folders, filenames/timestamps, class/end/segment markers, sensor order/calibration/template coordinates and filter tables',documented='Original data licence, modality roles, single-session NeuRow protocol and cohort summary',assigned='Encoded labels, whole-subject split, cue ordinal and common safe crop; no invented individual demographics'),
         missing_or_inconsistent_metadata=['Pilot foldersp01-p03 use filename subject01-03 tokens; folder IDs remain primary, both kept','Reference/ground, individual demographics/timezone and measured geometry unavailable','Some source trials have lost-sample gaps; exclude complete affected trials, preserve markers','Different imagery cue counts are retained, not forced to nominal40','ME executed-movement recordings excluded; feedback conditions pooled as one problem'])),
 'polo':dict(COMMON,name='ImaginedAnkleRest',source='PoloHortiguela2025 / ankle exoskeleton',cache='PoloHortiguela2025',hz=250,points=1000,train_subjects=4,splitter=polo_split,
     validation_updates=dict(source_sensor_identity='Every native MAT configured channel/index table checked; exact first28 EEG array order and uppercaseZspelling retained, no invented montage'),
     labels={'1':'relaxation','2':'imagined_dominant_ankle_dorsal_and_plantar_flexion'},doi='10.5281/zenodo.14672334',paper='Polo-Hortiguela,Ortiz,Ianez,Azorin(2025), EEG Signal Dataset During Dorsiflexion and Plantar Flexion Movements, original Zenodo',
     cache_evidence_files=['original-source-record.json','moabb-polohortiguela2025.py'],
     metadata_updates=dict(reference='Not established in distributed configuration',ground='Unknown',original_source_url='https://zenodo.org/records/14672334',
         case_order='Release participant ID, STATIC then MOTION, native repetition filename order, original task-phase order within repetition',
         split_definition='Whole-subject release IDs B01-B04 TRAIN,B05-B06 TEST; STATIC/MOTION pooled conditions within originalS1, no validation archive',
         unit_evidence='Native raw float64 numbers unchanged; microvolt interpretation follows loader/amplitude convention, not an explicit unit field recovered from original MAT',
         preprocessing='Select native session.data_EEG first28rows, first4seconds of each native rest/MI phase as pinned MOABB interval; not supplied processed blocks. No added filter/resampling/reference/normalisation.',
         metadata_evidence=dict(direct='Native configured channel labels/order/indexes/frequency/2Dpositions, release/native IDs/date/repetition, sample task codes/phase bounds and preprocessing-step table',documented='Original licence,28EEG/4EOG/3inertial roles, single-visit ankle imagery/exoskeleton protocol',inferred='Microvolt scale only, factor1; coordinate units and missing reference not invented',assigned='Whole-subject split and encoded classes; release IDs linked explicitly to native aliases'),
         missing_or_inconsistent_metadata=['Release folder IDs may differ from native user_code/filename; one-to-one mapping must hold across all files/conditions','Some MATLAB string objects opaque to SciPy; originals retained rather than guessed','Physical units, reference/ground and individual demographics not explicitly recovered','Native configured2D positions retained, coordinate units/frame/measurement status unknown','Trigger quality vectors retained by source bounds/hash/ranges; semantics not guessed or used for undocumented rejection'])),
 'leeuwis':dict(COMMON,name='ImaginedHandsFeedback',source='Leeuwis2021 / Psychological and Cognitive Factors in MI BCI',cache='Leeuwis2021',hz=250,points=1250,train_subjects=41,
     labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.34894/Z7ZVOD',paper='Leeuwis,Paas,Alimardani(2021), Vividness of Visual Imagery and Personality Impact Motor-Imagery Brain Computer Interfaces, DOI10.3389/fnhum.2021.634748',
     cache_evidence_files=['original-source-record.json','moabb-leeuwis2021.py','readme.txt','Data Report.pdf','Questionnaires.csv','BCI_OnlineClassificationErrors.csv'],
     validation_updates=dict(source_sensor_identity='Every native CSV header and selected EEG column order checked; actual array order retained rather than prose electrode-list order',cross_split_overlapping_intervals=None,original_continuous_interval_overlap='Unknown: distributed CSV trials are epoched; stored-row bounds are not continuous acquisition offsets'),
     metadata_updates=dict(reference='Right earlobe, original Data Report/paper',ground='AFz, original Data Report/paper',original_source_url='https://doi.org/10.34894/Z7ZVOD',reference_paper_doi='10.3389/fnhum.2021.634748',
         case_order='Numeric native subject IDs ascending, pinned calibration/feedback file-ID sequence, original CSV trial order; absolute cross-file acquisition chronology unavailable',
         split_definition='Whole-subject first41numeric native IDs TRAIN,remaining14TEST. Pool calibration and feedback phases; original adaptive per-person online classifier is not reproduced. No official fixed benchmark test split supplied.',
         unit_evidence='Native CSV float64 decimal values unchanged, presumed microvolts following source loader; CSV/report do not explicitly state physical units',
         preprocessing='CSV supplied as raw EEG; paper acquisition/online pipeline describes0.5-30Hz bandpass and48-52Hz notch, exact distributed CSV filter history unlabelled. Archive selects native t0..4.996s, no added DSP.',
         metadata_evidence=dict(direct='Native CSV sensor order, trial/class/time axes, subject/file IDs; original questionnaires provide individual demographics/cognitive scores',documented='Original licence,250Hz,one visit/four phases, reference/ground and paper processing protocol',inferred='Microvolt interpretation only, native numbers unchanged; no guessed XYZ',assigned='Encoded1/2labels and whole-subject benchmark split; source calibration/feedback phases retained'),
         missing_or_inconsistent_metadata=['CSV physical units and exact supplied filtering history not explicit; inferred microvolt scale, factor1','No original continuous offsets, visit/date IDs or individual electrode positions','Original Data Report lists36female+21male=57 while description/release has55EEG subjects; use actual CSV membership and mapped questionnaire records','README prose electrode list order differs from actual CSV column order; actual CSV is authoritative','Subject40 feedback filenames irregular; preserve exact filenames and pinned file-ID/run mapping']))
}
READERS={'batista':batista_records,'polo':polo_records,'leeuwis':leeuwis_records}


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False,identity_reference_metadata=None):
    spec=copy.deepcopy(SPECS[key]);cache=Path(cache_root)/spec['cache'];spec['intermediate_directory']='classification-intermediate-'+('pilot' if pilot else 'full')
    if pilot:
        spec.update(name=spec['name']+'Pilot',subjects={'batista':['01','p03'],'polo':['B01','B06'],'leeuwis':['7','67']}[key])
        output=cache/'pilot-output'
    spec['evidence_files'] += [key+'-mi-source-lock.json']
    if key=='batista':
        spec['identity_reference_metadata']=identity_reference_metadata
        durations=[]
        for _,_,p,events in batista_paths(cache,spec):
            retained,_=batista_trials(events);durations.extend(r['native_duration'] for r in retained)
        if not durations:raise ValueError('No complete source imagery trials')
        spec['points']=min(2500,min(durations))
        if spec['points']<1000:raise ValueError('Unexpectedly short native imagery; review source before harmonisation')
        spec['metadata_updates']['window_decision']=f'Common min(2500,minimum valid native S10-minus-cue)={spec["points"]}samples; discontinuous trials excluded before deriving crop'
        spec['evidence_files'] += ['batista-vagaja-'+('pilot' if pilot else 'full')+'-identity.json']
    # An epoched CSV has numeric native IDs: pad only for ordering, never for identity.
    if key=='leeuwis':
        ids=sorted(map(str,leeuwis_map(cache/'moabb-leeuwis2021.py')),key=int)
        training=set(ids[:41]);spec['splitter']=lambda people,chunks:set(people)&training
    core.SPECS[key]=spec;core.READERS[key]=READERS[key]
    result=core.prepare(key,cache_root,output)
    return finish_sidecars(result,key)


def finish_sidecars(result,key):
    spec=SPECS[key];folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    m['case_order']=spec['metadata_updates']['case_order']
    channels={'batista':EEG,'polo':POLO_CHANNELS,'leeuwis':LEE_CHANNELS}[key];first=m['recordings'][0]
    for sensor in m['sensors']:
        i=channels.index(sensor['name']);sensor.update(native_channel_index=i,units_evidence=m['unit_evidence'])
        if key=='polo':sensor.update(source_x=first['native_electrode_positions_x'][i],source_y=first['native_electrode_positions_y'][i],position_evidence='Native configured2D layout, units/frame/measurement status unspecified')
        elif key=='batista':sensor.update(source_coordinate_triplet=first['native_coordinates'][i] if first['native_coordinates'] else None,position_evidence='Native acquisition template where available, not individual measured geometry')
        else:sensor.update(position=None,reference=m['reference'])
    indices=[s['native_channel_index'] for s in m['sensors']]
    for r in m['recordings']:r['exported_native_channel_indices']=indices
    m['aliases']=[CONFIG[key]['source']];m['source_case_count']=sum(r['source_case_count'] for r in m['recordings']);m['excluded_case_count']=sum(len(r.get('excluded_cases',[])) for r in m['recordings'])
    titles={'batista':'Physiological Signals During Motor Imagery Brain-Computer Interface Training Using Virtual Reality and Haptics',
            'polo':'EEG Signal Dataset During Dorsiflexion and Plantar Flexion Movements',
            'leeuwis':'Psychological and Cognitive Factors in Motor Imagery Brain Computer Interfaces'}
    m['original_dataset_title']=titles[key];m['aliases'].append(titles[key])
    m['secondary_source_views']=[dict(repository='NEMAR',id={'batista':'nm000318','polo':'nm000302','leeuwis':'nm000327'}[key],evidence='Declared in pinned MOABB loader; no separate NEMAR arrays downloaded')]
    m['secondary_id_mapping_evidence']='Pinned MOABB loader; these are secondary loader IDs, not replacements for native participant identifiers'
    if key=='batista':m['moabb_subject_to_archive_subject']={**{str(n):f'{n:02d}' for n in list(range(1,10))+list(range(12,20))},'20':'p01','21':'p02','22':'p03'}
    elif key=='polo':m['moabb_subject_to_archive_subject']={str(n):f'B{n:02d}' for n in range(1,7)}
    else:
        native=leeuwis_map(folder/'source_metadata/moabb-leeuwis2021.py')
        m['moabb_subject_to_archive_subject']={str(i+1):str(n) for i,n in enumerate(native)}
    m['archive_transformations']=dict(dtype='float64',native_eeg_channel_indices=list(range(len(channels))),
        native_channel_names=channels,exported_native_channel_indices=indices,window_samples=result['timepoints'],window_seconds=result['timepoints']/result['frequency'],
        numerical_operation='Float32 digital counts cast to float64 before per-channel native microvolt resolution multiplication' if key=='batista' else 'Original numeric scale unchanged; CSV round-trip float64 parse' if key=='leeuwis' else 'Original raw data_EEG float64 numeric scale unchanged',
        additional_filtering=False,resampling=False,rereferencing=False,baseline_correction=False,flat_channel_policy=m['channel_quality']['policy'])
    if result['train_cases']+result['test_cases']+m['excluded_case_count']!=m['source_case_count']:raise ValueError('Source case accounting mismatch')
    if key=='leeuwis':
        m['participant_metadata']={r['participant_id']:r['participant_metadata'] for r in m['recordings']}
        m['distributed_gender_counts']=dict(Counter(p['Gender'] for p in m['participant_metadata'].values()))
        m['demographic_evidence']='Individual source questionnaire rows linked by ppnr; full distributed55person cohort36Female/19Male. Original report57person totals retained as a documented discrepancy. BCI_Novice raw strings retained without guessing question coding.'
    if key=='polo':
        m['original_repetition_count']=len(m['recordings'])
        m['classification_cases_per_repetition']='Two relaxation phases and one imagery phase; first4seconds of each, no sliding/overlapping windows'
        m['release_native_participant_mapping']={r['participant_id']:r['native_participant_id'] for r in m['recordings']}
        same=all(r['native_electrode_positions_x']==first['native_electrode_positions_x'] and r['native_electrode_positions_y']==first['native_electrode_positions_y'] for r in m['recordings'])
        m['configured_layout_consistent_all_recordings']=same
        if not same:
            for sensor in m['sensors']:sensor['source_x']=sensor['source_y']=None;sensor['position_evidence']='Native layouts vary; inspect per-recording positions, no global geometry asserted'
    if key=='batista':
        for recording in m['recordings']:
            recording['native_channel_types_documented']=['EEG']*32+[{'PPG':'PPG','ECG':'ECG','Resp':'respiration','x_dir':'accelerometer','y_dir':'accelerometer','z_dir':'accelerometer'}.get(n,'misc') for n in recording['native_channel_names'][32:]]
            recording['auxiliary_type_evidence']='Native named modalities retained; generic Aux per-index role is unknown, not assigned from MOABB renaming'
        m['native_auxiliary_channel_schemas']=[list(schema) for schema in sorted({tuple(r['native_channel_names'][32:]) for r in m['recordings']})]
        m['auxiliary_channel_evidence']='Only excluded auxiliary labels vary. Native32EEG names/order consistent. Named PPG/ECG/Resp preserved, generic Aux roles left misc; no renaming/reordering or guessed wiring.'
        caveat='Excluded auxiliary labels differ across source recordings; generic Aux1-Aux3 physiological identities cannot be assigned from the named schema without evidence'
        if caveat not in m['missing_or_inconsistent_metadata']:m['missing_or_inconsistent_metadata'].append(caveat)
        same=bool(first['native_coordinates']) and all(r['native_coordinates']==first['native_coordinates'] for r in m['recordings']);m['coordinate_template_consistent_all_recordings']=same
        m['native_coordinate_table_availability']=dict(present=sum(bool(r['native_coordinates']) for r in m['recordings']),missing=sum(not r['native_coordinates'] for r in m['recordings']))
        if not same:
            for sensor in m['sensors']:sensor['source_coordinate_triplet']=None
        configurations=set()
        for recording in m['recordings']:
            filters=[]
            for line in recording['native_header_text'].splitlines():
                fields=line.split()
                if len(fields)>=8 and fields[0].isdigit() and fields[1] in EEG:
                    filters.append(dict(name=fields[1],low_cutoff_seconds=fields[5],high_cutoff_hz=fields[6],notch_hz=fields[7]));configurations.add(tuple(fields[5:8]))
            recording['native_hardware_eeg_filter_table']=filters
            recording['native_hardware_eeg_filter_table_complete']=[f['name'] for f in filters]==EEG
            recording['native_software_filters']='Disabled' if re.search(r'S o f t w a r e  F i l t e r s\s*=+\s*Disabled',recording['native_header_text']) else 'See native header'
        m['source_hardware_eeg_filter_configurations']=[dict(low_cutoff_seconds=a,high_cutoff_hz=b,notch_hz=c) for a,b,c in sorted(configurations)]
        m['source_hardware_filter_table_availability']=dict(complete=sum(r['native_hardware_eeg_filter_table_complete'] for r in m['recordings']),unknown_or_partial=sum(not r['native_hardware_eeg_filter_table_complete'] for r in m['recordings']))
        m['source_software_filter_settings']=sorted({r['native_software_filters'] for r in m['recordings']})
        if m['native_coordinate_table_availability']['missing']:
            caveat='Some source headers omit coordinates and/or hardware filter tables; retain unknowns, no generated montage or assumed filter history substituted'
            if caveat not in m['missing_or_inconsistent_metadata']:m['missing_or_inconsistent_metadata'].append(caveat)
    docs=spec['evidence_files']+[key+'-mi-source-lock.json']
    if key=='batista':docs+=['batista-vagaja-'+('pilot' if name.endswith('Pilot') else 'full')+'-identity.json']
    if not name.endswith('Pilot'):
        extra={'batista':['batista-full-native-marker-audit.json','batista-native-sensor-variations.json','batista-native-coordinate-availability.json'],
               'polo':['polo-release-native-file-audit.json','polo-native-pilot-inspection.json'],'leeuwis':[]}[key]
        docs += [n for n in extra if (ROOT/'docs'/n).is_file()]
    return finish(result,m,docs,spec['conversion_files'],dict(label_mapping=spec['labels'],split_definition=m['split_definition'],original_source_url=m['original_source_url'],unit_evidence=m['unit_evidence'],licence_url='https://creativecommons.org/licenses/by/4.0/',
        conversion_details=m['archive_transformations'],case_order=m['case_order'],excluded_case_count=m['excluded_case_count']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=SPECS);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');p.add_argument('--identity-reference-metadata',type=Path,help='Existing Vagaja metadata for mandatory Batista identity audit; defaults to D-drive archive');a=p.parse_args();prepare(a.dataset,a.cache_root,a.output,a.pilot,a.identity_reference_metadata)
