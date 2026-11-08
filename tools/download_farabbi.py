"""Download publisher-checksummed original Farabbi2020 data separately."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]


def download(root=Path('D:/Data/EEGSources/Farabbi2020'),pilot=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'docs/imagined-hands-robot-source-lock.json').read_text(encoding='utf-8'))
    evidence=ROOT/'docs/source-evidence/farabbi-zenodo-original.json'
    if sha(evidence)!=lock['evidence_sha256'] or json.loads(evidence.read_text(encoding='utf-8'))['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Unverified original data licence')
    files=[f for f in lock['files'] if not pilot or f['name'] in ['01.zip','12.zip','chanlocs.locs']]
    def one(f):
        path=root/f['name'];fetch(f['url'],path,f['checksum'],f['bytes']);print('Verified '+f['name'],flush=True)
        return dict(f,sha256=sha(path))
    with ThreadPoolExecutor(2) as pool:files=list(pool.map(one,files))
    shutil.copy2(evidence,root/'original-zenodo-record.json')
    fetch('https://raw.githubusercontent.com/NeuroTechX/moabb/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/farabbi2020.py',root/'moabb-farabbi2020.py')
    receipt=dict(dataset='Farabbi2020',source_record_id=lock['source_record_id'],source_revision=lock['source_revision'],licence=lock['licence'],files=files,pilot=pilot)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',lock);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/Farabbi2020'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.root,a.pilot)
