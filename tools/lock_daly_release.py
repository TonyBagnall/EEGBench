"""Pin Daly's original BIDS metadata and annex identities before EEG retrieval."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump

COMMIT='f704b13bed4383af66b6aef93faa18aeb336c0ca'
ROOT=Path(__file__).resolve().parents[1]


def lock(cache=Path('D:/Data/EEGSources/Daly2020')):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    tree_url=f'https://api.github.com/repos/OpenNeuroDatasets/ds002720/git/trees/{COMMIT}?recursive=1'
    tree_path=cache/'original-release-tree.json';fetch(tree_url,tree_path)
    tree=json.loads(tree_path.read_text(encoding='utf-8'))
    if tree.get('truncated'):raise ValueError('Incomplete source tree')
    by={e['path']:e for e in tree['tree'] if e['type']=='blob'}
    p=cache/'original-metadata-repository.zip';fetch('https://codeload.github.com/OpenNeuroDatasets/ds002720/zip/'+COMMIT,p)
    files=[];skipped=[]
    with zipfile.ZipFile(p) as z:
        prefix=z.namelist()[0]
        for name,e in by.items():
            b=z.read(prefix+name)
            if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=e['sha']:raise ValueError('Original Git blob mismatch '+name)
            if name.startswith(('code/','.')) or e['mode']=='120000':continue
            f=(cache/name).resolve()
            if not f.is_relative_to(cache.resolve()):raise ValueError('Unsafe BIDS path')
            f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
            files.append(dict(name=name,url=f'https://raw.githubusercontent.com/OpenNeuroDatasets/ds002720/{COMMIT}/{name}',bytes=len(b),checksum='sha256:'+hashlib.sha256(b).hexdigest(),git_blob_sha1=e['sha']))
        for name,e in by.items():
            if not name.endswith('_eeg.edf'):continue
            if name.endswith('_task-run1_eeg.edf'):
                skipped.append(dict(name=name,reason='Original calibration run1, excluded consistently even when events have1/2 labels'));continue
            events=name.replace('_eeg.edf','_events.tsv');rows=list(csv.DictReader(io.StringIO(z.read(prefix+events).decode()),delimiter='\t'))
            if not any(row.get('trial_type') in ['1','2'] for row in rows):
                skipped.append(dict(name=name,reason='No labelled1/2 events in original events.tsv'));continue
            pointer=z.read(prefix+name).decode();m=re.search(r'(SHA256|MD5)E-s(\d+)--([0-9a-f]+)\.edf',pointer)
            if not m or len(m[3])!= {'SHA256':64,'MD5':32}[m[1]]:raise ValueError('Unknown original annex key '+name)
            files.append(dict(name=name,url='https://s3.amazonaws.com/openneuro.org/ds002720/'+name,bytes=int(m[2]),checksum=m[1].lower()+':'+m[3],git_annex_pointer=pointer,git_blob_sha1=e['sha']))
    evidence=ROOT/'docs/source-evidence/mi-to-30'
    dump(evidence/'daly-original-files.json',files);dump(evidence/'daly-excluded-empty-event-recordings.json',skipped)
    (evidence/'daly-original-readme.txt').write_bytes((cache/'README').read_bytes())
    print(dict(pinned_files=len(files),edf=sum(f['name'].endswith('.edf') for f in files),source_GB=sum(f['bytes'] for f in files)/1e9,excluded_empty_event_recordings=len(skipped)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources/Daly2020'));lock(p.parse_args().cache)
