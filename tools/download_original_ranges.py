"""Bounded, resumable HTTP ranges with final publisher digest verification."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import shutil
import time
import urllib.request


def verify(path,size,checksum):
    if not path.is_file() or path.stat().st_size!=size:return False
    algorithm,expected=checksum.split(':',1)
    if algorithm=='s3-multipart-md5-5242880':
        chunks=[]
        with path.open('rb') as f:
            for b in iter(lambda:f.read(5242880),b''):chunks.append(hashlib.md5(b).digest())
        return hashlib.md5(b''.join(chunks)).hexdigest()+'-'+str(len(chunks))==expected
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()==expected


def fetch_ranges(url,path,checksum,size,workers=4,chunk_bytes=8*1024*1024):
    """Only use a publisher size/digest; reject ignored or mismatched ranges."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if verify(path,size,checksum):return path
    if path.exists():raise ValueError('Existing completed source differs from publisher digest')
    if checksum.split(':',1)[0] not in ['md5','sha256','s3-multipart-md5-5242880']:raise ValueError('Known publisher digest required')
    directory=path.with_name(path.name+'.ranges');directory.mkdir(exist_ok=True)
    # Preserve a stopped ordinary downloader's existing prefix, never discard it.
    previous=path.with_name(path.name+'.part');prefix=directory/'prefix'
    if not prefix.exists() and previous.is_file() and 0<previous.stat().st_size<size:
        shutil.copy2(previous,prefix)
    offset=prefix.stat().st_size if prefix.exists() else 0
    parts=[(start,min(size,start+chunk_bytes)-1) for start in range(offset,size,chunk_bytes)]
    def one(bounds):
        start,end=bounds;target=directory/f'{start}-{end}';length=end-start+1
        if target.is_file() and target.stat().st_size==length:return target
        for attempt in range(4):
            try:
                req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','User-Agent':'EEGBench original data preparation'})
                with urllib.request.urlopen(req,timeout=90) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':raise ValueError('Publisher did not return the exact requested range')
                    with target.with_suffix('.part').open('wb') as out:shutil.copyfileobj(response,out,1024*1024)
                if target.with_suffix('.part').stat().st_size!=length:raise ValueError('Incomplete original range')
                target.with_suffix('.part').replace(target);print(path.name,'verified range length',start,end,flush=True);return target
            except Exception:
                if attempt==3:raise
                time.sleep(2)
    with ThreadPoolExecutor(workers) as pool:downloaded=list(pool.map(one,parts))
    assembled=directory/'assembled'
    with assembled.open('wb') as out:
        for part in ([prefix] if offset else [])+downloaded:
            with part.open('rb') as src:shutil.copyfileobj(src,out,1024*1024)
    if not verify(assembled,size,checksum):raise ValueError('Assembled original data failed publisher digest; cached ranges need review')
    assembled.replace(path)
    # Only remove these explicitly owned temporary files after the complete
    # original passes its publisher digest. No directory traversal/deletion.
    for part in downloaded+([prefix] if offset else []):
        if part.resolve().parent!=directory.resolve():raise ValueError('Unsafe temporary range path')
        part.unlink()
    if previous.is_file() and previous.resolve().parent==path.resolve().parent:previous.unlink()
    if not any(directory.iterdir()):directory.rmdir()
    return path
