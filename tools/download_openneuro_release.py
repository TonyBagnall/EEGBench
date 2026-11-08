"""Download an immutable OpenNeuro Git release, checking git-annex object hashes.

The Git snapshot supplies metadata and MD5E/SHA256E object identities; mutable
S3 paths are accepted only if their bytes match those release-pinned objects.
No archive paths or symbolic links are blindly extracted or followed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import dump, sha


def annex_identity(target):
    match=re.fullmatch(r'(MD5E|SHA256E)-s(\d+)--([a-f0-9]+)(?:\..*)?',PurePosixPath(target).name)
    if not match:raise ValueError(f'Unsupported annex identity: {target}')
    algorithm={'MD5E':'md5','SHA256E':'sha256'}[match[1]]
    if len(match[3])!={'md5':32,'sha256':64}[algorithm]:raise ValueError('Invalid object digest')
    return algorithm,int(match[2]),match[3]


def safe_relative(member):
    path=PurePosixPath(member)
    if path.is_absolute() or '..' in path.parts or '\\' in member or ':' in member:raise ValueError('Unsafe snapshot path')
    return path


def download(dataset,revision,root,expected_licence,pilot_subjects=None):
    if not re.fullmatch(r'ds\d{6}',dataset) or not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('Pin dataset and commit')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    archive=root/'release-snapshot.tar.gz'
    fetch(f'https://api.github.com/repos/OpenNeuroDatasets/{dataset}/tarball/{revision}',archive)
    entries=[]
    with tarfile.open(archive) as source:
        for member in source:
            relative=PurePosixPath(member.name).parts[1:]
            if not relative or relative[0].startswith('.'):continue
            path=safe_relative('/'.join(relative));name=path.as_posix()
            if pilot_subjects and path.parts[0].startswith('sub-') and path.parts[0] not in pilot_subjects:continue
            if member.isdir():continue
            target=root.joinpath(*path.parts);target.parent.mkdir(parents=True,exist_ok=True)
            if member.issym():
                algorithm,size,digest=annex_identity(member.linkname)
                entries.append(dict(name=name,url=f'https://s3.amazonaws.com/openneuro.org/{dataset}/{name}',bytes=size,publisher_checksum=f'{algorithm}:{digest}',annex_key=PurePosixPath(member.linkname).name))
            elif member.isfile():
                data=source.extractfile(member).read();target.write_bytes(data)
                entries.append(dict(name=name,url=f'https://raw.githubusercontent.com/OpenNeuroDatasets/{dataset}/{revision}/{name}',bytes=len(data),publisher_checksum='sha256:'+hashlib.sha256(data).hexdigest()))
            else:raise ValueError('Unexpected snapshot member type')
    description=json.loads((root/'dataset_description.json').read_text())
    if description.get('License')!=expected_licence:raise ValueError('Unreviewed original data licence')
    licence=next(f for f in entries if f['name']=='LICENSE')
    fetch(licence['url'],root/'LICENSE',licence['publisher_checksum'],licence['bytes'])
    if expected_licence=='CC0' and 'creativecommons.org/publicdomain/zero/1.0' not in (root/'LICENSE').read_text():raise ValueError('Original licence text disagrees')
    print(f'{len(entries)} files, {sum(f["bytes"] for f in entries)/1e9:.3f} GB pinned source bytes',flush=True)
    def one(entry):
        path=root/entry['name'];fetch(entry['url'],path,entry['publisher_checksum'],entry['bytes'])
        return dict(entry,sha256=sha(path))
    files=[]
    with ThreadPoolExecutor(6) as pool:
        for number,entry in enumerate(pool.map(one,entries),1):
            files.append(entry)
            if number%50==0:print(f'{dataset}: verified {number}/{len(entries)}',flush=True)
    receipt=dict(dataset=dataset,source_record_id=dataset,source_revision=revision,licence='CC0-1.0' if expected_licence=='CC0' else expected_licence,
        source_url=f'https://openneuro.org/datasets/{dataset}',snapshot_sha256=sha(archive),files=files,pilot_subjects=pilot_subjects)
    dump(root/'download-receipt.json',receipt);dump(root/'source-record.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset');p.add_argument('revision');p.add_argument('--root',type=Path,required=True);p.add_argument('--licence',required=True);p.add_argument('--pilot-subjects',nargs='+');a=p.parse_args()
    download(a.dataset,a.revision,a.root,a.licence,a.pilot_subjects)
