"""Recover MIMED cross-ID copies without guessing the correct identity/label."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from tools.prepare_compact_imagery import mimed_records,SPECS


def audit(cache=Path('D:/Data/EEGSources/MIMED2024')):
    groups=defaultdict(list);flat=[];files={}
    for x,rows,names,info in mimed_records(Path(cache),SPECS['mimed']):
        row=rows[0];source=row['source_file'];index=row['source_block_index']
        if source not in files:files[source]=loadmat(Path(cache)/source,simplify_cells=True)
        block=np.ascontiguousarray(files[source]['joined_data'][index],dtype='<f8')
        entry={k:row[k] for k in ['participant_id','source_file','source_block_index','label']}
        entry.update(crop_sha256=hashlib.sha256(x.tobytes()).hexdigest(),native_block_shape=list(block.shape),
            full_block_sha256=hashlib.sha256(block.tobytes()).hexdigest(),minimum_channel_std=float(x.std(axis=2).min()),
            native_mat_subject=str(files[source]['subject']).strip())
        groups[entry['crop_sha256']].append(entry)
        if (np.ptp(x,axis=2)==0).any():flat.append(entry)
    duplicates=[g for g in groups.values() if len(g)>1]
    implicated=sorted({e['participant_id'] for g in duplicates for e in g})
    return dict(source='MIMED2024 v3 imagery archive',cases=sum(len(g) for g in groups.values()),crop=[384,896],
        duplicate_groups=duplicates,duplicate_group_count=len(duplicates),constant_cases=flat,
        conflicting_class_groups=sum(len({e['label'] for e in g})>1 for g in duplicates),
        implicated_participants=implicated,unimplicated_participants=[f'P{i:02d}' for i in range(1,31) if f'P{i:02d}' not in implicated],
        pair_counts=dict(Counter(','.join(e['participant_id'] for e in g) for g in duplicates)),
        interpretation='No label/participant repaired. Identical nonflat crops across IDs; compare full-block hashes and shapes. Whole release cannot pass duplicate/subject provenance admission.',
        decision='Full conversion stopped; defer or explicitly document an unimplicated-participant subset before proceeding')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources/MIMED2024'));p.add_argument('--report',type=Path,default=Path('docs/mimed-native-quality-audit.json'));a=p.parse_args()
    r=audit(a.cache)
    a.report.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k not in ['duplicate_groups','constant_cases']},indent=2))
