"""Native BIDS diagnostic windows with explicit source labels and EEG metadata."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re
import warnings

import h5py
import numpy as np
from tools import prepare_open_moabb as core
from tools.download_eegdash_diagnosis import CONFIG
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]
AUDITORY_LABELS={'Normal':'1','MCI':'2','Mild AD':'3','Moderate AD':'3'}


def diagnostic_subject_split(participants):
    """Fixed approximately75/25 membership within each verified diagnosis."""
    groups={};excluded=[]
    for row in participants:
        person=row['participant_id'].removeprefix('sub-');label=AUDITORY_LABELS.get(row['Group'])
        if label is None:
            excluded.append(dict(participant_id=person,original_group=row['Group'],reason='Original diagnosis unavailable; no MMSE-based relabelling'));continue
        groups.setdefault(label,[]).append(person)
    training=set()
    for label,people in groups.items():
        people=sorted(people);count=int(np.floor(.75*len(people)))
        if count<2 or len(people)-count<1:raise ValueError('Insufficient independent people for class split')
        training.update(people[:count])
    return training,excluded


def h5value(f,dataset):
    if dataset.attrs.get('MATLAB_empty',0):return None
    a=np.asarray(dataset)
    if dataset.attrs.get('MATLAB_class')==b'char':return ''.join(chr(int(v)) for v in a.ravel())
    return core.native_json(a.ravel().tolist())


def h5scalar(dataset):return float(np.asarray(dataset).item())


def native_set(path):
    with h5py.File(path) as f:
        g=f['EEG'] if 'EEG' in f else f
        info={k:h5value(f,g[k]) for k in ['history','ref','subject','group','xmin','xmax','data','datfile']}
        info.update(sfreq=h5scalar(g['srate']),channels=int(h5scalar(g['nbchan'])),samples=int(h5scalar(g['pnts'])),trials=int(h5scalar(g['trials'])))
        locations=g['chanlocs'];sensors=[]
        for i,ref in enumerate(np.asarray(locations['labels']).ravel()):
            sensor=dict(native_channel_index=i,name=h5value(f,f[ref]))
            for field in locations:sensor[field]=h5value(f,f[np.asarray(locations[field]).ravel()[i]])
            sensors.append(sensor)
        info['native_sensors']=sensors
        events=[];event_group=g['event']
        for index,ref in enumerate(np.asarray(event_group['latency']).ravel()):
            latency=float(np.asarray(f[ref]).item());type_ref=np.asarray(event_group['type']).ravel()[index];code=np.asarray(f[type_ref]).ravel()
            if code.size!=1:raise ValueError('Unknown native event type schema')
            events.append(dict(index=index,latency_1based=latency,code=int(code.item())))
        info['native_events']=events
    fdt=path.with_suffix('.fdt')
    if info['trials']!=1 or fdt.stat().st_size!=info['channels']*info['samples']*4:raise ValueError('Native FDT schema/size mismatch')
    if info['data']!=fdt.name or info['datfile']!=fdt.name:raise ValueError('Native FDT pointer differs from actual source pairing')
    # MATLAB column-major channels x samples => samples x channels in C order.
    data=np.memmap(fdt,dtype='<f4',mode='r').reshape(info['samples'],info['channels']).T
    return data,info


def stimulus_windows(events,native_events,hz,n_samples,points=1000):
    if len(events)!=len(native_events):raise ValueError('BIDS/native marker counts differ')
    windows=[];offsets=[]
    for ordinal,(event,native) in enumerate(zip(events,native_events,strict=True)):
        onset=float(event['onset']);duration=float(event['duration']);start=int(round(onset*hz));sample=int(event['sample']);code=int(event['value'])
        if sample!=start+1 or native['code']!=code:raise ValueError('BIDS onset/sample/event identity mismatch')
        delta=native['latency_1based']-sample
        if abs(delta)>1.000001:raise ValueError('Native marker differs from BIDS by more than one sample')
        offsets.append(dict(event_index=ordinal,bids_sample_1based=sample,native_latency_1based=native['latency_1based'],native_minus_bids_samples=delta))
        expected='Stimulus' if code==2 else 'Rest' if code==1 else None
        if expected is None or event['trial_type']!=expected:raise ValueError('Unrecognised source condition mapping')
        if code!=2:continue
        duration_samples=int(round(duration*hz))
        if duration!=40 or start<0 or start+duration_samples>n_samples:raise ValueError('Incomplete or changed native stimulus interval')
        for within,offset in enumerate(range(0,duration_samples-points+1,points)):
            windows.append(dict(event_index=ordinal,window_index=within,start_sample=start+offset,end_sample=start+offset+points,original_event=event,native_marker=native))
    if not windows:raise ValueError('No complete auditory stimulus windows')
    return windows,offsets


def auditory_records(cache,spec):
    participants=core.table(cache/'participants.tsv');by_person={r['participant_id'].removeprefix('sub-'):r for r in participants}
    if len(by_person)!=len(participants):raise ValueError('Duplicate native participant ID')
    train,excluded=diagnostic_subject_split(participants)
    spec['metadata_updates']['excluded_participants']=excluded
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    for file in sorted(receipt['files'],key=lambda f:f['name']):
        if not file['name'].endswith('_eeg.set'):continue
        match=re.fullmatch(r'sub-(\d{2})/eeg/sub-(\d{2})_task-40HzAuditoryEntrainment_eeg.set',file['name'])
        if not match or match[1]!=match[2]:raise ValueError('Unrecognised native recording identity')
        person=match[1];participant=by_person[person];group=participant['Group']
        if group not in AUDITORY_LABELS:continue
        if spec.get('subjects') and person not in spec['subjects']:continue
        path=cache/file['name'];data,info=native_set(path);stem=str(path)[:-7]
        channels=core.table(stem+'channels.tsv');events=core.table(stem+'events.tsv');bids=json.loads(Path(stem+'eeg.json').read_text(encoding='utf-8'))
        names=[s['name'] for s in info['native_sensors']]
        if info['sfreq']!=250 or bids['SamplingFrequency']!=250 or info['channels']!=19 or names!=[c['name'] for c in channels]:raise ValueError('Native/BIDS sensor order or sampling mismatch')
        if str(info['subject'])!=person:raise ValueError('Native subject differs from BIDS path')
        windows,offsets=stimulus_windows(events,info['native_events'],250,info['samples'])
        # Independent reader check validates the native FDT axis/calibration path.
        import mne
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_eeglab(path,preload=False,verbose=False)
        if raw.ch_names!=names or raw.info['sfreq']!=250 or raw.n_times!=info['samples']:raise ValueError('Independent EEGLAB reader disagrees')
        test_samples=min(2000,info['samples'])
        if not np.allclose(raw.get_data(start=0,stop=test_samples)*1e6,np.asarray(data[:,:test_samples],dtype='<f8'),rtol=1e-12,atol=1e-12):raise ValueError('Independent calibration/FDT ordering mismatch')
        rows=[];values=[]
        for index,w in enumerate(windows):
            row=core.base_row(person,'native_session_unspecified','40HzAuditoryEntrainment',file['name'],index,w['start_sample'],1000,250,group,AUDITORY_LABELS[group])
            row.update(source_event_row=w['event_index'],source_window_within_event=w['window_index'],source_condition='Stimulus',source_event_code='2',
                source_epoch_index='',source_event_onset=w['original_event']['onset'],source_event_duration=w['original_event']['duration'],
                source_event_sample_1based=w['original_event']['sample'],native_marker_latency_1based=w['native_marker']['latency_1based'],
                source_label_scope='Original participant Group, distinct from stimulus event code',original_participant_id=participant['participant_id'],
                original_group=group,age=participant['Age'],gender=participant['Gender'],MMSE=participant['MMSE'],
                session_id_evidence='No native BIDS session entity; internal key does not imply a recovered visit ID',
                source_array_index=f'Native float32 FDT all19channels, samples[{w["start_sample"]}:{w["end_sample"]}], cast to float64; native numerical values unchanged')
            row['source_event_sample']=int(w['original_event']['sample'])-1
            rows.append(row);values.append(np.ascontiguousarray(data[:,w['start_sample']:w['end_sample']],dtype='<f8'))
        yield np.stack(values),rows,names,dict(source_file=file['name'],source_file_sha256=file['sha256'],source_fdt=file['name'][:-4]+'.fdt',participant_id=person,participant_metadata=participant,
            source_eeg_indices=list(range(19)),native_channel_names=names,native_channel_types=[s['type'] for s in info['native_sensors']],native_eeglab=info,native_bids_channels=channels,native_bids_eeg=bids,
            event_alignment_audit=offsets,event_timing_decision='Use original BIDS onset/sample grid; native SET markers differ by at most one4ms sample, discrepancy retained, no time interpolation',
            unit_evidence='Source BIDS units n/a; EEGLAB microvolt storage convention independently checked against MNE SI decode. Native float32 values cast to float64, factor1; physical interpretation format-based, not an explicit source unit field',
            coordinate_evidence='Native SET chanlocs retained; history indicates standard template locations, not individual measured geometry; units/frame unverified',
            source_case_count=len(rows),native_sampling_frequency_hz=250)


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    if key=='ucsd':
        from tools.prepare_eegdash_ucsd import prepare as prepare_ucsd
        return prepare_ucsd(cache_root,output,pilot)
    if key=='iowa_rest':
        from tools.prepare_eegdash_iowa import prepare as prepare_iowa
        return prepare_iowa(cache_root,output,pilot)
    if key in ['psychosis1','psychosis2']:
        from tools.prepare_eegdash_psychosis import prepare as prepare_psychosis
        return prepare_psychosis(key,cache_root,output,pilot)
    if key!='auditory':raise ValueError('Source adapter not yet reviewed')
    conf=CONFIG[key];cache=Path(cache_root)/'EEGDash'/conf['dataset'];participants=core.table(cache/'participants.tsv');train,excluded=diagnostic_subject_split(participants)
    spec=dict(name='AlzheimersAuditory',source='Lahijanian2024 / OpenNeuro ds005048 / EEGDash on005048',cache='EEGDash/'+conf['dataset'],hz=250,points=1000,classes=3,train_subjects=len(train),
        licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',moabb_revision=None,doi='10.18112/openneuro.ds005048.v1.0.1',paper='Lahijanian,Aghajan,Vahabi(2024), Auditory gamma-band entrainment enhances default mode network connectivity in dementia patients, DOI10.1038/s41598-024-63727-z',
        labels={'1':'normal','2':'mild_cognitive_impairment','3':'alzheimers_disease'},splitter=lambda people,chunks:set(people)&train,
        evidence_files=['eegdash-diagnosis-plan.md','ds005048-diagnosis-source-lock.json'],
        cache_evidence_files=['dataset_description.json','participants.tsv','participants.json','README','task-40HzAuditoryEntrainment_events.json','original-source-lock.json'],
        conversion_files=['prepare_eegdash_diagnosis.py','download_eegdash_diagnosis.py','requirements-eegdash-diagnosis.txt'],intermediate_directory='classification-intermediate-'+('pilot' if pilot else 'full'),
        note='Participant diagnosis classification during original40Hz auditory stimulation; Normal/MCI/AD, mild+moderate AD merged, unknown-group participants excluded. All complete4second windows within40second Stimulus events, rest excluded. Native250Hz float32 FDT numbers cast to float64; inferred microvolt format convention, no extra DSP. Distributed data already preprocessed; native history/reference/geometry and BIDS differences retained.',
        metadata_updates=dict(domain='Med',paper_reference='Lahijanian et al.(2024), DOI10.1038/s41598-024-63727-z',eegdash_id=conf['eegdash'],moabb_revision=None,
            original_source_url=f'https://openneuro.org/datasets/{conf["dataset"]}/versions/{conf["ref"]}',source_reference='CC0 original dataset_description; original README and paper retained',
            split_definition='Fixed whole-subject within each diagnosis: sorted original IDs, floor0.75*n TRAIN, remainder TEST; known group membership only. Actual memberships saved; no validation archive.',
            preprocessing='No conversion-added filtering/resampling/reference/baseline/interpolation. Native SET history includes1-70Hz filter, channel cleaning/interpolation, ASR, average rereference and ICA/dipfit processing steps; BIDS JSON only describes1Hz highpass/50Hz notch and average reference. Preserve complete histories, do not infer exact final ICA rejection from history alone.',
            reference='BIDS average reference; native SET ref=common, original history includes average rereferencing',eeg_reference='Original BIDS and SET fields retained separately',
            original_sampling_frequency_hz=None,original_frequency_evidence='Distributed SET/BIDS directly establish250Hz; earlier acquisition rate not verified',
            window_overlap_seconds=0,unit_evidence='EEGLAB microvolt format convention, source BIDS units n/a; factor1 numeric export, format-based physical interpretation',
            metadata_evidence=dict(direct='Native SET/FDT arrays, exact sensor names/order/template fields/history/events, original BIDS diagnoses/demographics and event timing',documented='Original data licence and paper diagnosis/stimulation protocol',inferred='Microvolt physical interpretation from EEGLAB convention, not explicit BIDS units',assigned='Whole-subject split and label encoding; mild/moderateAD grouped without MMSE relabelling'),
            missing_or_inconsistent_metadata=['BIDS channel type/units n/a; EEG scalp modality documented, unit interpretation format-based','Source labels include one moderateAD participant: merge severity within AD rather than invent an untestable singleton class','Unknown diagnoses excluded; do not infer from MMSE','Native/BIDS cue times may differ by one sample; original BIDS grid used and differences retained','Native template coordinates are not measured geometry; coordinate units/frame unverified','Distributed preprocessing history is richer than BIDS filter summary; no claim of raw acquisition signals','Different participant recording lengths yield different case counts; evaluate with participant grouping']))
    if pilot:spec.update(name=spec['name']+'Pilot',subjects=conf['pilot']);output=cache/'pilot-output'
    spec['cache_evidence_files']=[p for p in spec['cache_evidence_files'] if (cache/p).is_file()]
    core.SPECS['eegdash_'+key]=spec;core.READERS['eegdash_'+key]=auditory_records
    result=core.prepare('eegdash_'+key,cache_root,output);folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    for sensor in m['sensors']:sensor.update(native_channel_index=sensor['pre_flat_removal_array_index'],unit_evidence='EEGLAB format convention; native BIDS units n/a',type_evidence='Scalp EEG modality documented; native/BIDS type fields may be empty')
    result=finish(result,m,spec['evidence_files'],spec['conversion_files'],dict(label_mapping=spec['labels'],split_definition=m['split_definition'],excluded_participants=m['excluded_participants'],eegdash_id=conf['eegdash'],unit_evidence=m['unit_evidence']))
    core.dump(ROOT/'docs'/('ds005048-diagnosis-'+('pilot' if pilot else 'conversion')+'-result.json'),result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=['auditory','psychosis1','psychosis2','iowa_rest','ucsd']);p.add_argument('--pilot',action='store_true');p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args();prepare(a.dataset,a.cache_root,a.output,a.pilot)
