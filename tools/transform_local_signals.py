"""Staged, backed-up local signal transformations with full float64 readback.

Explicitly scoped to the approved MatchWords and VideoEmotions transformations.
Original folders are moved to a separate backup root only after validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np
import pandas as pd

from tools.prepare_moabb import dump,sha,lines

SPECS={
    'MatchWords':dict(channels=157,points=1500,drop=55,gain=1e15,before_unit='T',after_unit='fT',counts={'TRAIN':360,'TEST':360},reason='Original axis 55 is exactly constant in all 720 cases; source-order name MEG 056 is marked bad. Convert tesla to femtotesla.'),
    'VideoEmotions':dict(channels=26,points=2000,drop=6,gain=1.,before_unit='uV',after_unit='uV',counts={'TRAIN':15629,'TEST':3588},reason='F8 (original axis 6) is effectively flat for all 156 windows of participant 030. Remove globally for a common sensor axis set; preserve the existing numeric scale.'),
}


def hash_case(array,dtype='<f8'):
    return hashlib.sha256(np.asarray(array,dtype=dtype).tobytes()).hexdigest()


def transform_values(segments,drop,gain):
    old=np.stack([np.fromstring(s,sep=',',dtype=np.float64) for s in segments])
    keep=[i for i in range(len(segments)) if i!=drop]
    new=np.asarray(old[keep],dtype='<f8')*np.float64(gain)
    if gain==1:
        output=':'.join(segments[i] for i in keep)  # Preserve retained tokens exactly.
    else:
        output=':'.join(','.join(format(float(v),'.17g') for v in ch) for ch in new)
    return old,new,output


def transform_file(source,target,name,spec):
    digest=hashlib.sha256();expected=[];before_hashes=[];before_f32=[];labels=[];classes=Counter();nflat=0;source_stat=source.stat()
    with source.open('rb') as reader,target.open('w',encoding='utf-8',newline='\n') as writer:
        writer.write(f'# Local transformation: remove original axis {spec["drop"]}; gain {spec["gain"]:.17g}; output units {spec["after_unit"]}. See sidecars.\n')
        dimension_seen=False
        for raw in reader:
            digest.update(raw);line=raw.decode('utf-8-sig').rstrip('\r\n');lower=line.strip().lower()
            if lower=='@data':
                if not dimension_seen:writer.write(f'@dimensions {spec["channels"]-1}\n')
                writer.write('@data\n');break
            if lower.startswith('@problemname '):line=f'@problemName {name}'
            if re.match(r'@dimensions?\s',lower):line=f'@dimensions {spec["channels"]-1}';dimension_seen=True
            writer.write(line+'\n')
        else:raise ValueError('Missing @data marker')
        for raw in reader:
            digest.update(raw);line=raw.decode('ascii').strip()
            if not line:continue
            body,label=line.rsplit(':',1);segments=body.split(':')
            if len(segments)!=spec['channels']:raise ValueError('Unexpected source channel count')
            old,new,output=transform_values(segments,spec['drop'],spec['gain'])
            if old.shape!=(spec['channels'],spec['points']) or not np.isfinite(old).all():raise ValueError('Invalid source shape/values')
            if np.ptp(old[spec['drop']])==0:nflat+=1
            expected.append(hash_case(new));before_hashes.append(hash_case(old));before_f32.append(hash_case(old,'<f4'))
            labels.append(label);classes[label]+=1;writer.write(output+':'+label+'\n')
            if len(labels)%2000==0:print(f'{name} {source.stem}: {len(labels)} cases written',flush=True)
    if (source_stat.st_size,source_stat.st_mtime_ns)!=(source.stat().st_size,source.stat().st_mtime_ns):raise ValueError('Source changed during conversion')
    return dict(source_sha256=digest.hexdigest(),source_bytes=source_stat.st_size,source_mtime_ns=source_stat.st_mtime_ns,
                hashes=expected,previous_hashes=before_hashes,previous_float32_hashes=before_f32,labels=labels,class_counts=dict(classes),removed_axis_exact_flat_cases=nflat)


def validate_file(path,spec,expected):
    count=0;constant=0;tiny=0;minimum=np.inf;classes=Counter()
    for count,(line,hashed,label) in enumerate(itertools.zip_longest(lines(path),expected['hashes'],expected['labels']),1):
        if line is None or hashed is None or label is None:raise ValueError('Changed number/order of cases')
        body,actual_label=line.strip().rsplit(':',1)
        x=np.stack([np.fromstring(s,sep=',',dtype=np.float64) for s in body.split(':')])
        if x.shape!=(spec['channels']-1,spec['points']) or not np.isfinite(x).all():raise ValueError('Invalid transformed shape/values')
        if hash_case(x)!=hashed or actual_label!=label:raise ValueError('Full float64 readback/label mismatch')
        span=np.ptp(x,axis=1);sd=x.std(axis=1,ddof=0);constant+=int((span==0).sum());tiny+=int(((sd<=1e-7)&(span!=0)).sum())
        minimum=min(minimum,float(sd[span>0].min()));classes[actual_label]+=1
    if constant or tiny:raise ValueError(f'Remaining constant/tiny pairs: {constant}/{tiny}')
    if dict(classes)!=expected['class_counts']:raise ValueError('Class counts changed')
    return dict(cases=count,shape=[count,spec['channels']-1,spec['points']],labels_and_order_unchanged=True,
                exact_float64_roundtrip=True,finite=True,exact_constant_pairs=constant,aeon_tiny_nonconstant_pairs=tiny,
                minimum_nonconstant_std=minimum,class_counts=dict(classes),sha256=sha(path),bytes=path.stat().st_size)


def update_rows(stage,name,transformed):
    for split,result in transformed.items():
        files=[stage/f'{name}_{split}_rows.tsv'] if name=='MatchWords' else [stage/f'{name}_rows.tsv']
        for path in files:
            # VideoEmotions' combined table is updated once below.
            if name!='MatchWords':continue
            with path.open(newline='',encoding='utf-8') as file:reader=csv.DictReader(file,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
            if len(rows)!=len(result['labels']):raise ValueError('Case metadata length mismatch')
            for i,row in enumerate(rows):
                if int(row['case_index_0based'])!=i or row['class_label']!=result['labels'][i]:raise ValueError('Legacy case metadata row/label mismatch')
                row.update(previous_local_signal_sha256=result['previous_hashes'][i],previous_local_hash_dtype='<f8',signal_sha256=result['hashes'][i],signal_hash_dtype='<f8')
            with path.open('w',newline='',encoding='utf-8') as file:
                writer=csv.DictWriter(file,list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    if name=='VideoEmotions':
        path=stage/f'{name}_rows.tsv'
        with path.open(newline='',encoding='utf-8') as file:reader=csv.DictReader(file,delimiter='\t');rows=list(reader)
        for split,result in transformed.items():
            selected=[r for r in rows if r['split']==split]
            if len(selected)!=len(result['labels']):raise ValueError('Combined case metadata length mismatch')
            for i,row in enumerate(selected):
                if int(row['row'])!=i or row['label']!=result['labels'][i] or row['signal_sha256']!=result['previous_float32_hashes'][i]:raise ValueError('Source float32 case/hash/label alignment mismatch')
                row['source_signal_sha256']=row['signal_sha256'];row['source_signal_hash_dtype']='<f4'
                row['previous_local_signal_sha256']=result['previous_hashes'][i];row['previous_local_hash_dtype']='<f8'
                row['signal_sha256']=result['hashes'][i];row['signal_hash_dtype']='<f8'
            parquet=stage/f'cases_{split.lower()}.parquet';frame=pd.read_parquet(parquet)
            if len(frame)!=len(selected) or frame['signal_sha256'].tolist()!=result['previous_float32_hashes']:raise ValueError('Parquet case hash alignment mismatch')
            frame['source_signal_sha256']=frame['signal_sha256'];frame['source_signal_hash_dtype']='<f4'
            frame['previous_local_signal_sha256']=result['previous_hashes'];frame['previous_local_hash_dtype']='<f8'
            frame['signal_sha256']=result['hashes'];frame['signal_hash_dtype']='<f8';frame.to_parquet(parquet,index=False)
        with path.open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)


def smoke(stage,name):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.utils.validation.collection import check_collection_variance
    from aeon.classification.feature_based import SummaryClassifier
    loaded={}
    with tempfile.TemporaryDirectory(dir=stage) as tmp:
        for split in ['TRAIN','TEST']:
            path=stage/f'{name}_{split}.ts';prefix=[];chosen={}
            with path.open() as file:
                for line in file:
                    prefix.append(line)
                    if line.strip().lower()=='@data':break
                for line in file:
                    label=line.rsplit(':',1)[1].strip();chosen.setdefault(label,[])
                    if len(chosen[label])<4:chosen[label].append(line)
                    # Read the rest cheaply only until all expected classes are collected.
                    required=2 if name=='MatchWords' else 8
                    if len(chosen)==required and all(len(v)==4 for v in chosen.values()):break
            subset=Path(tmp)/f'{split}.ts';subset.write_text(''.join(prefix)+''.join(line for group in chosen.values() for line in group))
            loaded[split]=load_from_ts_file(subset);assert check_collection_variance(loaded[split][0])
        clf=SummaryClassifier(random_state=0,n_jobs=1);clf.fit(*loaded['TRAIN']);prediction=clf.predict(loaded['TEST'][0])
        if len(prediction)!=len(loaded['TEST'][1]):raise ValueError('Classifier compatibility failed')
    return dict(passed=True,aeon_version=aeon.__version__,classifier='SummaryClassifier',train_cases=len(loaded['TRAIN'][1]),test_cases=len(prediction),variance_check=True,note='Representative all-class load/fit/predict; every full case independently checked numerically.')


def transform_dataset(root,backup_root,name,batch):
    spec=SPECS[name];root=Path(root).resolve();backup_root=Path(backup_root).resolve();source=root/name
    if source.resolve().parent!=root or backup_root.is_relative_to(root) or root.anchor!=backup_root.anchor:raise ValueError('Unsafe source/backup locations')
    original=json.loads((source/f'{name}_metadata.json').read_text(encoding='utf-8'))
    if original.get('local_transform_revision'):raise ValueError('This local transformation has already been applied')
    keep=[i for i in range(spec['channels']) if i!=spec['drop']]
    oldnames=original['channel_names'] if name=='VideoEmotions' else None
    if name=='MatchWords':
        with (source/f'{name}_channels.tsv').open(newline='',encoding='utf-8') as file:channel_rows=list(csv.DictReader(file,delimiter='\t'))
        oldnames=[r['name'] for r in channel_rows]
    if len(oldnames)!=spec['channels']:raise ValueError('Source sensor count mismatch')
    if name=='VideoEmotions' and oldnames[6]!='F8':raise ValueError('Expected source F8 at axis 6')
    backup=backup_root/batch/name
    if backup.exists():raise FileExistsError(backup)
    with tempfile.TemporaryDirectory(prefix=f'.transform-{name}-',dir=root) as tmp:
        stage=Path(tmp)
        for path in source.iterdir():
            if path.name in [f'{name}_TRAIN.ts',f'{name}_TEST.ts']:continue
            if path.is_dir():shutil.copytree(path,stage/path.name)
            else:shutil.copy2(path,stage/path.name)
        history=stage/'history'/batch;history.mkdir(parents=True)
        for path in source.iterdir():
            if path.name in [f'{name}_metadata.json',f'{name}_validation.json',f'{name}_manifest.json',f'README_{name}.md',f'{name}_channels.tsv','channels.txt']:
                shutil.copy2(path,history/path.name)
        transformed={};validation={}
        for split in ['TRAIN','TEST']:
            transformed[split]=transform_file(source/f'{name}_{split}.ts',stage/f'{name}_{split}.ts',name,spec)
            if len(transformed[split]['labels'])!=spec['counts'][split]:raise ValueError('Unexpected source case count')
            if name=='MatchWords' and transformed[split]['removed_axis_exact_flat_cases']!=spec['counts'][split]:raise ValueError('Requested MatchWords axis is not globally flat')
            validation[split]=validate_file(stage/f'{name}_{split}.ts',spec,transformed[split]);print(f'{name} {split}: full float64 readback and variance checks passed',flush=True)
        shared=set(transformed['TRAIN']['hashes'])&set(transformed['TEST']['hashes'])
        if shared:raise ValueError('Cross-split duplicate cases after transformation')
        update_rows(stage,name,transformed)
        metadata=copy.deepcopy(original);newnames=[oldnames[i] for i in keep]
        change=dict(id=batch,kind='channel_selection_and_unit_conversion' if spec['gain']!=1 else 'channel_selection',gain=spec['gain'],units_before=spec['before_unit'],units_after=spec['after_unit'],computation_dtype='float64',signal_hash_dtype='<f8',output_precision='17 significant digits' if spec['gain']!=1 else 'Retained original decimal tokens exactly',removed_channels=[dict(original_array_index=spec['drop'],name=oldnames[spec['drop']],reason=spec['reason'])],kept_source_array_indices=keep,case_order='unchanged',labels='unchanged',split_membership='unchanged',backup=str(backup),source_files={s:{k:r[k] for k in ['source_sha256','source_bytes','source_mtime_ns']} for s,r in transformed.items()},before_shapes={s.lower():[spec['counts'][s],spec['channels'],spec['points']] for s in spec['counts']},after_shapes={s.lower():validation[s]['shape'] for s in spec['counts']})
        metadata.update(local_transform_revision=batch,change_history=[*metadata.get('change_history',[]),change],name=name,dtype='float64',source_numeric_dtype=original.get('dtype','not established'),channel_count=len(keep),channel_names=newnames,channels=newnames,shapes=change['after_shapes'],units=spec['after_unit'],source_channel_names_before_transform=oldnames,source_shapes_before_transform=change['before_shapes'])
        if name=='MatchWords':
            shutil.copy2(source/f'{name}_channels.tsv',stage/f'{name}_source_channels.tsv')
            newrows=[]
            for i,j in enumerate(keep):
                row=channel_rows[j].copy();row.update(array_index_0based=i,source_array_index_0based=j,source_units=row['units'],units='fT');newrows.append(row)
            with (stage/f'{name}_channels.tsv').open('w',newline='',encoding='utf-8') as file:
                writer=csv.DictWriter(file,list(newrows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(newrows)
            metadata['local_data']['dimensions_per_case']['channels']=len(keep)
            metadata['local_data']['values_unit']='fT; prior local values in source-consistent T multiplied by 1e15 in float64'
            metadata['local_data']['channel_mapping']['kept_previous_array_indices']=keep
            metadata['local_data']['channel_mapping']['post_transform_axis_mapping_verified']=True
            metadata['local_data']['channel_mapping']['names_and_order']='156 retained axes in previous array order, excluding original index 55. Names follow the source correspondence; physical array-to-source-name verification remains unavailable.'
            metadata['source_channels']['file']=f'{name}_source_channels.tsv'
            metadata['source_channels']['note']=f'Original source roster retained unchanged; current export removes original local axis {spec["drop"]}. Physical array-to-source-name correspondence remains the documented legacy limitation.'
        else:
            metadata['source_sensors_before_transform']=metadata['sensors'];sensors=[]
            for i,j in enumerate(keep):
                sensor=copy.deepcopy(original['sensors'][j]);sensor['source_array_index']=j;sensor['array_index']=i
                if 'unit' in sensor:sensor['source_mne_unit']=sensor.pop('unit')
                if 'unit_mul' in sensor:sensor['source_mne_unit_mul']=sensor.pop('unit_mul')
                sensor['units']='uV';sensors.append(sensor)
            metadata['sensors']=sensors;metadata.pop('local_export_validation',None)
            metadata['local_output_units_note']='Existing upstream microvolt numeric scale preserved; historical MNE voltage tags retained only as source_mne_unit.'
            metadata['preprocessing_scope_note']='Preprocessing describes the upstream 26-channel preparation. The subsequent local F8 removal is recorded in change_history.'
        (stage/'channels.txt').write_text(', '.join(newnames)+'\n',encoding='utf-8')
        if name=='VideoEmotions':
            with (stage/f'{name}_channels.tsv').open('w',newline='',encoding='utf-8') as file:
                writer=csv.DictWriter(file,['array_index_0based','source_array_index_0based','name','channel_type','units'],delimiter='\t');writer.writeheader();writer.writerows(dict(array_index_0based=i,source_array_index_0based=j,name=oldnames[j],channel_type='EEG',units='uV') for i,j in enumerate(keep))
        validation.update(quality_status='passed',cross_split_duplicate_cases=0,metadata_rows_verified=sum(spec['counts'].values()),channel_order='Original axes selected in order; mapping retained in change history',aeon=smoke(stage,name),transform_revision=batch)
        dump(stage/f'{name}_metadata.json',metadata);dump(stage/f'{name}_validation.json',validation);dump(stage/f'{name}_changes.json',change)
        (stage/f'README_{name}.md').write_text(f'# {name}\n\nCurrent local revision: {batch}. Units: {spec["after_unit"]}; {len(keep)} channels x {spec["points"]} timepoints.\n\n{spec["reason"]}\n\nCase order, labels and split membership are unchanged. See metadata/change history for original-axis mapping, gain, precision and source hashes. Original metadata and validation snapshots are in history/. Original files remain in the separate backup folder recorded in the change history.\n\nFull float64 readback and aeon variance checks passed for every case. Sensor/source metadata limits and source licences remain as documented in the metadata.\n',encoding='utf-8')
        code=stage/'conversion_code';code.mkdir(exist_ok=True);shutil.copy2(__file__,code/Path(__file__).name)
        new_manifest=dict(name=name,local_revision=batch,status='validated',format='aeon multivariate .ts with case/sensor sidecars',source_provenance=original.get('provenance',original.get('source_dataset')),transformation=change,validation=validation,previous_metadata=f'history/{batch}/{name}_metadata.json',backup=str(backup),artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in stage.rglob('*') if p.is_file() and p.name!=f'{name}_manifest.json'})
        # Include the historical manifest even though it has the same basename.
        historical=history/f'{name}_manifest.json'
        if historical.exists():new_manifest['artifacts'][historical.relative_to(stage).as_posix()]=dict(sha256=sha(historical),bytes=historical.stat().st_size)
        dump(stage/f'{name}_manifest.json',new_manifest)
        for split,result in transformed.items():
            current=source/f'{name}_{split}.ts';stat=current.stat()
            if (stat.st_size,stat.st_mtime_ns)!=(result['source_bytes'],result['source_mtime_ns']):raise ValueError('Original changed before publishing')
        backup.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve().parent!=root or stage.resolve().parent!=root or backup.resolve().parent!=backup.parent.resolve():raise ValueError('Unsafe final move')
        source.rename(backup)
        try:stage.rename(source)
        except BaseException:
            backup.rename(source);raise
    print(f'{name}: published validated revision {batch}; original backup {backup}',flush=True)
    return dict(dataset=name,revision=batch,backup=str(backup),validation=validation,change=change)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('D:/Data/EEG'))
    parser.add_argument('--backup-root',type=Path,default=Path('D:/Data/EEG_Backups'))
    parser.add_argument('--datasets',nargs='+',choices=list(SPECS),default=list(SPECS))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.apply:print(json.dumps(SPECS,indent=2));return
    batch=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-scale-channels'
    results=[transform_dataset(args.root,args.backup_root,name,batch) for name in args.datasets]
    dump(Path(__file__).parents[1]/'docs/signal-cleanup-results.json',dict(revision=batch,datasets=results))


if __name__=='__main__':main()
