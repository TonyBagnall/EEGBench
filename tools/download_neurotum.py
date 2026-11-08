"""Download original NeuroTUM EEG/marker files to a configurable temporary cache."""
import argparse
import json
from pathlib import Path
import shutil
import requests
from tools.download_compact_imagery import sha

ROOT=Path(__file__).resolve().parents[1]


def download(cache_root=Path('D:/Data/EEGSources'),pilot=False):
    root=Path(cache_root)/'NeuroTUMBCI2025';root.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(root).free<4_000_000_000:raise OSError('Need at least4GB free before starting this small source')
    r=requests.get('https://zenodo.org/api/records/18087806',timeout=40);r.raise_for_status();d=r.json()
    if d['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Original data licence changed')
    evidence=root/'original-record.json';evidence.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    selected=[f for f in d['files'] if f['key'].endswith('_mapping.yaml') or f['key'].endswith('_data.xdf')]
    if pilot:selected=[f for f in selected if f['key'].endswith('_mapping.yaml') or f['key'] in ['P1_S1_data.xdf','P1_S5_data.xdf','P2_S1_data.xdf','P2_S3_data.xdf']]
    files=[]
    for f in sorted(selected,key=lambda f:f['key']):
        path=root/f['key'];md5=f['checksum'].split(':')[1]
        valid=path.exists() and path.stat().st_size==f['size'] and sha(path,'md5')==md5
        if not valid:
            part=path.with_name(path.name+'.part');response=requests.get(f['links']['self'],stream=True,timeout=(30,90));response.raise_for_status()
            with part.open('wb') as target:
                for block in response.iter_content(1024*1024):target.write(block)
            if part.stat().st_size!=f['size'] or sha(part,'md5')!=md5:raise ValueError('Original publisher checksum/size mismatch')
            part.replace(path)
        files.append(dict(name=f['key'],url=f['links']['self'],bytes=f['size'],checksum=f['checksum'],sha256=sha(path)))
        print('Verified',f['key'],f['size'],flush=True)
    receipt=dict(dataset='NeuroTUMBCI2025',source_record_id=18087806,source_revision='Zenodo18087806 v1.0.0',licence='CC-BY-4.0',
        original_source_url='https://zenodo.org/records/18087806',original_evidence_sha256=sha(evidence),files=files,pilot=pilot,
        excluded='Separate ASR calibration files are not labelled task recordings; not downloaded')
    for p in [root/'download-receipt.json',root/'source-record.json',ROOT/'docs/neurotum-source-lock.json']:p.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.cache_root,a.pilot)
