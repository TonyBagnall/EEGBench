"""Original MILimb imagery CSV epochs -> ImaginedHandFootActions."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import numpy as np
from tools import prepare_open_moabb as core
from tools.download_milimb import PATTERN
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
CHANNELS='FC5 F3 Fz F4 FC6 FC1 FC2 Cz T7 CP5 C3 CP1 CP2 C4 CP6 T8'.split()
LABELS={'1':'baseline_eyes_open','2':'imagined_left_hand_closing','3':'imagined_right_hand_closing','4':'imagined_left_foot_dorsiflexion',
 '5':'imagined_left_foot_plantarflexion','6':'imagined_right_foot_dorsiflexion','7':'imagined_right_foot_plantarflexion','8':'rest_between_imagined_tasks'}


def native_csv(path):
    with Path(path).open(encoding='utf-8',newline='') as f:header=next(csv.reader(f))
    if header[0] not in ['', 'NaN'] or header[1:]!=[str(i) for i in range(16)]:raise ValueError('Changed original CSV channel column order')
    x=np.loadtxt(path,delimiter=',',skiprows=1,dtype=np.float64)
    if x.shape!=(500,17) or not np.array_equal(x[:,0],np.arange(500)) or not np.isfinite(x).all():raise ValueError('Invalid native epoch/index/shape')
    return np.ascontiguousarray(x[:,1:].T,dtype='<f8')


def file_order(f):
    p=PATTERN.fullmatch(Path(f['name']).name)
    if not p:raise ValueError('Unknown original imagery filename')
    return int(p[1][1:]),int(p[2][1:]),int(p[3]),tuple(int(x) for x in p[4].split('_'))


def source_exclusions():
    audit=json.loads((ROOT/'docs/milimb-native-quality-audit.json').read_text(encoding='utf-8'))
    if audit['cases']!=3719 or len(audit['duplicate_groups'])!=31:raise ValueError('Source copy audit changed: review before exclusions')
    excluded={}
    for group in audit['duplicate_groups']:
        if len(group)!=2 or {e['participant_id'] for e in group}!={'S1','S2'} or {e['source_label'] for e in group}!={'8'}:raise ValueError('Unexpected copy/label scope')
        if len({e['sha256'] for e in group})!=1:raise ValueError('Expected exact publisher-byte copies')
        for e in group:excluded[e['name']]=dict(e,reason='Original rest waveforms copied across S1/S2; correct owner unresolved. Exclude both copies without guessing identity.')
    return excluded


def records(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    files=[f for f in receipt['files'] if 'participant_id' in f];excluded=source_exclusions()
    for person in sorted({f['participant_id'] for f in files},key=lambda p:int(p[1:])):
        if spec.get('pilot') and person not in ['S3','S60']:continue
        source_files=[f for f in files if f['participant_id']==person]
        rejected=[]
        for f in source_files:
            if f['name'] in excluded:
                if f['sha256']!=excluded[f['name']]['sha256']:raise ValueError('Excluded source changed')
                rejected.append(excluded[f['name']])
        selected=sorted((f for f in source_files if f['name'] not in excluded),key=file_order);values=[];rows=[];native=[]
        for f in selected:
            path=cache/f['name'];match=PATTERN.fullmatch(path.name);x=native_csv(path);values.append(x)
            row=core.base_row(person,'unknown',match[2],f['name'],0,0,500,125,match[3],match[3])
            row.update(source_epoch_index=path.stem,source_trial_id=path.stem,source_event_sample='',source_array_index='CSV rows0:500, native numeric channel columns0:16; leading sample-index column excluded',
                source_trial_suffix=match[4],source_task_repetition_tokens=json.dumps(match[4].split('_')),source_listing_index=f['source_listing_index'],
                source_file_sha256=f['sha256'],source_file_id=f['source_file_id'],sample_reference='Native epoch-local samples; original continuous offsets unavailable',
                original_continuous_start_sample='',original_continuous_end_sample='',source_paradigm_token='I',
                session_id_evidence='Actual recording visit not recovered; R1 is native experiment/run repetition, not a verified separate visit',
                label_evidence='Original filename I1..I8 and original author encoding figure; rest suffixes retained without inferred acquisition chronology')
            rows.append(row);native.append(dict(source_file=f['name'],sha256=f['sha256'],source_file_id=f['source_file_id'],native_shape=[500,17],native_sample_index_column=True,native_channel_headers=[str(i) for i in range(16)],source_label=match[3],source_trial_suffix=match[4]))
        info=dict(participant_id=person,session_id=None,native_run_ids=sorted({f['run_id'] for f in selected}),source_case_count=len(rows),source_input_epoch_files=len(source_files),excluded_epoch_files=rejected,
            source_epoch_files=native,native_channel_headers=[str(i) for i in range(16)],source_sensor_mapping_figure='16_OpenBCI_electrodes_10_10system.png',
            source_sensor_indices_1based=list(range(1,17)),documented_channel_names=CHANNELS,sampling_frequency_documented_hz=125,
            unit_evidence='Original release explicitly documents CSV electrode values as microvolts; native numeric values unchanged')
        yield np.stack(values),rows,list(CHANNELS),info


def specification(pilot=False):
    return dict(name='ImaginedHandFootActions'+('CleanPilot' if pilot else ''),pilot=pilot,source='MILimbEEG imagery/baseline/rest CSVs',cache='MILimbEEG',hz=125,points=500,classes=8,train_subjects=45,
        splitter=lambda people,chunks:set(sorted(people,key=lambda p:int(p[1:]))[:1 if pilot else 45]),labels=LABELS,doi='10.17632/x8psbz3f6x.2',
        paper='Asanza et al.(2023),Motor and motor imagery limb EEG dataset (MILimbEEG); 10.1016/j.dib.2023.109540',
        intermediate_directory='clean-pilot-classification-intermediate' if pilot else 'quality-filtered-classification-intermediate',
        note='Select original I1..I8 imagery/baseline/rest files only, not motor execution M files. Native16 numbered CSV columns map in order to author numbered electrode figure1..16; discard explicit0..499sample index column. Retain500samples (4seconds125Hz), original float64-parsed microvolt numbers without rescaling/filtering/resampling/reference changes. Keep exact source filenames/labels/suffixes and global flat policy. S1-S45 train,S46-S60test; no original official split or continuous offsets. Exclude all62 ambiguous cross-ID rest copies from S1/S2, without choosing an owner; source exclusion list retained. S22 lacks I2trial5, no fabricated case. Baseline/rest retained as separate original classes.',
        evidence_files=['milimb-source-lock.json','milimb-preparation.md','milimb-native-quality-audit.json','milimb-header-audit.json'],cache_evidence_files=['original-record.json','16_OpenBCI_electrodes_10_10system.png','CSV_files_encoding.png','Test_Subject_Annotations.csv'],
        conversion_files=['prepare_milimb.py','download_milimb.py','update_dataset_sidecars.py'],
        validation_updates=dict(source_sensor_identity='Every CSV header0..15 checked; anatomical mapping recovered from original numbered electrode figure1..16',
            cross_split_overlapping_intervals=None,original_continuous_interval_overlap='Unknown original continuous offsets; distributed native epochs and source participants disjoint'),
        metadata_updates=dict(reference_paper_doi='10.1016/j.dib.2023.109540',reference_paper='Asanza et al.(2023),Motor and motor imagery limb EEG dataset (MILimbEEG)',original_source_url='https://data.mendeley.com/datasets/x8psbz3f6x/2',source_study='MILimbEEG, one mixed execution/imagery study',
            reference='Monopolar relative to neutral electrode on both ear lobes, documented in original release; native CSV reference absent',ground='Not independently recovered',
            split_definition='S1-S45 TRAIN,S46-S60TEST, numeric original ID order, whole subjects; archive assigned, original data unsplit',
            case_order='Participant numeric ID, native run R token, task code, numeric suffix order. Deterministic source file order, not claimed original acquisition chronology; original API listing index retained.',
            original_partition='Unsplit original epoch files',unit_evidence='Original release explicitly states CSV electrode values in microvolts. Float64 parse, multiplier1; leading sample-index column excluded.',
            preprocessing='Distributed source CSV epochs preserved. Original release documents5-50Hz active bandpass and60Hz notch; example7-31Hz filtering/normalisation/feature extraction are not reapplied by archive. No added filter/resample/rereference/baseline/normalisation.',
            missing_or_inconsistent_metadata=['Original continuous recording offsets, acquisition timestamps and visits unavailable; R1 is native repetition token, not asserted session date',
                '31original rest file pairs copied across S1/S2; both members excluded symmetrically, no correct owner/label guessed. S1/S2 retain their unambiguous baseline/imagery epochs but no class8rest.',
                'Native CSV sensor headers are numeric; anatomical identities are recovered from original indexed author figure, not from CSV text',
                'Source reference/filter/rate/physical units documented by original release rather than embedded in CSV',
                'No measured individual sensor coordinates; original placement figure retained, no synthetic geometry',
                'Version2 lists7440 epoch files across60subject folders; selected imagery files3719, all R1, unlike larger published headline/repetition counts',
                'S22R1I2_5.csv absent from original listing; retain299 left-hand cases, no invented or relabelled replacement',
                'Participant annotations contain mixed-language/format values and inconsistent height units; originals retained as strings without guessed corrections'],
            metadata_evidence=dict(direct='Original CSV sample index, numeric channel order, exact waveforms, file-based subject/run/class/trial IDs and original participant annotations',
                documented='Author numbered placement and filename encoding figures; original125Hz, microvolt units, reference/filter/protocol description',
                assigned='Whole-subject split and deterministic source-file ordering; unknown session placeholder is not a recovered visit',
                missing='Continuous offsets/dates and individually measured electrode geometry')))


def finish_sidecars(result):
    folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    m.update(specification()['metadata_updates'])
    for s in m['sensors']:
        i=s['pre_flat_removal_array_index'];s.update(native_channel_index=i,native_csv_column_header=str(i),author_sensor_index_1based=i+1,
            identity_evidence='Original author figure explicitly numbers physical channels1..16; CSV0..15 order preserved',position=None,position_evidence='Original placement graphic retained; no individual XYZ invented')
    for r in m['recordings']:r['exported_native_channel_indices']=[s['native_channel_index'] for s in m['sensors']]
    m['conversion_chunk_count']=len(m['recordings']);m['recording_count']=None;m['native_epoch_file_count']=sum(r['source_case_count'] for r in m['recordings'])
    m['recording_count_evidence']='One exporter chunk per participant; native continuous acquisition count not recoverable from the per-epoch CSVs'
    m['source_input_epoch_file_count']=sum(r['source_input_epoch_files'] for r in m['recordings'])
    m['excluded_epoch_files']=[e for r in m['recordings'] for e in r['excluded_epoch_files']]
    m['excluded_epoch_file_count']=len(m['excluded_epoch_files'])
    if m['source_input_epoch_file_count']!=m['native_epoch_file_count']+m['excluded_epoch_file_count']:raise ValueError('Source/exclusion/case accounting mismatch')
    m['sessions_per_subject']={p:None for p in m['session_ids']}
    cache=Path(result['source_cache'])
    with (cache/'Test_Subject_Annotations.csv').open(encoding='utf-8-sig',newline='') as f:participants=list(csv.DictReader(f))
    m['participants']=[p for p in participants if p.get('ID Subject') in m['session_ids']]
    if len(m['participants'])!=m['subjects']:raise ValueError('Incomplete native participant annotation join')
    m['participant_annotation_evidence']='Original public CSV string fields unmodified; birth dates not converted to age, mixed height/unit fields not repaired'
    m['aliases']=['MILimbEEG','MILimbEEG motor imagery only'];m['metadata_evidence']['availability']=dict(subject_id=True,run_id=True,session_visit=False,trial_id=True,native_sample_index='epoch-local',
        channel_names='original author figure, native CSV numeric headers',channel_type='documented EEG',positions='placement graphic only',physical_units='original release explicit',participant_annotations=True,original_partition=False)
    return finish(result,m,['milimb-source-lock.json','milimb-preparation.md','milimb-native-quality-audit.json','milimb-header-audit.json'],['prepare_milimb.py','download_milimb.py','audit_milimb.py','requirements-moabb.txt'],
        dict(original_source_url=m['original_source_url'],label_mapping=LABELS,split_definition=m['split_definition'],split_unit='participant',source_cache=result['source_cache'],
            original_input_epoch_files=m['source_input_epoch_file_count'],excluded_epoch_files=m['excluded_epoch_file_count'],retained_epoch_files=m['native_epoch_file_count'],
            licence_url='https://creativecommons.org/licenses/by/4.0/',storage_note='Originally prepared under C:/Temp while D was offline; verified relocation to the current archive paths is recorded separately'))


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output).free<4_000_000_000:raise OSError('Keep4GB destination reserve before conversion')
    key='milimb';core.SPECS[key]=specification(pilot);core.READERS[key]=records
    result=core.prepare(key,cache_root,output);result['source_cache']=str(Path(cache_root)/'MILimbEEG')
    return finish_sidecars(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',action='store_true');p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
