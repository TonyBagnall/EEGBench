"""Read-only streaming archive audit: exact flatlines, aeon threshold and scale.

Does not change data, sidecars, splits, registry or benchmark results. Metrics
are computed in float64, matching normal aeon .ts loading. Detailed metrics are
saved outside the data directory; only derived summaries need publishing.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
import datetime
import json
from pathlib import Path
import time

import numpy as np


THRESHOLD=1e-7
METRICS=['minimum','maximum','mean','std','first','finite_count','length','nan_count','inf_count']


def dump(path,value):
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [clean(v) for v in x]
        if isinstance(x,np.generic):return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x):return None
        return x
    Path(path).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def metrics(channels):
    arrays=[np.fromstring(s.replace('?','nan'),sep=',',dtype=np.float64) for s in channels]
    if any(len(x)==0 for x in arrays):raise ValueError('Empty or unparseable channel')
    result=np.empty((len(METRICS),len(arrays)),dtype=np.float64)
    # Vectorized reductions when all channels have equal length within a case.
    if len({len(x) for x in arrays})==1:
        x=np.stack(arrays);finite=np.isfinite(x);nan=np.isnan(x);inf=np.isinf(x)
        if finite.all():
            result[0]=x.min(axis=1);result[1]=x.max(axis=1)
            result[2]=x.mean(axis=1);result[3]=x.std(axis=1,ddof=0)
        else:
            with np.errstate(invalid='ignore',divide='ignore'):
                result[0]=np.nanmin(x,axis=1);result[1]=np.nanmax(x,axis=1)
                result[2]=np.nanmean(x,axis=1);result[3]=np.nanstd(x,axis=1,ddof=0)
        result[4]=x[:,0];result[5]=finite.sum(axis=1);result[6]=x.shape[1]
        result[7]=nan.sum(axis=1);result[8]=inf.sum(axis=1)
    else:
        for ch,x in enumerate(arrays):
            with np.errstate(invalid='ignore',divide='ignore'):
                result[:,ch]=[np.nanmin(x),np.nanmax(x),np.nanmean(x),np.nanstd(x,ddof=0),x[0],np.isfinite(x).sum(),len(x),np.isnan(x).sum(),np.isinf(x).sum()]
    return result


def masks(values):
    lo,hi,mean,std,first,nfinite,length,nan,inf=values
    ranges=hi-lo
    full=(nfinite==length)&(length>=2)
    constant=(ranges==0)&full
    # Exact aeon check_collection_variance criterion, NaNs ignored by nanstd.
    aeon=(std<=THRESHOLD)&(ranges!=0)
    return dict(exact_constant=constant,zero_constant=constant&(lo==0),
                nonzero_constant=constant&(lo!=0),aeon_tiny_nonconstant=aeon,
                nonfinite=(nan+inf)>0,
                relative_flat_nonconstant=full&(ranges>0)&(ranges<=1e-12*np.maximum(abs(lo),abs(hi))),
                numpy_allclose_to_first=full&(np.maximum(abs(lo-first),abs(hi-first))<=1e-8+1e-5*abs(first)),
                max_abs_below_1e7=full&(np.maximum(abs(lo),abs(hi))<1e-7),
                range_below_1e7=full&(ranges<1e-7))


def quantiles(values):
    values=np.asarray(values);values=values[np.isfinite(values)]
    if not len(values):return dict(min=None,p01=None,p05=None,median=None,p95=None,p99=None,max=None)
    q=np.quantile(values,[0,.01,.05,.5,.95,.99,1])
    return dict(zip(['min','p01','p05','median','p95','p99','max'],map(float,q)))


def summarize(values):
    flags=masks(values);lo,hi,mean,std,_,nfinite,length,nan,inf=values
    nonconstant=(hi>lo)&np.isfinite(std)&(nfinite==length)
    output=dict(cases=values.shape[1],channels=values.shape[2],case_channel_pairs=int(std.size),
                sample_count=int(length.sum()),nan_values=int(nan.sum()),inf_values=int(inf.sum()),
                counts={k:int(v.sum()) for k,v in flags.items()},
                std_nonconstant=quantiles(std[nonconstant]),std_all=quantiles(std),
                max_abs=quantiles(np.maximum(abs(lo),abs(hi))),mean=quantiles(mean),
                timepoints=quantiles(length))
    return output,flags


def audit_dataset(name,root,output):
    started=time.monotonic();folder=Path(root)/name;out=Path(output)/name;out.mkdir(parents=True,exist_ok=True)
    reports={};channel_rows=[];constant_rows=[];source=[]
    for split in ['TRAIN','TEST']:
        path=folder/f'{name}_{split}.ts';before=path.stat();source.append(dict(path=str(path),bytes=before.st_size,mtime_ns=before.st_mtime_ns))
        values=[];labels=[];header=[];nchannels=None;ndata=0
        with path.open(encoding='utf-8-sig') as file:
            for line in file:
                header.append(line.rstrip())
                if line.strip().lower()=='@data':break
            else:raise ValueError(f'Missing @data: {path}')
            if any(line.lower().startswith('@timestamps true') for line in header):raise ValueError('Timestamped data needs a separate parser')
            for line in file:
                line=line.strip()
                if not line or line.startswith('#'):continue
                body,label=line.rsplit(':',1);channels=body.split(':')
                if nchannels is None:nchannels=len(channels)
                if len(channels)!=nchannels:raise ValueError(f'Inconsistent number of channels at {name} {split} row {ndata}')
                values.append(metrics(channels));labels.append(label);ndata+=1
                if ndata%5000==0:print(f'{name} {split}: {ndata} cases read',flush=True)
        data=np.stack(values,axis=1);del values
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Source changed while being audited')
        np.savez_compressed(out/f'{split.lower()}_metrics.npz',values=data,labels=np.asarray(labels),metric_names=np.asarray(METRICS))
        report,flags=summarize(data);report['labels']=dict(Counter(labels));reports[split]=report
        for ch in range(nchannels):
            row=dict(dataset=name,split=split,channel_index_0based=ch,cases=ndata,
                     **{k:int(v[:,ch].sum()) for k,v in flags.items()})
            active=(data[1,:,ch]>data[0,:,ch])&np.isfinite(data[3,:,ch])
            row.update({f'std_nonconstant_{k}':v for k,v in quantiles(data[3,:,ch][active]).items()})
            row['max_abs']=float(np.nanmax(np.maximum(abs(data[0,:,ch]),abs(data[1,:,ch]))))
            channel_rows.append(row)
        for case,ch in np.argwhere(flags['exact_constant']):
            constant_rows.append(dict(dataset=name,split=split,row_0based=int(case),channel_index_0based=int(ch),label=labels[case],value=float(data[0,case,ch]),length=int(data[6,case,ch])))
        (out/f'{split.lower()}_header.txt').write_text('\n'.join(header)+'\n',encoding='utf-8')
        print(f'{name} {split} complete: {report["counts"]}',flush=True)
    for filename,rows in [('channels.csv',channel_rows),('constants.csv',constant_rows)]:
        with (out/filename).open('w',newline='',encoding='utf-8') as file:
            if rows:
                writer=csv.DictWriter(file,list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=dict(dataset=name,source_files=source,partitions=reports,seconds=time.monotonic()-started)
    dump(out/'summary.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('D:/Data/EEG'))
    parser.add_argument('--output',type=Path,default=Path('.openeegbench/signal-audit'))
    parser.add_argument('--datasets',nargs='+',default=None)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--summary-name',default='summary.json')
    args=parser.parse_args()
    from neuroverse.datasets import neuroverse
    names=args.datasets or neuroverse
    if args.output.resolve().is_relative_to(args.root.resolve()):raise ValueError('Audit output must be separate from the dataset archive')
    args.output.mkdir(parents=True,exist_ok=True)
    jobs=[];completed=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for name in names:
            old=args.output/name/'summary.json'
            if args.resume and old.exists():
                result=json.loads(old.read_text())
                unchanged=all((p:=Path(s['path'])).is_file() and (p.stat().st_size,p.stat().st_mtime_ns)==(s['bytes'],s['mtime_ns']) for s in result['source_files'])
                if unchanged:completed.append(result);continue
            jobs.append((name,pool.submit(audit_dataset,name,args.root,args.output)))
        lookup={future:name for name,future in jobs}
        for future in as_completed(lookup):
            name=lookup[future]
            try:completed.append(future.result())
            except Exception as exc:
                dump(args.output/name/'error.json',dict(dataset=name,error=repr(exc)));print(f'FAILED {name}: {exc}',flush=True)
            dump(args.output/args.summary_name,dict(generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),threshold=THRESHOLD,criterion='np.nanstd(ddof=0) <= 1e-7 AND np.nanmax - np.nanmin != 0; exact constants counted separately',metrics=METRICS,datasets=sorted(completed,key=lambda x:x['dataset'])))
    print(f'Audit completed: {len(completed)}/{len(names)} datasets',flush=True)


if __name__=='__main__':main()
