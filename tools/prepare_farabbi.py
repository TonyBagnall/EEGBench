"""Original Farabbi2020 GDF -> ImaginedHandsRobot, preserving phase splits."""
import argparse
import copy
import json
from pathlib import Path
import re

import numpy as np
from tools import prepare_open_moabb as core
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]


def locations(path):
    result=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        fields=line.split();index=int(fields[0])-1
        if index!=len(result) or len(fields)!=4:raise ValueError('Unknown original indexed sensor layout')
        result.append(dict(native_channel_index=index,name=fields[3],theta=float(fields[1]),radius=float(fields[2])))
    if len(result)!=35 or [s['name'] for s in result[32:]]!=['ACC_X','ACC_Y','ACC_Z']:raise ValueError('Unexpected EEG/ACC layout')
    return result


def identity(path,root):
    parts=path.relative_to(root).parts
    if len(parts)!=4 or not re.fullmatch(r'\d{2}',parts[0]) or not re.fullmatch(r'\d{2}_session_\d',parts[1]):raise ValueError('Unknown native subject/session path')
    match=re.fullmatch(r'(1st|3rd)-person-(training|online)-\[([\d.]+-[\d.]+)\]\.gdf',path.name)
    if not match:raise ValueError('Unknown native condition/phase filename')
    view,phase,date=match.groups();condition=re.fullmatch(r'(\d)_condition_(\d)',parts[2])
    if not condition or condition[2]!=('1' if view=='1st' else '2'):raise ValueError('Native feedback condition disagrees with filename')
    return dict(person=parts[0],session=parts[1],condition_folder=parts[2],view=view,phase=phase,date=date)


def archive_partition(row):return 'TRAIN' if row['original_partition']=='training' else 'TEST' if row['original_partition']=='online' else None


def native_cues(extra):
    events=extra['events'];positions=np.asarray(events[1],dtype=int);types=np.asarray(events[2],dtype=int)
    if len(positions)!=int(events[0]) or len(types)!=len(positions):raise ValueError('Invalid GDF native event table')
    result=[]
    for i in np.flatnonzero(np.isin(types,[769,770])):
        trial=np.flatnonzero((types==768)&(positions<=positions[i]))
        if not len(trial):raise ValueError('Class cue without original trial-start marker')
        result.append(dict(event_index=int(i),position=int(positions[i]),type=int(types[i]),trial_index=int(trial[-1]),trial_position=int(positions[trial[-1]]),duration=int(events[4][i])))
    if len({r['trial_index'] for r in result})!=len(result):raise ValueError('Multiple class cues share one source trial')
    return result


def records(cache,spec):
    import mne
    people=spec.get('subjects',[f'{i:02}' for i in range(1,13)]);root=cache/'extracted';loc=locations(cache/'chanlocs.locs');names=[s['name'] for s in loc[:32]]
    for person in people:core.extract_selected(cache/f'{person}.zip',root,lambda n:n.lower().endswith('.gdf'))
    paths=[p for person in people for p in (root/person).rglob('*.gdf') if 'rest' not in p.name.lower()]
    identities={p:identity(p,root) for p in paths};paths.sort(key=lambda p:(0 if identities[p]['phase']=='training' else 1,int(identities[p]['person']),identities[p]['session'],identities[p]['date'],p.as_posix()))
    for path in paths:
        ids=identities[path];raw=mne.io.read_raw_gdf(path,preload=True,verbose=False);extra=raw._raw_extras[0]
        if raw.ch_names!=[f'Channel {i}' for i in range(1,36)] or raw.info['sfreq']!=250 or extra['orig_nchan']!=35:raise ValueError('Changed native GDF channel order/rate')
        if not np.array_equal(np.asarray(extra['units'])[:32],np.full(32,1e-6)):raise ValueError('Changed native EEG physical units')
        cues=native_cues(extra);decoded=[int(raw.time_as_index([o],use_rounding=True)[0]) for o,d in zip(raw.annotations.onset,raw.annotations.description) if d in ['769','770']]
        if decoded!=[r['position'] for r in cues]:raise ValueError('Native GDF/MNE annotation indexing differs')
        data=np.asarray(raw.get_data(picks=list(range(32))),dtype='<f8')*1e6;values=[];rows=[];excluded=[];source=path.relative_to(root).as_posix()
        for cue in cues:
            start=cue['position'];end=start+1000
            if end>raw.n_times:excluded.append(dict(cue,reason='Recording ends before complete four-second imagery window'));continue
            row=core.base_row(ids['person'],ids['session'],path.stem,source,cue['event_index'],start,1000,250,str(cue['type']),'1' if cue['type']==769 else '2')
            row.update(source_epoch_index='',original_partition=ids['phase'],source_event_sample_1based=start+1,
                source_trial_start_event_index=cue['trial_index'],source_trial_start_sample_1based=cue['trial_position']+1,
                source_event_duration_samples=cue['duration'],cue_delay_from_trial_start_seconds=(start-cue['trial_position'])/250,
                condition_folder=ids['condition_folder'],feedback_perspective=ids['view']+'-person',source_filename_datetime=ids['date'],
                source_array_index=f'MNE GDF physical EEG[0:32,{start}:{end}], float64 volts*1e6',
                source_label_description='left_hand_cue' if cue['type']==769 else 'right_hand_cue',
                handedness_documented='ambidextrous' if ids['person']=='05' else 'right',handedness_evidence='Publisher description: participant05 ambidextrous, others right-handed; not native GDF demographics',
                original_trial_id_evidence='Native trial-start event index and samples retained; no invented original epoch ID')
            rows.append(row);values.append(core.crop(data,start,1000))
        info=dict(core.mne_info(raw),source_file=source,source_file_sha256=core.sha(path),participant_id=ids['person'],session_id=ids['session'],run_id=path.stem,
            native_subject_info=dict(raw.info['subject_info']) if raw.info['subject_info'] else None,native_measurement_datetime=raw.info['meas_date'].isoformat() if raw.info['meas_date'] else None,
            source_condition=ids,native_gdf_cal=extra['cal'],native_gdf_offsets=extra['offsets'],native_gdf_event_table=extra['events'],
            native_highpass=extra.get('highpass'),native_lowpass=extra.get('lowpass'),source_eeg_indices=list(range(32)),
            sensor_identity_evidence='Original chanlocs.locs numbered1-35 maps native GDF ChannelN; first32 EEG, last3ACC from original source record',
            source_sensor_locations=loc,source_motion_or_imagery='Cued imagination, not executed movement',
            source_case_count=len(cues),excluded_incomplete_cases=excluded,source_partition=ids['phase'],
            auxiliary_unit_caveat='GDF uses same voltage-unit prefix for all35 inputs; last3 are documented accelerometers, physical ACC units not independently established; excluded from X',
            native_timezone='Not established; retain filename and MNE interpretation separately')
        info['mne_default_channel_types']=info.pop('native_channel_types');info['channel_types_documented']=['EEG']*32+['accelerometer']*3
        raw.close();yield np.stack(values),rows,names,info


SPEC=dict(name='ImaginedHandsRobot',source='Farabbi2020 / Motor-Imagery EEG Dataset During Robot-Arm Control',cache='Farabbi2020',hz=250,points=1000,classes=2,train_subjects=0,
    labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.5281/zenodo.5882500',paper='Farabbi et al., Motor-Imagery EEG Dataset During Robot-Arm Control; related thesis hdl.handle.net/10589/164451',
    case_splitter=archive_partition,allow_subject_overlap=True,subject_overlap_reason='Archive preserves source training-phase versus online-test-phase files within each participant/session/feedback condition. All people and sessions intentionally shared; pooled across days, not independent-person or strict chronological session transfer.',
    note='Original GDF calibrated by MNE then float64 volts*1e6; four-second windows at native769/770 class-cue events, never trial-start+nominal2sec. Original indexed chanlocs.locs supplies32EEG identities/order/polar positions; native names are generic Channel1-35. Exclude3ACC, no filter/resample/reference/baseline. Training-phase files form TRAIN, online-test files TEST across3sessions and2feedback perspectives, no validation. Native phase semantics preserved; pooling is an archive protocol, not reproduction of the original per-session fitted decoder.',
    evidence_files=['imagined-hands-robot-preparation.md','imagined-hands-robot-source-lock.json','farabbi-pilot-source-inspection.json'],
    cache_evidence_files=['original-zenodo-record.json','moabb-farabbi2020.py','chanlocs.locs'],conversion_files=['prepare_farabbi.py','download_farabbi.py','update_dataset_sidecars.py'],
    validation_updates=dict(source_sensor_identity='Every GDF native Channel1-35 order checked; named EEG mapping from original source numbered chanlocs.locs'),
    metadata_updates=dict(original_partition='Original training/online file phases',original_source_url='https://zenodo.org/records/5882500',reference_paper_doi=None,
        reference='Not recovered from native GDF/original source metadata; no assumed rereference',ground='Unknown',
        split_definition='TRAIN all source training-phase runs; TEST all source online-test-phase runs, pooled across participants/sessions/perspectives; people shared intentionally. Not original per-session decoder fitting.',
        case_order='Original training phase then online phase; participant numeric ID, native session token, filename datetime, original cue event order',
        unit_evidence='GDF physical calibration and EEG voltage-unit multiplier1e-6 from native header decoder; calibrated MNE volts cast to float64 and multiplied by1e6',
        missing_or_inconsistent_metadata=['GDF sensor names generic; author numbered chanlocs.locs supplies anatomical mapping, not native embedded names',
            'Reference/ground, individual measured3D geometry, age/sex and original timezone not established',
            'Native class-cue timing differs from nominal two-second baseline; use recorded769/770 onset, not reconstructed schedule',
            'Auxiliary GDF voltage prefixes do not establish real accelerometer units; three ACC inputs excluded',
            'Training/online phases pooled across days; intentional subject/session overlap, not a chronological or independent-person split'],
        metadata_evidence=dict(direct='Native GDF generic names/fs/calibration/events/source session/run/file IDs and decoded samples',
            documented='Original indexed chanlocs names/polar positions, EEG/ACC roles, phase protocol and participant05 handedness',
            assigned='Encoded labels, pooled phase archive split, new epoch ordinals; original native event indices retained',missing='Individual demographics, measured sensor3D positions, reference/ground and original timezone')))


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPEC)
    if pilot:spec.update(name='ImaginedHandsRobotPilot',subjects=['01','12'])
    core.SPECS['farabbi']=spec;core.READERS['farabbi']=records
    return finish_sidecars(core.prepare('farabbi',cache_root,output))


def finish_sidecars(result):
    folder=Path(result['path']);m=json.loads((folder/(result['dataset']+'_metadata.json')).read_text(encoding='utf-8'));loc=m['recordings'][0]['source_sensor_locations']
    for sensor in m['sensors']:
        i=sensor['pre_flat_removal_array_index'];sensor.update(native_channel_index=i,native_gdf_name=f'Channel {i+1}',identity_evidence='Original source chanlocs.locs indexed map to native GDF ChannelN',
            source_polar_theta=loc[i]['theta'],source_polar_radius=loc[i]['radius'],position_evidence='Author supplied polar layout, not individual measured3D geometry',units_evidence=m['unit_evidence'])
    indices=[s['native_channel_index'] for s in m['sensors']]
    for r in m['recordings']:r['exported_native_channel_indices']=indices
    m['aliases']=['Farabbi2020','Motor-Imagery EEG Dataset During Robot-Arm Control'];m['source_case_count']=sum(r['source_case_count'] for r in m['recordings']);m['excluded_case_count']=sum(len(r['excluded_incomplete_cases']) for r in m['recordings'])
    if result['train_cases']+result['test_cases']+m['excluded_case_count']!=m['source_case_count']:raise ValueError('Source cue accounting mismatch')
    return finish(result,m,SPEC['evidence_files'],SPEC['conversion_files'],dict(label_mapping=SPEC['labels'],split_definition=m['split_definition'],original_source_url=m['original_source_url'],licence_url='https://creativecommons.org/licenses/by/4.0/'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
