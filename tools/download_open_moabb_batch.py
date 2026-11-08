"""Cache the next original-host-verified open MOABB sources, smallest transfer first.

This only downloads native archives; it does not convert or register problems.
Pinned record IDs, file membership, byte counts and publisher checksums live in
docs/open-moabb-download-source-lock.json. Existing valid files are reused.
Run from repo root: python -m tools.download_open_moabb_batch
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch

ROOT = Path(__file__).resolve().parents[1]


def download(output=Path('D:/Data/EEGSources'), datasets=None):
    lock = json.loads((ROOT / 'docs/open-moabb-download-source-lock.json').read_text())
    if datasets:
        if set(datasets) - {item['dataset'] for item in lock}:
            raise ValueError('Unknown dataset name')
        lock = [item for item in lock if item['dataset'] in datasets]
    lock.sort(key=lambda item: sum(f['bytes'] for f in item['files']))
    results = []
    for item in lock:
        if item['license']['id'] != 'cc-by-4.0':
            raise ValueError('Batch only permits the reviewed CC BY 4.0 source records')
        folder = Path(output) / item['dataset']; folder.mkdir(parents=True, exist_ok=True)
        print(f"Starting {item['dataset']}: {sum(f['bytes'] for f in item['files'])/1e6:.1f} MB", flush=True)
        fetch(item['metadata_url'], folder / 'source-record.json')
        record = json.loads((folder / 'source-record.json').read_text(encoding='utf-8'))
        if record['id'] != item['record_id'] or record['metadata']['license']['id'] != 'cc-by-4.0':
            raise ValueError('Pinned source identity/licence mismatch')
        actual = {f['key']: f for f in record['files']}
        for f in item['files']:
            if Path(f['name']).name != f['name']:
                raise ValueError('Source filename must be a basename')
            if actual[f['name']]['checksum'] != f['checksum'] or actual[f['name']]['size'] != f['bytes']:
                raise ValueError('Publisher source files changed since metadata review')

        def one(f):
            path = fetch(f['url'], folder / f['name'], f['checksum'], f['bytes'])
            print(f"Verified {item['dataset']}/{f['name']}", flush=True)
            return dict(f, sha256=sha(path))

        files = list(ThreadPoolExecutor(4).map(one, item['files']))
        receipt = dict(dataset=item['dataset'], source_record_id=item['record_id'],
                       licence='CC-BY-4.0', source_doi=item['doi'], output=str(folder),
                       status='Native sources downloaded and publisher checksums verified; conversion pending',
                       files=files, downloaded_bytes=sum(f['bytes'] for f in files))
        dump(folder / 'download-receipt.json', receipt)
        results.append(receipt)
        dump(ROOT / 'docs/open-moabb-download-results.json', results)
        print(f"Completed {item['dataset']}", flush=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('D:/Data/EEGSources'))
    parser.add_argument('--datasets', nargs='+')
    args = parser.parse_args()
    download(args.output, args.datasets)
