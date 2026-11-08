"""Download version/hash-pinned original competition Track5 data separately."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import shutil
import urllib.request
import ssl
import certifi
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'docs/walking-targets-source-lock.json'

def download(root=Path('D:/Data/EEGSources/WalkingERP'),pilot=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);lock=json.loads(LOCK.read_text())
    if lock['licence']!='CC-BY-4.0':raise ValueError('Unreviewed licence')
    sources={
        'original-osf-project.json':'https://api.osf.io/v2/nodes/pq7vb/',
        'original-osf-licence.json':'https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/',
        'moabb-walking-erp.py':f'https://raw.githubusercontent.com/NeuroTechX/moabb/{lock["moabb_revision"]}/moabb/datasets/bcicomp2020_walking_erp.py'}
    for name,url in sources.items():
        if not (root/name).exists():fetch(url,root/name)
    project=json.loads((root/'original-osf-project.json').read_text())
    licence=json.loads((root/'original-osf-licence.json').read_text())
    if project['data']['relationships']['license']['data']['id']!='563c1cf88c5e4a3877f9e96a' or licence['data']['attributes']['url']!='https://creativecommons.org/licenses/by/4.0/legalcode':raise ValueError('Original data licence changed/unverified')
    chosen=[f for f in lock['files'] if not pilot or f['subject_id'] in [None,'01']]
    def one(f):
        path=(root/f['name']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Unsafe source path')
        fetch(f['url'],path,'sha256:'+f['sha256'],f['bytes'])
        return dict(f,checksum='sha256:'+f['sha256'])
    print(f'Downloading {len(chosen)} verified files, {sum(f["bytes"] for f in chosen)/1e6:.1f} MB',flush=True)
    with ThreadPoolExecutor(4) as pool:
        files=[]
        for i,f in enumerate(pool.map(one,chosen),1):
            files.append(f);print(f'{i}/{len(chosen)}: {f["name"]}',flush=True)
    receipt=dict(dataset=lock['dataset'],source_record_id='OSF pq7vb Track5',source_revision='OSF versions and SHA256 values in walking-targets-source-lock.json',licence=lock['licence'],files=files)
    dump(root/('pilot-download-receipt.json' if pilot else 'download-receipt.json'),receipt);dump(root/'source-record.json',lock)
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',action='store_true');p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/WalkingERP'));a=p.parse_args();download(a.root,a.pilot)
