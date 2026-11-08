"""Pinned native PRED+CT mirrors: clinical EEG sources, not analysis derivatives.

Data rights: original PRED+CT downloads page grants PDDL v1.0 to database and
contents; each mirror root LICENSE.txt agrees. No dataset code is executed.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import urllib.request

import certifi

from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'docs/predct-source-lock.json'


def bootstrap():
    """Freeze metadata already inspected during EEG-Bench source review."""
    source=ROOT/'.openeegbench/eth-eeg-review/hf';items=[]
    for name,accession in [('Cavanagh2018b','d002'),('Singh2020','d011'),('Gruendler2009','d008')]:
        metadata=json.loads((source/f'{name}.json').read_text())
        tree=json.loads((source/f'{name}-file-tree.json').read_text())
        selected=[]
        for f in tree:
            if f['type']!='file':continue
            path=f['path']
            if path=='.gitattributes' or path.endswith('.parquet'):continue
            if name=='Singh2020' and not (path.startswith('raw_data/') or '/' not in path or path in ['scripts/Patients_MS.xlsx','scripts/Step1_EEG_Pedaling_PreProcess.m']):continue
            selected.append(dict(path=path,bytes=f['size'],checksum=('sha256:'+f['lfs']['oid']) if f.get('lfs') else 'gitblob:'+f['oid'],
                url=f'https://huggingface.co/datasets/jalauer/{name}/resolve/{metadata["sha"]}/'+urllib.parse.quote(path)))
        items.append(dict(dataset=name,predct_accession=accession,repo='jalauer/'+name,revision=metadata['sha'],
            licence='PDDL-1.0',original_licence_url='https://predict.cs.unm.edu/downloads.php',files=selected))
    dump(LOCK,items)
    return items


def download(root=Path('D:/Data/EEGSources/PREDCT'),pilot=False):
    lock=json.loads(LOCK.read_text()) if LOCK.exists() else bootstrap()
    root=Path(root);receipts=[]
    for item in sorted(lock,key=lambda x:sum(f['bytes'] for f in x['files'])):
        folder=root/item['dataset'];folder.mkdir(parents=True,exist_ok=True)
        chosen=item['files']
        if pilot:
            if item['dataset']=='Cavanagh2018b':signals=[f for f in chosen if f['path'].startswith('data/') and f['path'].endswith('.mat')][:1]
            elif item['dataset']=='Gruendler2009':signals=sorted([f for f in chosen if f['path'].endswith('.cnt')],key=lambda f:f['bytes'])[:1]
            else:
                first=next(f['path'].rsplit('.',1)[0] for f in chosen if f['path'].endswith('.vhdr'))
                signals=[f for f in chosen if f['path'].rsplit('.',1)[0]==first]
            small=[f for f in chosen if f['bytes']<250000 and not f['path'].startswith('raw_data/')]
            chosen=list({f['path']:f for f in small+signals}.values())
        print(f"Starting {'pilot' if pilot else 'native download'} {item['dataset']}: {sum(f['bytes'] for f in chosen)/1e6:.1f} MB",flush=True)
        def one(f):
            path=(folder/f['path']).resolve()
            if not path.is_relative_to(folder.resolve()):raise ValueError('Unsafe source path')
            fetch(f['url'],path,f['checksum'],f['bytes'])
            return dict(f,sha256=sha(path))
        files=[]
        with ThreadPoolExecutor(4) as executor:
            for i,f in enumerate(executor.map(one,chosen),1):
                files.append(f)
                if i%10==0:print(f"{item['dataset']}: {i}/{len(chosen)} files verified",flush=True)
        dump(folder/('pilot-receipt.json' if pilot else 'download-receipt.json'),dict(item,files=files,downloaded_bytes=sum(f['bytes'] for f in files)))
        receipts.append(dict(dataset=item['dataset'],files=len(files),bytes=sum(f['bytes'] for f in files),pilot=pilot))
        print('Completed',item['dataset'],flush=True)
    dump(ROOT/'docs'/('predct-pilot-downloads.json' if pilot else 'predct-download-results.json'),receipts)
    return receipts


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',action='store_true');p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/PREDCT'));a=p.parse_args();download(a.root,a.pilot)
