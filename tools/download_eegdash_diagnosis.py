"""Pin native OpenNeuro BIDS releases discovered through EEGDash; no corpus DSP."""
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

import requests
from tools.prepare_moabb import dump,sha
from tools.prepare_small_moabb import fetch

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/source-evidence/eegdash-diagnosis'
CONFIG={'auditory':dict(dataset='ds005048',eegdash='on005048',ref='1.0.1',commit='165a4d407983e5d7d42441ecc007caf6c98d3fad',pilot=['01','02','17','31','32','35']),
        'ucsd':dict(dataset='ds002778',eegdash='on002778',ref='1.0.5',commit='2890cbd8da62179735aae536a520008154630dd6',pilot=['hc1','hc33','pd3','pd28']),
        'psychosis1':dict(dataset='ds003944',eegdash='on003944',ref='1.0.1',commit='dcee4de6ada80b018ef8fe4f75463ee4b22cdcd4',pilot=['1448','2140A','2223','1824','2218']),
        'psychosis2':dict(dataset='ds003947',eegdash='on003947',ref='1.0.1',commit='8cbb08a80ccc1be499f2c435a8b04d43678dadc6',pilot=['2235A','2574A','2237A','2581A']),
        'iowa_rest':dict(dataset='ds004584',eegdash='on004584',ref='1.0.0',commit='261510fd9780d738a77fee52b906b3d56b69b74e',pilot=['001','100','101','149'])}


def blob_sha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def lock(key,cache_root=Path('D:/Data/EEGSources/EEGDash')):
    conf=CONFIG[key];ds=conf['dataset'];cache=Path(cache_root)/ds;cache.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
    tree_path=cache/'original-release-tree.json';fetch(f'https://api.github.com/repos/OpenNeuroDatasets/{ds}/git/trees/{conf["commit"]}?recursive=1',tree_path)
    tree=json.loads(tree_path.read_text(encoding='utf-8'))
    if tree.get('truncated'):raise ValueError('Incomplete original source tree')
    archive=cache/'original-metadata.zip';fetch(f'https://codeload.github.com/OpenNeuroDatasets/{ds}/zip/{conf["commit"]}',archive)
    files=[];native=[]
    with zipfile.ZipFile(archive) as z:
        prefix=z.namelist()[0]
        for entry in tree['tree']:
            if entry['type']!='blob':continue
            name=entry['path'];data=z.read(prefix+name)
            if blob_sha(data)!=entry['sha']:raise ValueError('Original Git blob differs '+name)
            if entry['mode']=='120000':
                if Path(name).suffix not in ['.fdt','.set','.bdf','.edf','.vhdr','.eeg','.vmrk']:continue
                pointer=data.decode();m=re.search(r'(SHA256|MD5)E-s(\d+)--([0-9a-f]+)\.[^/]+',pointer)
                if not m or len(m[3])!={'SHA256':64,'MD5':32}[m[1]]:raise ValueError('Unknown original annex key '+name)
                native.append(dict(name=name,url=f'https://s3.amazonaws.com/openneuro.org/{ds}/{name}',bytes=int(m[2]),checksum=m[1].lower()+':'+m[3],git_blob_sha1=entry['sha'],git_annex_pointer=pointer))
            else:
                if name.startswith(('.','code/')):continue
                target=(cache/name).resolve()
                if not target.is_relative_to(cache.resolve()):raise ValueError('Unsafe original source path')
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                files.append(dict(name=name,url=f'https://raw.githubusercontent.com/OpenNeuroDatasets/{ds}/{conf["commit"]}/{name}',bytes=len(data),checksum='sha256:'+hashlib.sha256(data).hexdigest(),git_blob_sha1=entry['sha']))
    description=json.loads((cache/'dataset_description.json').read_text(encoding='utf-8'))
    if description.get('License')!='CC0':raise ValueError('Original data licence needs separate review')
    for name in ['dataset_description.json','participants.tsv','participants.json','README','README.md','CHANGES']:
        if (cache/name).is_file():shutil.copy2(cache/name,EVIDENCE/(ds+'-'+name))
    record=dict(dataset=ds,eegdash_id=conf['eegdash'],original_ref=conf['ref'],original_commit=conf['commit'],licence='CC0-1.0',licence_evidence='Original pinned dataset_description.json License=CC0; original README retained for conflict review',
        source_doi=description.get('DatasetDOI'),source_revision=f'OpenNeuro {ds} v{conf["ref"]}, Git {conf["commit"]}',metadata_files=files,native_files=native,
        metadata_archive_sha256=sha(archive),source_urls=[f'https://openneuro.org/datasets/{ds}/versions/{conf["ref"]}',f'https://data.eegdash.org/api/eegdash/datasets/{conf["eegdash"]}'])
    dump(EVIDENCE/(ds+'-original-files.json'),record);dump(cache/'original-source-lock.json',record)
    return record


def download(key,cache_root=Path('D:/Data/EEGSources/EEGDash'),pilot=False):
    conf=CONFIG[key];cache=Path(cache_root)/conf['dataset'];record=lock(key,cache_root)
    selected=[]
    for f in record['native_files']:
        person=re.search(r'(?:^|/)sub-([^/]+)',f['name'])
        if pilot and (not person or person[1] not in conf['pilot']):continue
        selected.append(f)
    def one(f):
        p=cache/f['name'];fetch(f['url'],p,f['checksum'],f['bytes']);print('Verified',f['name'],flush=True);return dict(f,sha256=sha(p))
    with ThreadPoolExecutor(3) as pool:native=list(pool.map(one,selected))
    metadata=[dict(f,sha256=sha(cache/f['name'])) for f in record['metadata_files']]
    receipt=dict(dataset=record['dataset'],source_record_id=record['dataset'],source_revision=record['source_revision'],licence=record['licence'],pilot=pilot,eegdash_id=record['eegdash_id'],files=metadata+native,
        discovery='EEGDash catalogue; native original OpenNeuro release, not converted corpus',licence_evidence=record['licence_evidence'],source_urls=record['source_urls'])
    dump(cache/'download-receipt.json',receipt);dump(cache/'source-record.json',receipt);dump(cache/('download-receipt-pilot.json' if pilot else 'download-receipt-full.json'),receipt)
    dump(ROOT/'docs'/(record['dataset']+'-diagnosis-source-lock.json'),receipt)
    return receipt


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=CONFIG);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources/EEGDash'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.dataset,a.cache_root,a.pilot)
