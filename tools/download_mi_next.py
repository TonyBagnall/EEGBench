"""Checksum-pinned original Batista/Polo/Leeuwis sources; pilot before cohort."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]
REVISION='bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'
CONFIG={
    'batista':dict(source='Batista2022',record=7664069,pilot=['sub-01.zip','sub-p03.zip']),
    'polo':dict(source='PoloHortiguela2025',record=14672334,pilot=['B01_S1_STATIC.zip','B06_S1_STATIC.zip']),
    'leeuwis':dict(source='Leeuwis2021',record=None),
}


def leeuwis_map(path):
    """Read the pinned file-ID literal, without executing downloaded loader code."""
    tree=ast.parse(Path(path).read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_FILE_IDS' for t in node.targets):return ast.literal_eval(node.value)
    raise ValueError('Missing original subject/file-ID mapping')


def download(key,cache_root=Path('D:/Data/EEGSources'),pilot=False):
    conf=CONFIG[key];root=Path(cache_root)/conf['source'];root.mkdir(parents=True,exist_ok=True)
    evidence=ROOT/'docs/source-evidence/motor-imagery-survey'/(conf['source']+('-roadmap' if key=='leeuwis' else '')+'.json')
    record=json.loads(evidence.read_text(encoding='utf-8'));files=[]
    loader_name={'batista':'batista2022','polo':'polohortiguela2025','leeuwis':'leeuwis2021'}[key]
    loader=root/('moabb-'+loader_name+'.py')
    fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{REVISION}/moabb/datasets/{loader_name}.py',loader)
    if key=='leeuwis':
        v=record['data']['latestVersion']
        if (v['versionNumber'],v['versionMinorNumber'],v['id'])!=(1,0,3733) or 'https://creativecommons.org/licenses/by/4.0/' not in v['termsOfUse']:raise ValueError('Unverified original Dataverse version/licence')
        mapping=leeuwis_map(loader);selected=set(mapping[min(mapping)]+mapping[max(mapping)])
        for item in v['files']:
            f=item['dataFile'];name=(item.get('directoryLabel','')+'/'+f['filename']).lstrip('/')
            if item.get('restricted'):raise ValueError('Restricted source file')
            is_eeg=f['id'] in {i for ids in mapping.values() for i in ids}
            if pilot and is_eeg and f['id'] not in selected:continue
            files.append(dict(name=name,url=f'https://dataverse.nl/api/access/datafile/{f["id"]}',bytes=f['filesize'],checksum=f['checksum']['type'].lower().replace('-','')+':'+f['checksum']['value'],datafile_id=f['id'],is_eeg=is_eeg))
        source_record_id='doi:10.34894/Z7ZVOD';revision='DataverseNL10.34894/Z7ZVOD v1.0; versionID3733'
    else:
        if record['id']!=conf['record'] or record['metadata']['license']['id']!='cc-by-4.0':raise ValueError('Unverified original Zenodo version/licence')
        for f in sorted(record['files'],key=lambda f:f['key']):
            if pilot and f['key'] not in conf['pilot']:continue
            files.append(dict(name=f['key'],url=f['links']['self'],bytes=f['size'],checksum=f['checksum']))
        source_record_id=conf['record'];revision=f'Zenodo{source_record_id} v1'
    def one(f):
        path=(root/f['name']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Unsafe original path')
        fetch(f['url'],path,f['checksum'],f['bytes']);print('Verified '+f['name'],flush=True)
        return dict(f,sha256=sha(path))
    with ThreadPoolExecutor(2) as pool:files=list(pool.map(one,files))
    shutil.copy2(evidence,root/'original-source-record.json')
    receipt=dict(source_record_id=source_record_id,source_revision=revision,licence='CC-BY-4.0',pilot=pilot,evidence_sha256=sha(evidence),files=files,moabb_revision=REVISION)
    dump(root/('download-receipt-pilot.json' if pilot else 'download-receipt-full.json'),receipt)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',receipt)
    dump(ROOT/'docs'/(key+'-mi-source-lock.json'),receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',choices=CONFIG);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.dataset,a.cache_root,a.pilot)
