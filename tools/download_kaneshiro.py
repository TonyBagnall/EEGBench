"""Verified original Stanford VisualCategories source files; never arrays in Git."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump,sha

ROOT=Path(__file__).resolve().parents[1]


def download(root=Path('D:/Data/EEGSources/Kaneshiro2015'),pilot=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'docs/visual-categories-source-lock.json').read_text())
    evidence=ROOT/'docs/source-evidence/kaneshiro-stanford.xml'
    if sha(evidence)!=lock['source_xml_sha256'] or lock['data_licence']!='CC-BY-3.0' or lock['licence_url'] not in evidence.read_text():raise ValueError('Unverified original licence snapshot')
    files=[f for f in lock['files'] if not pilot or f['name'] in ['S1.mat','S10.mat','Kaneshiro_etAl_objectCategoryEEG_README.pdf']]
    def one(f):
        path=root/f['name'];fetch(f['url'],path,'md5:'+f['checksums']['md5'],f['bytes'])
        if sha(path,'sha1')!=f['checksums']['sha1']:raise ValueError('Publisher SHA1 mismatch')
        print(f'Verified {f["name"]}',flush=True);return dict(f,sha256=sha(path))
    with ThreadPoolExecutor(2) as pool:files=list(pool.map(one,files))
    shutil.copy2(evidence,root/'original-stanford.xml')
    receipt=dict(dataset='Kaneshiro2015',source_record_id='Stanford bq914sc3730',source_revision=lock['source_revision'],licence='CC-BY-3.0',files=files,pilot=pilot)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',lock)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('D:/Data/EEGSources/Kaneshiro2015'));p.add_argument('--pilot',action='store_true');a=p.parse_args();download(a.root,a.pilot)
