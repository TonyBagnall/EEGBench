"""Download original OSF Track4 versions for ImaginedGrasps, separate cache."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump

ROOT=Path(__file__).resolve().parents[1]


def download(root=Path('D:/Data/EEGSources/BCIComp2020UpperLimb'),pilot=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'docs/imagined-grasps-source-lock.json').read_text(encoding='utf-8'))
    for name,url in {'original-osf-project.json':'https://api.osf.io/v2/nodes/pq7vb/',
        'original-osf-licence.json':'https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/',
        'moabb-upper-limb.py':f'https://raw.githubusercontent.com/NeuroTechX/moabb/{lock["moabb_revision"]}/moabb/datasets/bcicomp2020_upper_limb.py'}.items():
        if not (root/name).exists():fetch(url,root/name)
    project=json.loads((root/'original-osf-project.json').read_text(encoding='utf-8'));licence=json.loads((root/'original-osf-licence.json').read_text(encoding='utf-8'))
    if project['data']['relationships']['license']['data']['id']!='563c1cf88c5e4a3877f9e96a' or licence['data']['attributes']['url']!='https://creativecommons.org/licenses/by/4.0/legalcode':raise ValueError('Original data licence not established')
    files=[f for f in lock['files'] if not pilot or f['subject_id'] in [None,'01']]
    def one(f):
        path=(root/f['name']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Unsafe source path')
        fetch(f['url'],path,'sha256:'+f['sha256'],f['bytes']);print('Verified '+f['name'],flush=True);return dict(f,checksum='sha256:'+f['sha256'])
    with ThreadPoolExecutor(3) as pool:files=list(pool.map(one,files))
    receipt=dict(dataset=lock['dataset'],source_record_id='OSF pq7vb Track4',source_revision='OSF file IDs/versions/SHA256 in imagined-grasps-source-lock.json',licence=lock['licence'],files=files,pilot=pilot)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',lock);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/BCIComp2020UpperLimb'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.root,a.pilot)
