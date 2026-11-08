"""Wang2016 -> FlickerSymbols, native epochs with exact float64 decimal export.

Source EEG cache is temporary by default; use --keep-source to retain downloaded
MAT files. Metadata, checksums and original source URLs are always retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
from scipy.io import loadmat

from tools.prepare_moabb import MOABB_REVISION, dump, fetch, lines, sha

NAME = 'FlickerSymbols'
RECORD = 14865172
SOURCE_MD5 = {'S29.mat': 'md5:8a7c994120f1b1ee9cf14f84957ac2bc', 'S24.mat': 'md5:8d1a27bb45baecba380dddded435dfc6', 'S12.mat': 'md5:036678899589c341658ba75bfd845bff', 'S20.mat': 'md5:7c50f866da76b184cf8c3a8dd8749b91', 'S25.mat': 'md5:3b3f8b02ca96fe96033e016583209dd0', 'S18.mat': 'md5:421ce3e424fb0d152679fbc3c2019e51', 'S19.mat': 'md5:63c7f37b58c5830455107f1374ccccd5', 'S32.mat': 'md5:416b434283bd4ae5bc8581e17503551e', 'S21.mat': 'md5:06d7657e4371650b19ff231a566f9c05', 'S28.mat': 'md5:909c2e5945b6f367a91a098f15874742', 'S22.mat': 'md5:e9e530f82842636963982c028c8cdea3', 'S16.mat': 'md5:72d5cfe8c2e1f322aa873fdfa662d4f9', 'S33.mat': 'md5:24aa136669e9e032a15547c699d82c35', 'S14.mat': 'md5:e8733da6dae847d94224bb4ac0fd6484', 'S34.mat': 'md5:f622bc4fea31f7b90df6d6ec8b9a8c62', 'S17.mat': 'md5:a872db3268978dc465e6396ea7805abc', 'S4.mat': 'md5:6dd06df6ffb00d3dcc563c8602d87c3b', 'S11.mat': 'md5:9d968c6e04b6f82c6e3fbe99235ceefc', 'S6.mat': 'md5:5c1e3401097deba330a2eccedb4a883d', 'S31.mat': 'md5:ea14e036a6d6267cbb019c25a0f1c16e', 'S13.mat': 'md5:b35627676664ae92a0ff7803941fc70b', 'S30.mat': 'md5:02b71137aef753cf0a74cbc7637ba7fe', 'S15.mat': 'md5:12bcc1dd51a65806e53a08925bbfa715', 'S9.mat': 'md5:7957d827bbb28f1eb6b918fa0236dc61', 'S27.mat': 'md5:54948d6d2166706f883a86dd523306fb', 'S26.mat': 'md5:958a806714a11cc74c7a4827f7256fe7', 'S23.mat': 'md5:cd5d107d9b17004e0d987781f502641a', 'S8.mat': 'md5:c3b945bf6ac866f3b9546fd1138ee268', 'S7.mat': 'md5:fe63a5523576f76e5b5b3e7108cad720', 'S5.mat': 'md5:dd9016d2844698010dec5f5061c5c81a', 'S10.mat': 'md5:c61d6d7d99b783618ed8dd2fd54f52d3', 'S3.mat': 'md5:fb752ad0ad957c3544b4584bc293cfee', 'Readme.txt': 'md5:541f7945746131110464f2cc2518e635', 'S1.mat': 'md5:281fc8e77da9f1957823624c85b40feb', 'Sub_info.txt': 'md5:14e180db4a34252fcb32622e48b02277', '64-channels.loc': 'md5:21cae78341d49df7b2239b2229c842fd', 'S35.mat': 'md5:c80b7c72abad0e17ab8eab27d549e316', 'S2.mat': 'md5:004c1e52b0b2c5607f5b6b347dc8fc2d'}
SFREQ, POINTS = 250, 1500
TRAIN = tuple([*range(1, 7), *range(9, 29)])
BASE = 'https://bci.med.tsinghua.edu.cn/upload/yijun/'
RESOURCE_SHA256 = {'Freq_Phase.mat': '6059f712688ec9e5df0beace9244dc0a4b03c418dacdef86bac50cf2b95f71b5', 'original-Readme.txt': '3bf106f1901a2ce2c7c309fee948eb13a692597a00e23cbc8d8b9ae170988e69', 'original-64-channels.loc': 'da8c1d84451930234392b9283fccffb7994d69ed97bb452c6927613bb33c3ab0', 'pinned-moabb-wang.py': 'c63bf84a19e58a29cba6da57194acc08d3bfdec9bc35168727df00654d76492b', 'nemar-dataset-description.json': '8e61c5bc77d7c481847d12d35d6ca7250963095b6afdc31ccc2d3b8646d2b433'}
FIELDS = ['split', 'row', 'example_id', 'participant_id', 'source_subject_id',
          'session_id', 'session_id_evidence', 'run_id', 'block_index_0based',
          'source_file', 'source_array_index', 'source_target_index_0based',
          'source_trial_within_block_chronology', 'original_recording_start_sample',
          'original_recording_end_sample', 'epoch_start_sample', 'epoch_end_sample',
          'epoch_start_relative_stimulus_seconds', 'epoch_end_relative_stimulus_seconds',
          'source_label', 'label', 'frequency_hz', 'phase_radians',
          'original_partition', 'signal_sha256', 'signal_hash_dtype']


def digest_case(x):
    return hashlib.sha256(np.asarray(x, dtype='<f8').tobytes()).hexdigest()


def parse_channels(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip(): continue
        index, theta, radius, name = line.split()
        rows.append(dict(array_index=len(rows), source_electrode_index=int(index),
                         name=name, type='EEG', units='uV',
                         source_polar_theta_degrees=float(theta),
                         source_polar_radius=float(radius),
                         position_evidence='Original EEGLAB .loc polar coordinates; no individual 3D coordinates'))
    if len(rows) != 64 or [r['source_electrode_index'] for r in rows] != list(range(1, 65)):
        raise ValueError('Unexpected original channel count/order')
    return rows


def iter_cases(data):
    """Match the pinned loader's target-major, block-minor source indexing."""
    if data.shape != (64, POINTS, 40, 6) or data.dtype != np.float64:
        raise ValueError('Changed source dimensions/dtype')
    for target in range(40):
        for block in range(6):
            yield target, block, np.ascontiguousarray(data[:, :, target, block])


def format_case(x):
    # Python repr gives the shortest decimal recovering the exact binary64 value.
    return ':'.join(','.join(map(repr, ch.tolist())) for ch in x)


def resources(cache, download=True):
    cache.mkdir(parents=True, exist_ok=True)
    record_path = cache / f'zenodo-record-{RECORD}.json'
    if download:
        fetch(f'https://zenodo.org/api/records/{RECORD}', record_path)
    record = json.loads(record_path.read_text())
    if record['id'] != RECORD or record['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Source version/data licence changed')
    files = {f['key']: f for f in record['files']}
    if {k:f['checksum'] for k,f in files.items()} != SOURCE_MD5:
        raise ValueError('Pinned source file roster or checksums changed')
    for name in ['Readme.txt', '64-channels.loc', 'Sub_info.txt']:
        f = files[name]
        if download: fetch(f['links']['self'], cache/name, f['checksum'], f['size'])
        if 'md5:'+sha(cache/name, 'md5') != f['checksum']: raise ValueError(name)
    for name, url in {
        'Freq_Phase.mat': BASE+'Freq_Phase.mat',
        'original-Readme.txt': BASE+'Readme.txt',
        'original-64-channels.loc': BASE+'64-channels.loc',
        'pinned-moabb-wang.py': f'https://raw.githubusercontent.com/NeuroTechX/moabb/{MOABB_REVISION}/moabb/datasets/ssvep_wang.py',
        'nemar-dataset-description.json': 'https://data.nemar.org/nm000126/v1.0.3/dataset_description.json',
    }.items():
        if download: fetch(url, cache/name)
        if not (cache/name).is_file(): raise FileNotFoundError(name)
        if sha(cache/name) != RESOURCE_SHA256[name]: raise ValueError('Pinned metadata changed: '+name)
    if (cache/'64-channels.loc').read_bytes() != (cache/'original-64-channels.loc').read_bytes():
        raise ValueError('Original and mirror channel orders differ')
    return record, files


def validate(folder, split, expected):
    hashes = set(); counts = Counter(); people = set(); tiny = flat = 0
    with (folder/f'cases_{split.lower()}.tsv').open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    import itertools
    for i, pair in enumerate(itertools.zip_longest(lines(folder/f'{NAME}_{split}.ts'), rows)):
        line, row = pair
        if line is None or row is None: raise ValueError('Case/metadata count mismatch')
        body, label = line.strip().rsplit(':', 1)
        x = np.stack([np.fromstring(ch, sep=',', dtype=np.float64) for ch in body.split(':')])
        if x.shape != (64, POINTS) or not np.isfinite(x).all(): raise ValueError('Invalid case')
        h = digest_case(x)
        if h != row['signal_sha256'] or row['label'] != label or int(row['row']) != i:
            raise ValueError('Exact float64 source/case/label alignment failed')
        if h in hashes: raise ValueError('Duplicate within partition')
        hashes.add(h); counts[label] += 1; people.add(row['participant_id'])
        sd = x.std(axis=1); span = np.ptp(x, axis=1)
        flat += int((span == 0).sum()); tiny += int(((sd <= 1e-7) & (span != 0)).sum())
    if len(rows) != expected*240 or dict(counts) != {str(i):expected*6 for i in range(1,41)}:
        raise ValueError('Unexpected class/case counts')
    if flat or tiny: raise ValueError(f'Quality review required: {flat} constant, {tiny} tiny pairs')
    return dict(shape=[len(rows),64,POINTS],cases=len(rows),class_counts=dict(counts),
                subjects=sorted(people),exact_float64_roundtrip=True,metadata_order_verified=True,
                finite=True,exact_constant_pairs=flat,aeon_tiny_nonconstant_pairs=tiny), hashes


def smoke(folder):
    from aeon.classification.feature_based import SummaryClassifier
    from aeon.datasets import load_from_ts_file
    from aeon.utils.validation.collection import check_collection_variance
    samples=[]
    with tempfile.TemporaryDirectory() as tmp:
        for split in ['TRAIN','TEST']:
            counts=Counter(); p=Path(tmp)/f'{split}.ts'
            with p.open('w') as f:
                f.write(header())
                for line in lines(folder/f'{NAME}_{split}.ts'):
                    label=line.strip().rsplit(':',1)[1]
                    if counts[label]<2:f.write(line);counts[label]+=1
                    if len(counts)==40 and min(counts.values())==2:break
            x,y=load_from_ts_file(p);check_collection_variance(x);samples.append((x,y))
        clf=SummaryClassifier(random_state=0,n_jobs=1)
        clf.fit(*samples[0]);pred=clf.predict(samples[1][0])
        if len(pred)!=80:raise ValueError('aeon prediction count')
    return dict(aeon_load_fit_predict=True,train_smoke_cases=80,test_smoke_cases=80,classes=40)


def header():
    return (f'# Wang2016 native microvolt epochs, float64; see sidecars.\n@problemName {NAME}\n'
            '@timestamps false\n@missing false\n@univariate false\n@dimensions 64\n'
            '@equalLength true\n@seriesLength 1500\n@classLabel true '+
            ' '.join(map(str,range(1,41)))+'\n@data\n')


def ensure_source(cache, subject, files, download):
    f=files[f'S{subject}.mat'];p=cache/f['key']
    if download:fetch(f['links']['self'],p,f['checksum'],f['size'])
    if 'md5:'+sha(p,'md5')!=f['checksum']:raise ValueError('Changed source signal')
    return p


def convert(cache, output, subjects=tuple(range(1,36)), train=TRAIN, download=True, keep=False):
    cache=Path(cache);output=Path(output);folder=output/NAME
    if folder.exists():raise FileExistsError(folder)
    subjects=tuple(sorted(subjects));train=set(train)&set(subjects)
    if len(set(subjects))!=len(subjects) or not set(subjects)<=set(range(1,36)):raise ValueError('Invalid/duplicate subject')
    if not train or not set(subjects)-train:raise ValueError('Both partitions require subjects')
    record,files=resources(cache,download);sensors=parse_channels(cache/'64-channels.loc')
    fp=loadmat(cache/'Freq_Phase.mat');freq=fp['freqs'].ravel();phase=fp['phases'].ravel()
    if freq.shape!=(40,) or phase.shape!=(40,) or len(set(freq))!=40:raise ValueError('Target map changed')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{NAME}-',dir=output) as tmp:
        stage=Path(tmp);counts=Counter();inventory=[];handles={};tables={};writers={}
        pool=ThreadPoolExecutor(max_workers=4)
        pending={s:pool.submit(ensure_source,cache,s,files,download) for s in subjects[:4]}
        try:
            for split in ['TRAIN','TEST']:
                handles[split]=(stage/f'{NAME}_{split}.ts').open('w',encoding='ascii',newline='\n');handles[split].write(header())
                tables[split]=(stage/f'cases_{split.lower()}.tsv').open('w',newline='',encoding='utf-8')
                writers[split]=csv.DictWriter(tables[split],FIELDS,delimiter='\t',lineterminator='\n');writers[split].writeheader()
            for subject_index,subject in enumerate(subjects):
                f=files[f'S{subject}.mat'];p=pending.pop(subject).result()
                inventory.append(dict(file=p.name,url=f['links']['self'],md5=f['checksum'],sha256=sha(p),bytes=p.stat().st_size))
                data=loadmat(p)['data'];split='TRAIN' if subject in train else 'TEST';sid=f'{subject:02d}'
                for target,block,x in iter_cases(data):
                    if not np.isfinite(x).all():raise ValueError('Nonfinite source')
                    row=dict.fromkeys(FIELDS,'')
                    row.update(split=split,row=counts[split],example_id=f'Wang2016/{sid}/{target+1:02d}/{block+1:02d}',
                        participant_id=sid,source_subject_id=f'S{sid}',session_id='0',session_id_evidence='one documented acquisition session; no original date/ID',
                        run_id=f'{block+1:02d}',block_index_0based=block,source_file=p.name,source_array_index=f'[:,:,{target},{block}]',
                        source_target_index_0based=target,epoch_start_sample=0,epoch_end_sample=1500,
                        epoch_start_relative_stimulus_seconds=-0.5,epoch_end_relative_stimulus_seconds=5.5,
                        source_label=target+1,label=target+1,frequency_hz=float(freq[target]),phase_radians=float(phase[target]),
                        original_partition='No fixed source partition; source evaluation used blocks',signal_sha256=digest_case(x),signal_hash_dtype='<f8')
                    writers[split].writerow(row);handles[split].write(format_case(x)+f':{target+1}\n');counts[split]+=1
                del data
                if not keep and download:p.unlink()  # Only this adapter's verified downloaded cache file.
                if subject_index+4<len(subjects):
                    next_subject=subjects[subject_index+4];pending[next_subject]=pool.submit(ensure_source,cache,next_subject,files,download)
                print(f'{NAME}: subject {sid}, cases {dict(counts)}, bytes {sum(h.tell() for h in handles.values())}',flush=True)
        finally:
            pool.shutdown(wait=True,cancel_futures=True)
            for h in [*handles.values(),*tables.values()]:h.close()
        reports={};hashes={}
        for split,n in [('TRAIN',len(train)),('TEST',len(set(subjects)-train))]:
            reports[split],hashes[split]=validate(stage,split,n);print(split+' full float64 validation passed',flush=True)
        if hashes['TRAIN']&hashes['TEST']:raise ValueError('Duplicate across partitions')
        if set(reports['TRAIN']['subjects'])&set(reports['TEST']['subjects']):raise ValueError('Subject leakage')
        validation=dict(partitions=reports,cross_split_duplicate_cases=0,subject_overlap=0,channel_order='Every case uses original 64-axis source order; identical external .loc mapping',aeon=smoke(stage))
        splitdef=dict(unit='subject',train_subjects=sorted(f'{s:02d}' for s in train),test_subjects=sorted(f'{s:02d}' for s in set(subjects)-train),
            reason='Fixed EEGBench split; full cohort has 6 experienced/20 naive train and 2 experienced/7 naive test',validation_partition=None,
            order='Ascending participant, then source target index, then source block index; no trial shuffling',source_protocol='Original source evaluated within subject over blocks; EEGBench uses disjoint subjects')
        labels={str(i+1):dict(source_target=i+1,frequency_hz=float(freq[i]),phase_radians=float(phase[i]),character=None) for i in range(40)}
        missing=['Original continuous-recording sample offsets and dates','Within-block presentation chronology (source array is target-indexed)','Original speller character identity not recovered; labels identify targets by source index/frequency/phase','Individual 3D sensor coordinates; original .loc polar coordinates retained','Original lab README contains no explicit licence grant; publication rights require review despite CC BY declarations in distributed releases']
        preprocessing=dict(local='None: no filtering, demeaning, referencing, gain, crop or resampling',upstream='Amplifier 0.15–200 Hz; acquisition notch 50 Hz; native 1000 Hz recordings epoched and downsampled to 250 Hz',
            moabb_difference='Pinned loader demeans and reconstructs synthetic continuous data; its paradigm crops to stimulation. This export reads unmodified full native epochs directly.',output='Shortest exact float64 decimal representation; original uV numeric scale preserved',window_seconds=6,stimulus_seconds=5,overlap='Original extracted trials are distinct; continuous offsets unavailable')
        metadata=dict(name=NAME,source='Wang2016 / Tsinghua 40-target SSVEP Benchmark',source_record=RECORD,source_doi='10.1109/TNSRE.2016.2627556',
            licence='CC-BY-4.0 declared by Zenodo data release and NEMAR; original lab README has no explicit grant',release_status='Local research preparation; original-grant applicability to redistribution remains review item',
            dtype='float64',units='uV',units_evidence='Pinned MOABB loader interprets original MATLAB values as microvolts (multiplies by 1e-6 for MNE volts); no unit field is embedded in the MATLAB array',frequency=250,original_frequency=1000,channel_count=64,channel_names=[s['name'] for s in sensors],sensors=sensors,
            reference='Vertex/Cz, documented by source',montage='Original 64-channels.loc; preserve CB1/CB2, do not silently map to P9/P10',
            subjects=len(subjects),sessions_per_subject=1,blocks_per_subject=6,source_recording_count_unknown=True,source_epoch_files=len(subjects),
            shapes={s.lower():reports[s]['shape'] for s in reports},label_mapping=labels,class_distributions={s.lower():reports[s]['class_counts'] for s in reports},
            split=splitdef,preprocessing=preprocessing,missing_metadata=missing,metadata_evidence=dict(direct='MAT axis dimensions, file/target/block indices, participant roster, original .loc, frequency/phase MATLAB file',documented='Source README: timing, acquisition, montage and reference; no invented recording offsets'),
            nemar_caveat='NEMAR derivative reports 34 participants; this export uses all 35 original MATLAB release files and does not substitute that derivative')
        dump(stage/f'{NAME}_metadata.json',metadata);dump(stage/f'{NAME}_validation.json',validation)
        dump(stage/'metadata-completeness.json',dict(available=metadata['metadata_evidence'],missing=missing))
        (stage/'channels.txt').write_text(', '.join(metadata['channel_names'])+'\n')
        with (stage/'channels.tsv').open('w',newline='') as f:
            w=csv.DictWriter(f,list(sensors[0]),delimiter='\t');w.writeheader();w.writerows(sensors)
        evidence=stage/'source_metadata';evidence.mkdir()
        for p in cache.iterdir():
            if p.is_file() and p.name!='S1.mat' and not p.name.startswith('S') and not p.name.endswith('.part'):shutil.copy2(p,evidence/p.name)
        shutil.copy2(cache/'Sub_info.txt',evidence/'Sub_info.txt')
        (stage/'ATTRIBUTION.txt').write_text('Wang, Y.; Chen, X.; Gao, X.; Gao, S. A Benchmark Dataset for SSVEP-Based Brain-Computer Interfaces. DOI 10.1109/TNSRE.2016.2627556. Tsinghua laboratory release, mirrored at Zenodo 14865172. Data-release licence declaration: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Changes: deterministic subject split, case/sensor sidecars and lossless decimal .ts conversion; no numerical preprocessing. Original lab README has no explicit licence grant; release review remains required.\n')
        (stage/f'README_{NAME}.md').write_text('# FlickerSymbols\n\nWang2016: classify the attended target among 40 frequency/phase-coded visual symbols. Original 64-channel, 1500-point epochs at 250 Hz in microvolt numeric scale. No additional filtering, demeaning, referencing, cropping, gain or resampling. Exact float64 decimal export.\n\nThe case TSVs are ordered exactly like the corresponding .ts files. IDs are strings. Source target/block indices are retained; original continuous-recording offsets and within-block presentation order are unknown. Channels follow the original .loc order, including CB1/CB2 without invented standard aliases.\n\nThe fixed subject split balances experience groups and is defined in the metadata/manifest. It differs from the original within-subject block evaluation. There is no validation partition. See source_metadata, channels.tsv, metadata-completeness.json, attribution and validation for source terms and limitations.\n')
        code=stage/'conversion_code';code.mkdir();shutil.copy2(__file__,code/Path(__file__).name);shutil.copy2(Path(__file__).with_name('prepare_moabb.py'),code/'prepare_moabb.py')
        dump(stage/f'{NAME}_manifest.json',dict(name=NAME,source_revision=f'Zenodo record {RECORD}',moabb_revision=MOABB_REVISION,source_files=inventory,
            source_urls=[BASE,f'https://zenodo.org/records/{RECORD}'],licence=metadata['licence'],release_status=metadata['release_status'],split=splitdef,conversion=preprocessing,validation=validation,
            artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(folder)
    result=dict(dataset=NAME,train_cases=counts['TRAIN'],test_cases=counts['TEST'],subjects=len(subjects),channels=64,timepoints=POINTS,classes=40,frequency=SFREQ,
                size_GB=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9,licence=metadata['licence'],validation=validation)
    print(json.dumps(result,indent=2),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,default=Path('.openeegbench/wang2016'))
    p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--subjects',default=','.join(map(str,range(1,36))))
    p.add_argument('--train-subjects',default=','.join(map(str,TRAIN)));p.add_argument('--offline',action='store_true');p.add_argument('--keep-source',action='store_true')
    a=p.parse_args();result=convert(a.cache,a.output,tuple(map(int,a.subjects.split(','))),tuple(map(int,a.train_subjects.split(','))),not a.offline,a.keep_source)
    if len(result['validation']['partitions']['TRAIN']['subjects'])==26:
        dump(Path(__file__).parents[1]/'docs/flicker-symbols-local-results.json',result)


if __name__=='__main__':main()
