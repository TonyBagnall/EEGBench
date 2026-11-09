"""Native motor imagery conversion, separate from benchmark experiments."""
import argparse
import copy
import json
from pathlib import Path
import re

import h5py
import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
LOCAL='Native epoch-local samples; original continuous offsets unavailable'
PAN_SECONDARY='FC5 FC3 FC1 FCz FC2 FC4 FC6 C5 C3 C1 Cz C2 C4 C6 CP5 CP3 CP1 CPz CP2 CP4 CP6 P5 P3 P1 Pz P2 P4 P6'.split()


def pan25_partition(row):
    return 'TEST' if row['session_id']=='2' and int(row['source_epoch_index'])>=30 else 'TRAIN'


def pan_epoch_arrays(path,key):
    """Return native task crops, labels, exact order and timing evidence."""
    if key=='pan23':
        with h5py.File(path) as f:
            if set(f)!= {'data','fs','label'}:raise ValueError('Changed Pan2023 native fields')
            hz=float(np.asarray(f['fs']).item());raw=np.asarray(f['data']);labels=np.asarray(f['label']).ravel()
        if hz!=250 or raw.ndim!=3 or raw.shape[1:]!=(1750,28):raise ValueError('Changed Pan2023 array schema')
        names=[f'source_column_{i+1:02d}' for i in range(28)];cue=750
        x=np.ascontiguousarray(raw[:,cue:cue+1000,:].transpose(0,2,1),dtype='<f8')
        extra=dict(native_epoch_samples=1750,native_channel_names=None,channel_identity_status='Anatomical names absent in native MAT; opaque original column identifiers, no reordering',
                   secondary_channel_name_mapping=PAN_SECONDARY,secondary_mapping_evidence='Pinned MOABB Pan2023 loader; not independently verified against original author channel table',native_data_dtype=str(raw.dtype))
    else:
        d=loadmat(path,simplify_cells=True);info=d['Info'];raw=np.asarray(d['data']);labels=np.asarray(d['label']).ravel()
        names=list(map(str,np.atleast_1d(info['chaninfo'])));hz=float(info['fs']);period=np.asarray(info['period']).ravel()
        if hz!=250 or raw.ndim!=3 or raw.shape[:2]!=(28,1375) or not np.array_equal(period,[-1.5,4]):raise ValueError('Changed Pan2025 native epoch schema')
        task=np.asarray(info['taskpoints']).ravel()
        if not np.array_equal(task,np.arange(376,1376)):raise ValueError('Changed native one-based task indices')
        cue=375;x=np.ascontiguousarray(raw[:,cue:cue+1000,:].transpose(2,0,1),dtype='<f8')
        extra=dict(native_epoch_samples=1375,native_channel_names=names,native_epoch_period=period.tolist(),native_taskpoints_1based=task.tolist(),native_data_dtype=str(raw.dtype))
    if len(names)!=28 or len(set(names))!=28 or len(labels)!=len(x) or not set(labels)<= {1,2}:raise ValueError('Invalid Pan channels or labels')
    return x,labels,names,cue,extra


def pan_records(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));key=spec['key']
    for f in sorted(receipt['files'],key=lambda f:(f['subject'],f['session'])):
        if spec.get('subjects') and f['subject'] not in spec['subjects']:continue
        x,labels,names,cue,extra=pan_epoch_arrays(cache/f['name'],key);rows=[]
        if re.fullmatch(r'S(\d{2})D([12])\.mat',f['name']).groups()!=(f['subject'],f['session']):raise ValueError('Native filename IDs disagree with pinned mapping')
        for i,label in enumerate(labels):
            row=core.base_row(f['subject'],f['session'],'native_session_file',f['name'],i,cue,1000,250,int(label),int(label))
            phase='unsplit' if key=='pan23' else 'session1_offline' if f['session']=='1' else 'session2_training' if i<30 else 'session2_online_test'
            row.update(sample_reference=LOCAL,original_trial_id=str(i+1),trial_id_evidence='One-based position in distributed native epoch array; original continuous trial number unavailable',
                       native_cue_sample_within_epoch=cue,native_epoch_samples=extra['native_epoch_samples'],native_datafile_id=str(f['datafile_id']),
                       original_partition=phase,source_array_index=f'Original trial {i}, all28 original columns, epoch samples[{cue}:{cue+1000}], no channel reordering',
                       original_continuous_start_sample='',original_continuous_end_sample='')
            rows.append(row)
        yield x,rows,names,dict(extra,source_file=f['name'],source_file_sha256=f['sha256'],participant_id=f['subject'],session_id=f['session'],
            source_eeg_indices=list(range(28)),native_channel_types=['EEG']*28,native_sampling_frequency_hz=250,source_case_count=len(x),
            native_units='No explicit units field; native numbers unchanged, microvolt interpretation follows pinned source loader')


def h5char(f,dataset):
    a=np.asarray(dataset)
    return ''.join(chr(int(v)) for v in a.ravel()) if a.dtype.kind in 'ui' else str(a)


def mibmpi_arrays(path,label_path):
    with h5py.File(path) as f:
        def scalar(k):return float(np.asarray(f[k]).item())
        if (scalar('srate'),scalar('nbchan'),scalar('pnts'),scalar('xmin'))!=(128,13,448,-1):raise ValueError('Changed MI-BMPI native schema')
        raw=np.asarray(f['data']);locations=f['chanlocs'];sensors=[]
        for i,ref in enumerate(np.asarray(locations['labels']).ravel()):
            s=dict(name=h5char(f,f[ref]),native_channel_index=i)
            for k in locations:
                v=f[np.asarray(locations[k]).ravel()[i]];a=np.asarray(v)
                if k in ['labels','type','ref']:s[k]=h5char(f,v)
                else:s[k]=core.native_json(a.ravel().tolist())
            sensors.append(s)
        reference=h5char(f,f['ref']);times=np.asarray(f['times']).ravel()
        # This release's EEGLAB times field is in seconds, unlike the usual
        # EEGLAB millisecond convention. Check the values, not a format guess.
        if raw.shape[1:]!=(448,13) or not np.allclose(times,np.arange(-128,320)/128):raise ValueError('Changed native MI-BMPI time axis')
        info=dict(native_sensor_fields=sensors,native_reference=reference,native_history=h5char(f,f['history']),native_comments=h5char(f,f['comments']),
                  native_epoch_samples=448,native_epoch_xmin=-1,native_epoch_xmax=scalar('xmax'),native_sampling_frequency_hz=128,native_data_dtype=str(raw.dtype),
                  native_session=str(int(scalar('session'))),native_times_field_units='seconds, verified numerically against srate and xmin/xmax')
    labels=np.asarray(loadmat(label_path,simplify_cells=True)['labels']).ravel()
    if len(labels)!=len(raw) or not set(labels)<={1,2} or len({s['name'] for s in sensors})!=13:raise ValueError('Invalid native MI-BMPI labels/channels')
    return np.ascontiguousarray(raw[:,128:448,:].transpose(0,2,1),dtype='<f8'),labels,[s['name'] for s in sensors],info


def mibmpi_records(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    for f in sorted(receipt['files'],key=lambda f:f['name']):
        match=re.fullmatch(r'(D0[1-8])_s([12])\.set',f['name'])
        if not match:continue
        person,session=match.groups()
        if spec.get('subjects') and person not in spec['subjects']:continue
        x,labels,names,info=mibmpi_arrays(cache/f['name'],cache/(f['name'][:-4]+'_labels.mat'))
        if info['native_session']!=session:raise ValueError('Native session disagrees with filename')
        rows=[]
        for i,label in enumerate(labels):
            row=core.base_row(person,session,'native_session_file',f['name'],i,128,320,128,int(label),int(label))
            row.update(sample_reference=LOCAL,original_trial_id=str(i+1),native_cue_sample_within_epoch=128,native_epoch_samples=448,
                       trial_id_evidence='Native stored epoch ordinal, not reconstructed continuous trial index',source_label_file=f['name'][:-4]+'_labels.mat',
                       source_array_index=f'Native HDF5 data[{i},128:448,:], transposed time/sensor; float32 cast to float64',
                       original_continuous_start_sample='',original_continuous_end_sample='')
            rows.append(row)
        yield x,rows,names,dict(info,source_file=f['name'],source_file_sha256=f['sha256'],participant_id=person,session_id=session,
            source_eeg_indices=list(range(13)),native_channel_names=names,native_channel_types=[s['type'] for s in info['native_sensor_fields']],source_case_count=len(x))


COMMON=dict(classes=2,licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',
 evidence_files=['mi-to-30-preparation.md'],conversion_files=['prepare_mi_to_30.py','download_mi_to_30.py'],
 note='Native numbers cast to float64; presumed microvolts according to pinned loader, physical unit not embedded. No added filtering, resampling, demeaning, baseline or reference. Native epoch/crop identity retained; original continuous offsets unavailable.')
SPECS={
 'pan23':dict(COMMON,name='ImaginedHandsCrossSession',source='Pan2023',cache='Pan2023',hz=250,points=1000,train_subjects=10,
   splitter=lambda people,chunks:set(people)&{f'{i:02d}' for i in range(1,11)},labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.7910/DVN/251NOW',paper='Pan et al.(2023), DOI10.1088/1741-2552/ad0a01'),
 'pan25':dict(COMMON,name='ImaginedHandsOnline',source='Pan2025',cache='Pan2025',hz=250,points=1000,train_subjects=10,
   case_splitter=pan25_partition,allow_subject_overlap=True,subject_overlap_reason='Original within-person online protocol: session1 plus session2 first30 trials TRAIN, later session2 trials TEST',
   labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.7910/DVN/GH74ZG',paper='Pan(2025), Cross-Session Motor Imagery EEG dataset; related Pan et al.(2023), DOI10.1088/1741-2552/ad0a01'),
 'mibmpi':dict(COMMON,name='ImaginedPhoneGestures',source='MIBMPI2024',cache='MIBMPI2024',hz=128,points=320,train_subjects=6,
   splitter=lambda people,chunks:set(people)&{f'D{i:02d}' for i in range(1,7)},licence='CC-BY-NC-4.0',licence_url='https://creativecommons.org/licenses/by-nc/4.0/',
   labels={'1':'imagined_screen_tap','2':'imagined_thumb_swipe_down'},doi='10.21203/rs.3.rs-4268007/v1',paper='Yilmaz,Yilmaz,Kose; MI-BMPI. Related paper DOI10.1007/s00521-024-10917-5')}
from tools.mi_to_30_native import extra_specs,READERS as NATIVE_READERS
SPECS.update(extra_specs(COMMON))


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPECS[key]);spec['key']=key;cache=Path(cache_root)/spec['cache']
    spec['intermediate_directory']='classification-intermediate-'+('pilot' if pilot else 'full')
    spec['evidence_files'] += [key+'-to-30-source-lock.json'];spec['conversion_files'] += ['mi_to_30_native.py','download_original_ranges.py','lock_daly_release.py']
    if key=='daly':spec['evidence_files'] += ['daly-duplication-investigation.md','daly-cross-subject-duplicate-audit.json']
    if key in ['pan23','pan25'] and not pilot:
        identity=json.loads((ROOT/'docs/pan-full-native-identity-audit.json').read_text(encoding='utf-8'))
        if not identity['admission_gate_passed']:raise ValueError('Full Pan identity audit has not passed')
        spec['evidence_files'] += ['pan-full-native-identity-audit.json']
    if pilot:
        spec.update(name=spec['name']+'Pilot',subjects={'pan23':['01','14'],'pan25':['01','10'],'mibmpi':['D01','D08'],'cho':['01','52'],'rozado':['1','15'],'daly':['01','18']}[key]);output=cache/'pilot-output'
    split='Whole-subject original01-10 TRAIN,11-14 TEST' if key=='pan23' else 'Original session1 and session2 first30 trials TRAIN, remaining session2 trials TEST; intentional shared participants' if key=='pan25' else 'Whole-subject D01-D06 TRAIN,D07-D08 TEST'
    if key in NATIVE_READERS:
        split={'cho':'Whole-subject01-39 TRAIN,40-52 TEST','rozado':'Whole-subject1-11 and16-26 TRAIN;12-15 and27-30 TEST','daly':'Whole-subject01-13 TRAIN,14-18 TEST; all native labelled non-calibration runs retained'}[key]
        spec['note']={'cho':'Native class-array values cast to float64, presumed microvolts; actual imagery_event onsets define3-second crops. Original trial_sequence values order cases across classes. No mean removal, synthetic gaps or extra DSP. Native coordinates retained; no anatomical names embedded.',
                      'rozado':'Explicit native XDF EEG microvolts cast to float64; select32 EEG by native type/order, exclude trigger/EX/AUX. Six seconds at nominal512Hz per cue. Raw common-host timestamps retained; no clock correction, interpolation, filter or reference change. Known noisy subjects retained with flags.',
                      'daly':'Original calibrated EDF volts multiplied by1e6 in float64; native BIDS event onsets define20-second cases. Both byte-identical09/15run10 copies excluded because true participant attribution is unresolved; all other unique complete runs retained and strictly audited for duplicates. No extra DSP. Original README CC BY4.0 and dataset_description CC0 discrepancy retained, conservative attribution terms.'}[key]
    spec['metadata_updates']=dict(split_definition=split,original_source_url='https://zenodo.org/records/13626922' if key=='mibmpi' else 'https://doi.org/'+spec['doi'],
        unit_evidence=spec['note'],metadata_evidence=dict(direct='Original arrays, epoch labels/indices, filename IDs and native sampling rates; Pan2025 and MI-BMPI native ordered sensor labels',
        secondary='Pinned MOABB task/label and unit interpretation, Pan2023 anatomical mapping not native',assigned='Encoded class strings, archive memberships where no source test phase; original epoch ordinal'),
        missing_or_inconsistent_metadata=['Original continuous offsets and absolute original trial IDs unavailable','Units not explicitly embedded; native numerical scale unchanged','Individual demographic mapping and visit dates not recovered'],
        channel_identity_status='Unverified anatomical identities: opaque original column IDs' if key=='pan23' else 'Directly recovered native ordered channel labels',
        original_sampling_frequency_hz=spec['hz'] if key not in ['pan23','pan25'] else 1000,original_frequency_evidence='Native distributed recording rate' if key not in ['pan23','pan25'] else 'Documented acquisition rate, distributed files250Hz; not measured from original continuous acquisition')
    if key=='pan23':spec['metadata_updates']['missing_or_inconsistent_metadata'].append('No native anatomical names: secondary mapping retained separately, no anatomical order asserted')
    if key=='pan23':
        spec['metadata_updates'].update(original_sampling_frequency_hz=None,original_frequency_evidence='Native fs and publisher description establish250Hz distributed rate; earlier acquisition rate not verified',
          preprocessing='Publisher describes0.01-200Hz filtering; stage relative to250Hz sampling not established. Native trial crops only, no added DSP.')
        spec['metadata_updates']['missing_or_inconsistent_metadata'].append('Publisher description mentions trial_info not present in native MAT and an upper filter cutoff above released Nyquist; preserve discrepancies')
    if key=='pan25':spec['metadata_updates']['preprocessing']='Publisher:1000Hz acquisition,0.01-200Hz bandpass,50Hz notch,downsample250Hz. Exact native Info.taskpoints selected; no added DSP.'
    spec['metadata_updates']['metadata_evidence']['direct']='Native signal arrays, labels/events and source IDs; per-recording headers/tables include actual sensor names/types where present. Anatomical labels absent for Pan2023/Cho, explicitly flagged.'
    if key=='mibmpi':
        spec['metadata_updates'].update(reference='Native EEGLAB ref=average; per-sensor ref fields retained',coordinate_information='Native chanlocs X/Y/Z and spherical fields retained per recording; units/frame and measured versus template status unestablished',
          preprocessing='Distributed preprocessed EEGLAB epochs: average reference declared in native fields; native history retained. Select task samples128:448, cast float32 to float64; no added DSP.',
          source_doi_role='Zenodo metadata DOI identifies associated preprint, not an independently verified dataset DOI',licence_restrictions='CC BY-NC4.0 in original Zenodo description; commercial studies require permission')
    if key in ['rozado','daly']:
        spec['metadata_updates']['missing_or_inconsistent_metadata']=['No individual measured montage recovered','Original benchmark partitions absent: archive defines whole-subject split','Absolute original trial identifiers unavailable; native event ordinal retained']
        spec['metadata_updates']['unit_evidence']=spec['note']
    if key=='rozado':spec['metadata_updates'].update(reference='BioSemi source hardware; native header retained, no new reference applied',timestamp_warning='Raw XDF timestamps include packet jitter and nonmonotonic steps; no interpolation or artificial continuity. Nominal512Hz six-second windows preserve native stored samples; original timestamps and clock offsets retained.')
    if key=='cho':
        spec['metadata_updates'].update(channel_identity_status='Opaque original EEG column identifiers; native anatomical names absent',reference='BioSemi CMS/DRL, documented hardware',missing_or_inconsistent_metadata=['No original anatomical names in MAT; preserve numbered source columns and measured coordinates, do not invent montage labels','Native class arrays separate left/right trials; original sequence values retained, continuous clock units/run membership not established','Microvolt interpretation from source loader, no explicit native units field'])
    if key=='daly':spec['metadata_updates'].update(reference='FCz, original BIDS EEGReference',licence_discrepancy='Original rights-holder README CC BY4.0, dataset_description CC0; both retained, conservative attribution grant',
        preprocessing='Native EDF physical calibration, float64 volts times1e6; BIDS onset rounded to nearest millisecond,20seconds. Exclude calibration, targetless recordings and incomplete final trials; no extra filter/resampling/reference.',
        missing_or_inconsistent_metadata=spec['metadata_updates']['missing_or_inconsistent_metadata']+['Source README19 participants versus18 released IDs','Some final labelled events extend beyond native EDF end; incomplete windows excluded explicitly','Original09/15run10 EDF and event tables are identical; true owner unknown, both ambiguous recordings excluded; other native run10 retained when unique'])
    if key in ['pan23','cho']:
        spec['validation_updates']=dict(source_sensor_identity='Opaque original column IDs verified in array order; anatomical names unavailable in native files',anatomical_channel_names_verified=False)
    else:spec['validation_updates']=dict(source_sensor_identity='All native embedded channel labels/types and order checked against selected array indices')
    # Keep the bibliographic citation separate from the electrical reference.
    spec['metadata_updates']['paper_reference']=spec['paper']
    spec['metadata_updates']['eeg_reference']=spec['metadata_updates'].get('reference')
    core.SPECS[key]=spec;core.READERS[key]=NATIVE_READERS[key] if key in NATIVE_READERS else mibmpi_records if key=='mibmpi' else pan_records
    result=core.prepare(key,cache_root,output);folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    for s in m['sensors']:
        s['native_channel_index']=s['pre_flat_removal_array_index'] if 'pre_flat_removal_array_index' in s else s['source_array_index']
        if key in ['pan23','cho']:s.update(identity_evidence='Opaque original column identifier; anatomical label unavailable',anatomical_name=None)
        if key=='rozado':s['native_channel_index']+=1
    # Native coordinates/reference remain per-recording evidence; do not fabricate a montage.
    manifest_fields=dict(label_mapping=spec['labels'],split_definition=split,licence_url=spec['licence_url'],original_source_url=m['original_source_url'])
    if key=='daly':manifest_fields.update(excluded_ambiguous_recordings=m['excluded_ambiguous_recordings'],duplicate_handling=m['duplicate_handling'])
    result=finish(result,m,spec['evidence_files'],spec['conversion_files'],manifest_fields)
    core.dump(ROOT/'docs'/(key+'-to-30-'+('pilot' if pilot else 'conversion')+'-result.json'),result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=SPECS);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.dataset,a.cache_root,a.output,a.pilot)
