"""Download the original CC BY4.0 Kueper movement dataset into a source cache."""
import argparse
import json
from pathlib import Path
import shutil
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]


def download(root=Path('D:/Data/EEGSources/Kueper2024')):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'docs/arm-coordination-source-lock.json').read_text())
    evidence=ROOT/'docs/source-evidence/kueper-zenodo-10229480.json'
    if sha(evidence)!=lock['licence_evidence_sha256'] or json.loads(evidence.read_text())['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Unverified original data licence')
    files=[]
    for entry in lock['files']:
        path=root/entry['name'];print(f'Downloading {entry["name"]}: {entry["bytes"]/1e9:.3f}GB',flush=True)
        fetch(entry['url'],path,entry['checksum'],entry['bytes']);files.append(dict(entry,sha256=sha(path)))
    shutil.copy2(evidence,root/'original-zenodo-record.json')
    fetch('https://raw.githubusercontent.com/NeuroTechX/moabb/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/kueper2024.py',root/'moabb-kueper2024.py')
    receipt=dict(dataset='Kueper2024',source_record_id=lock['source_record_id'],source_revision=lock['source_revision'],licence=lock['licence'],files=files)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',lock)
    print('Source checksum verified',flush=True);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/Kueper2024'));a=p.parse_args();download(a.root)
