"""Audit all native MILimb imagery epochs without silently resolving copies."""
from collections import defaultdict,Counter
import json
from pathlib import Path
import numpy as np
from tools.prepare_milimb import native_csv
from tools.prepare_wang import digest_case


def audit(cache=Path('D:/Data/EEGSources/MILimbEEG')):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));groups=defaultdict(list);flat=[];quality=np.zeros(16,dtype=int)
    files=[f for f in receipt['files'] if 'participant_id' in f]
    for i,f in enumerate(files,1):
        x=native_csv(cache/f['name']);sd=x.std(axis=1);quality+=sd<=1e-7
        e={k:f[k] for k in ['name','participant_id','run_id','source_label','trial_suffix','sha256']}
        e.update(signal_sha256=digest_case(x),minimum_channel_std=float(sd.min()),maximum_absolute_value=float(np.abs(x).max()))
        groups[e['signal_sha256']].append(e)
        if np.any(sd<=1e-7):flat.append(e)
        if i%500==0:print('Audited',i,'/',len(files),flush=True)
    duplicate=[g for g in groups.values() if len(g)>1]
    r=dict(source='Mendeley x8psbz3f6x v2 imagery CSVs',cases=len(files),duplicate_groups=duplicate,duplicate_group_count=len(duplicate),
        cases_in_duplicate_groups=sum(len(g) for g in duplicate),cross_subject_duplicate_groups=sum(len({e['participant_id'] for e in g})>1 for g in duplicate),
        conflicting_label_duplicate_groups=sum(len({e['source_label'] for e in g})>1 for g in duplicate),
        duplicate_cases_by_class=dict(Counter(e['source_label'] for g in duplicate for e in g)),effectively_flat_case_counts_per_channel=quality.tolist(),effectively_flat_cases=flat,
        decision='Full conversion stopped before publishing arrays; determine original-source identity/placeholder issues before admission. No label or owner guessed.')
    Path('docs/milimb-native-quality-audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k not in ['duplicate_groups','effectively_flat_cases']},indent=2))
    return r


if __name__=='__main__':audit()
