"""ERP CORE N400 / WordRelatedness from a checksummed original OSF manifest."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import datetime
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
import pandas as pd
from scipy.io import loadmat

from tools.prepare_moabb import MOABB_REVISION, dump, fetch, lines, sha, signal_hash

NAME, SFREQ, POINTS, PRE = "WordRelatedness", 1024, 1024, 205
MANIFEST_URL = "https://zenodo.org/records/14866307/files/erpcore_manifest.csv?download=1"
MANIFEST_SHA256 = "16ffd88374e29f121e7fd77cade429d25704526baac11ede027a484c50af5cff"
CHANNELS = ["FP1","F3","F7","FC3","C3","C5","P3","P7","P9","PO7","PO3","O1","Oz","Pz","CPz","FP2","Fz","F4","F8","FC4","FCz","Cz","C4","C6","P4","P8","P10","PO8","PO4","O2"]
LABELS = {211:1,212:1,221:2,222:2}
LABEL_NAMES = {1:"Related",2:"Unrelated"}
FIELDS = ["split","row","example_id","group","participant_id","source_participant_id",
          "session_id","run_id","loader_session_id","loader_run_id","recording_id","source_file",
          "source_events_row_index","original_eeglab_event_index","original_urevent_id","target_trial_index",
          "source_sample_1based","event_sample_0based","start_sample","end_sample","source_onset_seconds",
          "event_time_seconds","start_time_seconds","end_time_seconds","source_label","label","label_description",
          "word_list_id","prime_source_label","prime_source_sample_1based","response_codes","response_samples_1based",
          "first_response_correct","first_response_time_seconds","source_trial_type","stim_file","original_partition","signal_sha256"]


def safe(value):
    if isinstance(value,dict):return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [safe(v) for v in value]
    if isinstance(value,np.generic):return safe(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return str(value)


def sources(cache,subjects,download=True):
    cache=Path(cache);manifest=cache/"erpcore_manifest.csv"
    if download:fetch(MANIFEST_URL,manifest)
    if sha(manifest)!=MANIFEST_SHA256:raise ValueError("Source download manifest revision changed")
    frame=pd.read_csv(manifest,dtype=str,keep_default_na=False)
    selected=frame[(frame.component=="N400") & ((frame.participant_id=="") | frame.participant_id.isin([f"sub-{s:03d}" for s in subjects]))]
    def ensure(row):
        relative=Path(row['local_path'].removeprefix('erpcore/N400/'))
        path=cache/relative
        if relative.is_absolute() or '..' in relative.parts or not path.resolve().is_relative_to(cache.resolve()):raise ValueError("Unsafe source path")
        if download:fetch(row['url'],path,row['hash'],int(row['size']))
        if not path.is_file() or path.stat().st_size!=int(row['size']) or 'md5:'+sha(path,'md5')!=row['hash']:raise ValueError(f"Missing or modified source: {relative}")
        return dict(path=relative.as_posix(),url=row['url'],checksum=row['hash'],sha256=sha(path),bytes=path.stat().st_size)
    with ThreadPoolExecutor(max_workers=4) as pool:inventory=list(pool.map(ensure,selected.to_dict('records')))
    if 'CC BY-SA 4.0' not in (cache/'LICENSE').read_text():raise ValueError("Original data licence changed")
    loader=cache/'moabb-erpcore-loader.py'
    if download:fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/erpcore2021.py',loader)
    if not loader.exists():raise ValueError("Missing pinned loader evidence")
    return inventory


def read_recording(cache,subject):
    stem=f"sub-{subject:03d}_task-N400"
    directory=Path(cache)/f"sub-{subject:03d}"/'eeg'
    file=directory/f'{stem}_eeg.set'
    eeg=loadmat(file,simplify_cells=True)['EEG']
    names=[ch['labels'] for ch in eeg['chanlocs']]
    channels=pd.read_csv(directory/f'{stem}_channels.tsv',sep='\t',dtype=str,keep_default_na=False)
    if names!=channels.name.tolist():raise ValueError("EEGLAB and sidecar channel order disagree")
    picks=[i for i,row in channels.iterrows() if row['type'].upper()=='EEG']
    if [names[i] for i in picks]!=CHANNELS or len(channels)!=33 or sum(channels.type.str.upper()=='EOG')!=3:raise ValueError("Inconsistent actual EEG/EOG channel names/types/order")
    if channels.units.tolist()!=['microV']*33:raise ValueError("Unexpected original signal units")
    if int(eeg['nbchan'])!=33 or int(eeg['trials'])!=1 or float(eeg['srate'])!=SFREQ:raise ValueError("Unexpected EEGLAB recording schema")
    binary=directory/f'{stem}_eeg.fdt'
    if eeg['data']!=binary.name or binary.stat().st_size!=int(eeg['pnts'])*33*4:raise ValueError("Incorrect binary reference or size")
    data=np.memmap(binary,dtype='<f4',mode='r',shape=(int(eeg['pnts']),33))
    events=pd.read_csv(directory/f'{stem}_events.tsv',sep='\t',dtype=str,keep_default_na=False)
    native=eeg['event'] if isinstance(eeg['event'],list) else [eeg['event']]
    lookup={(float(event['latency']),str(event['type'])):(i+1,event.get('urevent','')) for i,event in enumerate(native)}
    positions=pd.read_csv(directory/f'{stem}_electrodes.tsv',sep='\t',dtype=str,keep_default_na=False)
    if positions.name.tolist()!=names:raise ValueError("Position sidecar order disagrees with signal axes")
    coord=json.loads((directory/f'{stem}_coordsystem.json').read_text())
    if coord.get('EEGCoordinateUnits')!='mm':raise ValueError("Unexpected position units")
    eeg_json=json.loads((directory/f'{stem}_eeg.json').read_text())
    return eeg,data,events,lookup,channels,positions,coord,eeg_json,picks


def target_rows(events,lookup):
    """Verify one-based source samples against native EEGLAB event identities."""
    targets=[]
    rows=events.to_dict('records')
    for source_index,row in enumerate(rows):
        try:code=int(row['value'])
        except ValueError:continue
        if code not in LABELS or row['trial_type'].lower()!='stimulus':continue
        sample=float(row['sample'])
        if sample!=round(sample) or (sample,str(code)) not in lookup:raise ValueError("Original EEGLAB target event does not match BIDS sample/code")
        # The supplied sample column contains MATLAB/EEGLAB one-based latencies.
        zero=int(sample)-1
        if abs(float(row['onset'])*SFREQ-zero)>0.052:raise ValueError("Source event sample base/time mismatch")
        original_index,urevent=lookup[(sample,str(code))]
        prime=None
        for previous in reversed(rows[:source_index]):
            if previous['value'] in ['111','112','121','122']:
                prime=previous;break
        if prime is not None and int(prime['value'])!=code-100:raise ValueError("Prime and target conditions disagree")
        responses=[]
        for following in rows[source_index+1:]:
            if following['value'] in ['111','112','121','122','211','212','221','222']:break
            if following['value'] in ['201','202']:responses.append(following)
        targets.append(dict(source_index=source_index,row=row,code=code,sample=int(sample),zero=zero,
                            original_index=original_index,urevent=str(int(urevent)) if isinstance(urevent,(float,int)) else str(urevent),prime=prime,responses=responses))
    if not targets or set(LABELS[item['code']] for item in targets)!={1,2}:raise ValueError("Missing a relatedness class")
    return targets


def header():
    return (f"# ERP CORE N400, CC BY-SA 4.0. See provenance, sensor and case sidecars.\n"
            f"@problemName {NAME}\n@timestamps false\n@missing false\n@univariate false\n"
            "@dimensions 30\n@equalLength true\n@seriesLength 1024\n@classLabel true 1 2\n@data\n")


def validate_split(folder,split):
    count=0;counts=Counter();people=set();hashes=set();last=(-1,-1)
    with (folder/f'cases_{split.lower()}.tsv').open(newline='',encoding='utf-8') as file:
        rows=iter(csv.DictReader(file,delimiter='\t'))
        for count,line in enumerate(lines(folder/f'{NAME}_{split}.ts'),1):
            row=next(rows,None)
            if row is None or row['split']!=split or int(row['row'])!=count-1:raise ValueError("Case metadata row alignment failed")
            parts=line.strip().split(':')
            if len(parts)!=31:raise ValueError("Incorrect exported EEG channel count")
            array=np.stack([np.fromstring(ch,dtype='<f4',sep=',') for ch in parts[:-1]])
            label=int(parts[-1]);hashed=signal_hash(array);code=int(row['source_label'])
            if array.shape!=(30,POINTS) or hashed!=row['signal_sha256'] or LABELS[code]!=label or int(row['label'])!=label:raise ValueError("Signal/label differs from source epoch")
            event=int(row['event_sample_0based']);key=(int(row['participant_id']),event)
            if event!=int(row['source_sample_1based'])-1 or int(row['start_sample'])!=event-PRE or int(row['end_sample'])!=event-PRE+POINTS or key<=last:raise ValueError("Sample reference, crop or source order changed")
            last=key;counts[label]+=1;people.add(row['participant_id']);hashes.add(hashed)
        if next(rows,None) is not None:raise ValueError("Extra metadata rows")
    return dict(cases=count,shape=[count,30,POINTS],class_counts=dict(sorted(counts.items())),subjects=sorted(people),exact_float32_roundtrip=True,metadata_rows_verified=True),hashes


def smoke_test(folder):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier
    loaded={}
    with tempfile.TemporaryDirectory(dir=folder,prefix='aeon-check-') as tmp:
        for split in ['TRAIN','TEST']:
            examples={1:[],2:[]}
            for line in lines(folder/f'{NAME}_{split}.ts'):
                label=int(line.rsplit(':',1)[1])
                if len(examples[label])<4:examples[label].append(line)
                if all(len(v)==4 for v in examples.values()):break
            path=Path(tmp)/f'{split}.ts';path.write_text(header()+''.join(line for rows in examples.values() for line in rows),encoding='ascii');loaded[split]=load_from_ts_file(path)
        classifier=SummaryClassifier(random_state=0,n_jobs=1);classifier.fit(*loaded['TRAIN']);predicted=classifier.predict(loaded['TEST'][0])
        if len(predicted)!=len(loaded['TEST'][1]):raise ValueError("aeon classifier compatibility failed")
    return dict(passed=True,aeon_version=aeon.__version__,classifier='SummaryClassifier',train_cases=len(loaded['TRAIN'][1]),test_cases=len(predicted),note='Representative compatibility check; full numeric readback checked separately. No benchmark scores.')


def convert(cache,output,subjects=tuple(range(1,41)),train=tuple(range(1,31)),download=True,smoke=True):
    cache,output=Path(cache).resolve(),Path(output).resolve();subjects=tuple(sorted(subjects));train=set(train)
    if len(subjects)!=len(set(subjects)) or not set(subjects)<=set(range(1,41)) or not train or not train<set(subjects):raise ValueError("Invalid participant split")
    folder=output/NAME
    if folder.exists():raise FileExistsError(f"Refusing to overwrite {folder}")
    if smoke:
        from aeon.datasets import load_from_ts_file  # noqa: F401
        from aeon.classification.feature_based import SummaryClassifier  # noqa: F401
    inventory=sources(cache,subjects,download);demographics=pd.read_csv(cache/'participants.tsv',sep='\t',dtype=str,keep_default_na=False).set_index('participant_id')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{NAME}-',dir=output) as tmp:
        stage=Path(tmp);evidence=stage/'source_metadata';evidence.mkdir();handles={};tables={};writers={};counts=Counter();all_rows=[];records=[];discarded=[];sensor_rows=None;position_sets=[]
        fmt=','.join(['%.9g']*POINTS)
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{NAME}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header())
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',encoding='utf-8',newline='')
                writers[split]=csv.DictWriter(tables[split],FIELDS,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for subject in subjects:
                eeg,data,events,lookup,channels,positions,coord,eeg_json,picks=read_recording(cache,subject)
                targets=target_rows(events,lookup);subject_id=f'{subject:03d}';stem=f'sub-{subject_id}_task-N400';split='TRAIN' if subject in train else 'TEST'
                raw_date=safe(eeg.get('etc',{}).get('T0',[]));measurement=''
                if isinstance(raw_date,list) and len(raw_date)==6:
                    try:measurement=datetime.datetime(*[int(v) for v in raw_date]).isoformat()
                    except ValueError:pass
                n=0
                for trial,item in enumerate(targets):
                    zero=item['zero'];start=zero-PRE;end=start+POINTS;code=item['code'];label=LABELS[code]
                    if start<0 or end>len(data):discarded.append(dict(participant_id=subject_id,source_event_row=item['source_index'],reason='incomplete one-second epoch'));continue
                    case=np.asarray(data[start:end][:,picks].T,dtype='<f4')
                    if not np.isfinite(case).all():raise ValueError("Nonfinite source EEG")
                    prime=item['prime'];responses=item['responses'];source=item['row']
                    row=dict(split=split,row=counts[split],example_id=f'ERP-CORE/N400/sub-{subject_id}/events-row-{item["source_index"]}',group=subject_id,participant_id=subject_id,source_participant_id=f'sub-{subject_id}',
                             session_id=measurement,run_id='',loader_session_id='0',loader_run_id='0',recording_id=stem,source_file=stem+'_eeg.fdt',source_events_row_index=item['source_index'],original_eeglab_event_index=item['original_index'],original_urevent_id=item['urevent'],target_trial_index=trial,
                             source_sample_1based=item['sample'],event_sample_0based=zero,start_sample=start,end_sample=end,source_onset_seconds=source['onset'],event_time_seconds=zero/SFREQ,start_time_seconds=start/SFREQ,end_time_seconds=end/SFREQ,
                             source_label=code,label=label,label_description=LABEL_NAMES[label],word_list_id=code%10,prime_source_label=prime['value'] if prime else '',prime_source_sample_1based=prime['sample'] if prime else '',
                             response_codes=json.dumps([int(r['value']) for r in responses]),response_samples_1based=json.dumps([float(r['sample']) for r in responses]),first_response_correct=str(responses[0]['value']=='201') if responses else '',
                             first_response_time_seconds=(float(responses[0]['sample'])-item['sample'])/SFREQ if responses else '',source_trial_type=source['trial_type'],stim_file=source.get('stim_file',''),original_partition='unpartitioned',signal_sha256=signal_hash(case))
                    writers[split].writerow(row);all_rows.append(row);handles[split].write(':'.join(fmt%tuple(channel.tolist()) for channel in case)+f':{label}\n');counts[split]+=1;n+=1
                compact=safe({key:eeg.get(key) for key in ['nbchan','pnts','trials','srate','xmin','xmax','ref','setname','filename','data','subject','session','run','etc','chanlocs','event']})
                dump(evidence/f'{stem}_eeglab-header.json',compact)
                subdirectory=evidence/f'sub-{subject_id}';subdirectory.mkdir()
                for path in (cache/f'sub-{subject_id}'/'eeg').iterdir():
                    if path.suffix not in ['.set','.fdt']:shutil.copy2(path,subdirectory/path.name)
                position_sets.append(positions.to_dict('records'))
                if sensor_rows is None:
                    sensor_rows=[dict(original_array_index=i,name=row['name'],type=row['type'],units=row['units'],included_in_arrays=i in picks,exported_array_index=picks.index(i) if i in picks else None,position=positions.iloc[i].to_dict(),coordinate_system=coord) for i,row in channels.iterrows()]
                records.append(dict(participant_id=subject_id,recording_id=stem,samples=int(eeg['pnts']),frequency=SFREQ,channels=channels.to_dict('records'),positions=positions.to_dict('records'),coordinate_system=coord,measurement_datetime_unzoned=measurement,original_T0=raw_date,reference=eeg.get('ref'),bids=eeg_json,demographics=demographics.loc[f'sub-{subject_id}'].to_dict(),target_events=len(targets),exported_cases=n))
                print(f'{subject_id}: {n} {split} cases',flush=True)
        finally:
            for file in [*handles.values(),*tables.values()]:file.close()
        reports={};hashes={}
        for split in ['TRAIN','TEST']:
            reports[split],hashes[split]=validate_split(stage,split);print(f'Full {split} readback passed',flush=True)
        if hashes['TRAIN']&hashes['TEST'] or set(reports['TRAIN']['subjects'])&set(reports['TEST']['subjects']):raise ValueError("Signals or participants cross TRAIN/TEST")
        if set(reports['TRAIN']['subjects'])!={f'{s:03d}' for s in train} or set(reports['TEST']['subjects'])!={f'{s:03d}' for s in set(subjects)-train}:raise ValueError("Participant membership mismatch")
        all_rows.sort(key=lambda row:(row['split']!='TRAIN',row['row']))
        if len({row['example_id'] for row in all_rows})!=len(all_rows):raise ValueError("Repeated source case IDs")
        with (stage/f'{NAME}_rows.tsv').open('w',encoding='utf-8',newline='') as file:
            writer=csv.DictWriter(file,FIELDS,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(all_rows)
        aeon_check=smoke_test(stage) if smoke else dict(passed=False,status='not run')
        validation=dict(quality_status='passed' if smoke else 'signal validation passed; aeon not run',partitions=reports,aeon=aeon_check,metadata_rows_verified=len(all_rows),subject_overlap=[],cross_split_duplicate_signal_hashes=0,source_channel_order_verified=True,source_binary_dtype='little-endian float32',one_based_events_verified_against_eeglab=True,dropped_events=discarded)
        split_definition=dict(unit='participant',train=[f'{s:03d}' for s in sorted(train)],test=[f'{s:03d}' for s in sorted(set(subjects)-train)],validation='none',origin='EEGBench-defined fixed subject split; no universal MOABB TRAIN/TEST partition')
        metadata=dict(name=NAME,source_dataset_name='ERP CORE N400',source_aliases=['ErpCore2021_N400','ERP-CORE','OpenNeuro ds003068 v1.0.0','NEMAR nm000132'],target='Related versus unrelated visual word pairs, target-word epochs',domain='Psy',subjects=len(subjects),recordings=len(records),sessions_per_subject=1,
                      session_definition='One N400 recording per person. session_id reconstructed from EEGLAB etc.T0, timezone unspecified; original named session/run IDs absent. Loader session/run 0/0 are separate.',
                      source_url='https://osf.io/29xpq/',source_doi='10.18115/D5JW4R',original_bids_doi='10.18112/openneuro.ds003068.v1.0.0',paper_doi='10.1016/j.neuroimage.2020.117465',reference='Kappenman, Farrens, Zhang, Stewart and Luck (2021). ERP CORE: An open resource for human event-related potential research. NeuroImage 225, 117465.',
                      license='CC-BY-SA-4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',license_evidence='Original LICENSE and https://erpinfo.org/erp-core',licence_conflict='Original BIDS dataset_description says CC0; other mirror/MOABB metadata says CC BY. Original explicit LICENSE and authors website specify CC BY-SA 4.0; share-alike retained for this derivative.',
                      frequency=SFREQ,sampling_frequency_hz=SFREQ,original_sampling_frequency_hz=SFREQ,channel_count=30,channel_names=CHANNELS,channels=CHANNELS,sensors=sensor_rows,source_channel_count=33,excluded_channel_types={'EOG':3},source_sensor_metadata='All 33 source channels retained as metadata; only 30 EEG axes exported, in source order.',
                      positions_units='mm',positions_coordinate_system=records[0]['coordinate_system'],positions_consistent=all(p==position_sets[0] for p in position_sets),positions_evidence='Distributed electrode/coordsystem TSV/JSON files; no transform to MNE head coordinates and no claim of individual digitization.',
                      channel_reference='BIDS EEGReference CMS; EEGLAB ref common. No rereferencing added.',units='microV, original FDT/sidecar scale',dtype='float32',axis_order=['case','channel','time'],timepoints=POINTS,classes=2,label_map={'1':'Related','2':'Unrelated'},original_label_map={'211':'Related/list1','212':'Related/list2','221':'Unrelated/list1','222':'Unrelated/list2'},
                      shapes={s.lower():reports[s]['shape'] for s in reports},class_counts={s.lower():reports[s]['class_counts'] for s in reports},window_seconds=1,
                      epoch_definition='Zero-based event = original EEGLAB/BIDS sample - 1; start=event-205; end=start+1024 exclusive. Approximate nominal [-0.2,0.8) seconds at 1024Hz.',
                      preprocessing=dict(filtering='none added',resampling='none',baseline='none',referencing='unchanged',scaling='none',dtype='source float32 retained; .ts 9 significant digits',monitor_latency='No additional monitor latency shift; original acquisition marker alignment retained. MOABB mentions a 26ms LCD delay.'),
                      split_policy=split_definition,case_metadata=dict(file=f'{NAME}_rows.tsv',ordering='TRAIN then TEST; zero-based row within split; IDs strings preserve 001-009'),
                      behavior='All target words retained regardless of response accuracy. Response codes after target and before next prime/target are retained, including multiple responses; no response means missing.',
                      missing_metadata=['actual word strings (stim_file n/a)','original named session/run IDs','timezone of EEGLAB T0','verified individual digitization provenance'],
                      metadata_evidence=dict(distributed_files=['participant demographics','channel names/order/types/units','electrode coordinates and declared frame','original event samples/codes/urevent IDs','word list','prime/response events','EEGLAB date/reference','source EEG JSON and hardware information'],local_definitions=['fixed subject split','binary label mapping','half-open sample bounds','one-based to zero-based index conversion','response association before next prime/target']))
        dump(stage/f'{NAME}_metadata.json',metadata);dump(stage/f'{NAME}_validation.json',validation);dump(stage/'recordings.json',records);dump(stage/'dropped-events.json',discarded);dump(stage/'metadata-completeness.json',dict(evidence=metadata['metadata_evidence'],missing=metadata['missing_metadata']))
        (stage/'channels.txt').write_text(', '.join(CHANNELS)+'\n',encoding='utf-8')
        (stage/'channels.tsv').write_text('array_index\tname\ttype\tunits\n'+''.join(f'{i}\t{n}\tEEG\tmicroV\n' for i,n in enumerate(CHANNELS)),encoding='utf-8')
        for path in cache.iterdir():
            if path.is_file() and path.suffix not in ['.gdf','.fdt','.set']:shutil.copy2(path,evidence/path.name)
        shutil.copy2(cache/'LICENSE',stage/'LICENSE')
        (stage/'ATTRIBUTION.txt').write_text('Kappenman, Emily; Farrens, Jaclyn; Zhang, Wendy; Stewart, Andrew X.; Luck, Steven J. (2020/2021). ERP CORE: An Open Resource for Human Event-Related Potential Research. Data DOI 10.18115/D5JW4R; paper DOI 10.1016/j.neuroimage.2020.117465.\nOriginal LICENSE: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/. This derivative is distributed under the same terms.\nEEGBench changes: EEG-only selection, semantic label mapping, verified zero-based epoch extraction, fixed subject split, float32 .ts serialization and sidecars. No filtering/resampling/reference or signal scale change.\n',encoding='utf-8')
        (stage/f'README_{NAME}.md').write_text(f'# {NAME}\n\nERP CORE N400: related (1) versus unrelated (2) target words. Source codes 211/212 and 221/222 and list identities are preserved in case tables.\n\nOne-second 30-channel EEG epochs at 1024Hz. Original one-based EEGLAB latencies are converted to zero-based array indices; crops start 205 samples before that marker and end 1024 samples later, exclusive. No added monitor delay, filters, baseline, resampling or reference changes. Source microvolt float32 values are retained.\n\nPer-split TSVs align exactly with cases; combined rows are TRAIN then TEST. Read IDs as strings. Original prime/response events, demographics and all 33 sensor definitions (including three excluded EOG channels) remain in sidecars/source metadata.\n\nCC BY-SA 4.0 per original LICENSE and authors website; conflicting CC0/CC BY metadata are documented. See attribution, metadata, source manifest and validation. No benchmark scores are included.\n',encoding='utf-8')
        code=stage/'conversion_code';code.mkdir();shutil.copy2(__file__,code/Path(__file__).name)
        from tools import prepare_moabb
        shutil.copy2(prepare_moabb.__file__,code/'prepare_moabb.py')
        manifest=dict(name=NAME,status=validation['quality_status'],source=dict(url=metadata['source_url'],data_doi=metadata['source_doi'],original_bids_doi=metadata['original_bids_doi'],licence='CC-BY-SA-4.0',download_manifest_url=MANIFEST_URL,download_manifest_sha256=MANIFEST_SHA256,files=inventory),moabb_revision=MOABB_REVISION,split=split_definition,conversion=metadata['preprocessing'],validation=validation,
                      artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file()})
        dump(stage/f'{NAME}_manifest.json',manifest);stage.rename(folder)
    print(json.dumps(dict(dataset=NAME,output=str(folder),train=counts['TRAIN'],test=counts['TEST'],validation=validation['quality_status'])),flush=True)
    return metadata,validation
