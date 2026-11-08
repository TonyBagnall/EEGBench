"""Publisher-verified original MIMED, MOVING and Zhang source retrieval."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'mimed': ('MIMED2024', 'https://data.mendeley.com/datasets/zs25xxjkm9/3'),
    'moving': ('MOVING2024', 'https://zenodo.org/records/12804784'),
    'zhang': ('Zhang2017', 'https://doi.org/10.6084/m9.figshare.5579461.v1'),
}


def sha(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def download(key, cache_root=Path('D:/Data/EEGSources')):
    name, url = SOURCES[key]
    root = Path(cache_root) / name
    root.mkdir(parents=True, exist_ok=True)
    evidence = ROOT / 'docs/source-evidence/motor-imagery-survey'
    if key == 'mimed':
        u = 'https://data.mendeley.com/public-files/datasets/zs25xxjkm9/files/3dc41eb1-8999-4e0d-a77a-0394b53ba04e/file_downloaded'
        # Pinned object ETag verified by HEAD during original-host inspection.
        files = [dict(name='Motor Imagery.zip', url=u, bytes=19526072, md5='82726a38955c7ca8041018010fd33a30')]
        page = requests.get(url, timeout=40); page.raise_for_status()
        if 'CC BY 4.0' not in page.text: raise ValueError('Original data licence not found')
        (root / 'original-release.html').write_text(page.text, encoding='utf-8')
        revision = 'Mendeley zs25xxjkm9 v3; imagery object cZvz73BnHgnl2VH81tQm6WDgyOy0O3uA'
    else:
        source = json.loads((evidence / (name + '.json')).read_text(encoding='utf-8'))
        if key == 'moving':
            if source['metadata']['license']['id'] != 'cc-by-4.0': raise ValueError('Unexpected licence')
            files = [dict(name=f['key'], url=f['links']['self'], bytes=f['size'], md5=f['checksum'].split(':')[1]) for f in source['files'] if f['key'] == 'edf.rar']
            revision = 'Zenodo 12804784 v1'
        else:
            if source['license']['name'] != 'CC BY 4.0': raise ValueError('Unexpected licence')
            files = [dict(name=f['name'], url=f['download_url'], bytes=f['size'], md5=f['computed_md5']) for f in source['files']]
            revision = 'Figshare 5579461 v1'
        shutil.copy2(evidence / (name + '.json'), root / 'original-record.json')
    for f in files:
        path = root / f['name']
        valid = path.exists() and path.stat().st_size == f['bytes'] and sha(path, 'md5') == f['md5']
        if not valid:
            part = path.with_name(path.name + '.part')
            response = requests.get(f['url'], stream=True, timeout=(30, 120)); response.raise_for_status()
            total = 0
            with part.open('wb') as target:
                for block in response.iter_content(4 * 1024 * 1024):
                    target.write(block); total += len(block)
                    if total // 100000000 != (total-len(block)) // 100000000: print(name, total, '/', f['bytes'], flush=True)
            if part.stat().st_size != f['bytes'] or sha(part, 'md5') != f['md5']: raise ValueError('Publisher checksum/size mismatch')
            part.replace(path)
        f['sha256'] = sha(path)
        print('Verified', name, f['name'], f['bytes'], flush=True)
    receipt = dict(dataset=name, source_record_id=name, source_url=url, source_revision=revision, licence='CC-BY-4.0', files=files)
    for filename in ['download-receipt.json', 'source-record.json']:
        (root / filename).write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    (ROOT / 'docs' / (key+'-imagery-source-lock.json')).write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('datasets', nargs='+', choices=list(SOURCES))
    p.add_argument('--cache-root', type=Path, default=Path('D:/Data/EEGSources'))
    args=p.parse_args()
    for key in args.datasets: download(key, args.cache_root)
