"""CodedSymbols: source-pinned Thielen2021 offline 20-target trials.

Reads original raw GDF (512 Hz), not the separate 180 Hz MATLAB buffers.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import re
import shutil
import ssl
import tempfile
import time
import urllib.request

import certifi
import h5py
import numpy as np
from scipy.io import loadmat

from tools.prepare_erpcore import safe
from tools.prepare_moabb import MOABB_REVISION, dump, lines, sha, signal_hash

NAME='CodedSymbols'
BASE='https://public.data.ru.nl/dcc/DSC_2018.00122_448_v3/'
MANIFEST_SHA256='8fb809122ade5446fc137b3d5ad8e36e357bf252f01d7f1e9404a65dcae4633b'
LICENSE_SHA256='240cd1c345932866b833dd34c637d7b4832cd02218792feee0501349f312353b'
SFREQ,POINTS=512,16128
NATIVE=['AF3','F3','FC5','P7','P8','FC6','F4','AF4']
CHANNELS=['Fpz','T7','O1','POz','Oz','Iz','O2','T8']
RESOURCES=['LICENSE.txt','README.txt','resources/nt_cap8.loc','resources/nt_cap8.txt','resources/subset_20.mat','resources/mgold_61_6521_flip_balanced_20.mat','resources/mgold_61_6521_flip_balanced_20.txt']
FIELDS=['split','row','example_id','group','participant_id','source_participant_id','session_id','run_id','loader_session_id','loader_run_id','recording_id','source_file','source_labels_file','trial_index','source_label_index','marker_event_index','marker_code','cycle_marker_count','cycle_marker_samples','max_cycle_deviation_samples','cycle_timing_warning','event_sample','start_sample','end_sample','start_time_seconds','end_time_seconds','source_label','label','label_description','original_partition','signal_sha256']


def fetch_verified(url,path,checksum=None):
    """Atomic, retried transfer using publisher SHA256 and a verified TLS bundle."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and (checksum is None or sha(path)==checksum):return path
    context=ssl.create_default_context(cafile=certifi.where())
    for attempt in range(8):
        try:
            part=path.with_name(path.name+'.part')
            request=urllib.request.Request(url,headers={'User-Agent':'EEGBench source-pinned preparation','Cache-Control':'no-cache'})
            with urllib.request.urlopen(request,context=context,timeout=90) as response,part.open('wb') as file:
                shutil.copyfileobj(response,file,1024*1024)
            if checksum and sha(part)!=checksum:raise ValueError(f'Publisher checksum mismatch: {path.name}')
            part.replace(path);return path
        except Exception as exc:
            if attempt==7:raise RuntimeError(f'Unable to fetch {url}: {exc}') from exc
            time.sleep(min(2**attempt,20))


def publisher_manifest(cache,download=True):
    cache=Path(cache);path=cache/'MANIFEST.txt'
    if download:fetch_verified(BASE+'MANIFEST.txt',path,MANIFEST_SHA256)
    if sha(path)!=MANIFEST_SHA256:raise ValueError('Pinned publisher manifest changed')
    result={}
    for line in path.read_text(encoding='utf-8').splitlines():
        checksum,name=line.split(' ',1)
        if not re.fullmatch('[a-f0-9]{64}',checksum):raise ValueError('Invalid publisher SHA256')
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe original source path')
        result[name]=checksum
    return result


def recording_files(manifest,subject,run):
    prefix=f'sourcedata/offline/sub-{subject:02d}/block_{run}/'
    gdf=[p for p in manifest if p.startswith(prefix) and re.fullmatch(r'sub-\d{2}_\d{8}_block_\d_main_eeg.gdf',Path(p).name)]
    if len(gdf)!=1:raise ValueError('Missing/ambiguous original GDF recording')
    return [gdf[0],*[prefix+name for name in ['trainlabels.mat','cfg.mat','hdr.mat']]]


def sources(cache,subjects,runs,download=True):
    cache=Path(cache);manifest=publisher_manifest(cache,download)
    # Establish original data licensing before any signal downloads.
    licence=cache/'LICENSE.txt'
    if download:fetch_verified(BASE+'LICENSE.txt',licence,LICENSE_SHA256)
    if sha(licence)!=LICENSE_SHA256 or not licence.read_text().startswith('CC0 1.0 Universal'):raise ValueError('Unexpected original data licence')
    needed=list(RESOURCES)
    for subject in subjects:
        for run in runs:needed.extend(recording_files(manifest,subject,run))
    def ensure(name):
        path=cache/name
        if download:fetch_verified(BASE+name,path,manifest[name])
        if not path.is_file() or sha(path)!=manifest[name]:raise ValueError(f'Missing/modified source: {name}')
        return dict(path=name,url=BASE+name,sha256=manifest[name],bytes=path.stat().st_size)
    with ThreadPoolExecutor(max_workers=4) as pool:
        inventory=[]
        for i,item in enumerate(pool.map(ensure,needed),1):
            inventory.append(item)
            if i%25==0:print(f'{i}/{len(needed)} original files verified',flush=True)
    loader=cache/'moabb-thielen2021.py'
    if download:fetch_verified(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/thielen2021.py',loader)
    if not loader.is_file():raise ValueError('Missing pinned loader evidence')
    return manifest,inventory


def matlab_value(path):
    """Decode source v7.3 structs/cells/chars without interpreting configurations."""
    if not h5py.is_hdf5(path):return loadmat(path,simplify_cells=True)['v']
    with h5py.File(path,'r') as file:
        def decode(obj):
            if isinstance(obj,h5py.Group):return {k:decode(v) for k,v in obj.items() if not k.startswith('#')}
            value=obj[()]
            kind=obj.attrs.get('MATLAB_class',b'')
            if isinstance(kind,bytes):kind=kind.decode()
            if obj.attrs.get('MATLAB_empty',0):return []
            if kind=='char':return ''.join(chr(int(x)) for x in value.ravel())
            if h5py.check_dtype(ref=obj.dtype) is not None:
                values=[decode(file[ref]) if ref else None for ref in value.ravel()]
                return values[0] if len(values)==1 else values
            value=np.asarray(value)
            if value.size==1:return safe(value.item())
            if value.ndim==2 and 1 in value.shape:return safe(value.ravel())
            return safe(value.T)
        return decode(file['v'])


def trial_groups(events,labels,sfreq=SFREQ):
    labels=np.asarray(labels).ravel()
    if len(labels)!=20 or not np.array_equal(np.sort(labels),np.arange(1,21)):raise ValueError('Expected original 1..20 target labels once per block')
    if len(events)==0 or np.any(np.diff(events[:,0])<=0):raise ValueError('Missing or unordered STATUS events')
    gaps=np.diff(events[:,0])/sfreq
    starts=np.r_[0,1+np.flatnonzero((gaps<1.8)|(gaps>2.4))]
    if len(starts)!=20:raise ValueError('STATUS grouping does not recover 20 original trials')
    if np.any(np.diff(events[starts,0])<round(31.5*sfreq)):raise ValueError('Nominal full trials overlap')
    result=[]
    for trial,(start,stop) in enumerate(zip(starts,np.r_[starts[1:],len(events)],strict=True)):
        group=events[start:stop]
        if len(group) not in [15,16]:raise ValueError('Unexpected number of code-cycle markers')
        samples=group[:,0]
        deviation=float(np.max(np.abs((samples-samples[0])-np.arange(len(group))*2.1*sfreq)))
        result.append(dict(trial=trial,event_index=int(start),sample=int(samples[0]),code=int(group[0,2]),samples=samples.tolist(),label=int(labels[trial]),max_deviation_samples=deviation,timing_warning=deviation>0.1*sfreq))
    return result


def inspect_recording(cache,gdf_name,subject):
    import mne
    cache=Path(cache);directory=(cache/gdf_name).parent
    cfg=matlab_value(directory/'cfg.mat');hdr=matlab_value(directory/'hdr.mat');labels=matlab_value(directory/'trainlabels.mat')
    # The numeric subjectid is 1 for sub-23 too, so it does not match the
    # dataset's participant index. Preserve it without grouping by it.
    if cfg['main']['subject']!=f'sub-{subject:02d}':raise ValueError('Configuration participant mismatch')
    if cfg['main']['trainlabels']!=labels:raise ValueError('Original target labels disagree with acquisition configuration')
    if cfg['main']['trialtime']!=31.5 or cfg['stimulation']['rate']!=60 or cfg['stimulation']['layout']!=list(range(1,21)):raise ValueError('Changed symbol timing/layout protocol')
    raw=mne.io.read_raw_gdf(cache/gdf_name,stim_channel='status',preload=True,verbose='ERROR')
    if raw.info['sfreq']!=SFREQ or raw.ch_names!=['STATUS',*NATIVE] or raw.get_channel_types()!=['stim',*(['eeg']*8)]:raise ValueError('Unexpected GDF channels/order/types/frequency')
    extras=raw._raw_extras[0]
    if not np.all(np.asarray(extras['units'][1:])==1e-6):raise ValueError('Unexpected EEG physical units')
    events=mne.find_events(raw,verbose='ERROR');groups=trial_groups(events,labels)
    data=raw.get_data(picks=list(range(1,9)))
    for group in groups:
        start=group['sample']-raw.first_samp;end=start+POINTS
        if start<0 or end>raw.n_times:raise ValueError('Incomplete full 31.5-second trial')
        group['case']=np.asarray(data[:,start:end],dtype='<f4')
        if not np.isfinite(group['case']).all():raise ValueError('Nonfinite selected EEG')
    native=dict(names=raw.ch_names,types=raw.get_channel_types(),sampling_frequency_hz=raw.info['sfreq'],samples=raw.n_times,first_samp=raw.first_samp,native_subject_info=raw.info.get('subject_info'),measurement_datetime=raw.info.get('meas_date'),native_loc=[ch['loc'] for ch in raw.info['chs']],original_units=raw._orig_units,gdf_header={k:extras.get(k) for k in ['units','cal','offsets','physical_min','physical_max','digital_min','digital_max','ref','gnd','highpass','lowpass','notch']},status_events=events,nonfinite_eeg_values=int((~np.isfinite(data)).sum()))
    raw.close()
    return groups,safe(native),cfg,hdr


def header():
    return (f'# Thielen2021 offline, CC0. See ordered sensor/case sidecars.\n@problemName {NAME}\n'
            '@timestamps false\n@missing false\n@univariate false\n@dimensions 8\n@equalLength true\n'
            '@seriesLength 16128\n@classLabel true '+' '.join(map(str,range(1,21)))+'\n@data\n')


def validate(folder,split):
    counts=Counter();people=set();hashes=set();n=0;last=(-1,-1,-1)
    with (folder/f'cases_{split.lower()}.tsv').open(newline='',encoding='utf-8') as file:
        rows=iter(csv.DictReader(file,delimiter='\t'))
        for n,line in enumerate(lines(folder/f'{NAME}_{split}.ts'),1):
            row=next(rows,None)
            if row is None or row['split']!=split or int(row['row'])!=n-1:raise ValueError('Case metadata alignment failed')
            parts=line.strip().split(':');label=int(parts[-1]);case=np.stack([np.fromstring(p,sep=',',dtype='<f4') for p in parts[:-1]])
            hashed=signal_hash(case);key=tuple(int(row[k]) for k in ['participant_id','run_id','trial_index'])
            if case.shape!=(8,POINTS) or not np.isfinite(case).all() or hashed!=row['signal_sha256']:raise ValueError('Full numeric roundtrip mismatch')
            if label!=int(row['source_label']) or label!=int(row['label']) or key<=last:raise ValueError('Label/source order mismatch')
            markers=json.loads(row['cycle_marker_samples'])
            if len(markers)!=int(row['cycle_marker_count']) or int(row['start_sample'])!=markers[0] or int(row['end_sample'])-markers[0]!=POINTS:raise ValueError('Original marker/epoch bounds mismatch')
            if hashed in hashes:raise ValueError('Duplicate exported case within partition')
            hashes.add(hashed);people.add(row['participant_id']);counts[label]+=1;last=key
        if next(rows,None) is not None:raise ValueError('Extra case metadata rows')
    return dict(cases=n,shape=[n,8,POINTS],class_counts=dict(sorted(counts.items())),subjects=sorted(people),exact_float32_roundtrip=True),hashes


def smoke_test(folder):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier
    loaded={}
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        for split in ['TRAIN','TEST']:
            selected={i:[] for i in range(1,21)}
            for line in lines(folder/f'{NAME}_{split}.ts'):
                label=int(line.rsplit(':',1)[1])
                if len(selected[label])<2:selected[label].append(line)
                if all(len(v)==2 for v in selected.values()):break
            path=Path(tmp)/f'{split}.ts';path.write_text(header()+''.join(line for group in selected.values() for line in group),encoding='ascii')
            loaded[split]=load_from_ts_file(path)
        classifier=SummaryClassifier(random_state=0,n_jobs=1);classifier.fit(*loaded['TRAIN']);pred=classifier.predict(loaded['TEST'][0])
        if len(pred)!=len(loaded['TEST'][1]):raise ValueError('aeon classifier compatibility failed')
    return dict(passed=True,aeon_version=aeon.__version__,classifier='SummaryClassifier',train_cases=len(loaded['TRAIN'][1]),test_cases=len(pred),scope='Representative all-class .ts check; full numeric readback independently covers every case')


def convert(cache,output,subjects=tuple(range(1,31)),train=tuple(range(1,23)),runs=tuple(range(1,6)),download=True,smoke=True):
    import mne
    cache,output=Path(cache).resolve(),Path(output).resolve();subjects=tuple(sorted(subjects));train=set(train);runs=tuple(sorted(runs))
    if len(subjects)!=len(set(subjects)) or not set(subjects)<=set(range(1,31)) or not train or not train<set(subjects) or not runs or not set(runs)<=set(range(1,6)):raise ValueError('Invalid source selection/split')
    folder=output/NAME
    if folder.exists():raise FileExistsError(f'Refusing to overwrite {folder}')
    manifest,inventory=sources(cache,subjects,runs,download)
    montage_rows=[line.split() for line in (cache/'resources/nt_cap8.loc').read_text().splitlines() if line.strip()]
    if [r[-1] for r in montage_rows]!=CHANNELS:raise ValueError('Original montage channel order changed')
    codes=loadmat(cache/'resources/mgold_61_6521_flip_balanced_20.mat')['codes']
    if codes.shape!=(126,20) or not set(np.unique(codes))<={0,1}:raise ValueError('Changed code-to-symbol mapping')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{NAME}-',dir=output) as tmp:
        stage=Path(tmp);evidence=stage/'source_metadata';evidence.mkdir();counts=Counter();records=[];handles={};tables={};writers={}
        fmt=','.join(['%.9g']*POINTS)
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{NAME}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header())
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',encoding='utf-8',newline='')
                writers[split]=csv.DictWriter(tables[split],FIELDS,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for subject in subjects:
                for run in runs:
                    files=recording_files(manifest,subject,run);gdf=files[0];groups,native,cfg,hdr=inspect_recording(cache,gdf,subject)
                    date=re.search(r'_(\d{8})_',Path(gdf).name).group(1);sid=f'{subject:02d}';split='TRAIN' if subject in train else 'TEST'
                    for group in groups:
                        start=group['sample'];label=group['label'];case=group['case'];trial=group['trial']
                        row=dict(split=split,row=counts[split],example_id=f'Thielen2021/offline/{sid}/{run}/{trial:02d}',group=sid,participant_id=sid,source_participant_id=f'sub-{sid}',session_id=date,run_id=f'{run:02d}',loader_session_id='0',loader_run_id=str(run-1),recording_id=Path(gdf).stem,source_file=gdf,source_labels_file=files[1],trial_index=trial,source_label_index=trial,marker_event_index=group['event_index'],marker_code=group['code'],cycle_marker_count=len(group['samples']),cycle_marker_samples=json.dumps(group['samples']),event_sample=start,start_sample=start,end_sample=start+POINTS,start_time_seconds=start/SFREQ,end_time_seconds=(start+POINTS)/SFREQ,source_label=label,label=label,label_description=f'symbol_{label:02d}',original_partition='offline; no official train/test split',signal_sha256=signal_hash(case))
                        row['max_cycle_deviation_samples']=group['max_deviation_samples']
                        row['cycle_timing_warning']=group['timing_warning']
                        writers[split].writerow(row);handles[split].write(':'.join(fmt%tuple(ch.tolist()) for ch in case)+f':{label}\n');counts[split]+=1
                    sub=evidence/f'sub-{sid}'/f'block_{run}';sub.mkdir(parents=True)
                    for file in files[1:]:shutil.copy2(cache/file,sub/Path(file).name)
                    dump(sub/'decoded-source.json',dict(native_gdf=native,configuration=cfg,processed_buffer_header=hdr))
                    records.append(dict(participant_id=sid,session_id=date,session_evidence='original filename date; raw GDF measurement datetime unavailable',run_id=f'{run:02d}',source_file=gdf,cases=len(groups),native_gdf=native,matlab_buffer_frequency=hdr['Fs'],configuration_subject=cfg['main']['subject'],montage_first_label=CHANNELS[0],alternative_processed_header_first_label=hdr['cap']['label'][0]))
                    records[-1]['max_cycle_deviation_samples']=max(g['max_deviation_samples'] for g in groups)
                    records[-1]['trials_with_cycle_deviation_over_100ms']=sum(g['timing_warning'] for g in groups)
                print(f'{NAME}: participant {sid}, cases {dict(counts)}',flush=True)
        finally:
            for handle in [*handles.values(),*tables.values()]:handle.close()
        reports={};hashes={}
        for split in ['TRAIN','TEST']:
            reports[split],hashes[split]=validate(stage,split);print(f'{split} full numeric readback passed',flush=True)
        if hashes['TRAIN']&hashes['TEST'] or set(reports['TRAIN']['subjects'])&set(reports['TEST']['subjects']):raise ValueError('Participants or duplicate signals cross train/test')
        for split,people in [('TRAIN',train),('TEST',set(subjects)-train)]:
            if reports[split]['cases']!=len(people)*len(runs)*20 or reports[split]['class_counts']!={i:len(people)*len(runs) for i in range(1,21)}:raise ValueError('Unexpected shapes/class counts')
        with (stage/f'{NAME}_rows.tsv').open('w',encoding='utf-8',newline='') as target:
            writer=csv.DictWriter(target,FIELDS,delimiter='\t',lineterminator='\n');writer.writeheader()
            for split in ['train','test']:
                with (stage/f'cases_{split}.tsv').open(newline='',encoding='utf-8') as source:writer.writerows(csv.DictReader(source,delimiter='\t'))
        split_definition=dict(unit='participant',train=[f'{s:02d}' for s in sorted(train)],test=[f'{s:02d}' for s in subjects if s not in train],official_split=False,validation='none',order='numeric participant, numeric block, original chronological trial/label-vector order')
        validation=dict(quality_status='passed_with_documented_sensor_and_timing_limits',partitions=reports,metadata_rows_verified=sum(counts.values()),subject_overlap=[],duplicate_cases_across_splits=0,duplicates_within_partitions=0,channel_order_verified_every_recording=True,all_exported_cases_finite=True,aeon=smoke_test(stage) if smoke else {'passed':None})
        metadata=dict(name=NAME,source_dataset_name='Thielen2021 offline',source_aliases=['Thielen2021','nm000214','DSC_2018.00122_448_v3'],source_study_id='10.34973/9txv-z787',source_url=BASE,source_doi='10.34973/9txv-z787',paper_doi='10.1088/1741-2552/abecef',source_version=3,licence='CC0-1.0',license='CC0-1.0',license_evidence=BASE+'LICENSE.txt',target='Attended symbol/code identity, all 20 offline targets; not binary code-bit state',domain='BCI',subjects=len(subjects),sessions=len(subjects),sessions_per_subject=1,recordings=len(records),sampling_frequency_hz=SFREQ,original_sampling_frequency_hz=SFREQ,frequency=SFREQ,channel_count=8,channel_names=CHANNELS,channel_types=['EEG']*8,source_channel_count=9,excluded_channel_types={'STIM':1},native_axis_indices=list(range(1,9)),timepoints=POINTS,shapes={s.lower():reports[s]['shape'] for s in reports},classes=20,label_map={str(i):f'symbol_{i:02d}' for i in range(1,21)},label_encoding='Original 1-based trainlabels.mat target/code-column IDs preserved unchanged',class_counts={s.lower():reports[s]['class_counts'] for s in reports},window_seconds=31.5,epoch_interval='[first trial STATUS marker, marker+16128), zero-based original GDF samples, end exclusive',overlap='Full trials do not overlap; 15 cycles per trial are not separate cases',preprocessing=dict(epoching='Full raw-GDF trial at first grouped STATUS marker, 15 cycles',filtering='none added',resampling='none',referencing='unchanged',baseline='none',units='MNE-calibrated volts from GDF microvolt physical unit tags; no additional amplitude scaling',dtype='float32; .ts nine significant digits, exact float32 numeric roundtrip',source_axis_selection='STATUS axis 0 excluded; native axes 1..8 retained, without reordering'),channel_name_evidence=dict(native_gdf=NATIVE,exported=CHANNELS,source_montage='resources/nt_cap8.loc',mapping_evidence='Pinned MOABB custom electrode mapping and source .loc axis order',first_sensor_conflict=dict(loc_and_loader='Fpz',txt_and_processed_header='Fp1',publication_overview='Fz',decision='Use literal .loc name Fpz; preserve all conflicting aliases; true physical first-electrode site unresolved')),sensors=[dict(array_index=i,name=name,type='EEG',native_gdf_name=NATIVE[i],native_gdf_axis=i+1,template_polar_angle_degrees=float(montage_rows[i][1]),template_polar_radius=float(montage_rows[i][2]),position_evidence='Original .loc template, not individual digitization',physical_name_uncertain=i==0) for i,name in enumerate(CHANNELS)],reference='CMS/DRL per source study/loader acquisition description; no re-reference added',montage='Custom eight-electrode template; .loc and .txt/header disagreements retained',split_policy=split_definition,case_metadata=dict(files=['cases_train.tsv','cases_test.tsv',f'{NAME}_rows.tsv'],ordering='TRAIN then TEST in combined table; zero-based row per partition',identifiers='strings; preserve leading zeros'),separate_processed_buffers=dict(sampling_frequency_hz=180,evidence='hdr.mat Fs and traintrials pilot shape 20 x 5670 x 8',used_in_export=False,note='Configuration filter/downsampling settings describe other processed buffers, not a transformation applied to these raw GDF exports'),publication_evidence=dict(participants='30 healthy adults, 17 female/13 male, ages 19–62; aggregate evidence only',protocol='Five offline blocks of 20 targets, one cue per target and 15 repeats of 126-bit codes at 60 Hz'),metadata_evidence=dict(distributed_files=['publisher licence and SHA256 manifest','subject/date/block filenames','cfg participant and label order','raw GDF frequency/calibration/types/native order','STATUS marker samples/codes','20 target labels','code matrix','montage files and native header aliases'],publication_or_loader=['corrected custom electrode mapping','first-site Fz alias','reference/CMS-DRL','aggregate demographics'],locally_defined=['subject train/test split','trial groups and half-open crop bounds','case IDs']),missing_metadata=['Unambiguous physical identity of the first electrode (Fpz/Fp1/Fz conflict)','Individual measured sensor positions','Individual demographics','Exact GDF acquisition time and native subject string','Verified glyph-to-index mapping for the calculator symbols'])
        metadata['timing_quality']=dict(nominal_window_seconds=31.5,max_cycle_deviation_samples=max(r['max_cycle_deviation_samples'] for r in records),trials_with_cycle_deviation_over_100ms=sum(r['trials_with_cycle_deviation_over_100ms'] for r in records),policy='Preserve original marker times and samples; report drift without time warping. Trial count, labels, complete windows and non-overlap remain mandatory.')
        validation['source_timing']=metadata['timing_quality']
        dump(stage/f'{NAME}_metadata.json',metadata);dump(stage/f'{NAME}_validation.json',validation);dump(stage/'recordings.json',records)
        dump(stage/'metadata-completeness.json',dict(evidence=metadata['metadata_evidence'],missing=metadata['missing_metadata']))
        (stage/'channels.txt').write_text(', '.join(CHANNELS)+'\n',encoding='utf-8')
        with (stage/'channels.tsv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,['array_index','name','type','native_gdf_axis','native_gdf_name','physical_name_uncertain'],delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(metadata['sensors'])
        for file in ['MANIFEST.txt','moabb-thielen2021.py',*RESOURCES]:
            dest=evidence/file;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(cache/file,dest)
        dump(evidence/'codes.json',dict(presentation_rate_hz=60,cycles_per_trial=15,original_label_to_column='source label minus one',codes=codes.tolist()))
        (stage/'ATTRIBUTION.txt').write_text('Thielen, J.; Marsman, P.; Farquhar, J.; Desain, P. From full calibration to zero training for a code-modulated visual evoked potentials brain computer interface. Data DOI 10.34973/9txv-z787, version 3; paper DOI 10.1088/1741-2552/abecef. CC0 1.0, original LICENSE.txt retained.\nData were provided (in part) by the Radboud University, Nijmegen, The Netherlands.\nEEGBench changes: raw-GDF EEG selection, full-trial epochs, float32 conversion, participant split and .ts export. No added filters, resampling or reference changes.\n',encoding='utf-8')
        (stage/f'README_{NAME}.md').write_text('# CodedSymbols\n\nThielen2021 offline attended-symbol task: original target IDs 1–20. Each case is 31.5 seconds of eight raw EEG axes at 512 Hz. Train/test .ts files have exactly aligned case TSVs; combined rows are TRAIN then TEST. Read IDs as strings. Original STATUS samples, cycle markers and MATLAB label-vector indices are retained.\n\nThe first channel is labelled Fpz according to the supplied .loc file, with conflicting Fp1/Fz aliases preserved and its true physical site flagged as unresolved. Native GDF cap names are known placeholders; axes are never reordered. Template positions are not individual measurements.\n\nThe separate 180 Hz MATLAB buffers and their preprocessing are not used. GDF calibrated volts are cast to float32 and written at nine significant digits. No added filters, resampling, scaling or reference changes. See metadata, original licence, source headers, manifests and validation.\n',encoding='utf-8')
        code=stage/'conversion_code';code.mkdir()
        for name in ['prepare_thielen.py','prepare_moabb.py','prepare_erpcore.py','requirements-moabb.txt']:shutil.copy2(Path(__file__).with_name(name),code/name)
        dump(stage/f'{NAME}_manifest.json',dict(name=NAME,source_revision='DSC_2018.00122_448_v3',source_url=BASE,source_doi=metadata['source_doi'],licence='CC0-1.0',publisher_manifest_sha256=MANIFEST_SHA256,license_sha256=LICENSE_SHA256,source_files=inventory,moabb_revision=MOABB_REVISION,mne_version=mne.__version__,numpy_version=np.__version__,split=split_definition,conversion=metadata['preprocessing'],validation=validation,artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(folder)
    return metadata,validation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources/Thielen2021'))
    parser.add_argument('--output',type=Path,default=Path('D:/Data/EEG'))
    parser.add_argument('--subjects',default=','.join(map(str,range(1,31))))
    parser.add_argument('--train-subjects',default=','.join(map(str,range(1,23))))
    parser.add_argument('--runs',default='1,2,3,4,5')
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    convert(args.cache,args.output,tuple(map(int,args.subjects.split(','))),tuple(map(int,args.train_subjects.split(','))),tuple(map(int,args.runs.split(','))),not args.offline)


if __name__=='__main__':main()
