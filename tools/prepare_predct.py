"""Pinned PRED+CT native EEG -> four-second clinical classification .ts.

Run download_predct_batch first, then python -m tools.prepare_predct.
No filter, resampling, baseline subtraction or rereferencing is applied.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import io
import json
import math
from pathlib import Path
import re
import warnings

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.predct_inspect import xlsx_records, xlsx_rows

ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=Path('D:/Data/EEGSources/PREDCT')
SOURCES={
    'Singh2020':('ParkinsonsPedalling','10.1016/j.clinph.2019.12.399',
        'Singh et al. (2020), Frontal theta and beta oscillations during lower-limb movement in Parkinson\u2019s disease, Clinical Neurophysiology 131, 694-702'),
    'Cavanagh2018b':('ParkinsonsRest','10.1016/j.clinph.2017.11.023',
        'Cavanagh et al. (2018), Diminished EEG habituation to novel events effectively classifies Parkinson\u2019s patients, Clinical Neurophysiology 129, 409-418'),
    'Gruendler2009':('ObsessiveCompulsiveSymptoms','10.1016/j.neuropsychologia.2009.03.010',
        'Grundler et al. (2009), Task-related dissociation in ERN amplitude as a function of obsessive-compulsive symptoms, Neuropsychologia 47, 1978-1987'),
}

def group_split(people,chunks):
    groups=defaultdict(set);seen={}
    for _,rows in chunks:
        for r in rows:
            p=r['participant_id'];label=r['label']
            if p in seen and seen[p]!=label:raise ValueError('Participant has inconsistent group labels')
            seen[p]=label;groups[label].add(p)
    if set(seen)!=set(people) or len(groups)!=2:raise ValueError('Incomplete participant classes')
    train=set()
    for group in groups.values():
        ordered=sorted(group)
        if len(ordered)<2:raise ValueError('Insufficient subjects to split each class')
        train.update(ordered[:max(1,min(len(ordered)-1,math.floor(.75*len(ordered))))])
    return train

def window_bounds(start,end,points=2000):
    if start<0 or end<start:raise ValueError('Invalid source interval')
    return [(s,s+points) for s in range(int(start),int(end)-points+1,points)]

def rest_intervals(events,n_samples,hz=500):
    """Group observed one-second markers; never bridge an instruction gap."""
    groups=[]
    for event in events:
        match=re.fullmatch(r'S\s*([1-4])',event['description'])
        if not match:continue
        state='eyes_open' if match[1] in ['1','2'] else 'eyes_closed'
        sample=event['sample']
        if groups and sample<groups[-1]['samples'][-1]:raise ValueError('Nonchronological rest markers')
        if not groups or groups[-1]['condition']!=state or sample-groups[-1]['samples'][-1]>1.5*hz:
            groups.append(dict(condition=state,samples=[]))
        groups[-1]['samples'].append(sample)
    intervals=[]
    for i,g in enumerate(groups):
        end=min(n_samples,g['samples'][-1]+hz,groups[i+1]['samples'][0] if i+1<len(groups) else n_samples)
        intervals.append((g['samples'][0],end,g['condition']))
    return intervals,groups

def clinical_csv(path):
    # The source uses literal backslash-t escapes, not tab bytes.
    text=Path(path).read_text(encoding='utf-8-sig')
    if '\\t' in text.splitlines()[0]:text=text.replace('\\t','\t')
    return list(csv.DictReader(io.StringIO(text),delimiter='\t'))

def original_label_fields(source,row):
    """Verify encoded targets against recovered original clinical variables."""
    if source=='Singh2020':
        original=json.loads(row['clinical_variables'])['Group']
        mapping={'Control':'2','PDwithFOG':'1','PDwithoutFOG':'1'}
        if original not in mapping:raise ValueError('Unreviewed clinical group')
        expected=mapping[original];evidence='Native ALL_data_Modeling.csv Group; both PD subgroups encode1'
    elif source=='Gruendler2009':
        original=str(row['OCI']);expected='1' if float(original)>=21 else '2'
        evidence='Native Info.xlsx SELECT columnB numerical OCI score; categorical target assigned by threshold21'
    else:
        original=row['group'];expected={'parkinsons':'1','control':'2'}[original]
        evidence='Native clinical table PD_ID versus MATCH CTL_ID plus author PDsx/CTLsx lists'
    if row['label']!=expected:raise ValueError('Encoded target differs from original clinical variable')
    return dict(source_label=original,source_label_evidence=evidence)

def info_native(raw):
    return dict(core.mne_info(raw),native_highpass_hz=raw.info['highpass'],native_lowpass_hz=raw.info['lowpass'],
        native_channel_positions_m=[c['loc'][:3] for c in raw.info['chs']],
        mne_channel_calibrations=[{k:c[k] for k in ['ch_name','cal','range','unit','unit_mul','kind']} for c in raw.info['chs']],
        native_custom_reference_applied=int(raw.info['custom_ref_applied']),
        positions_evidence='Distributed header as interpreted by MNE; no standard montage assigned')

def extra_header_notes(raw):
    measured=raw.info.get('meas_date');subject=raw.info.get('subject_info') or {};montage=raw.get_montage()
    return dict(native_measurement_time_mne=measured.isoformat() if measured is not None else None,
        measurement_time_evidence='MNE representation of native header timestamp; original time zone not independently established. Not assigned as a session ID.',
        native_subject_header_fields={k:(str(v) if k=='his_id' else v) for k,v in subject.items() if k in ['his_id','sex','hand','height','weight']},
        native_montage_mne=montage.get_positions() if montage is not None else None,
        montage_evidence='MNE interpretation of native header positions; may include MNE-estimated fiducials. No claim of individual digitisation.')

def make_cases(data,names,person,session,file,label,intervals,extra,events):
    rows=[];values=[]
    for start,end,condition in intervals:
        for a,b in window_bounds(start,end):
            row=core.base_row(person,session,'unknown',file,len(rows),a,2000,500,extra['group'],label)
            row.update(extra,source_trial_id='',source_epoch_id_evidence='Archive-defined continuous window, not an original trial',
                source_epoch_index='',source_event_sample='',event_index_evidence='Archive window ordinal, not a native event or trial index',
                run_id_evidence='Original run identifier unavailable; native recording filename is retained',
                condition=condition,source_array_index=f'Native EEG rows in recording metadata; samples[{a}:{b}]',
                native_events_in_window=json.dumps([e for e in events if a<=e['sample']<b],separators=(',',':')))
            rows.append(row);values.append(core.crop(data,a,2000))
    if not rows:raise ValueError(f'No complete windows: {file}')
    return np.stack(values),rows,names

def singh_records(cache,spec):
    import mne
    clinical=clinical_csv(cache/'ALL_data_Modeling.csv')
    demo={('Control' if r['Group']=='Control' else 'PD')+r['Pedal_ID']:r for r in clinical}
    files=sorted((cache/'raw_data').glob('*.vhdr'))
    if len(files)!=39:raise ValueError('Expected 39 original pedalling recordings')
    for p in files:
        person=p.stem
        if person not in demo:raise ValueError('Recording missing clinical table row')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            raw=mne.io.read_raw_brainvision(p,preload=True,verbose=False)
        if raw.info['sfreq']!=500 or raw.ch_names[-3:]!=['X','Y','Z']:raise ValueError('Unreviewed pedalling header')
        keep=mne.pick_types(raw.info,eeg=True,exclude=[]).tolist();names=[raw.ch_names[i] for i in keep]
        if len(names)!=63:raise ValueError('Unexpected number of EEG electrodes')
        if any(raw._orig_units[n] not in ['\u00b5V','\u03bcV','uV'] for n in names):raise ValueError('EEG calibration units differ')
        events=[dict(sample=int(raw.time_as_index([o],use_rounding=True)[0]),description=str(d)) for o,d in zip(raw.annotations.onset,raw.annotations.description)]
        extra=dict(group='control' if person.startswith('Control') else 'parkinsons',
            source_participant_id=demo[person]['Pedal_ID'],clinical_variables=json.dumps(demo[person],sort_keys=True),
            session_evidence='One distributed recording per participant; separate visit identifier unavailable')
        file=p.relative_to(cache).as_posix()
        x,rows,names=make_cases(raw.get_data(picks=keep)*1e6,names,person,'unknown',file,'2' if person.startswith('Control') else '1',
            [(0,raw.n_times,'pedalling_recording_including_intertrial_periods')],extra,events)
        info=dict(info_native(raw),source_file=file,participant_id=person,session_id='unknown',source_eeg_indices=keep,
            clinical_variables=demo[person],excluded_auxiliary_channels=['X','Y','Z'],
            channel_name_uncertainty='Aa, Bb and Cc are native labels and are not relabelled as standard electrodes',
            native_header_text=p.read_text(encoding='utf-8',errors='replace'),
            tail_samples_discarded=raw.n_times%2000)
        yield x,rows,names,info

def cava_records(cache,spec):
    demo=xlsx_records(cache/'IMPORT_ME_REST.xlsx')
    pd={r['PD_ID']:r for r in demo if r.get('PD_ID','').isdigit()}
    ctl={r['MATCH CTL_ID']:r for r in pd.values()}
    selected=[]
    for person,r in pd.items():
        session='1' if r['1st Visit Meds Status']=='OFF' else '2'
        if person=='803':continue # author explicitly rejects 803 session 1 (OFF)
        selected.append((person,session,'1',r))
    selected.extend((p,'1','2',r) for p,r in ctl.items())
    if len(selected)!=55:raise ValueError('Unexpected rest clinical identities')
    for person,session,label,d in sorted(selected):
        p=cache/'data'/f'{person}_{session}_PD_REST.mat';e=loadmat(p,simplify_cells=True)['EEG']
        locs=e['chanlocs'];names=[str(c['labels']) for c in locs]
        if e['srate']!=500 or names[-4:]!=['VEOG','X','Y','Z'] or len(names)!=67:raise ValueError('Unreviewed resting header')
        events=[]
        for i,event in enumerate(e['event']):
            latency=float(event['latency'])
            if not latency.is_integer():raise ValueError('Fractional resting marker sample')
            events.append(dict(sample=int(latency)-1,description=str(event['type']),source_event_index=i))
        intervals,marker_groups=rest_intervals(events,e['data'].shape[1])
        extra=dict(group='parkinsons' if label=='1' else 'control',medication_status='OFF' if label=='1' else 'not_applicable',
            age=d['PD_Age'] if label=='1' else d['MATCH CTL_Age'],sex_source_code=d['PD_Sex'] if label=='1' else d['MATCH CTL_Sex'],
            matched_participant_id=d['MATCH CTL_ID'] if label=='1' else d['PD_ID'])
        x,rows,outnames=make_cases(np.asarray(e['data'][:63],dtype='<f8'),names[:63],person,session,p.relative_to(cache).as_posix(),label,intervals,extra,events)
        yield x,rows,outnames,dict(source_file=p.relative_to(cache).as_posix(),participant_id=person,session_id=session,
            source_eeg_indices=list(range(63)),native_channel_names=names,native_chanlocs=locs,native_reference=e['ref'],
            documented_reference='CPz (author import script); EEGLAB native ref field common retained without rereference',
            native_history=e['history'],native_events=e['event'],selected_intervals=intervals,clinical_variables=d,
            rest_marker_groups=marker_groups,marker_gap_threshold_samples=750,
            unused_short_marker_groups=[g for g,(a,b,_) in zip(marker_groups,intervals) if b-a<2000],
            units_evidence='EEGLAB numerical microvolts imported by author pop_loadbv; no 1e6 multiplication',
            native_shape=e['data'].shape,excluded_auxiliary_channels=names[-4:])

def gruendler_demo(cache):
    # Duplicate OCI header columns are retained as raw cell evidence; use the
    # original B column explicitly rather than silently overwriting with J.
    rows=xlsx_rows(cache/'Info.xlsx','SELECT')
    return {r['A']:r for r in rows[1:] if r.get('A','').isdigit() and len(r['A'])==3}

def inspect_gruendler_headers(cache):
    """Header-only preflight; never allocate data from an untrusted sample count."""
    import mne
    audit=[]
    for p in sorted((cache/'data').glob('*.cnt')):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            raw=mne.io.read_raw_cnt(p,data_format='int32',preload=False,verbose=False)
        required=int(raw.n_times)*len(raw.ch_names)*4;size=p.stat().st_size
        audit.append(dict(file=p.relative_to(cache).as_posix(),bytes=size,header_samples=int(raw.n_times),
            header_seconds=raw.n_times/500,frequency=raw.info['sfreq'],channels=len(raw.ch_names),channel_names=raw.ch_names,
            minimum_expected_signal_bytes=required,impossible_sample_count=required>size,
            processed_ready=p.name.endswith('_ready.cnt'),included=not p.name.endswith('_ready.cnt')))
    result=dict(mne_version=mne.__version__,data_format='int32',scope='Header-only inspection; conservative physical bound, no repair',
        interpretation='MNE header interpretations; physical bounds flag reader/header compatibility problems, not proven original signal corruption',recordings=audit)
    core.dump(cache/'source-header-audit.json',result)
    return result

def gruendler_records(cache,spec):
    import mne
    demo=gruendler_demo(cache);all_files=sorted((cache/'data').glob('*.cnt'))
    files=[p for p in all_files if not p.name.endswith('_ready.cnt')]
    if len(all_files)!=46 or len(files)!=35:raise ValueError('Expected 46 distributed recordings, 35 nominal raw retained')
    inspect_gruendler_headers(cache)
    for p in files:
        person=re.match(r'(\d+)',p.name)[1];d=demo[person];high=float(d['B'])>=21
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            raw=mne.io.read_raw_cnt(p,data_format='int32',eog=['HEOG','VEOG'],ecg=['EKG'],preload=False,verbose=False)
        if raw.info['sfreq']!=500 or len(raw.ch_names)!=67 or raw.ch_names[-3:]!=['HEOG','VEOG','EKG']:raise ValueError(f'Unreviewed CNT layout: {p.name}')
        if raw.n_times*len(raw.ch_names)*4>p.stat().st_size:raise ValueError(f'Impossible CNT sample count: {p.name}')
        raw.load_data(verbose=False)
        keep=mne.pick_types(raw.info,eeg=True,exclude=[]).tolist();names=[raw.ch_names[i] for i in keep]
        if keep!=list(range(64)):raise ValueError('Unexpected native EEG channel order')
        events=[dict(sample=int(raw.time_as_index([o],use_rounding=True)[0]),description=str(d)) for o,d in zip(raw.annotations.onset,raw.annotations.description)]
        extra=dict(group='high_OC_symptoms' if high else 'low_OC_symptoms',OCI=d['B'],age=d.get('H',''),sex_source_code=d.get('G',''),
            session_evidence='One distributed recording per participant; visit identifier not supplied')
        x,rows,names=make_cases(raw.get_data(picks=keep)*1e6,names,person,'unknown',p.relative_to(cache).as_posix(),'1' if high else '2',
            [(0,raw.n_times,'flanker_recording_including_practice_and_breaks')],extra,events)
        yield x,rows,names,dict(info_native(raw),source_file=p.relative_to(cache).as_posix(),participant_id=person,session_id='unknown',
            source_eeg_indices=keep,native_demographic_cells=d,
            source_demographic_header=xlsx_rows(cache/'Info.xlsx','SELECT')[0],
            native_bad_channels=raw.info['bads'],tail_samples_discarded=raw.n_times%2000,
            reader_evidence='Author Step1_PreProc.m explicitly pop_loadcnt dataformat int32; MNE auto byte-size inference fails on pilot, so int32 is explicit',
            documented_reference='Original online reference not independently recovered; no archive rereference',
            auxiliary_types_evidence='Author script: first 64 EEG incl M1/M2 and CB1/CB2; native labels identify HEOG/VEOG/EKG. Script later swaps EOG variable assignment, so labels are retained.')

READERS={'Singh2020':singh_records,'Cavanagh2018b':cava_records,'Gruendler2009':gruendler_records}

def spec_for(source):
    name,doi,paper=SOURCES[source]
    labels={'1':'high_obsessive_compulsive_symptoms_OCI_ge_21','2':'low_obsessive_compulsive_symptoms_OCI_lt_21'} if source=='Gruendler2009' else {'1':'parkinsons','2':'control'}
    note=('Four-second consecutive non-overlapping windows at native 500 Hz. Group classification uses participant labels, not stimulus labels. Native sensor labels/order are verified across all recordings; float64 microvolts; globally remove sensors constant/effectively flat in any case. No filter, resampling, baseline or rereference. '
        + {'Singh2020':'All 39 native pedalling recordings, including intertrial periods. 63 EEG; accelerometers X/Y/Z excluded. Preserve Aa/Bb/Cc labels; positions unknown where header omits them. V to uV uses 1e6, unlike ETH loader 1e5. PD subgroups retained in clinical table.',
           'Cavanagh2018b':'One OFF-medication visit per patient; control visit 1. Exclude patient 803 because OFF visit 1 is explicitly bad in original import script. Retain 27 PD and 28 controls; catalogue says 27+27, mirror has 28+28. Both eyes-closed and eyes-open native marker-bounded periods retained; 8070 has incomplete closed period. CPz reference documented, native common reference field retained. Exclude VEOG/X/Y/Z. No reconstructed CPz electrode or suggested later rereferencing/bad-channel processing is applied.',
           'Gruendler2009':'35 nominal raw student recordings retained, 12 high/23 low symptoms, not a clinical OCD diagnosis study. Exclude all 11 Neuroscan-processed _ready files: uncertain interpolation/reference/bad-segment history and several impossible header sample counts. These excluded files include 10 high/1 low, so processing variant is strongly associated with group. OCI column B >=21 follows ETH threshold; raw duplicate columns retained. Whole flanker recording including practice and breaks. Author specifies int32 CNT; validate physical sample bounds before loading. 64 EEG incl M1/M2/CB1/CB2; HEOG/VEOG/EKG excluded; no magnitude-based heuristic scaling. Author documents online reference between Cz/CPz; no archive rereference.'}[source])
    return dict(name=name,source=f'{source} / PRED+CT',cache=source,hz=500,points=2000,classes=2,train_subjects=0,
        labels=labels,doi=doi,paper=paper,note=note,licence='PDDL-1.0',licence_url='https://opendatacommons.org/licenses/pddl/1-0/',moabb_revision=None,
        splitter=group_split,evidence_files=['predct-source-lock.json','predct-licence-evidence.json','predct-preparation.md'],
        cache_evidence_files=['LICENSE.txt','README.md']+{
            'Singh2020':['ORIGINAL_README.txt','ALL_data_Modeling.csv','scripts/Patients_MS.xlsx','scripts/Step1_EEG_Pedaling_PreProcess.m','additional-metadata-receipt.json'],
            'Cavanagh2018b':['IMPORT_ME_REST.xlsx','QUALITY_CHECK.xlsx','PD_Rest_from_BV.m'],
            'Gruendler2009':['Info.xlsx','ORIGINAL_README.rtf','source-header-audit.json','scripts/Step1_PreProc.m','scripts/NScan_Chanlocs_60.mat']
        }[source],conversion_files=['prepare_predct.py','predct_inspect.py','download_predct_batch.py'],
        metadata_updates=dict(split_definition='Within each class, lexicographically sorted original participant IDs: first floor(75%) train, remainder test. No shared participants; explicit memberships retained.',
            original_data_source='https://predict.cs.unm.edu/downloads.php',
            source_doi_kind='Reference paper DOI; original dataset has no DOI identified',
            source_loader='Native adapter, not MOABB or OpenEEGBench fixed partitions',
            metadata_completeness=dict(participant_id='Direct native filename and clinical table',
                session_id='Direct numbered visit and medication table' if source=='Cavanagh2018b' else 'Unavailable: unknown; one distributed recording per participant',
                recording_id='Direct native filename',original_trial_id='Not applicable to archive-defined continuous windows; native events preserved',
                sample_indices='Exact distributed continuous recording samples, zero-based half-open',
                labels='Clinical group from filename and clinical table' if source!='Gruendler2009' else 'Assigned high/low by OCI column B >=21; score directly recovered',
                channel_names_order='Direct native labels, verified across every included recording',
                channel_types='Native labels plus original author script; auxiliary exclusions explicit',
                sensor_positions='Available per-record native header/chanlocs; no claim of individual measured geometry',
                reference='CPz documented by author, native common field retained' if source=='Cavanagh2018b' else 'Pz documented in paper; native header preserved' if source=='Singh2020' else 'Author README: online between Cz/CPz; stored _ready file references uncertain',
                original_partition='Unavailable; unsplit source, deterministic participant split assigned',
                licence='PDDL original catalogue plus pinned root data licence',
                frequency='Direct native 500 Hz; unchanged',preprocessing='Author import script/native headers directly preserved; paper acquisition statements labelled documented'),
            missing_metadata=['Visit IDs absent for single-recording sources: unknown, not invented','Sex code definitions not recovered; original codes retained','Original BrainVision files for resting MAT derivatives unavailable; sample indices refer to distributed MAT recordings'],
            cross_dataset_participant_identity='Original IDs are source-scoped. PDDys rest shares a cohort with other PDDys tasks; pedalling/interval-task identity crosswalk unresolved. Different recordings do not establish distinct people.',
            original_source_subject_count={'Singh2020':39,'Cavanagh2018b':56,'Gruendler2009':46}[source],
            original_source_recording_count={'Singh2020':39,'Cavanagh2018b':84,'Gruendler2009':46}[source],
            original_source_sensor_count={'Singh2020':66,'Cavanagh2018b':67,'Gruendler2009':67}[source],
            source_group_discrepancy='OCI>=21 in distributed column B gives 22 high/24 low; catalogue says 23+23' if source=='Gruendler2009' else 'Mirror 28 PD/28 control; catalogue 27+27. Archive excludes explicitly bad OFF recording 803/1, retaining 27 PD/28 control' if source=='Cavanagh2018b' else None,
            window_overlap_samples=0))

def prepare(source,root=SOURCE_ROOT,output=Path('D:/Data/EEG')):
    cache=Path(root)/source;receipt=json.loads((cache/'download-receipt.json').read_text())
    if receipt['repo']!='jalauer/'+source or receipt['licence']!='PDDL-1.0':raise ValueError('Unreviewed source')
    lock=next(x for x in json.loads((ROOT/'docs/predct-source-lock.json').read_text()) if x['dataset']==source)
    if receipt['revision']!=lock['revision']:raise ValueError('Source revision mismatch')
    receipt.update(source_record_id=receipt['predct_accession'],source_revision=f'Hugging Face {receipt["repo"]}@{receipt["revision"]}')
    for f in receipt['files']:f['name']=f['path']
    core.dump(cache/'download-receipt.json',receipt);core.dump(cache/'source-record.json',lock)
    if source=='Singh2020':additional_metadata_receipt(cache,receipt)
    core.SPECS[source]=spec_for(source);core.READERS[source]=READERS[source]
    result=core.prepare(source,Path(root),output)
    return complete_sidecars(source,root,output,result)

def additional_metadata_receipt(cache,receipt):
    names=['scripts/Patients_MS.xlsx','scripts/Step1_EEG_Pedaling_PreProcess.m'];files=[]
    for name in names:
        f=next(f for f in receipt['files'] if f.get('path',f.get('name'))==name)
        files.append(dict(path=name,name=name,bytes=f['bytes'],checksum=f['checksum'],sha256=f['sha256'],url=f['url']))
    core.dump(cache/'additional-metadata-receipt.json',dict(revision=receipt['revision'],files=files))

def removal_pair_audit(cache,folder,metadata):
    """Tie every removed-sensor failure to its exact archived case/hash."""
    from collections import Counter
    from tools.prepare_wang import digest_case
    q=metadata['channel_quality'];path=folder/'channel-removal-audit.tsv'
    previous=q.get('removal_pair_audit')
    if previous and path.exists() and core.sha(path)==previous['sha256']:return previous
    lookup={(r['source_file'],int(r['event_index'])):r for split in ['train','test'] for r in core.table(folder/f'cases_{split}.tsv')}
    keep=[q['source_channel_names'].index(n) for n in metadata['channel_names']]
    failures=[];counts=Counter();verified=set()
    for index,recording in enumerate(metadata['recordings']):
        with np.load(cache/'classification-intermediate'/f'recording-{index:04d}.npz',allow_pickle=False) as saved:x=saved['X']
        if x.shape[1]!=len(q['source_channel_names']):raise ValueError('Intermediate sensor schema changed')
        sd=x[:,q['removed_indices'],:].std(axis=2)
        for case,local in np.argwhere(sd<=1e-7):
            old=q['removed_indices'][local];key=(recording['source_file'],int(case));row=lookup[key]
            if key not in verified:
                if digest_case(x[case,keep])!=row['signal_sha256']:raise ValueError('Removal audit source/case hash mismatch')
                verified.add(key)
            signal=x[case,old];exact=bool(np.ptp(signal)==0);counts[old]+=1
            failures.append(dict(example_id=row['example_id'],split=row['split'],row=row['row'],participant_id=row['participant_id'],
                source_file=row['source_file'],event_index=row['event_index'],start_sample=row['start_sample'],end_sample=row['end_sample'],
                label=row['label'],pre_removal_channel_index=old,native_channel_index=recording['source_eeg_indices'][old],
                channel_name=q['source_channel_names'][old],exact_constant=exact,std_uV=float(sd[case,local]),constant_value_uV=float(signal[0]) if exact else ''))
    expected={i:n for i,n in enumerate(q['effectively_flat_case_counts']) if n}
    if dict(counts)!=expected:raise ValueError('Removal audit differs from original full-source quality counts')
    if not failures:raise ValueError('Removed channels without audited failures')
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,list(failures[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(failures)
    return dict(file=path.name,sha256=core.sha(path),pairs=len(failures),affected_cases=len(verified),
        source_to_export_hash_verified=True,threshold_std_uV=1e-7)

def complete_sidecars(source,root=SOURCE_ROOT,output=Path('D:/Data/EEG'),result=None):
    """Enrich completed sidecars only; numeric arrays/case order never change."""
    import shutil
    spec=spec_for(source);cache=Path(root)/source;folder=Path(output)/spec['name']
    if not folder.is_dir():raise FileNotFoundError(folder)
    path=folder/f'{spec["name"]}_metadata.json';metadata=json.loads(path.read_text())
    if source=='Singh2020':additional_metadata_receipt(cache,json.loads((cache/'download-receipt.json').read_text()))
    metadata.update(spec['metadata_updates'])
    metadata['source_doi']=None
    metadata['reference_paper_doi']=spec['doi']
    metadata['original_label_definition']={'Singh2020':'Native Group string: Control, PDwithFOG or PDwithoutFOG; PD subgroups both map1, Control maps2',
        'Cavanagh2018b':'PD/control identified by original PD_ID and MATCH CTL_ID columns and author subject lists',
        'Gruendler2009':'Original numerical OCI score from SELECT columnB; no original binary label assumed. Encode1 for OCI>=21,2 otherwise'}[source]
    metadata['source_loader_revision']='EEGBench native converter; ETH source inspection db78d893ead8d7ca847f6ae172c0f83d93e4fa2f'
    times={}
    if source in ['Singh2020','Gruendler2009']:
        import mne
        for recording in metadata['recordings']:
            p=cache/recording['source_file']
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',RuntimeWarning)
                raw=mne.io.read_raw_brainvision(p,preload=False,verbose=False) if source=='Singh2020' else mne.io.read_raw_cnt(p,data_format='int32',eog=['HEOG','VEOG'],ecg=['EKG'],preload=False,verbose=False)
            if raw.ch_names!=recording['native_channel_names']:raise ValueError('Metadata source sensor order changed')
            notes=extra_header_notes(raw);recording.update(notes);times[recording['source_file']]=notes['native_measurement_time_mne']
        metadata['metadata_evidence']['mne_inferred']='Montage coordinates/fiducials and timestamp representation may include MNE interpretations; raw-header evidence retained and not equated to individual measurements or a verified time zone'
    if source=='Singh2020':
        metadata['documented_acquisition']=dict(reference='Pz',ground='FPz',highpass_hz=.1,sampling_frequency_hz=500,
            evidence='Singh et al. (2020), section 2.3; documented publication information, not inferred from amplitude')
        workbook=xlsx_rows(cache/'scripts/Patients_MS.xlsx','AllPedaling')
        identities=[r['A']+r['B'] for r in workbook]
        if set(identities)!=set(metadata['actual_subjects']['train']+metadata['actual_subjects']['test']) or len(identities)!=39:
            raise ValueError('Original participant workbook differs from retained subjects')
        metadata['original_participant_workbook']=dict(file='scripts/Patients_MS.xlsx',sheet='AllPedaling',contains_header=False,identities=identities,verified_against_all_case_participants=True)
        metadata['original_author_sensor_roles']='Step1_EEG_Pedaling_PreProcess.m removes XYZ at indices63:66 and treats retained first63 as EEG; Aa/Bb/Cc anatomical labels unresolved, no renaming'
        metadata['original_event_mapping']={'S  1':'warning_cue','S  2':'GO_cue'}
        metadata['author_analysis_not_applied']=['GO-cue epochs [-1,+3]s','Pz reconstruction','Fp1/Fp2/FT10/TP9/TP10 removal','average/FCz rereferencing','mean removal','APPLE/FASTER channel/trial/ICA rejection and interpolation']
    if source=='Cavanagh2018b':
        metadata['original_acquisition_scope']='Author PD_Rest_from_BV.m loads {subject}_{visit}_ODDBALL.vhdr and crops the initial resting phase. Rest and oddball derivatives may therefore share original acquisitions; different MAT names do not establish recording independence.'
        metadata['original_acquisition_sample_mapping']='Source script selects time starting at0, suggesting offset0 into original VHDR. This is documented/inferred, not verified against unavailable original BrainVision files; case samples refer directly to distributed MAT.'
        metadata['source_quality_notes']=dict(author_flagged_channels=['FT9','TP9','TP10','FT10'],
            evidence='Optional processing block in original PD_Rest_from_BV.m identifies these as consistently bad',
            archive_policy='Retained because archive removal is based on constant/effectively flat channels, not undocumented artifact correction',
            baseline='Large native DC offsets remain in the raw microvolt values; no centring or rereferencing is applied')
        for sensor in metadata['sensors']:
            sensor['source_author_quality']='Flagged consistently bad in optional author processing block; retained nonconstant sensor' if sensor['name'] in ['FT9','TP9','TP10','FT10'] else 'No channel-specific author flag recovered'
    if source=='Gruendler2009':
        metadata['original_study_participants_as_documented']=60
        metadata['publication_analysis_participants_as_documented']=36
        metadata['source_preprocessing_variants']=dict(nominal_raw_recordings=35,neuroscan_processed_ready_recordings=11,
            evidence='Original author ORIGINAL_README.rtf, not inferred from amplitude',
            ready_uncertainty='Some electrodes may have been interpolated; possible bad-section markers; rereference to linked mastoids possible but not known',
            original_online_reference='Between Cz and CPz')
        metadata['original_source_sensor_count']=None
        metadata['distributed_source_sensor_counts']=[66,67]
        metadata['retained_source_sensor_count']=67
        metadata['excluded_source_files']=[dict(source_file=f['path'],reason='Processed _ready variant: uncertain history; several impossible header sample counts; deferred pending reliable decoding') for f in json.loads((cache/'download-receipt.json').read_text())['files'] if f['path'].endswith('_ready.cnt')]
        metadata['symptom_group_counts']=dict(distributed=dict(high=22,low=24),retained=dict(high=12,low=23),excluded=dict(high=10,low=1))
        metadata['source_and_conversion_notes']=spec['note']
        metadata['missing_metadata']+=['Exact pre-distribution interpolation/reference history unavailable for _ready files',
            'Possible native Neuroscan bad-section markers are not independently audited for complete MNE decoding',
            'Original study60 participants, distributed46 and publication analyses36 (author README); exact original selection not reconstructible']
        for recording in metadata['recordings']:
            ready='_ready.cnt' in recording['source_file']
            recording['source_preprocessing_variant']='author_neuroscan_processed_ready' if ready else 'author_described_raw'
            recording['documented_reference']='Online between Cz and CPz; stored reference unknown for processed _ready files' if ready else 'Author README: online between Cz and CPz; file described as nominal raw'
    changed=[path]
    if metadata['channel_quality']['removed_indices']:
        metadata['channel_quality']['removal_pair_audit']=removal_pair_audit(cache,folder,metadata)
        changed.append(folder/'channel-removal-audit.tsv')
    for recording in metadata['recordings']:
        recording['exported_native_channel_indices']=[recording['native_channel_names'].index(n) for n in metadata['channel_names']]
    core.dump(path,metadata)
    if source=='Cavanagh2018b':
        p=folder/'channels.tsv'
        with p.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,list(metadata['sensors'][0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(metadata['sensors'])
        changed.append(p)
    completeness=folder/'metadata-completeness.json'
    core.dump(completeness,dict(fields=metadata['metadata_completeness'],evidence=metadata['metadata_evidence'],
        missing_or_inconsistent=metadata['missing_metadata']+metadata['missing_or_inconsistent_metadata']))
    changed.append(completeness)
    attribution=folder/'ATTRIBUTION.txt'
    attribution.write_text(f'{spec["source"]}. Original data: https://predict.cs.unm.edu/downloads.php . No original dataset DOI identified. Reference: {spec["paper"]}; paper DOI {spec["doi"]}. Data: PDDL-1.0 https://opendatacommons.org/licenses/pddl/1-0/ .\nChanges: native EEG selection, four-second windows, participant split and float64 microvolt .ts export. See metadata for exclusions and acquisition evidence.\n',encoding='utf-8')
    changed.append(attribution)
    # Older in-flight conversions used the sole-recording ordinal 1. It is not
    # a recovered original run ID; make this missing value explicit in sidecars.
    for split in ['train','test']:
        p=folder/f'cases_{split}.tsv'
        with p.open(encoding='utf-8',newline='') as f:
            reader=csv.DictReader(f,delimiter='\t');fields=list(reader.fieldnames);rows=list(reader)
        report=metadata['shapes'][split]
        if len(rows)!=report[0] or any(int(row['row'])!=i or row['split']!=split.upper() for i,row in enumerate(rows)):
            raise ValueError('Metadata alignment changed before sidecar enrichment')
        if 'run_id_evidence' not in fields:fields.append('run_id_evidence')
        for row in rows:
            row['run_id']='unknown';row['run_id_evidence']='Original run identifier unavailable; native recording filename is retained'
            row['source_epoch_index']='';row['source_event_sample']=''
            row['event_index_evidence']='Archive window ordinal, not a native event or trial index'
            row.update(original_label_fields(source,row))
        if 'event_index_evidence' not in fields:fields.append('event_index_evidence')
        if 'source_label_evidence' not in fields:fields.append('source_label_evidence')
        indices={r['source_file']:r['exported_native_channel_indices'] for r in metadata['recordings']}
        if 'exported_native_channel_indices' not in fields:fields.append('exported_native_channel_indices')
        for row in rows:row['exported_native_channel_indices']=json.dumps(indices[row['source_file']],separators=(',',':'))
        if times:
            if 'native_measurement_time_mne' not in fields:fields.append('native_measurement_time_mne')
            for row in rows:row['native_measurement_time_mne']=times[row['source_file']] or ''
        if source=='Cavanagh2018b':
            for key in ['original_acquisition_identifier','original_acquisition_evidence']:
                if key not in fields:fields.append(key)
            for row in rows:
                row['original_acquisition_identifier']=f'{row["participant_id"]}_{row["session_id"]}_ODDBALL.vhdr'
                row['original_acquisition_evidence']='Original author import script filename pattern; original BrainVision file not distributed in this mirror'
        if source=='Gruendler2009':
            for key in ['source_preprocessing_variant','source_reference_evidence']:
                if key not in fields:fields.append(key)
            for row in rows:
                ready='_ready.cnt' in row['source_file']
                row['source_preprocessing_variant']='author_neuroscan_processed_ready' if ready else 'author_described_raw'
                row['source_reference_evidence']='Stored reference uncertain: original author says possible linked mastoids' if ready else 'Author documents online reference between Cz and CPz; nominal raw file'
        with p.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
        changed.append(p)
    validation_path=folder/f'{spec["name"]}_validation.json';validation=json.loads(validation_path.read_text())
    validation['source_sensor_identity']={'Singh2020':'Native BrainVision labels/types/order',
        'Cavanagh2018b':'Native EEGLAB chanlocs labels/order; author import script supplies EEG/auxiliary roles',
        'Gruendler2009':'Native CNT labels/order; native names and original author script supply EEG/EOG/ECG roles'}[source]
    core.dump(validation_path,validation);changed.append(validation_path)
    for file in spec['cache_evidence_files']:
        dest=folder/'source_metadata'/file;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(cache/file,dest);changed.append(dest)
    for file in ['download-receipt.json','source-record.json']:
        dest=folder/'source_metadata'/file;shutil.copy2(cache/file,dest);changed.append(dest)
    if source=='Singh2020':
        for p in sorted((cache/'raw_data').iterdir()):
            if p.suffix.lower() not in ['.vhdr','.vmrk']:continue
            dest=folder/'source_metadata'/p.relative_to(cache);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest);changed.append(dest)
    for file in spec['evidence_files']:
        dest=folder/'source_metadata'/file;shutil.copy2(ROOT/'docs'/file,dest);changed.append(dest)
    snapshot=ROOT/'.openeegbench/predct-original-catalogue.html'
    if snapshot.exists():
        dest=folder/'source_metadata/predct-original-catalogue.html';shutil.copy2(snapshot,dest);changed.append(dest)
    for file in ['prepare_predct.py','predct_inspect.py','download_predct_batch.py']:
        dest=folder/'conversion_code'/file;shutil.copy2(ROOT/'tools'/file,dest);changed.append(dest)
    manifest=folder/f'{spec["name"]}_manifest.json';m=json.loads(manifest.read_text())
    m['source_files']=json.loads((cache/'download-receipt.json').read_text())['files']
    m['label_mapping']=metadata['label_mapping'];m['window_samples']=2000;m['sampling_frequency_hz']=500
    m['original_source_url']='https://predict.cs.unm.edu/downloads.php';m['licence_url']=spec['licence_url']
    m['source_doi']=None;m['reference_paper_doi']=spec['doi'];m['source_doi_kind']='No original dataset DOI identified; publication DOI stored separately'
    for p in changed:m['artifacts'][p.relative_to(folder).as_posix()]=dict(bytes=p.stat().st_size,sha256=core.sha(p))
    core.dump(manifest,m)
    results_path=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(results_path.read_text())
    result=results[source] if result is None else result
    result['validation']=validation
    result['channel_quality']=metadata['channel_quality']
    result['size_GB']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9
    results[source]=result;core.dump(results_path,results)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--datasets',nargs='+',choices=list(SOURCES),default=list(SOURCES));p.add_argument('--source-root',type=Path,default=SOURCE_ROOT);p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));a=p.parse_args()
    for source in a.datasets:prepare(source,a.source_root,a.output)
