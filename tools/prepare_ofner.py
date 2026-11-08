"""Ofner2017 execution and imagination: original GDF to .ts and sensor/case sidecars.

Requires MNE >=1.13 (NumPy 2 compatible GDF reader) and aeon for validation.
Run with --help. Source downloads can be shared by the two independent exports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import shutil
import tempfile
import time
import urllib.request

import numpy as np

from tools.prepare_erpcore import safe
from tools.prepare_moabb import MOABB_REVISION, dump, fetch, lines, sha, signal_hash

RECORD = 834976
MIRROR_REVISION = '74b85c0854dfd31339209db41010633ac92a7852'
MIRROR_MANIFEST_SHA256 = '7d5a70365849869cb65cbeff460a0b85872c9feb6d5e9fbf55cf6dffa2f5ccea'
SFREQ, POINTS = 512, 1536
NAMES = {'execution': 'ArmMovements', 'imagination': 'ImaginedArmMovements'}
CHANNELS = 'F3 F1 Fz F2 F4 FFC5h FFC3h FFC1h FFC2h FFC4h FFC6h FC5 FC3 FC1 FCz FC2 FC4 FC6 FTT7h FCC5h FCC3h FCC1h FCC2h FCC4h FCC6h FTT8h C5 C3 C1 Cz C2 C4 C6 TTP7h CCP5h CCP3h CCP1h CCP2h CCP4h CCP6h TTP8h CP5 CP3 CP1 CPz CP2 CP4 CP6 CPP5h CPP3h CPP1h CPP2h CPP4h CPP6h P3 P1 Pz P2 P4 PPO1h PPO2h'.split()
LABELS = ['elbow_flexion', 'elbow_extension', 'forearm_supination', 'forearm_pronation', 'hand_close', 'hand_open', 'rest']
FIELDS = ['split','row','example_id','group','participant_id','source_subject_id','session_id','session_task','measurement_datetime','run_id','loader_session_id','loader_run_id','recording_id','source_file','trial_index','annotation_index','source_gdf_event_index','source_event_sample_1based','source_event_duration_samples','event_sample','start_sample','end_sample','start_time_seconds','end_time_seconds','source_label','label','label_description','original_partition','signal_sha256']


def source_event_metadata(extra,start,code):
    if extra['event_sfreq']!=SFREQ:raise ValueError('Unexpected GDF event sampling frequency')
    _,positions,codes,_,durations=extra['events']
    matching=np.flatnonzero((positions==start)&(codes==code))
    if len(matching)!=1:raise ValueError('Ambiguous original GDF class event identity')
    index=int(matching[0])
    return dict(source_gdf_event_index=index,source_event_sample_1based=int(positions[index])+1,source_event_duration_samples=int(durations[index]))


def fetch_original(url,path,checksum,size,sha256):
    """Resume large immutable originals; publish only after both hashes verify."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    def valid(candidate):
        return candidate.is_file() and candidate.stat().st_size==size and 'md5:'+sha(candidate,'md5')==checksum and sha(candidate)==sha256
    if valid(path):return path
    part=path.with_name(path.name+'.part')
    for attempt in range(5):
        try:
            offset=part.stat().st_size if part.exists() else 0
            if offset>=size:
                if valid(part):part.replace(path);return path
                part.unlink();offset=0
            # Bounded requests avoid long-running transfers stalling near EOF.
            while offset<size:
                end=min(offset+8*1024*1024,size)-1
                request=urllib.request.Request(url,headers={'User-Agent':'EEGBench source-pinned download','Range':f'bytes={offset}-{end}'})
                with urllib.request.urlopen(request,timeout=60) as response:
                    partial=response.status==206
                    if partial and response.headers.get('Content-Range')!=f'bytes {offset}-{end}/{size}':raise ValueError('Unexpected partial response range')
                    with part.open('ab' if partial and offset else 'wb') as file:shutil.copyfileobj(response,file,length=1024*1024)
                updated=part.stat().st_size
                if updated<=offset:raise ValueError('Source transfer made no progress')
                offset=updated
            if not valid(part):raise ValueError('Original publisher/mirror checksum or size mismatch')
            part.replace(path);return path
        except Exception:
            if attempt==4:raise
            time.sleep(2**attempt)


def download_sources(cache,subjects=tuple(range(1,16)),modes=('execution','imagination'),runs=tuple(range(1,11)),workers=8):
    """Fetch immutable mirror objects, verifying original publisher MD5 as well."""
    cache=Path(cache)
    record_path=cache/'zenodo-record-834976.json'
    fetch('https://zenodo.org/api/records/834976',record_path)
    record=json.loads(record_path.read_text(encoding='utf-8'))
    if record['id']!=RECORD or record['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Unexpected source licence/revision')
    manifest=cache/'nemar-sourcedata-provenance.json'
    fetch(f'https://raw.githubusercontent.com/nemarDatasets/nm000173/{MIRROR_REVISION}/sourcedata/sourcedata_provenance.json',manifest)
    if sha(manifest)!=MIRROR_MANIFEST_SHA256:raise ValueError('Pinned mirror manifest changed')
    lookup={r['file']:r for r in json.loads(manifest.read_text())['files']}
    originals={r['key']:r for r in record['files']}
    def ensure(name):
        item=originals[name];mirror=lookup[name]
        if mirror['bytes']!=item['size']:raise ValueError('Mirror/publisher size mismatch')
        key=f"SHA256E-s{mirror['bytes']}--{mirror['sha256']}.gdf"
        path=fetch_original(f'https://nemar.s3.us-east-2.amazonaws.com/nm000173/objects/{key}',cache/name,item['checksum'],item['size'],mirror['sha256'])
        if sha(path)!=mirror['sha256']:raise ValueError('Mirror SHA256 mismatch')
        return name
    selected=[f'motor{mode}_subject{s}_run{r}.gdf' for mode in modes for s in subjects for r in runs]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i,name in enumerate(pool.map(ensure,selected),1):
            if i%10==0:print(f'{i}/{len(selected)} source files verified',flush=True)
    pdf=originals['data set description.pdf']
    fetch(pdf['links']['self'],cache/pdf['key'],pdf['checksum'],pdf['size'])
    fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/upper_limb.py',cache/'moabb-ofner-loader.py')


def header(name):
    return (f'# Ofner2017, CC BY 4.0; see accompanying provenance and sensor metadata.\n@problemName {name}\n'
            '@timestamps false\n@missing false\n@univariate false\n@dimensions 61\n'
            '@equalLength true\n@seriesLength 1536\n@classLabel true 0 1 2 3 4 5 6\n@data\n')


def channel_names(native, subject, mode):
    """Map the publisher's documented generic aliases, never reorder signal axes."""
    expected = [f'eeg-{i}' for i in range(61)]
    if native == CHANNELS:
        return CHANNELS.copy(), False
    if subject == 1 and mode == 'execution' and native == expected:
        return CHANNELS.copy(), True
    raise ValueError('Unexpected EEG channel order/names; explicit review required')


def epochs(raw, subject, mode):
    import mne
    if raw.info['sfreq'] != SFREQ or len(raw.ch_names) != 96:
        raise ValueError('Unexpected source sampling frequency/channel count')
    names, mapped = channel_names(raw.ch_names[:61], subject, mode)
    if raw.get_channel_types()[:64] != ['eeg']*61 + ['eog']*3:
        raise ValueError('Unexpected source sensor types')
    events = mne.events_from_annotations(raw, event_id={str(i): i for i in range(1536,1543)}, verbose='ERROR')[0]
    if Counter(events[:,2]) != Counter({i:6 for i in range(1536,1543)}):
        raise ValueError('Expected six events per class per original run')
    annotation_indices = [i for i, d in enumerate(raw.annotations.description) if d in {str(c) for c in range(1536,1543)}]
    data = raw.get_data(picks=list(range(61)))
    cases=[]
    for trial,(event, ai) in enumerate(zip(events, annotation_indices, strict=True)):
        start=int(event[0])-raw.first_samp;end=start+POINTS
        if int(raw.annotations.description[ai])!=int(event[2]) or int(round(raw.annotations.onset[ai]*SFREQ))!=int(event[0]):raise ValueError('Annotation/event sample alignment failed')
        if start<0 or end>data.shape[1]:raise ValueError('Incomplete selected epoch')
        case=np.asarray(data[:,start:end],dtype='<f4')
        if not np.isfinite(case).all():raise ValueError('Nonfinite samples in selected EEG epoch')
        cases.append((trial,ai,start,int(event[2]),case))
    invalid=np.flatnonzero(~np.isfinite(data).all(axis=0))
    return cases, dict(channel_names=names, generic_names_mapped=mapped,
                       nonfinite_eeg_values=int((~np.isfinite(data)).sum()),
                       nonfinite_sample_first=int(invalid[0]) if len(invalid) else None,
                       nonfinite_sample_last=int(invalid[-1]) if len(invalid) else None,
                       all_retained_epochs_finite=True)


def validate(folder, name, split):
    counts=Counter();people=set();hashes=set();n=0;last=(-1,-1,-1)
    with (folder/f'cases_{split.lower()}.tsv').open(newline='',encoding='utf-8') as file:
        rows=iter(csv.DictReader(file,delimiter='\t'))
        for n,line in enumerate(lines(folder/f'{name}_{split}.ts'),1):
            row=next(rows,None)
            if row is None or int(row['row'])!=n-1 or row['split']!=split:raise ValueError('Case metadata alignment failed')
            parts=line.strip().split(':');label=int(parts[-1])
            case=np.stack([np.fromstring(p,sep=',',dtype='<f4') for p in parts[:-1]])
            hashed=signal_hash(case);key=tuple(int(row[k]) for k in ['participant_id','run_id','trial_index'])
            if case.shape!=(61,POINTS) or not np.isfinite(case).all() or hashed!=row['signal_sha256']:raise ValueError('Numeric readback mismatch')
            if label!=int(row['label']) or label!=int(row['source_label'])-1536 or key<=last:raise ValueError('Label/source order mismatch')
            if int(row['end_sample'])-int(row['start_sample'])!=POINTS or row['event_sample']!=row['start_sample']:raise ValueError('Epoch bounds mismatch')
            if int(row['source_event_sample_1based'])!=int(row['event_sample'])+1:raise ValueError('Original GDF sample base mismatch')
            if hashed in hashes:raise ValueError('Duplicate case within partition')
            counts[label]+=1;people.add(row['participant_id']);hashes.add(hashed);last=key
        if next(rows,None) is not None:raise ValueError('Extra case metadata rows')
    return dict(cases=n,shape=[n,61,POINTS],class_counts=dict(sorted(counts.items())),subjects=sorted(people),exact_float32_roundtrip=True),hashes


def smoke_test(folder,name):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier
    loaded={}
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        for split in ['TRAIN','TEST']:
            selected={i:[] for i in range(7)}
            for line in lines(folder/f'{name}_{split}.ts'):
                label=int(line.rsplit(':',1)[1])
                if len(selected[label])<2:selected[label].append(line)
                if all(len(v)==2 for v in selected.values()):break
            path=Path(tmp)/f'{split}.ts';path.write_text(header(name)+''.join(line for group in selected.values() for line in group),encoding='ascii')
            loaded[split]=load_from_ts_file(path)
        classifier=SummaryClassifier(random_state=0,n_jobs=1);classifier.fit(*loaded['TRAIN']);pred=classifier.predict(loaded['TEST'][0])
        if len(pred)!=len(loaded['TEST'][1]):raise ValueError('aeon compatibility failed')
    return dict(passed=True,aeon_version=aeon.__version__,classifier='SummaryClassifier',train_cases=14,test_cases=14,scope='Representative classifier check; all cases independently read back numerically')


def convert(cache,output,mode,subjects=tuple(range(1,16)),train=tuple(range(1,12)),runs=tuple(range(1,11)),download=True,smoke=True):
    import mne
    cache,output=Path(cache).resolve(),Path(output).resolve();name=NAMES[mode]
    subjects=tuple(sorted(subjects));train=set(train);runs=tuple(sorted(runs))
    if len(subjects)!=len(set(subjects)) or not set(subjects)<=set(range(1,16)) or not train or not train<set(subjects) or not runs or not set(runs)<=set(range(1,11)):raise ValueError('Invalid source selection/split')
    folder=output/name
    if folder.exists():raise FileExistsError(f'Refusing to overwrite {folder}')
    record_path=cache/f'zenodo-record-{RECORD}.json'
    if download:fetch(f'https://zenodo.org/api/records/{RECORD}',record_path)
    record=json.loads(record_path.read_text(encoding='utf-8'))
    if record['id']!=RECORD or record['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Unexpected data licence/release')
    sources={f['key']:f for f in record['files']}
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{name}-',dir=output) as tmp:
        stage=Path(tmp);evidence=stage/'source_metadata';evidence.mkdir();counts=Counter();recordings=[];inventory=[];handles={};tables={};writers={}
        fmt=','.join(['%.9g']*POINTS)
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{name}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header(name))
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',encoding='utf-8',newline='')
                writers[split]=csv.DictWriter(tables[split],FIELDS,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for subject in subjects:
                for run in runs:
                    filename=f'motor{mode}_subject{subject}_run{run}.gdf';item=sources[filename];path=cache/filename
                    if download:fetch(item['links']['self'],path,item['checksum'],item['size'])
                    if not path.is_file() or path.stat().st_size!=item['size'] or 'md5:'+sha(path,'md5')!=item['checksum']:raise ValueError(f'Missing or modified source: {filename}')
                    raw=mne.io.read_raw_gdf(path,eog=['eog-l','eog-m','eog-r'],misc=list(range(64,96)),preload=True,verbose='ERROR')
                    cases,audit=epochs(raw,subject,mode);split='TRAIN' if subject in train else 'TEST';sid=f'{subject:02d}';session='1' if mode=='execution' else '2'
                    extra=raw._raw_extras[0]
                    for trial,ai,start,code,case in cases:
                        row=dict(split=split,row=counts[split],example_id=f'Ofner2017/{mode}/{sid}/{run:02d}/{trial:02d}',group=sid,participant_id=sid,source_subject_id=(raw.info.get('subject_info') or {}).get('his_id',''),session_id=session,session_task=mode,measurement_datetime=str(raw.info.get('meas_date') or ''),run_id=f'{run:02d}',loader_session_id='0execution' if mode=='execution' else '1imagination',loader_run_id=str(run-1),recording_id=filename[:-4],source_file=filename,trial_index=trial,annotation_index=ai,event_sample=start,start_sample=start,end_sample=start+POINTS,start_time_seconds=start/SFREQ,end_time_seconds=(start+POINTS)/SFREQ,source_label=code,label=code-1536,label_description=LABELS[code-1536],original_partition='unpartitioned',signal_sha256=signal_hash(case))
                        row.update(source_event_metadata(extra,start,code))
                        writers[split].writerow(row);handles[split].write(':'.join(fmt%tuple(ch.tolist()) for ch in case)+f':{code-1536}\n');counts[split]+=1
                    if not np.all(np.asarray(extra['units'][:61])==1) or not np.all(np.asarray(extra['cal'][:61])==1) or not np.all(np.asarray(extra['offsets'][:61])==0):raise ValueError('Unexpected EEG physical unit/calibration; review scale before combining recordings')
                    compact=dict(participant_id=sid,session_id=session,task=mode,run_id=f'{run:02d}',source_file=filename,samples=raw.n_times,frequency=raw.info['sfreq'],native_names=raw.ch_names,native_types=raw.get_channel_types(),native_subject_info=raw.info.get('subject_info'),measurement_datetime=raw.info.get('meas_date'),native_sensor_locations=[ch['loc'] for ch in raw.info['chs']],native_original_units=raw._orig_units,gdf_header={k:extra.get(k) for k in ['units','physical_min','physical_max','digital_min','digital_max','cal','offsets','ref','gnd','highpass','lowpass','notch','event_sfreq','events']},annotations=dict(onset=raw.annotations.onset,duration=raw.annotations.duration,description=raw.annotations.description),audit=audit)
                    compact['gdf_header']['events_position_convention']='MNE-parsed positions are zero-based; add one for original on-disk GDF event position'
                    dump(evidence/f'{filename}.json',safe(compact));recordings.append(safe({k:v for k,v in compact.items() if k not in ['gdf_header','annotations']}))
                    inventory.append(dict(filename=filename,url=item['links']['self'],checksum=item['checksum'],sha256=sha(path),bytes=item['size']))
                    raw.close();del raw,cases
                print(f'{name}: participant {sid} exported; cases {dict(counts)}',flush=True)
        finally:
            for handle in [*handles.values(),*tables.values()]:handle.close()
        reports={};hashes={}
        for split in ['TRAIN','TEST']:
            reports[split],hashes[split]=validate(stage,name,split);print(f'{name}: {split} full readback passed',flush=True)
        if hashes['TRAIN']&hashes['TEST'] or set(reports['TRAIN']['subjects'])&set(reports['TEST']['subjects']):raise ValueError('Participants or signals cross partitions')
        expected={s:len(train if s=='TRAIN' else set(subjects)-train)*len(runs)*42 for s in reports}
        if any(reports[s]['cases']!=expected[s] for s in reports):raise ValueError('Unexpected case count')
        validation=dict(quality_status='passed_with_documented_source_metadata_limits',partitions=reports,subject_overlap=[],duplicate_cases_across_splits=0,all_exported_epochs_finite=True,metadata_rows_verified=True,channel_order_verified_every_recording=True,aeon=smoke_test(stage,name) if smoke else {'passed':None})
        split_definition=dict(unit='participant',train=[f'{s:02d}' for s in sorted(train)],test=[f'{s:02d}' for s in subjects if s not in train],original='No official train/test split; EEGBench locally defines shared cohort split for both tasks',order='numeric participant, numeric run, chronological class cue',validation='none')
        metadata=dict(dataset=name,original_name='Ofner2017',task=mode,source_url='https://zenodo.org/records/834976',source_doi='10.5281/zenodo.834976',paper_doi='10.1371/journal.pone.0182578',licence='CC-BY-4.0',subjects=len(subjects),sessions=len(subjects),sessions_per_subject=1,original_study_sessions_per_subject=2,recordings=len(recordings),frequency=SFREQ,original_frequency=SFREQ,channel_names=CHANNELS,channel_types=['EEG']*61,channels=61,timepoints=POINTS,shapes={s.lower():reports[s]['shape'] for s in reports},classes=7,label_map={str(i):v for i,v in enumerate(LABELS)},original_label_map={str(1536+i):i for i in range(7)},class_counts={s.lower():reports[s]['class_counts'] for s in reports},window_seconds=3,epoch_interval='[class cue sample, cue sample+1536); zero-based, end exclusive',overlap='No overlap between selected trials; validated source event positions retained',preprocessing=dict(filtering='none added',resampling='none',referencing='unchanged',baseline='none',dtype='float32; 9 significant digits in .ts for exact roundtrip',channel_selection='original axes 0:61 EEG, no reordering; auxiliary signals excluded',units='GDF reader numeric scale unchanged; original physical-dimension metadata unspecified; MOABB interprets values as microvolts'),publication_evidence=dict(reference='right mastoid',ground='AFz',acquisition_filter='8th-order Chebyshev 0.01–200 Hz; 50 Hz notch',channel_mapping='Original data set description.pdf table 2; EEG 1–61, EOG 62–64, glove 65–83, exoskeleton 84–96',trial='Class cue at trial second 2; movement/imagination cue lasts 3 seconds'),channel_order='Native EEG names checked in every recording; subject 1 execution generic eeg-0..60 mapped using original PDF table, without reordering',sensor_positions='Native GDF/MNE loc/ref/gnd retained per recording; absent/zero coordinates are not claimed as measured positions',split=split_definition,study_relationship='Execution and imagination use distinct recordings from the same 15 participants; retain shared subject split',missing_metadata=['Unambiguous GDF physical signal units','Verified individual electrode coordinates','Reliable individual demographics; native GDF subject headers retained without interpreting invalid birthdays'],metadata_evidence=dict(distributed_files=['subject/run from filename','native subject headers and recording dates','event codes/times','native channel names/order','native sensor locations and filters','numeric samples','licence record'],publication=['generic channel-name mapping','sensor roles','reference/ground','acquisition filter','two-session protocol'],locally_defined=['train/test split','epoch bounds/IDs','encoded labels']))
        metadata.update(source_title=record['metadata']['title'],source_study_id='Ofner2017/Zenodo-834976',source_aliases=['Ofner2017','BNCI 001-2017','nm000173'],related_problem=NAMES['imagination' if mode=='execution' else 'execution'])
        dump(stage/f'{name}_metadata.json',metadata);dump(stage/f'{name}_validation.json',validation);dump(stage/'recordings.json',recordings)
        dump(stage/'metadata-completeness.json',dict(evidence=metadata['metadata_evidence'],missing=metadata['missing_metadata']))
        (stage/'channels.tsv').write_text('array_index\tname\ttype\n'+''.join(f'{i}\t{ch}\tEEG\n' for i,ch in enumerate(CHANNELS)),encoding='utf-8')
        for filename in ['zenodo-record-834976.json','data set description.pdf','moabb-ofner-loader.py']:
            item=sources.get(filename)
            if download and item:fetch(item['links']['self'],cache/filename,item['checksum'],item['size'])
            if not (cache/filename).is_file():raise ValueError(f'Missing source evidence: {filename}')
            shutil.copy2(cache/filename,evidence/filename)
        if (cache/'nemar-sourcedata-provenance.json').exists():shutil.copy2(cache/'nemar-sourcedata-provenance.json',evidence/'nemar-sourcedata-provenance.json')
        (stage/'ATTRIBUTION.txt').write_text('Ofner, P.; Schwarz, A.; Pereira, J.; Müller-Putz, G. (2017). Upper limb motor execution and imagery EEG. DOI 10.5281/zenodo.834976; paper 10.1371/journal.pone.0182578. CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nEEGBench modification: EEG selection, cue epochs, float32, participant split, .ts conversion; no added filtering, resampling, scaling or re-referencing.\n',encoding='utf-8')
        (stage/f'README_{name}.md').write_text(f'# {name}\n\nOfner2017 motor {mode}, seven right arm/hand/rest classes. Use TRAIN/TEST .ts with corresponding cases_train/test.tsv rows. Read identifiers as strings. Sample indices are zero-based; end is exclusive.\n\nMetadata and manifest distinguish direct file evidence from publication facts. Auxiliary channels are excluded. Nonfinite padding outside retained epochs is recorded, never imputed. Units are ambiguous in GDF; values preserve the reader numeric scale. Native locations and headers are retained without inventing individual positions.\n',encoding='utf-8')
        code=stage/'conversion_code';code.mkdir()
        for source in [Path(__file__),Path(__file__).with_name('prepare_moabb.py'),Path(__file__).with_name('prepare_erpcore.py')]:shutil.copy2(source,code/source.name)
        dump(stage/f'{name}_manifest.json',dict(dataset=name,source_revision='Zenodo 834976 v1',source_urls=[metadata['source_url'],'https://doi.org/10.1371/journal.pone.0182578'],licence='CC-BY-4.0',moabb_revision=MOABB_REVISION,mirror=dict(repository='nemarDatasets/nm000173',revision=MIRROR_REVISION,manifest_sha256=MIRROR_MANIFEST_SHA256,object_url_template='https://nemar.s3.us-east-2.amazonaws.com/nm000173/objects/SHA256E-s{bytes}--{sha256}.gdf',verification='Original Zenodo MD5 and size; mirror SHA256'),mne_version=mne.__version__,source_files=inventory,split=split_definition,conversion=metadata['preprocessing'],validation=validation,artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(folder)
    return metadata,validation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['execution','imagination','both'],default='both')
    parser.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources/Ofner2017'))
    parser.add_argument('--output',type=Path,default=Path('D:/Data/EEG'))
    parser.add_argument('--subjects',default=','.join(map(str,range(1,16))))
    parser.add_argument('--train-subjects',default=','.join(map(str,range(1,12))))
    parser.add_argument('--runs',default=','.join(map(str,range(1,11))))
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--download-only',action='store_true')
    args=parser.parse_args()
    modes=['execution','imagination'] if args.mode=='both' else [args.mode]
    if not args.download_only:
        for mode in modes:
            folder=args.output/NAMES[mode]
            if folder.exists():raise FileExistsError(f'Refusing to overwrite {folder}; choose another --output directory')
    subjects=tuple(map(int,args.subjects.split(',')));runs=tuple(map(int,args.runs.split(',')))
    if not args.offline:download_sources(args.cache,subjects,modes,runs)
    if args.download_only:return
    for mode in modes:
        convert(args.cache,args.output,mode,subjects,tuple(map(int,args.train_subjects.split(','))),runs,False)
    if len(modes)==2:
        cross_task_audit(args.output)


def cross_task_audit(output):
    """Record any exact shared cases between the distinct task recordings."""
    output=Path(output);hashes={}
    for name in NAMES.values():
        hashes[name]=set()
        for split in ['train','test']:
            with (output/name/f'cases_{split}.tsv').open(newline='',encoding='utf-8') as file:
                hashes[name].update(row['signal_sha256'] for row in csv.DictReader(file,delimiter='\t'))
    shared=hashes['ArmMovements']&hashes['ImaginedArmMovements']
    report=dict(problems=list(NAMES.values()),same_source_study=True,same_participant_cohort=True,distinct_recording_sessions=True,exact_shared_cases=len(shared),shared_signal_hashes=sorted(shared))
    for name in NAMES.values():dump(output/name/'cross-task-audit.json',report)
    for name in NAMES.values():
        path=output/name/f'{name}_manifest.json'
        if path.exists():
            manifest=json.loads(path.read_text(encoding='utf-8'));audit=output/name/'cross-task-audit.json'
            manifest['artifacts']['cross-task-audit.json']=dict(sha256=sha(audit),bytes=audit.stat().st_size)
            dump(path,manifest)
    if shared:raise ValueError('Exact cases shared across tasks; review cross-task-audit.json')


if __name__=='__main__':main()
