"""Kueper2024 -> ArmCoordination: unilateral/bilateral executed reaches."""
import argparse
import copy
from datetime import datetime
import json
from pathlib import Path
import re
import warnings

import numpy as np
from tools import prepare_open_moabb as core

ROOT=Path(__file__).resolve().parents[1]
PEOPLE=['AV82','JD68','JV43','QS70','RA12','UP28','XP01','ZS27']
EEG='FP1 FP2 F7 F3 FZ F4 F8 FC5 FC1 FC2 FC6 T7 C3 CZ C4 T8 TP9 CP5 CP1 CP2 CP6 TP10 P7 P3 PZ P4 P8 PO9 O1 OZ O2 PO10 AF7 AF3 AF4 AF8 F5 F1 F2 F6 FT9 FT7 FC3 FC4 FT8 FT10 C5 C1 C2 C6 TP7 CP3 CPZ CP4 TP8 P5 P1 P2 P6 PO7 PO3 POZ PO4 PO8'.split()
AUX=['x_dir','y_dir','z_dir']


def read_header(data):
    try:text=data.decode('utf-8-sig');encoding='utf-8'
    except UnicodeDecodeError:text=data.decode('cp1252');encoding='cp1252 fallback despite declared UTF-8'
    channels=[]
    for line in text.splitlines():
        match=re.fullmatch(r'Ch(\d+)=(.*)',line)
        if match:
            fields=match[2].split(',')
            if int(match[1])!=len(channels)+1:raise ValueError('Unordered native sensor table')
            channels.append(dict(name=fields[0],reference=fields[1],resolution=float(fields[2]),unit=fields[3]))
    if [c['name'] for c in channels]!=EEG+AUX or not all(c['unit'].replace('\u00b5','u').replace('\u03bc','u')=='uV' for c in channels[:64]):raise ValueError('Changed native sensor layout/EEG units')
    if not all(v in text for v in ['DataOrientation=MULTIPLEXED','BinaryFormat=IEEE_FLOAT_32','NumberOfChannels=67','SamplingInterval=2000']):raise ValueError('Changed native binary format')
    return channels,encoding,text


def read_markers(text):
    events=[]
    for line_number,line in enumerate(text.splitlines()):
        match=re.fullmatch(r'(Mk\d+)=(.*)',line)
        if not match:continue
        fields=match[2].split(',')
        events.append(dict(marker_key=match[1],marker_line_number_1based=line_number+1,marker_ordinal=len(events),
            type=fields[0],description=fields[1],code=fields[1].replace(' ',''),position_1based=int(fields[2]),
            duration_samples=int(fields[3]),channel=fields[4],timestamp=fields[5] if len(fields)>5 else ''))
    # Duplicate Mk keys are present in the original files; never use a dict keyed by Mk.
    return events


def physical_eeg(digital,resolutions):
    return np.ascontiguousarray(digital.T,dtype='<f8')*np.asarray(resolutions,dtype='<f8')[:,None]


def participant(path):
    text=path.read_text(encoding='utf-8-sig').replace('\r','')
    def value(key):return re.search(re.escape(key)+r'\s*:\s*([^\n]+)',text)[1].strip()
    return dict(participant_id=value('Subject Code'),age_years=int(value('Age')),gender=value('Gender'),
        handedness=value('Left/Right handed'),experiment_date=value('Date of experiment'),cap_size_raw=value('EEG Cap size'),
        source_metadata_file=path.name,source_metadata_text=text)


def context(events,start,next_start):
    return [dict(code=e['code'],position_1based=e['position_1based'],marker_ordinal=e['marker_ordinal']) for e in events
        if start<=e['position_1based']<next_start and e['code'] in ['S3','S26','S27','S28','S128']]


def records(cache,spec):
    import mne
    selected=set(spec.get('subjects',PEOPLE));extracted=cache/'extracted'
    core.extract_selected(cache/'EEG_dataset.zip',extracted,lambda n:n.lower().endswith(('.txt','.vhdr','.vmrk')) or any('/'+p+'/' in n for p in selected))
    paths=list(extracted.glob('EEG_dataset/EEG/*/*/*.vhdr'))
    paths.sort(key=lambda p:(p.parent.name,0 if '/unilateral/' in p.as_posix() else 1,p.name))
    for path in paths:
        person=path.parent.name
        if person not in selected:continue
        match=re.fullmatch(r'(\d{8})_r_([A-Z]{2}\d{2})_intentional_(unilateral|bilateral)_set(\d+)\.vhdr',path.name)
        if not match or match[2]!=person:raise ValueError('Unknown source file identity')
        date,_,condition,set_number=match.groups();demo=participant(extracted/'EEG_dataset/Metadata'/f'{person}.txt')
        if path.parent.parent.name!=condition:raise ValueError('Native condition folder and filename disagree')
        if datetime.strptime(demo['experiment_date'],'%d.%m.%Y').strftime('%Y%m%d')!=date:raise ValueError('Native experiment date differs from filename')
        channels,encoding,header=read_header(path.read_bytes());resolutions=[c['resolution'] for c in channels[:64]]
        if f'DataFile={path.with_suffix(".eeg").name}' not in header or f'MarkerFile={path.with_suffix(".vmrk").name}' not in header:raise ValueError('Native header references different binary/marker files')
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Online software filter detected.*')
            raw=mne.io.read_raw_brainvision(path,preload=False,verbose=False)
        if raw.ch_names!=EEG+AUX or raw.info['sfreq']!=500 or not np.array_equal(raw._cals[:64],np.array(resolutions)*1e-6):raise ValueError('MNE/native header identity or calibration disagreement')
        binary=path.with_suffix('.eeg')
        if binary.stat().st_size!=raw.n_times*67*4:raise ValueError('Native binary length mismatch')
        digital=np.memmap(binary,dtype='<f4',mode='r',shape=(raw.n_times,67))
        if not np.array_equal(np.asarray(digital[:64,:64].T,dtype='<f8')*raw._cals[:64,None],raw.get_data(picks=list(range(64)),start=0,stop=64)):raise ValueError('MNE/direct binary decoding disagreement')
        events=read_markers(path.with_suffix('.vmrk').read_text(encoding='utf-8-sig'))
        code='S100' if condition=='unilateral' else 'S101';onsets=[e for e in events if e['code']==code]
        mne_onsets=[int(raw.time_as_index([o],use_rounding=True)[0]) for o,d in zip(raw.annotations.onset,raw.annotations.description) if d.replace(' ','').split('/')[-1]==code]
        if mne_onsets!=[e['position_1based']-1 for e in onsets]:raise ValueError('Native/MNE motion-onset positions disagree')
        task_start=[e['position_1based'] for e in events if e['code']=='S8'];task_end=[e['position_1based'] for e in events if e['code']=='S9']
        if len(task_start)!=1 or len(task_end)!=1:raise ValueError('Ambiguous active-task markers')
        source=path.relative_to(extracted).as_posix();rows=[];values=[];excluded=[]
        for i,event in enumerate(onsets):
            onset=event['position_1based']-1;start=onset-1000;end=start+1500
            if start<0 or end>raw.n_times or not task_start[0]<=event['position_1based']<task_end[0]:
                excluded.append(dict(event,reason='Incomplete epoch or onset outside native active experiment'));continue
            if any(start<e['position_1based']-1<end and e['type']=='New Segment' for e in events):
                excluded.append(dict(event,reason='Epoch crosses native segment/lost-sample boundary'));continue
            next_start=onsets[i+1]['position_1based'] if i+1<len(onsets) else task_end[0];flags=context(events,event['position_1based'],next_start)
            row=core.base_row(person,date,condition+'_set'+set_number,source,i,start,1500,500,condition,'1' if condition=='unilateral' else '2')
            row.update(source_epoch_index='',source_event_sample=onset,source_event_sample_1based=event['position_1based'],
                native_marker_key=event['marker_key'],native_marker_ordinal=event['marker_ordinal'],native_marker_line_number_1based=event['marker_line_number_1based'],
                source_motion_marker=code,source_set_number=set_number,logical_set_id=condition+'_set'+('3' if person=='XP01' and condition=='unilateral' and set_number in ['3','4'] else set_number),
                session_id_evidence='Date grouping derived from native filename; original visit/session ID not separately supplied',original_session_id='unknown',
                source_array_index=f'Native float32 samples[{start}:{end}], channels[0:64], transposed and multiplied in float64 by native microvolt resolutions',
                epoch_start_relative_onset_seconds=-2,epoch_end_exclusive_relative_onset_seconds=1,
                source_interval_flags=json.dumps(flags,separators=(',',':')),following_error_presentation=any(f['code']=='S3' for f in flags),
                following_excluded_event_marker=any(f['code']=='S27' for f in flags),following_correct_end_marker=any(f['code']=='S128' for f in flags),
                flag_evidence='Native markers between this selected motion onset and the next; interval association, not a recovered original trial ID; all onsets kept regardless of flags',
                age_years=demo['age_years'],gender=demo['gender'],handedness=demo['handedness'],experiment_date=demo['experiment_date'],exported_native_channel_indices='[0:64]')
            rows.append(row);values.append(physical_eeg(digital[start:end,:64],resolutions))
        info=dict(core.mne_info(raw),source_file=source,source_file_sha256=core.sha(path),native_eeg_binary_sha256=core.sha(binary),
            native_vmrk_sha256=core.sha(path.with_suffix('.vmrk')),participant_id=person,session_id=date,run_id=condition+'_set'+set_number,
            source_eeg_indices=list(range(64)),native_channel_calibrations=channels,header_text_encoding=encoding,source_metadata=demo,
            native_markers=events,native_mne_highpass_hz=raw.info['highpass'],native_mne_lowpass_hz=raw.info['lowpass'],
            filter_evidence='Native amplifier table DC/131Hz; native software table time constant1.59155s (approximately0.1Hz)/249Hz; notchOff. MNE reports software249Hz and ignores hardware131Hz; both native tables preserved in VHDR. Paper describes effective0.1-131Hz.',
            source_motion_onsets=len(onsets),excluded_cases=excluded,native_measurement_datetime=raw.info['meas_date'].isoformat() if raw.info['meas_date'] else None,
            datetime_evidence='Native VMRK timestamp retained; timezone not specified by source, MNE UTC interpretation not independently confirmed',
            native_channel_locations=[c['loc'] for c in raw.info['chs']],coordinates_evidence='Native MNE fields only; no standard montage assigned',
            channel_types_documented=['EEG']*64+['accelerometer']*3)
        info['mne_default_channel_types']=info.pop('native_channel_types');info['native_channel_types']='No explicit type field; roles recovered from original README'
        raw.close();yield np.stack(values),rows,EEG,info


SPEC=dict(name='ArmCoordination',source='Kueper2024 / unilateral and bilateral reaching',cache='Kueper2024',hz=500,points=1500,classes=2,train_subjects=6,
    labels={'1':'unilateral_right_arm','2':'bilateral_both_arms'},doi='10.5281/zenodo.10229480',
    paper='Kueper, Kim and Kirchner (2024), Avoidance of specific calibration sessions in motor intention recognition for exoskeleton-supported rehabilitation through transfer learning on EEG data; Scientific Reports14:16690; DOI10.1038/s41598-024-65910-8',
    note='Executed reaching condition classification, not imagined movement or the original paper movement-versus-rest classifier. All native S100 unilateral/right and S101 bilateral/left motion onsets retained, including flagged/error/extra episodes; source flags preserved without guessed trial repair. Native float32 counts cast to float64 before applying explicit header microvolt resolution. Keep64 EEG in native uppercase order, exclude3 accelerometers. Native -2 to+1sec end-exclusive windows,1500 samples; no added filter/resampling/reference/baseline. Whole participants split6train/2test. XP01 unilateral set4 continues interrupted set3, not another40-trial session. Session IDs group native filename dates; original visit IDs absent.',
    evidence_files=['arm-coordination-preparation.md','arm-coordination-source-lock.json','kueper-native-marker-counts.json','kueper-active-phase-audit.json','kueper-source-zip-inventory.json'],
    cache_evidence_files=['original-zenodo-record.json','moabb-kueper2024.py'],conversion_files=['prepare_kueper.py','download_kueper.py'],
    metadata_updates=dict(original_source_url='https://zenodo.org/records/10229480',reference_paper_doi='10.1038/s41598-024-65910-8',reference='FCz; original README and publication',ground='AFz; original README',
        session_definition='One date group per participant; native filename/participant experiment date; original session ID not given',
        window_relative_onset_seconds=[-2,1],window_last_sample_relative_onset_seconds=0.998,
        original_frequency_evidence='Native VHDR500Hz and paper EEG500Hz; paper2000Hz concerns separate EMG, not this EEG release',
        unit_evidence='Native header explicitly microvolts with per-channel resolution; cast float32 counts to float64 before applying resolution, no V roundtrip',
        missing_or_inconsistent_metadata=['Original session IDs not embedded; date grouping is assigned and documented',
            'Native marker keys repeat; line ordinal and sample position uniquely identify source annotations',
            'Native source includes2003 selected motion onsets, exceeding nominal1920; all kept with interval flags, not forced to paper valid-trial subset',
            'S26/S28 semantics not supplied in README; preserve raw codes. S3=error, S27=excluded-event, S128=correct-trial end; interval flags do not establish original trial identity',
            'XP01 set3/4 jointly complete interrupted unilateral logical set3; retain physical recording boundaries',
            'Native hardware/software filter tables differ; preserve both, MNE lowpass249Hz alone omits hardware131Hz',
            'AV82 participant metadata lists filenames with20211210, while experiment date and actual filenames agree20211220',
            'Individual sensor positions and original timezone not established; no standard geometry or timezone invented'],
        metadata_evidence=dict(direct='Native channel names/order/units/resolutions/fs, marker lines/positions and source files; original participant text demographics/date/notes',
            documented='Sensor roles, FCz reference/AFz ground, motion-marker meaning and XP01 interrupted-set relationship from original README',
            assigned='Encoded condition labels, whole-participant split, filename-date session grouping and onset-to-next-onset flag association',
            missing='Individual sensor coordinates, distinct original session ID/timezone and unambiguous original trial-to-flag assignments')))


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPEC);cache=Path(cache_root)/spec['cache']
    if pilot:spec.update(name='ArmCoordinationPilot',subjects=['AV82','ZS27'],train_subjects=1)
    # All small source evidence; no raw binary copied into the archive sidecars.
    extracted=cache/'extracted'
    core.extract_selected(cache/'EEG_dataset.zip',extracted,lambda n:n.lower().endswith(('.txt','.vhdr','.vmrk')))
    spec['cache_evidence_files'] += [p.relative_to(cache).as_posix() for p in sorted(extracted.rglob('*')) if p.is_file() and p.suffix.lower() in ['.txt','.vhdr','.vmrk']]
    core.SPECS['kueper']=spec;core.READERS['kueper']=records
    return finish_sidecars(core.prepare('kueper',cache_root,output))


def finish_sidecars(result):
    import csv
    import shutil
    folder=Path(result['path']);name=result['dataset'];path=folder/f'{name}_metadata.json';m=json.loads(path.read_text());changed=[]
    indices=[EEG.index(n) for n in m['channel_names']]
    m['aliases']=['Kueper2024','EEG dataset of unilateral and bilateral movement executions']
    m['preprocessing']='Native float32 counts cast to float64 before multiplication by per-channel explicit microvolt resolution; select EEG in native order, peri-onset crops and global flat policy only. No additional filtering, resampling, reference or baseline.'
    m['source_motion_onsets']=sum(r['source_motion_onsets'] for r in m['recordings']);m['excluded_case_count']=sum(len(r['excluded_cases']) for r in m['recordings'])
    if result['train_cases']+result['test_cases']+m['excluded_case_count']!=m['source_motion_onsets']:raise ValueError('Motion-onset case accounting mismatch')
    m['participant_metadata']={r['participant_id']:r['source_metadata'] for r in m['recordings']}
    m['case_order']='Participant native IDs alphabetically; unilateral then bilateral; native filename/set order; original selected marker order within each recording'
    m['source_filter_tables']='Hardware DC/131Hz; online software1.59155s highpass time constant/249Hz; native headers copied. MNE reports0.1/249Hz, hardware131Hz still limits bandwidth; publication0.1-131Hz.'
    for r in m['recordings']:r['exported_native_channel_indices']=indices
    for sensor in m['sensors']:sensor.update(native_channel_index=EEG.index(sensor['name']),units_evidence='Explicit microvolt unit and resolution in native VHDR; digital counts calibrated in float64',reference='FCz, documented in original README',position=None)
    core.dump(path,m);changed.append(path)
    path=folder/'channels.tsv'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(m['sensors'][0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(m['sensors'])
    changed.append(path)
    for split in ['train','test']:
        path=folder/f'cases_{split}.tsv';rows=core.table(path)
        for row in rows:row['exported_native_channel_indices']=json.dumps(indices,separators=(',',':'))
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
        changed.append(path)
    path=folder/'metadata-completeness.json';core.dump(path,dict(direct=['native EEG labels/order/units/resolution/fs','source file/marker line/position/time','participant age/gender/handedness/date/cap token and notes'],
        documented=['sensor roles','FCz reference/AFz ground','source marker meanings','XP01 split-set relationship'],
        assigned=['class encoding','whole-subject split','date-based session grouping','interval flag association'],
        missing=['original distinct visit ID','individual electrode geometry','original timezone','complete original trial ID/flag matching'],
        inconsistencies=m['missing_or_inconsistent_metadata']));changed.append(path)
    for filename in SPEC['evidence_files']:
        path=folder/'source_metadata'/filename;shutil.copy2(ROOT/'docs'/filename,path);changed.append(path)
    for filename in ['prepare_kueper.py','prepare_open_moabb.py']:
        path=folder/'conversion_code'/filename;shutil.copy2(ROOT/'tools'/filename,path);changed.append(path)
    path=folder/f'{name}_manifest.json';manifest=json.loads(path.read_text());manifest.update(original_source_url=m['original_source_url'],reference_paper_doi=m['reference_paper_doi'],
        label_mapping=SPEC['labels'],split_definition=m['split_definition'],licence_url='https://creativecommons.org/licenses/by/4.0/',unit_evidence=m['unit_evidence'])
    for file in changed:manifest['artifacts'][file.relative_to(folder).as_posix()]=dict(bytes=file.stat().st_size,sha256=core.sha(file))
    core.dump(path,manifest)
    result['size_GB']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9
    path=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(path.read_text());results['kueper']=result;core.dump(path,results)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
