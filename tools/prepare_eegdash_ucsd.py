"""Original UCSD Parkinson's OFF versus control, native512Hz scalp EEG."""
import json
from pathlib import Path
import re
import numpy as np
from tools import prepare_open_moabb as core
from tools.download_eegdash_diagnosis import CONFIG
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]


def clinical_split(participants):
    groups={'hc':[],'pd':[]}
    for row in participants:
        person=row['participant_id'].removeprefix('sub-')
        match=re.fullmatch('(hc|pd)[0-9]+',person)
        if not match:raise ValueError('Unreviewed UCSD clinical identity')
        groups[match[1]].append(person)
    if len({p for ids in groups.values() for p in ids})!=len(participants):raise ValueError('Duplicate participant')
    return {p for ids in groups.values() for p in sorted(ids)[:int(.75*len(ids))]}


def records(cache,spec):
    import mne
    people={r['participant_id'].removeprefix('sub-'):r for r in core.table(cache/'participants.tsv')}
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    for file in sorted(receipt['files'],key=lambda r:r['name']):
        name=file['name']
        if not name.endswith('.bdf'):continue
        person=re.search(r'(?:^|/)sub-([^/]+)',name)[1]
        if spec.get('subjects') and person not in spec['subjects']:continue
        session=re.search(r'/ses-([^/]+)/',name)[1]
        if session!=('hc' if person.startswith('hc') else 'off'):continue
        path=cache/name;stem=str(path)[:-7];channels=core.table(stem+'channels.tsv')
        bids=json.loads(Path(stem+'eeg.json').read_text(encoding='utf-8'))
        raw=mne.io.read_raw_bdf(path,preload=False,verbose=False)
        names=[r['name'] for r in channels]
        if raw.ch_names!=names or raw.info['sfreq']!=512 or bids['SamplingFrequency']!=512:raise ValueError('UCSD native/BIDS sensor/rate mismatch')
        if len(names)!=41 or names[32:]!=[f'EXG{i}' for i in range(1,9)]+['Status']:raise ValueError('Unreviewed UCSD montage')
        if any(r['units']!='µV' or r['type']!='EEG' for r in channels[:32]):raise ValueError('Unknown scalp calibration/type')
        picks=list(range(32));data=raw.get_data(picks=picks)*1e6
        points=2048;label='1' if person.startswith('hc') else '2';original='Healthy control' if label=='1' else 'Parkinson disease, OFF medication'
        rows=[];values=[]
        for index,start in enumerate(range(0,raw.n_times-points+1,points)):
            row=core.base_row(person,session,'rest',name,index,start,points,512,original,label)
            row.update(source_epoch_index='',original_trial_id='',source_window_index=index,source_event_sample='',
                original_participant_id='sub-'+person,original_session_id=session,original_partition='unsplit',
                participant_metadata=json.dumps(people[person],sort_keys=True),
                source_array_index=f'Native BDF scalp channels0:32 samples[{start}:{start+points}], MNE SI decode to float64 microvolts')
            rows.append(row);values.append(np.ascontiguousarray(data[:,start:start+points]))
        if not rows:raise ValueError('No complete UCSD window')
        info=dict(source_file=name,source_file_sha256=file['sha256'],participant_id=person,participant_metadata=people[person],
            native_channel_names=names,source_eeg_indices=picks,native_bids_channels=channels,native_bids_eeg=bids,
            native_sampling_frequency_hz=512,native_samples=raw.n_times,source_case_count=len(rows),
            excluded_trailing_samples=raw.n_times%points,eeg_reference=bids.get('EEGReference'),
            sensor_selection='32named scalp EEG channels in source order. EXG1..8 all labelled EEG by BIDS but individual roles unverified; excluded rather than guessed. Status trigger excluded.',
            original_physical_units=raw._orig_units,units_evidence='BDF calibrated MNE decode in volts, multiplied float64 by1e6; source channels.tsv explicitly microvolts',
            montage='Source electrode coordinate files retained if available; no template or measured geometry invented')
        yield np.stack(values),rows,names[:32],info


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    conf=CONFIG['ucsd'];cache=Path(cache_root)/'EEGDash'/conf['dataset'];train=clinical_split(core.table(cache/'participants.tsv'))
    caution='Original README explicitly discourages diagnostic ML on this31person cohort because of small test-group size and clinical heterogeneity; requests pre-publication author contact. User explicitly authorised inclusion9November2026. Benchmark preparation is not evidence of clinical diagnostic validity.'
    spec=dict(name='ParkinsonsRestUCSD',source='UCSD / OpenNeuro ds002778 / EEGDash on002778',cache='EEGDash/ds002778',hz=512,points=2048,classes=2,train_subjects=len(train),
        licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',moabb_revision=None,doi='10.18112/openneuro.ds002778.v1.0.5',
        paper='Jackson,Cole,Voytek,Swann2019, Characteristics of Waveform Shape in Parkinson’s Disease Detected with Scalp Electroencephalography;10.1523/ENEURO.0151-19.2019',
        labels={'1':'healthy_control','2':'parkinsons_disease_off_medication'},splitter=lambda people,chunks:set(people)&train,
        evidence_files=['eegdash-diagnosis-plan.md','ds002778-diagnosis-source-lock.json'],
        cache_evidence_files=[p for p in ['dataset_description.json','participants.tsv','participants.json','README','original-source-lock.json'] if (cache/p).is_file()],
        conversion_files=['prepare_eegdash_ucsd.py','prepare_eegdash_diagnosis.py','download_eegdash_diagnosis.py','requirements-eegdash-diagnosis.txt'],
        intermediate_directory='classification-intermediate-'+('pilot' if pilot else 'full'),
        note='Clinically diagnosed PD OFF medication versus controls. Complete non-overlapping4s rest windows, native512Hz,32named scalp channels before flat review. ON medication sessions excluded to keep one acquisition condition and avoid mixing raw with2processed substitutions. Float64 calibrated microvolts; no new DSP. '+caution,
        metadata_updates=dict(domain='Med',eegdash_id='on002778',original_source_url='https://openneuro.org/datasets/ds002778/versions/1.0.5',
            paper_reference='Jackson et al.2019;10.1523/ENEURO.0151-19.2019; also Swann2015 and George2013 as requested in source README',
            reference='BIDS EEGReference n/a; no new reference',eeg_reference='Original electrical reference unspecified; retained native acquisition calibration, no rereferencing',
            split_definition='Within hc and pd groups: sorted original string IDs, floor0.75*n TRAIN, remainder TEST; all windows of each participant together, no validation export',
            window_overlap_seconds=0,preprocessing='MNE calibrated BDF decode to float64 microvolts and scalp channel selection only; no conversion filter,resampling,reference,baseline,normalisation. Source BIDS channel high_cutoff104Hz; source paper analysis preprocessing must not be assumed applied to distributed BDF.',
            original_sampling_frequency_hz=512,clinical_caution=caution,
            metadata_evidence=dict(direct='Original participant IDs, demographics and disease-duration fields, BDF names/order/calibration/sample bounds, BIDS metadata and session labels',
                documented='Paper reports15PD diagnosed by movement disorder specialist and16healthy controls,32channel BioSemi512Hz,OFF at least12hours after medication; clinical prefix semantics hc/pd',
                assigned='Whole-subject split, encoding and4second consecutive windows; no invented trial identities'),
            missing_or_inconsistent_metadata=['EXG1..8 source type EEG does not establish scalp/eye/ECG roles; exclude and preserve metadata','Reference/ground/placement BIDS n/a; no measured coordinates inferred','Authors explicit small-cohort diagnostic-ML caution retained','ON sessions not part of this classification; pd6/pd16 source notes say processed MAT substituted for ON, not used','No additional rest-onset or artifact annotations invented']))
    if pilot:spec.update(name=spec['name']+'Pilot',subjects=conf['pilot']);output=cache/'pilot-output'
    core.SPECS['ucsd']=spec;core.READERS['ucsd']=records
    result=core.prepare('ucsd',cache_root,output);folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    for sensor in m['sensors']:sensor['native_channel_index']=sensor['pre_flat_removal_array_index']
    result=finish(result,m,spec['evidence_files'],spec['conversion_files'],dict(label_mapping=spec['labels'],split_definition=m['split_definition'],eegdash_id='on002778',clinical_caution=caution))
    core.dump(ROOT/'docs'/('ds002778-diagnosis-'+('pilot' if pilot else 'conversion')+'-result.json'),result)
    return result
