"""Original-source downloads for the final motor imagery additions, outside Git."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import hashlib
import zipfile
import xml.etree.ElementTree as ET

from tools.prepare_moabb import dump,sha
from tools.prepare_small_moabb import fetch
from tools.download_original_ranges import fetch_ranges

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/source-evidence/mi-to-30'
REVISION='bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'
CONFIG={'mibmpi':dict(source='MIBMPI2024',licence='CC-BY-NC-4.0',loader='mibmpi2024'),
        'cho':dict(source='Cho2017',licence='CC0-1.0',loader='gigadb'),
        'pan23':dict(source='Pan2023',licence='CC0-1.0',loader='pan2023'),
        'pan25':dict(source='Pan2025',licence='CC0-1.0',loader='pan2025'),
        'rozado':dict(source='Rozado2015',licence='CC0-1.0',loader='rozado2015'),
        'daly':dict(source='Daly2020',licence='CC-BY-4.0',loader='daly2020')}


def daly_files(pilot=False):
    files=json.loads((EVIDENCE/'daly-original-files.json').read_text(encoding='utf-8'))
    if pilot:
        files=[f for f in files if not f['name'].startswith('sub-') or f['name'].startswith(('sub-01/','sub-18/'))]
    return files,'OpenNeuro ds002720 v1.0.1; Git commit f704b13bed4383af66b6aef93faa18aeb336c0ca, original annex MD5/SHA256 identities verified then SHA256 recorded','ds002720'


def source_files(key,pilot=False):
    if key=='daly':return daly_files(pilot)
    if key in ['pan23','pan25','rozado']:
        rights=json.loads((EVIDENCE/(key+'-datacite.json')).read_text(encoding='utf-8'))['data']['attributes']['rightsList']
        if not any(r.get('rightsIdentifier')=='cc0-1.0' for r in rights):raise ValueError('Original registered data grant not verified')
        files=json.loads((EVIDENCE/(key+'-original-files.json')).read_text(encoding='utf-8'))
        if pilot:
            files=[f for f in files if f.get('subject') in (['01','14'] if key=='pan23' else ['01','10'])] if key!='rozado' else [f for f in files if f['name']=='userdata1.rar']
        doi={'pan23':'10.7910/DVN/251NOW','pan25':'10.7910/DVN/GH74ZG','rozado':'10.7910/DVN/28932'}[key]
        version=json.loads((EVIDENCE/(key+'-datacite.json')).read_text(encoding='utf-8'))['data']['attributes'].get('version')
        return files,'Harvard Dataverse '+doi+'; publisher DataCite metadata version '+str(version)+'; immutable numeric datafile IDs and recorded content hashes (dataset-version API unavailable)',doi
    if key=='mibmpi':
        d=json.loads((EVIDENCE/'mibmpi-original.json').read_text(encoding='utf-8'))
        description=d['metadata']['description'].lower()
        if 'cc by-nc 4.0' not in description:raise ValueError('Original description no longer establishes noncommercial data licence')
        files=[]
        for f in sorted(d['files'],key=lambda f:f['key']):
            if pilot and not f['key'].startswith(('D01_','D08_')):continue
            if not re.fullmatch(r'D0[1-8]_s[12](?:_labels\.mat|\.set)',f['key']):raise ValueError('Unrecognised source file')
            files.append(dict(name=f['key'],url=f['links']['self'],bytes=f['size'],checksum=f['checksum']))
        return files,'Zenodo13626922 v1; original description specifies CC BY-NC4.0',13626922
    rights=json.loads((EVIDENCE/'cho-datacite.json').read_text(encoding='utf-8'))['data']['attributes']['rightsList']
    if not any(r.get('rightsIdentifier')=='cc0-1.0' for r in rights):raise ValueError('Original publisher data grant not verified')
    tree=ET.fromstring((EVIDENCE/'cho-original-object-list.xml').read_bytes());ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'};files=[]
    prefix='live/pub/10.5524/100001_101000/100295/'
    for item in tree.findall('s:Contents',ns):
        path=item.findtext('s:Key',namespaces=ns);name=path.removeprefix(prefix)
        if pilot and name.startswith('mat_data/') and name not in ['mat_data/s01.mat','mat_data/s52.mat']:continue
        checksum=item.findtext('s:ETag',namespaces=ns).strip('"')
        size=int(item.findtext('s:Size',namespaces=ns))
        if re.fullmatch('[a-f0-9]{32}',checksum):digest='md5:'+checksum;evidence='Publisher-hosted object ETag, verified against actual downloaded MD5'
        elif re.fullmatch(r'[a-f0-9]{32}-\d+',checksum) and int(checksum.split('-')[1])==(size+5242879)//5242880:
            digest='s3-multipart-md5-5242880:'+checksum;evidence='Original multipart ETag; require actual MD5-of-part-MD5s using5MiB parts and exact part count to match, not a plain file MD5. If this hypothesis does not match downloaded content, stop for review.'
        else:raise ValueError('Opaque publisher ETag requires another source checksum')
        files.append(dict(name=name,url='https://s3.ap-northeast-1.wasabisys.com/gigadb-datasets/'+path,bytes=size,checksum=digest,checksum_evidence=evidence))
    return files,'GigaDB10.5524/100295 release2017-05-05; exact publisher object MD5/size pins',100295


def download(key,cache_root=Path('D:/Data/EEGSources'),pilot=False):
    conf=CONFIG[key];root=Path(cache_root)/conf['source'];root.mkdir(parents=True,exist_ok=True)
    files,revision,record_id=source_files(key,pilot)
    def one(f):
        p=(root/f['name']).resolve()
        if not p.is_relative_to(root.resolve()):raise ValueError('Unsafe original source path')
        if key=='cho' and f['name'].endswith('.mat'):fetch_ranges(f['url'],p,f['checksum'],f['bytes'])
        else:fetch(f['url'],p,f['checksum'],f['bytes'])
        print('Verified '+f['name'],flush=True)
        return dict(f,sha256=sha(p))
    with ThreadPoolExecutor(2) as pool:files=list(pool.map(one,files))
    for file in EVIDENCE.glob(key+'-*'):
        shutil.copy2(file,root/file.name)
    fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{REVISION}/moabb/datasets/{conf["loader"]}.py',root/('moabb-'+conf['loader']+'.py'))
    receipt=dict(dataset=conf['source'],licence=conf['licence'],source_record_id=record_id,source_revision=revision,moabb_revision=REVISION,pilot=pilot,files=files,
                 licence_evidence='Original Zenodo description, structured licence field absent' if key=='mibmpi' else 'Publisher DataCite rightsList plus original readme_100295 data grant' if key=='cho' else 'Original publisher-registered DataCite rightsList, CC0-1.0',
                 limitations='Commercial studies require permission; noncommercial research preparation only' if key=='mibmpi' else None)
    if key=='daly':receipt.update(licence_evidence='Original README: copyright University of Reading2018, CC BY4.0; dataset_description separately says CC0',limitations='Conflicting permissive original declarations retained; conservative attribution/CC BY4.0 treatment')
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',receipt);dump(root/('download-receipt-pilot.json' if pilot else 'download-receipt-full.json'),receipt)
    dump(ROOT/'docs'/(key+'-to-30-source-lock.json'),receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=CONFIG);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.dataset,a.cache_root,a.pilot)
