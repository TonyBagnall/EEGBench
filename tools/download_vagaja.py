"""Download the original, fixed Zenodo v1 Vagaja2023 release (CC BY4.0)."""
import argparse
import json
from pathlib import Path
import shutil

from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'


def download(root=Path('D:/Data/EEGSources/Vagaja2023')):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    evidence = ROOT/'docs/source-evidence/motor-imagery-survey/Vagaja2023-roadmap.json'
    record = json.loads(evidence.read_text(encoding='utf-8'))
    if str(record['id']) != '8086086' or record['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Unexpected original source revision/licence')
    files = []
    for f in record['files']:
        if f['key'] != 'GROUPS.zip' or f['checksum'] != 'md5:e89017e33a730ffa37f5a1a02acfc74f':
            raise ValueError('Changed pinned source file')
        url = f['links']['self']
        path = root/f['key']
        fetch(url, path, f['checksum'], f['size'])
        files.append(dict(name=f['key'], url=url, bytes=f['size'], checksum=f['checksum'], sha256=sha(path)))
    shutil.copy2(evidence, root/'original-zenodo-record.json')
    fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{REVISION}/moabb/datasets/vagaja2023.py', root/'moabb-vagaja2023.py')
    lock = dict(source_record_id=8086086, source_revision='Zenodo 8086086 v1', licence='CC-BY-4.0',
                original_source_url='https://zenodo.org/records/8086086', doi='10.5281/zenodo.8086086',
                evidence_sha256=sha(evidence), files=files)
    dump(root/'source-record.json', lock)
    dump(root/'download-receipt.json', lock)
    print('Verified Vagaja2023 original ZIP and source licence', flush=True)
    return lock


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('D:/Data/EEGSources/Vagaja2023'))
    download(p.parse_args().root)
