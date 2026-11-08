"""Verified individual imagery CSV retrieval; avoids the full execution archive."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import threading
import time
import requests

ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'^(S\d+)(R\d+)I([1-8])_(\d+(?:_\d+)?)\.csv$')
LOCAL=threading.local()


def lock():
    evidence=ROOT/'docs/source-evidence/motor-imagery-survey'
    snapshot=json.loads((evidence/'milimb-original-snapshot.json').read_text(encoding='utf-8'))
    if snapshot['licence']['short_name']!='CC BY 4.0':raise ValueError('Original licence not verified')
    inventory=json.loads((evidence/'milimb-all-files.json').read_text(encoding='utf-8'));files=[]
    for folder in sorted(inventory,key=lambda f:int(f['subject_folder'][1:])):
        for ordinal,item in enumerate(folder['files']):
            match=PATTERN.fullmatch(item['filename'])
            if not match:continue
            if match[1]!=folder['subject_folder']:raise ValueError('File/folder participant mismatch')
            f=item['content_details']
            files.append(dict(name=folder['subject_folder']+'/'+item['filename'],bytes=f['size'],sha256=f['sha256_hash'],url=f['download_url'],
                participant_id=match[1],run_id=match[2],source_label=match[3],trial_suffix=match[4],source_listing_index=ordinal,source_file_id=item['id']))
    for item in json.loads((evidence/'milimb-file-list.json').read_text(encoding='utf-8')):
        f=item['content_details'];files.append(dict(name=item['filename'],bytes=f['size'],sha256=f['sha256_hash'],url=f['download_url']))
    result=dict(dataset='MILimbEEG imagery only',source_record_id='x8psbz3f6x',source_revision='Mendeley x8psbz3f6x v2',licence='CC-BY-4.0',
        original_source_url='https://data.mendeley.com/datasets/x8psbz3f6x/2',files=files,
        selection='All native I1..I8 imagery/baseline/rest CSVs; no M motor-execution CSVs; root sensor figure/encoding/demographics retained')
    (ROOT/'docs/milimb-source-lock.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def verified(path,f):
    if not path.exists() or path.stat().st_size!=f['bytes']:return False
    return hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']


def download(cache_root=Path('D:/Data/EEGSources'),pilot=False,workers=8):
    source=lock();cache=Path(cache_root)/'MILimbEEG';cache.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(cache).free<4_000_000_000:raise OSError('Keep4GB free on destination before retrieval')
    files=[f for f in source['files'] if not pilot or '/' not in f['name'] or f['participant_id'] in ['S1','S60']]
    def one(f):
        path=cache/f['name'];path.parent.mkdir(parents=True,exist_ok=True)
        if verified(path,f):return f
        if not hasattr(LOCAL,'session'):LOCAL.session=requests.Session()
        for attempt in range(4):
            try:
                response=LOCAL.session.get(f['url'],timeout=(20,60));response.raise_for_status()
                if len(response.content)!=f['bytes'] or hashlib.sha256(response.content).hexdigest()!=f['sha256']:raise ValueError('Publisher byte/hash mismatch '+f['name'])
                part=path.with_name(path.name+'.part');part.write_bytes(response.content);part.replace(path);return f
            except Exception:
                if attempt==3:raise
                time.sleep(1+attempt)
    with ThreadPoolExecutor(workers) as pool:
        for i,_ in enumerate(pool.map(one,files),1):
            if i%100==0 or i==len(files):print('MILimb verified',i,'/',len(files),flush=True)
    receipt=dict(source,files=files,pilot=pilot)
    for path in [cache/'download-receipt.json',cache/'source-record.json']:path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(ROOT/'docs/source-evidence/motor-imagery-survey/milimb-original-snapshot.json',cache/'original-record.json')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--pilot',action='store_true');p.add_argument('--workers',type=int,default=8);a=p.parse_args();download(a.cache_root,a.pilot,a.workers)
