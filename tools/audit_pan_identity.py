"""Compare both complete native Pan releases before counting independent problems."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from tools.prepare_mi_to_30 import pan_epoch_arrays
from tools.prepare_moabb import dump

ROOT=Path(__file__).resolve().parents[1]


def fingerprint(case):
    return hashlib.sha256(np.ascontiguousarray(case).tobytes()).hexdigest()


def inventory(cache,key):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    if receipt['pilot']:raise ValueError('Identity audit requires both full source releases')
    features=[];ids=[];hashes={t:{} for t in ['float64','float32','rounded_0.001_native_units']}
    for file in sorted(receipt['files'],key=lambda f:f['name']):
        x,labels,names,cue,extra=pan_epoch_arrays(cache/file['name'],key)
        for i,case in enumerate(x):
            identity=dict(file=file['name'],epoch=i,label=int(labels[i]))
            for kind,array in [('float64',case),('float32',case.astype('<f4')),('rounded_0.001_native_units',np.round(case,3))]:
                hashes[kind].setdefault(fingerprint(array),[]).append(identity)
            # Channelwise offset/scale-invariant temporal shape, all28 source
            # indices unchanged. Candidate search only; not a proof of independence.
            centred=case-case.mean(axis=1,keepdims=True);scale=centred.std(axis=1,keepdims=True)
            normalised=np.divide(centred,scale,out=np.zeros_like(centred),where=scale>0)
            feature=normalised[:,:992].reshape(28,32,31).mean(axis=2).ravel()
            norm=np.linalg.norm(feature)
            features.append(feature/norm if norm else feature);ids.append(identity)
        print(key,file['name'],len(ids),flush=True)
    return np.asarray(features),ids,hashes


def audit(cache_root=Path('D:/Data/EEGSources')):
    a,ai,ah=inventory(Path(cache_root)/'Pan2023','pan23');b,bi,bh=inventory(Path(cache_root)/'Pan2025','pan25')
    matches={kind:[dict(pan23=ah[kind][h],pan25=bh[kind][h]) for h in sorted(ah[kind].keys()&bh[kind].keys())] for kind in ah}
    dist,index=cKDTree(a).query(b,k=1);closest=np.argsort(dist)[:20];pairs=[]
    loaded={}
    for j in closest:
        left=ai[int(index[j])];right=bi[int(j)];cases=[]
        for key,source,identity in [('pan23','Pan2023',left),('pan25','Pan2025',right)]:
            token=(key,identity['file'])
            if token not in loaded:
                # Bound memory: retain at most the current two session arrays.
                if len(loaded)>=2:loaded.clear()
                loaded[token]=pan_epoch_arrays(Path(cache_root)/source/identity['file'],key)[0]
            cases.append(loaded[token][identity['epoch']].copy())
        channel_corr=[]
        for x,y in zip(*cases,strict=True):
            channel_corr.append(float(np.corrcoef(x,y)[0,1]) if x.std()>0 and y.std()>0 else None)
        pairs.append(dict(pan23=left,pan25=right,normalised_temporal_feature_distance=float(dist[j]),
            full_waveform_correlation=float(np.corrcoef(cases[0].ravel(),cases[1].ravel())[0,1]),channel_correlations=channel_corr))
    suspect=any(abs(p['full_waveform_correlation'])>.95 for p in pairs)
    report=dict(pan23_cases=len(ai),pan25_cases=len(bi),exact_or_quantised_matches=matches,closest_temporal_shape_pairs=pairs,
        admission_gate_passed=not any(matches.values()) and not suspect,
        method='All complete4-second28-column task crops: exact float64,float32 and0.001-unit rounded hashes. All-case channelwise offset/scale-normalised32-bin temporal features; nearest cross-release candidates, full waveform/channel correlations for closest20.',
        limitations='No exact or highly correlated matches is evidence against copied task crops, not proof of different people or absence of differently filtered/shifted recordings. Original accessions/protocol/cohort descriptions retained; participant IDs are local to each deposit.',
        source_revisions={s:json.loads((Path(cache_root)/s/'download-receipt.json').read_text())['source_revision'] for s in ['Pan2023','Pan2025']},
        source_file_sha256={s:{f['name']:f['sha256'] for f in json.loads((Path(cache_root)/s/'download-receipt.json').read_text())['files']} for s in ['Pan2023','Pan2025']})
    dump(ROOT/'docs/pan-full-native-identity-audit.json',report)
    if not report['admission_gate_passed']:raise ValueError('Pan source identity requires review before both admissions')
    print(json.dumps({k:report[k] for k in ['pan23_cases','pan25_cases','admission_gate_passed']}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));audit(p.parse_args().cache_root)
