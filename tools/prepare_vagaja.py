"""Vagaja2023 -> ImaginedHandsEmbodiment, native calibrated EEG and metadata."""
import argparse
import copy
from collections import Counter
import json
from pathlib import Path
import re
import warnings

import numpy as np
from tools import prepare_open_moabb as core
from tools.prepare_kueper import read_markers
from tools.update_dataset_sidecars import finish

ROOT = Path(__file__).resolve().parents[1]
EEG = 'Fp1 Fz F3 F7 FT9 FC5 FC1 C3 T7 TP9 CP5 CP1 Pz P3 P7 O1 Oz O2 P4 P8 TP10 CP6 CP2 Cz C4 T8 FT10 FC6 FC2 F4 F8 Fp2'.split()
AUX = ['EMGL', 'EMGR', 'Temp', 'x_dir', 'y_dir', 'z_dir']
EMBODIED = ['03','05','06','07','08','09','10','12','14','15','16','29','31']
CONTROL = [f'{n:02d}' for n in list(range(17,29))+[30]]
PEOPLE = sorted(EMBODIED+CONTROL)
TRAIN = set(EMBODIED[:10]+CONTROL[:10])
POINTS = 4997


def header(data,aux_names=None,require_coordinates=True):
    """Validate acquisition order and recover native calibration/coordinates."""
    text = data.decode('utf-8-sig')
    section = None
    channels, coordinates, common, binary = [], [], {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):continue
        if line.startswith('['):section=line;continue
        if '=' not in line:continue
        k,v=line.split('=',1)
        if section=='[Common Infos]':common[k]=v
        elif section=='[Binary Infos]':binary[k]=v
        elif section in ['[Channel Infos]','[Coordinates]'] and re.fullmatch(r'Ch\d+',k):
            target=channels if section=='[Channel Infos]' else coordinates
            if int(k[2:])!=len(target)+1:raise ValueError('Unordered native channel/coordinate table')
            fields=v.split(',')
            target.append(dict(name=fields[0],reference=fields[1],resolution=float(fields[2]),unit=fields[3]) if section=='[Channel Infos]' else list(map(float,fields)))
    if [c['name'] for c in channels]!=EEG+(AUX if aux_names is None else aux_names):raise ValueError('Native channel names/order changed')
    if not all(c['unit'].replace('\u00b5','u').replace('\u03bc','u')=='uV' and c['resolution']>0 for c in channels[:32]):raise ValueError('Unknown EEG calibration/units')
    if common.get('SamplingInterval')!='2000' or common.get('NumberOfChannels')!='38' or common.get('DataOrientation')!='MULTIPLEXED' or common.get('DataFormat')!='BINARY' or binary.get('BinaryFormat')!='IEEE_FLOAT_32':raise ValueError('Changed native recording format')
    if binary.get('UseBigEndianOrder','NO')!='NO' or len(coordinates) not in ([38] if require_coordinates else [0,38]):raise ValueError('Changed byte order or absent coordinate table')
    return channels,coordinates,common,text


def windows(events,n_samples):
    """Retain common cue windows only inside native end and segment bounds."""
    cues=[e for e in events if e['type']=='Stimulus' and e['code'] in ['S7','S8']]
    if Counter(e['code'] for e in cues)!=Counter({'S7':20,'S8':20}):raise ValueError('Changed native cue protocol')
    retained,excluded=[],[]
    for i,event in enumerate(cues):
        start=event['position_1based']-1
        next_start=cues[i+1]['position_1based']-1 if i+1<len(cues) else n_samples
        ends=[e for e in events if e['code']=='S10' and start<e['position_1based']-1<next_start]
        if len(ends)!=1:raise ValueError('Missing/ambiguous original trial end')
        duration=ends[0]['position_1based']-event['position_1based']
        if not POINTS<=duration<=5001:raise ValueError('Native imagery duration outside audited bounds')
        gaps=[e for e in events if e['type']=='New Segment' and start<e['position_1based']-1<start+POINTS]
        item=dict(trial_index=i,event=event,start=start,end=start+POINTS,end_event=ends[0],native_duration_samples=duration)
        if start<0 or start+POINTS>n_samples or gaps:
            excluded.append(dict(item,reason='Native lost-sample discontinuity or incomplete source window',segment_markers=gaps))
        else:retained.append(item)
    return retained,excluded


def split_people(people,chunks):
    # Same fixed rule works for the pilot without accidentally assigning all to TRAIN.
    return set(people)&TRAIN


def records(cache,spec):
    import mne
    selected=set(spec.get('subjects',PEOPLE))
    def select(name):
        p=Path(name)
        return p.suffix.lower() in ['.vhdr','.vmrk'] or (p.name.endswith('_MI.eeg') and p.parent.name.removeprefix('SUB') in selected)
    extracted=core.extract_selected(cache/'GROUPS.zip',cache/'extracted',select)
    paths=sorted(extracted.rglob('*_MI.vhdr'),key=lambda p:int(p.parent.name.removeprefix('SUB')))
    if len(paths)!=26:raise ValueError('Expected26 original MI recordings')
    for path in paths:
        person=path.parent.name.removeprefix('SUB')
        if person not in selected:continue
        group=path.parent.parent.name
        if person not in PEOPLE or group!=('Embodied' if person in EMBODIED else 'Control') or path.name!=f'SUB{person}_MI.vhdr':raise ValueError('Unknown native participant/group/file identity')
        channels,coordinates,common,text=header(path.read_bytes())
        markers=path.with_suffix('.vmrk');binary=path.with_suffix('.eeg')
        overrides=dict(data_fname=binary.name,marker_fname=markers.name)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw=mne.io.read_raw_brainvision(path,preload=False,verbose=False,overrides=overrides)
        resolutions=np.asarray([c['resolution'] for c in channels[:32]],dtype='<f8')
        if raw.ch_names!=EEG+AUX or raw.info['sfreq']!=500 or not np.array_equal(raw._cals[:32],resolutions*1e-6):raise ValueError('MNE/native sensor/calibration disagreement')
        if binary.stat().st_size!=raw.n_times*38*4:raise ValueError('Native binary length mismatch')
        digital=np.memmap(binary,dtype='<f4',mode='r',shape=(raw.n_times,38))
        calibrated=np.asarray(digital[:64,:32].T,dtype='<f8')*raw._cals[:32,None]
        if not np.array_equal(calibrated,raw.get_data(picks=list(range(32)),start=0,stop=64)):raise ValueError('Native/MNE binary decoding mismatch')
        events=read_markers(markers.read_text(encoding='utf-8-sig'))
        expected=[e['position_1based']-1 for e in events if e['type']=='Stimulus' and e['code'] in ['S7','S8']]
        actual=[int(raw.time_as_index([o],use_rounding=True)[0]) for o,d in zip(raw.annotations.onset,raw.annotations.description) if d.replace(' ','').split('/')[-1] in ['S7','S8']]
        if actual!=expected:raise ValueError('Native/MNE cue sample mismatch')
        retained,excluded=windows(events,raw.n_times)
        segments=[e for e in events if e['type']=='New Segment']
        if not segments or segments[0]['position_1based']!=1 or not re.fullmatch(r'\d{20}',segments[0]['timestamp']):raise ValueError('Missing native recording timestamp')
        timestamp=segments[0]['timestamp'];session=timestamp[:8];source=path.relative_to(extracted).as_posix();rows=[];values=[]
        for item in retained:
            event=item['event'];start=item['start'];stop=item['end'];code=event['code'];label='1' if code=='S7' else '2'
            row=core.base_row(person,session,'MI',source,event['marker_ordinal'],start,POINTS,500,event['description'],label)
            row.update(source_epoch_index='',source_trial_ordinal=item['trial_index'],source_participant_id=path.parent.name,source_group=group,
                source_run_id='MI',original_session_id='unknown',session_id_evidence='Calendar date from native first New Segment timestamp; one visit per source protocol',
                source_event_sample_1based=event['position_1based'],native_marker_key=event['marker_key'],native_marker_ordinal=event['marker_ordinal'],native_marker_line_number_1based=event['marker_line_number_1based'],
                native_trial_end_sample_1based=item['end_event']['position_1based'],native_trial_end_marker_key=item['end_event']['marker_key'],native_imagery_duration_samples=item['native_duration_samples'],
                recording_timestamp=timestamp,recording_timezone='unknown',source_array_index=f'Native float32 samples[{start}:{stop}], channels[0:32], transposed and calibrated in float64 to microvolts',
                exported_native_channel_indices='[0:32]',source_trial_id='unknown',handedness='right',handedness_evidence='Original release cohort description, not individual header')
            rows.append(row)
            values.append(np.ascontiguousarray(digital[start:stop,:32].T,dtype='<f8')*resolutions[:,None])
        info=dict(source_file=source,source_file_sha256=core.sha(path),native_binary_sha256=core.sha(binary),native_marker_sha256=core.sha(markers),
            participant_id=person,source_participant_id=path.parent.name,source_group=group,session_id=session,run_id='MI',
            native_channel_names=[c['name'] for c in channels],native_channel_types_documented=['EEG']*32+['EMG','EMG','temperature','accelerometer','accelerometer','accelerometer'],
            native_channels=channels,source_eeg_indices=list(range(32)),native_coordinates=coordinates,native_header_text=text,native_markers=events,
            header_filename_overrides=dict(declared_data_file=common['DataFile'],declared_marker_file=common['MarkerFile'],actual_data_file=binary.name,actual_marker_file=markers.name,
                reason='Original deposited same-stem files used; SUB31 header still has pre-rename references'),
            sampling_frequency_hz=500,native_samples=raw.n_times,source_case_count=40,retained_case_count=len(rows),excluded_cases=excluded,
            original_sampling_frequency_hz=500,native_recording_timestamp=timestamp,native_recording_timezone='unknown',
            sensor_position_evidence='Embedded BrainVision coordinate triplets from CLA-32.bvef template, retained verbatim; not measured individual positions',
            source_filter_evidence='Native per-channel hardware/software filter tables retained in native_header_text; no archive DSP',mne_version=mne.__version__)
        print('Decoded',source,'retained',len(rows),'excluded',len(excluded),flush=True)
        yield np.asarray(values,dtype='<f8'),rows,EEG,info


SPEC=dict(name='ImaginedHandsEmbodiment',source='Vagaja2023 / Electrophysiological Signals of Embodiment and MI-BCI Training in VR',cache='Vagaja2023',hz=500,points=POINTS,classes=2,train_subjects=20,splitter=split_people,
    labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.5281/zenodo.8086086',paper='Vagaja and Vourvopoulos(2023), original Zenodo dataset; thesis at VU University Amsterdam, no separate paper DOI established',
    note='Only native MI recording, no resting/embodiment-run relabelling. Native calibrated32EEG in original order, float64 microvolt calibration before export; no extra filter/resampling/reference/baseline. Common4997sample crop stays inside all1040 native S10 end markers; exclude windows crossing lost-sample New Segment markers. First10original IDs within each13-person Embodied/Control group train, remaining3/group test. Preserve original IDs/group/native sample indices and all markers; reference/ground and individual demographics not guessed.',
    evidence_files=['imagined-hands-embodiment-preparation.md','vagaja-source-lock.json','vagaja-native-header-audit.json','vagaja-native-archive-inventory.json'],
    cache_evidence_files=['original-zenodo-record.json','moabb-vagaja2023.py'],conversion_files=['prepare_vagaja.py','download_vagaja.py','prepare_kueper.py'],
    validation_updates=dict(source_sensor_identity='All native38-channel headers verified: first32 explicitly EEG in source description; native names/order and per-channel unit/resolution checked, auxiliary channels excluded'),
    metadata_updates=dict(original_source_url='https://zenodo.org/records/8086086',reference_paper_doi=None,reference='Unknown: native reference-name fields empty; no rereference applied',ground='Unknown electrode identity',
        split_definition='Archive-defined whole-subject split: first10native IDs in each Embodied/Control group TRAIN, remaining3/group TEST; memberships explicit. No official source partition.',
        case_order='Participant numeric ID ascending, native MI recording marker order; no shuffle',
        window_decision='4997samples (9.994seconds) is minimum S10-minus-cue spacing across all1040 trials; original nominal duration10s with observed4997..5001sample marker spacings; no post-trial samples included',
        window_overlap='None among retained source intervals',excluded_source_runs='Resting-state and embodiment-priming recordings,52runs, not additional MI classification problems',
        time_reference='Sample bounds index the stored native file; start/end seconds are index/500, not reconstructed wall-clock elapsed time across lost-sample gaps. Original New Segment timestamps retained, timezone unknown.',
        unit_evidence='Explicit native EEG microvolt units and per-channel resolution; cast float32 digital numbers to float64 before multiplying by native microvolt resolution; independent MNE calibrated-volts decode checked',
        preprocessing='Native hardware/software filters as recorded in each header; float64 calibration, EEG selection, common cue crop and global flat policy only; no added filter, resampling, baseline or rereference.',
        cohort_demographics_documented={'subjects':26,'male':10,'female':16,'handedness':'all right','prior_bci_experience':3,'individual_mapping':'Not distributed; original release says contact authors'},
        missing_or_inconsistent_metadata=['Original individual age/sex/experience mappings not distributed; cohort summaries only',
            'Reference/ground electrode names and individual measured geometry unknown; native coordinates are an acquisition template',
            'Original VHDR SUB31 uses pre-rename binary/marker filenames; actual same-stem deposited files used explicitly',
            'Lost-sample markers inside two imagery windows; those two cases excluded, all source markers retained',
            'S10 end timing varies4997..5001samples; common4997sample crop documented rather than guessing nominal endpoints',
            'No original train/test partition; stratified whole-subject archive split assigned',
            'Same laboratory/hardware as Batista2022 is not proof of shared recordings; future Batista admission must compare native filenames/dates/waveforms'],
        metadata_evidence=dict(direct='Native sensor names/order/calibration/coordinate triplets, header filter tables, subject/group folders, recording timestamps, all marker/sample indices and exclusions',
            documented='Original licence,26-person cohort,32EEG/auxiliary roles, handedness and one-visit VR protocol',
            assigned='Encoded labels, whole-subject split, date-based session IDs, source trial ordinals and common4997sample crop',
            missing='Original trial IDs, distinct visit IDs, individual demographics, timezone, electrode reference/ground and individually measured geometry')))


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPEC)
    spec['intermediate_directory']='classification-intermediate-full'
    if pilot:spec.update(name='ImaginedHandsEmbodimentPilot',subjects=['03','30'],intermediate_directory='classification-intermediate-pilot')
    cache=Path(cache_root)/SPEC['cache']
    # Copy every small native header/marker as evidence, never the large EEG binaries.
    inventory=json.loads((ROOT/'docs/vagaja-native-archive-inventory.json').read_text(encoding='utf-8'))
    spec['cache_evidence_files'] += ['extracted/'+f['name'] for f in inventory if f['name'].endswith(('.vhdr','.vmrk'))]
    core.SPECS['vagaja']=spec;core.READERS['vagaja']=records
    return finish_sidecars(core.prepare('vagaja',cache_root,output))


def finish_sidecars(result):
    folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    first=m['recordings'][0]
    m['time_reference']=SPEC['metadata_updates']['time_reference']
    same=all(r['native_coordinates']==first['native_coordinates'] for r in m['recordings'])
    filter_configurations=set()
    for recording in m['recordings']:
        filters=[]
        for line in recording['native_header_text'].splitlines():
            fields=line.split()
            if len(fields)>=8 and fields[0].isdigit() and fields[1] in EEG:
                filters.append(dict(name=fields[1],low_cutoff_seconds=fields[5],high_cutoff_hz=fields[6],notch_hz=fields[7]))
                filter_configurations.add(tuple(fields[5:8]))
        if [f['name'] for f in filters]!=EEG:raise ValueError('Incomplete native EEG hardware filter table')
        recording['native_hardware_eeg_filter_table']=filters
        recording['native_software_filters']='Disabled' if re.search(r'S o f t w a r e  F i l t e r s\s*=+\s*Disabled',recording['native_header_text']) else 'See native header'
    m['source_hardware_eeg_filter_configurations']=[dict(low_cutoff_seconds=a,high_cutoff_hz=b,notch_hz=c) for a,b,c in sorted(filter_configurations)]
    m['source_software_filter_settings']=sorted({r['native_software_filters'] for r in m['recordings']})
    for sensor in m['sensors']:
        i=EEG.index(sensor['name']);sensor.update(native_channel_index=i,source_coordinate_triplet=first['native_coordinates'][i] if same else None,
            position_evidence='Embedded CLA-32.bvef template triplet, not individual measured geometry; see per-recording header',units_evidence=m['unit_evidence'])
    indices=[s['native_channel_index'] for s in m['sensors']]
    for r in m['recordings']:r['exported_native_channel_indices']=indices
    m['aliases']=['Vagaja2023','NEMAR nm000292','Electrophysiological Signals of Embodiment and MI-BCI Training in VR']
    m['source_case_count']=sum(r['source_case_count'] for r in m['recordings']);m['excluded_case_count']=sum(len(r['excluded_cases']) for r in m['recordings'])
    m['coordinate_template_consistent_all_mi_recordings']=same
    if result['train_cases']+result['test_cases']+m['excluded_case_count']!=m['source_case_count']:raise ValueError('Native cue/export accounting mismatch')
    return finish(result,m,SPEC['evidence_files'],SPEC['conversion_files'],dict(original_source_url=m['original_source_url'],licence_url='https://creativecommons.org/licenses/by/4.0/',label_mapping=SPEC['labels'],split_definition=m['split_definition'],unit_evidence=m['unit_evidence']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true')
    a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
