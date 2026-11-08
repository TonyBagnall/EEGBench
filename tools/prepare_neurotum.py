"""NeuroTUM native XDF -> two single-participant session-transfer problems.

EEG values are untouched apart from float64 casting and authorised global flat
sensor removal. Native shared-host timestamps select indices; no clock fitting,
timestamp dejittering, resampling, filtering or invented montage is applied.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import numpy as np
import yaml
from tools import prepare_open_moabb as core
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
PEOPLE={
 'P1':dict(name='ImaginedRightHandFeetRest',sessions=['S1','S2','S3','S4','S5'],test='S5',labels={'1':'rest','2':'imagined_right_hand','3':'imagined_feet'},actions={'REST':'1','RIGHT HAND MI':'2','LEGS MI':'3'},population='Tetraplegic participant, documented by source paper/loader'),
 'P2':dict(name='ImaginedLeftRightHandRest',sessions=['S1','S2','S3'],test='S3',labels={'1':'rest','2':'imagined_left_hand','3':'imagined_right_hand'},actions={'REST':'1','LEFT HAND MI':'2','RIGHT HAND MI':'3'},population='Able-bodied participant, documented by source paper/loader')}


def session_partition(row):
    return 'TEST' if row['session_id']==PEOPLE[row['participant_id']]['test'] else 'TRAIN'


def native_sensors(info):
    if info['type']!=['EEG'] or info['channel_count']!=['24'] or float(info['nominal_srate'][0])!=250:raise ValueError('Unexpected native EEG stream schema')
    desc=info['desc'][0];group=desc['channels'][0];channels=group['channel']
    names=[c['label'][0] for c in channels]
    if len(names)!=24 or len(set(names))!=24 or group.get('type')!=['EEG']:raise ValueError('Missing/duplicate native EEG identities')
    locations=[]
    for c in channels:
        loc=c.get('location',[{}])[0]
        locations.append({axis:float(loc[axis][0]) if axis in loc else None for axis in ['X','Y','Z']})
    return names,locations,desc


def nearest_sample(times,stamp):
    times=np.asarray(times,dtype=np.float64)
    if len(times)<2 or not np.all(np.diff(times)>0):raise ValueError('Native EEG timestamps must be strictly increasing')
    right=int(np.searchsorted(times,stamp));candidates=[i for i in [right-1,right] if 0<=i<len(times)]
    index=min(candidates,key=lambda i:(abs(times[i]-stamp),i))
    if abs(times[index]-stamp)>0.5/250+1e-5:raise ValueError('Marker is not aligned to a native EEG sample')
    return index


def task_window(data,times,index):
    if index+750>len(data):raise ValueError('Incomplete native three-second window')
    gaps=np.diff(times[index:index+750])
    if not np.all((gaps>0)&(gaps<1.5/250)):raise ValueError('Native dropout inside selected task window')
    return np.ascontiguousarray(data[index:index+750].T,dtype='<f8')


def validate_timestamps(times,stamps):
    if not np.all(np.diff(times)>0) or not np.all(np.diff(stamps)>=0):raise ValueError('Changed native data/timestamp ordering')
    # P1S3 has two coincident empty marker entries. Preserve both and their
    # ordinals; they are not task cues and do not require sorting or dropping.
    return np.flatnonzero(np.diff(stamps)==0).tolist()


def records(cache,spec):
    import pyxdf
    person=spec['person'];cfg=PEOPLE[person]
    mapping=yaml.safe_load((cache/(person+'_mapping.yaml')).read_text(encoding='utf-8'))['mapping']
    if set(mapping.values())!=set(cfg['actions']) or any(not k.endswith(' BLACKSCREEN') for k in mapping):raise ValueError('Changed original participant task mapping')
    mapping={k:cfg['actions'][v] for k,v in mapping.items()}
    for session in cfg['sessions']:
        if spec.get('pilot') and session not in ['S1',cfg['test']]:continue
        path=cache/f'{person}_{session}_data.xdf'
        streams,file_header=pyxdf.load_xdf(str(path),synchronize_clocks=False,dejitter_timestamps=False)
        eegs=[s for s in streams if s['info']['type']==['EEG']];marks=[s for s in streams if s['info']['type']==['Markers']]
        if len(eegs)!=1 or len(marks)!=1:raise ValueError('Ambiguous original EEG/marker streams')
        eeg,markers=eegs[0],marks[0];names,locations,desc=native_sensors(eeg['info'])
        if eeg['info']['hostname']!=markers['info']['hostname']:raise ValueError('Different source clock hosts: alignment review required')
        data=eeg['time_series'];times=np.asarray(eeg['time_stamps']);stamps=np.asarray(markers['time_stamps'])
        if data.ndim!=2 or data.shape[1]!=24 or data.dtype!=np.float32:raise ValueError('Changed native data schema')
        coincident=validate_timestamps(times,stamps)
        values=[];rows=[];source=path.name
        for i,(stamp,entry) in enumerate(zip(stamps,markers['time_series'])):
            cue=str(entry[0]).strip()
            if cue not in mapping:continue
            index=nearest_sample(times,float(stamp));x=task_window(data,times,index)
            # A recorded later marker must not interrupt the three-second crop.
            if i+1>=len(stamps) or stamps[i+1]-stamp<3-1/250:raise ValueError('Native task is shorter than the selected three seconds')
            row=core.base_row(person,session,'data',source,i,index,750,250,cue,mapping[cue])
            row.update(source_epoch_index='',source_array_index=f'EEG.time_series[{index}:{index+750},:].T',source_marker_index=i,
                source_marker_timestamp=float(stamp),source_eeg_start_timestamp=float(times[index]),source_eeg_last_timestamp=float(times[index+749]),
                source_eeg_end_exclusive_timestamp=float(times[index+750]) if index+750<len(times) else '',
                source_next_marker_timestamp=float(stamps[i+1]),source_next_marker=str(markers['time_series'][i+1][0]),
                marker_alignment_error_seconds=float(times[index]-stamp),source_action=next(k for k,v in cfg['actions'].items() if v==mapping[cue]),
                timestamp_reference='Native XDF LSL shared-host monotonic clock, not UTC; no synchronisation/dejittering',
                run_id_evidence='Assigned data recording; original Pn_Sn filename identifies native participant/session')
            rows.append(row);values.append(x)
        if not rows:raise ValueError('No original labelled blackscreen markers')
        info=dict(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id=session,run_id='data',
            source_case_count=len(rows),native_shape=list(data.shape),native_dtype=str(data.dtype),native_channel_names=names,native_channel_types=['EEG']*24,
            native_sensor_positions=locations,native_eeg_info=eeg['info'],native_marker_info=markers['info'],native_eeg_footer=eeg['footer'],native_marker_footer=markers['footer'],
            native_xdf_file_header=file_header,native_eeg_clock_times=eeg['clock_times'],native_eeg_clock_offsets=eeg['clock_values'],
            native_marker_clock_times=markers['clock_times'],native_marker_clock_offsets=markers['clock_values'],
            native_coincident_marker_indices=coincident,
            native_label_mapping=mapping,native_marker_sequence=[dict(index=i,timestamp=float(t),value=str(v[0])) for i,(t,v) in enumerate(zip(stamps,markers['time_series']))],
            timestamp_step_min=float(np.diff(times).min()),timestamp_step_max=float(np.diff(times).max()),
            native_first_timestamp=float(times[0]),native_last_timestamp=float(times[-1]),
            physical_unit_evidence='No physical unit field in inspected native XDF; Smarting microvolt interpretation follows source loader and plausible amplitude. Native numbers unchanged.',
            original_sampling_frequency_hz=250,pyxdf_version=pyxdf.__version__)
        yield np.stack(values),rows,names,info


def specification(person,pilot=False):
    cfg=PEOPLE[person]
    return dict(name=cfg['name']+('Pilot' if pilot else ''),person=person,pilot=pilot,source='NeuroTUMBCI2025 / '+person,
        cache='NeuroTUMBCI2025',hz=250,points=750,classes=3,train_subjects=0,labels=cfg['labels'],doi='10.5281/zenodo.18087806',
        paper='neuroTUM e.V.(2025),neuroTUM-BCI:Cybathlon Dataset; Tscherniak et al.,10.48550/arXiv.2511.23384',
        case_splitter=session_partition,allow_subject_overlap=True,
        subject_overlap_reason='Intentional single-participant session-transfer problem. Last native session TEST, earlier sessions TRAIN; participant shared, recording sessions disjoint. Not unseen-person evaluation.',
        intermediate_directory=('pilot-' if pilot else '')+person+'-classification-intermediate',
        note='One original participant per problem, original subject-specific three-class map retained. Native 24EEG labels/order/locations recovered from XDF, no guessed standard names or montage. Source float32 numbers cast float64 unchanged, presumed microvolts. Nearest actual native EEG sample to blackscreen cue on shared-host LSL clocks,750samples; no clock fitting/dejittering, filtering, resampling or reference change. Global flat-channel policy. Last native session test, earlier sessions train; no archived validation.',
        evidence_files=['neurotum-source-lock.json','neurotum-preparation.md'],cache_evidence_files=['original-record.json',person+'_mapping.yaml'],
        conversion_files=['prepare_neurotum.py','download_neurotum.py','download_compact_imagery.py','update_dataset_sidecars.py','requirements-neurotum.txt'],
        validation_updates=dict(source_sensor_identity='Every native XDF EEG descriptor supplies24names/order/types; exact native spelling retained',
            distinct_recording_sessions_train_test=True),
        metadata_updates=dict(reference_paper_doi='10.48550/arXiv.2511.23384',reference_paper='Tscherniak et al., Improving motor imagery decoding methods for an EEG-based mobile brain-computer interface in the context of the2024Cybathlon',original_source_url='https://zenodo.org/records/18087806',source_participant_id=person,source_study='NeuroTUM Cybathlon, one study with two distinct individuals',
            population=cfg['population'],split_definition=f'{person}: native '+','.join(s for s in cfg['sessions'] if s!=cfg['test'])+' TRAIN; '+cfg['test']+' TEST. Archive-defined session split, not an official original train/test protocol.',
            published_analysis_preprocessing='Paper v4 Table1:4-36Hz filter, order16,10second initial crop,ASR and common-average reference followed by baseline correction/epoching and optional normalisation. These analysis operations are NOT reapplied to the archived native XDF values.',
            original_partition='unsplit original labelled session files',reference='Unknown; no reference field recovered',ground='Unknown',
            unit_evidence='Presumed microvolt scale; explicit physical units absent from native descriptor. Original float32 numeric values cast float64, multiplier1.',
            coordinate_evidence='Native Smarting/EasyCap XYZ descriptors retained in original numeric frame/units; individual measurement and physical coordinate units not established; no template substituted.',
            case_order='Native session-number order, native marker order within each session, no shuffle',
            missing_or_inconsistent_metadata=['One participant per problem; shared participant is intentional, not a cross-subject benchmark',
                'Physical unit field, original reference/ground, individual measured geometry and calendar dates/timezone not recovered',
                'Native positions appear cap geometry, but physical units/frame and individual measurement status unspecified',
                'LSL timestamps are monotonic clock values, not calendar times; same source hostname checked, no clock/dejitter transformations applied',
                'Original source has no fixed train/test split; native session-number split assigned by archive'],
            metadata_evidence=dict(direct='Native XDF sensor names/order/type/XYZ, sample values, marker labels/timestamps, stream descriptors and clock offsets; original YAML label map',
                documented='Participant clinical/healthy status and motor-imagination paradigm from source description/loader',
                assigned='Encoded classes, last-session split, nearest-sample alignment and three-second crop; run=data assigned',
                inferred='Presumed microvolt scale only; no standard sensor names or physical XYZ units invented')))


def finish_sidecars(result,person):
    folder=Path(result['path']);m=json.loads((folder/(result['dataset']+'_metadata.json')).read_text(encoding='utf-8'));first=m['recordings'][0]
    m.update(specification(person)['metadata_updates'])
    same=all(r['native_sensor_positions']==first['native_sensor_positions'] for r in m['recordings'])
    m['native_positions_consistent_across_sessions']=same
    for s in m['sensors']:
        i=s['pre_flat_removal_array_index'];s.update(native_channel_index=i,native_position=first['native_sensor_positions'][i] if same else None,
            position_evidence='Native descriptor coordinates, unknown physical units/frame/measurement status; per-recording values retained',identity_evidence='Native XDF channel label at original array column',units_evidence=m['unit_evidence'])
    for r in m['recordings']:r['exported_native_channel_indices']=[s['native_channel_index'] for s in m['sensors']]
    m['aliases']=['NeuroTUMBCI2025 '+person,'neuroTUM-BCI Cybathlon '+person]
    m['metadata_evidence']['availability']=dict(subject_id=True,session_id=True,run_id='assigned',trial_id='native marker ordinal',native_sample_indices=True,
        native_channel_names=True,native_channel_types=True,native_positions='present but coordinate units/frame/measurement status unknown',physical_units='inferred',
        reference=False,original_partition=False,calendar_date=False)
    return finish(result,m,['neurotum-source-lock.json','neurotum-preparation.md'],['prepare_neurotum.py','download_neurotum.py','download_compact_imagery.py','requirements-neurotum.txt'],
        dict(original_source_url=m['original_source_url'],label_mapping=PEOPLE[person]['labels'],split_definition=m['split_definition'],
            source_participant_id=person,split_unit='native session',train_sessions=[s for s in PEOPLE[person]['sessions'] if s!=PEOPLE[person]['test']],test_sessions=[PEOPLE[person]['test']],
            source_cache=result.get('source_cache','D:/Data/EEGSources/NeuroTUMBCI2025'),intentional_shared_subjects=[person],
            licence_url='https://creativecommons.org/licenses/by/4.0/',storage_note='Originally prepared under C:/Temp while D was offline; current archive location is given by source_cache and the output result path'))


def prepare(person,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output).free<4_000_000_000:raise OSError('Need4GB free before converting; keep destination free-space reserve')
    key='neurotum-'+person.lower();core.SPECS[key]=specification(person,pilot);core.READERS[key]=records
    result=core.prepare(key,cache_root,output);result['source_cache']=str(Path(cache_root)/'NeuroTUMBCI2025')
    return finish_sidecars(result,person)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('person',choices=list(PEOPLE));p.add_argument('--pilot',action='store_true');p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args();prepare(a.person,a.cache_root,a.output,a.pilot)
