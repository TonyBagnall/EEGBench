"""Correct approved local header/registry discrepancies without rewriting signals."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

import pandas as pd

from neuroverse.datasets import metadata as registry_metadata
from tools.prepare_moabb import dump,sha

SPECS={
    'Alzheimers':dict(channels=19,points=15000,frequency=500,counts={'TRAIN':45,'TEST':43},frequency_verified=False),
    'FingerMovements':dict(channels=28,points=50,frequency=100,counts={'TRAIN':316,'TEST':100},frequency_verified=True),
}


def inspect_file(path,channels,points):
    digest=hashlib.sha256();header=[];count=0;classes=Counter();before=path.stat()
    with path.open('rb') as file:
        for raw in file:
            digest.update(raw);line=raw.decode('utf-8-sig').rstrip('\r\n');header.append(line)
            if line.strip().lower()=='@data':break
        else:raise ValueError('Missing @data marker')
        declared=[int(line.split()[1]) for line in header if line.lower().startswith('@serieslength ')]
        if declared!=[points]:raise ValueError('Local header does not confirm the requested length')
        for raw in file:
            digest.update(raw);line=raw.decode('ascii').strip()
            if not line:continue
            body,label=line.rsplit(':',1);segments=body.split(':')
            if len(segments)!=channels or any(s.count(',')+1!=points for s in segments):raise ValueError('Actual signal dimensions differ from header')
            count+=1;classes[label]+=1
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Signal file changed during metadata inspection')
    return dict(cases=count,shape=[count,channels,points],class_counts=dict(classes),header=header,sha256=digest.hexdigest(),bytes=before.st_size,mtime_ns=before.st_mtime_ns)


def correct(root,backup_root,name,revision):
    root=Path(root).resolve();backup_root=Path(backup_root).resolve();folder=root/name;spec=SPECS[name]
    if folder.resolve().parent!=root or backup_root.is_relative_to(root):raise ValueError('Unsafe metadata/backup locations')
    metadata_path=folder/f'{name}_metadata.json';manifest_path=folder/f'{name}_manifest.json'
    old=json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    if old.get('metadata_correction_revision'):return dict(dataset=name,status='already corrected',revision=old['metadata_correction_revision'])
    files={s:inspect_file(folder/f'{name}_{s}.ts',spec['channels'],spec['points']) for s in ['TRAIN','TEST']}
    if any(files[s]['cases']!=spec['counts'][s] for s in files):raise ValueError('Unexpected local case count')
    if name=='FingerMovements' and not any(re.search(r'downsampled at 100 Hz',line,re.I) for line in files['TRAIN']['header']):raise ValueError('Missing explicit distributed 100 Hz evidence')
    previous=registry_metadata().loc[name].to_dict()
    previous={k:None if pd.isna(v) else v.item() if hasattr(v,'item') else v for k,v in previous.items()}
    backup=backup_root/revision/name;backup.mkdir(parents=True,exist_ok=False)
    for path in [metadata_path,manifest_path]:
        if path.exists():shutil.copy2(path,backup/path.name)
    dump(backup/'previous-registry-metadata.json',previous)
    channel_path=folder/'channels.txt';names=[]
    if channel_path.exists():
        import ast
        text=channel_path.read_text().strip()
        try:
            parsed=ast.literal_eval(text)
            if isinstance(parsed,(list,tuple)):names=list(parsed)
            else:names=[s.strip().strip("'\"") for s in re.split('[,\n]',text) if s.strip()]
        except (ValueError,SyntaxError):
            names=[s.strip().strip("'\"") for s in re.split('[,\n]',text) if s.strip()]
    if names and len(names)!=spec['channels']:raise ValueError('Channel sidecar count disagrees with local arrays')
    correction=dict(id=revision,kind='metadata_only',signals_rewritten=False,resampling_performed=False,
        fields=dict(length=dict(previous_registry=previous['length'],current=spec['points'])),
        evidence='Actual numeric field counts and @seriesLength in both local files',backup=str(backup))
    if name=='FingerMovements':correction['fields']['frequency']=dict(previous_registry=previous['frequency'],current=100,evidence='Distributed TRAIN comments: 500 ms, downsampled at 100 Hz, 50 observations')
    new=copy.deepcopy(old)
    new.update(schema_version=1,name=name,metadata_correction_revision=revision,change_history=[*new.get('change_history',[]),correction],
        shapes={s.lower():files[s]['shape'] for s in files},channel_count=spec['channels'],channel_names=names or None,
        timepoints=spec['points'],samples_per_case=spec['points'],frequency=spec['frequency'],sampling_frequency_hz=spec['frequency'],
        sampling_frequency_evidence='Explicit distributed source comments' if spec['frequency_verified'] else 'Retained paper/registry value; local .ts headers do not independently establish the sampling rate',
        sampling_frequency_verified_from_local_files=spec['frequency_verified'],class_distributions={s.lower():files[s]['class_counts'] for s in files},
        labels=sorted(set().union(*(set(r['class_counts']) for r in files.values()))),
        units=new.get('units'),numeric_scale_note='No scaling or numerical changes performed; physical signal units are not established by this metadata correction.',
        case_order='unchanged',split_membership='unchanged',previous_registry_metadata=previous,
        local_signal_files={s:{k:v for k,v in r.items() if k!='header'} for s,r in files.items()})
    if name=='Alzheimers':
        new['local_variant_note']='Headers identify Alzheimers_short with 15000 points. Whether this reflects shorter windows or a different sampling rate requires source confirmation; no resampling inferred.'
        new['window_seconds']=None
    else:
        new['window_seconds']=0.5;new['original_acquisition_frequency_hz']=1000
        new['acquisition_evidence']='Distributed source comments describe 1000 Hz acquisition and subsequent 100 Hz downsampling.'
    temp=metadata_path.with_suffix('.json.tmp');dump(temp,new);temp.replace(metadata_path)
    artifacts={}
    for path in folder.iterdir():
        if not path.is_file() or path==manifest_path:continue
        match=next((r for s,r in files.items() if path.name==f'{name}_{s}.ts'),None)
        artifacts[path.name]=dict(sha256=match['sha256'] if match else sha(path),bytes=path.stat().st_size)
    result=dict(name=name,revision=revision,status='metadata corrected; signals unchanged',correction=correction,
        validation=dict(source_headers_and_field_counts_verified=True,case_counts_verified=True,class_counts_unchanged=True,signals_rewritten=False),artifacts=artifacts)
    temp=manifest_path.with_suffix('.json.tmp');dump(temp,result);temp.replace(manifest_path)
    for split,record in files.items():
        stat=(folder/f'{name}_{split}.ts').stat()
        if (stat.st_size,stat.st_mtime_ns)!=(record['bytes'],record['mtime_ns']):raise ValueError('Signal changed unexpectedly')
    print(f'{name}: metadata corrected to {spec["points"]} points; frequency {spec["frequency"]} Hz; signal files unchanged',flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('D:/Data/EEG'))
    parser.add_argument('--backup-root',type=Path,default=Path('D:/Data/EEG_Backups'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.apply:print(json.dumps(SPECS,indent=2));return
    revision=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-metadata'
    results=[correct(args.root,args.backup_root,name,revision) for name in SPECS]
    dump(Path(__file__).parents[1]/'docs/metadata-corrections-results.json',dict(revision=revision,datasets=results))


if __name__=='__main__':main()
