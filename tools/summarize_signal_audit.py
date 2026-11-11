"""Summarize saved read-only metrics without rereading or editing EEG files."""
from collections import Counter
import csv
import datetime
import json
from pathlib import Path

import numpy as np

from neuroverse.datasets import metadata,neuroverse
from tools.audit_signal_scale import THRESHOLD,dump,masks,quantiles


def summarize(root=Path('.openeegbench/signal-audit'),output=Path('docs')):
    rows=[];candidates=[];details=[];snapshots=[];nonfinite=0;total_cases=0;total_pairs=0
    retired=['Blink','EpilepticSeizures','Sleep']
    documented_volts={'CodedSymbols','CovidSurvivors','ImaginedLeftRightHand','ImaginedRightHandFeet'}
    meg={'FaceDetection','HandMovementDirection','MindReading','MatchWords'}
    expected=metadata()
    for name in neuroverse:
        folder=root/name;summary=json.loads((folder/'summary.json').read_text())
        flags_by_split={};all_std=[];all_max=[];all_relative=[];counter={};parts={}
        for split in ['TRAIN','TEST']:
            z=np.load(folder/f'{split.lower()}_metrics.npz');v=z['values'];flags=masks(v)
            assert v.shape[1]==expected.loc[name,'train_size' if split=='TRAIN' else 'test_size']
            assert v.shape[2]==expected.loc[name,'channels']
            lengths=np.unique(v[6])
            active=(v[1]>v[0])&np.isfinite(v[3])
            case_median=np.nanmedian(np.where(active,v[3],np.nan),axis=1)
            relative=np.divide(v[3],case_median[:,None],out=np.full(v[3].shape,np.nan),where=case_median[:,None]>0)
            effective=active&(relative<1e-6)
            flags['relative_channel_flat']=effective
            flags_by_split[split]=flags
            parts[split]=dict(cases=v.shape[1],timepoints=[int(n) for n in lengths],std=quantiles(v[3][active]),
                exact_constant=int(flags['exact_constant'].sum()),aeon_tiny_nonconstant=int(flags['aeon_tiny_nonconstant'].sum()),
                relative_channel_flat=int(effective.sum()),tiny_after_gain_1e6=int((active&(v[3]*1e6<=THRESHOLD)).sum()),
                tiny_after_gain_1e15=int((active&(v[3]*1e15<=THRESHOLD)).sum()))
            all_std.extend(v[3][active]);all_max.extend(np.maximum(abs(v[0]),abs(v[1])).ravel())
            total_cases+=v.shape[1];total_pairs+=v.shape[1]*v.shape[2]
            nonfinite+=int((v[7]+v[8]).sum())
            for ch in range(v.shape[2]):
                details.append(dict(dataset=name,split=split,channel_index_0based=ch,cases=v.shape[1],exact_constant=int(flags['exact_constant'][:,ch].sum()),aeon_tiny_nonconstant=int(flags['aeon_tiny_nonconstant'][:,ch].sum()),relative_channel_flat=int(effective[:,ch].sum()),median_std=float(np.nanmedian(v[3,:,ch])),max_abs=float(np.nanmax(np.maximum(abs(v[0,:,ch]),abs(v[1,:,ch]))))))
        unit='native / unspecified'
        median_std=float(np.median(all_std))
        if name=='MatchWords':unit='T (source MEG sidecar); local scale consistent'
        elif name in documented_volts:unit='V (documented local preparation)'
        elif name not in meg and name!='MotorImagery' and 1e-7<median_std<1e-3:unit='V-like (inferred, not verified physical units)'
        else:
            meta=Path('D:/Data/EEG')/name/f'{name}_metadata.json'
            if meta.exists():
                data=json.loads(meta.read_text());u=data.get('units','') or ''
                if 'microvolt' in u.lower() or u.startswith('microV'):unit='microvolt scale (documented/interpreted)'
            if name in ['ArmMovements','ImaginedArmMovements']:unit='native; upstream interprets microvolts, GDF units ambiguous'
            if name=='FlickerAttention':unit='native FIF scale; physical calibration unresolved'
        row=dict(dataset=name,proposed_status='retire' if name in retired else 'retain',
            train_cases=parts['TRAIN']['cases'],test_cases=parts['TEST']['cases'],channels=int(expected.loc[name,'channels']),
            train_timepoints=parts['TRAIN']['timepoints'][0] if len(parts['TRAIN']['timepoints'])==1 else str(parts['TRAIN']['timepoints']),
            test_timepoints=parts['TEST']['timepoints'][0] if len(parts['TEST']['timepoints'])==1 else str(parts['TEST']['timepoints']),
            registry_timepoints=int(expected.loc[name,'length']),
            train_median_std=parts['TRAIN']['std']['median'],test_median_std=parts['TEST']['std']['median'],
            min_nonconstant_std=float(np.min(all_std)),max_abs=float(np.max(all_max)),
            exact_constant_pairs=sum(p['exact_constant'] for p in parts.values()),
            aeon_tiny_nonconstant_pairs=sum(p['aeon_tiny_nonconstant'] for p in parts.values()),
            relative_channel_flat_pairs=sum(p['relative_channel_flat'] for p in parts.values()),
            tiny_pairs_remaining_after_gain_1e6=sum(p['tiny_after_gain_1e6'] for p in parts.values()),
            unit_assessment=unit,unit_standardisation_candidate_gain=1e6 if unit.startswith(('V (','V-like')) else 1)
        rows.append(row)
        for ch in range(row['channels']):
            flat={s:int(flags_by_split[s]['exact_constant'][:,ch].sum()) for s in parts}
            low={s:int(flags_by_split[s]['relative_channel_flat'][:,ch].sum()) for s in parts}
            if sum(flat.values())+sum(low.values()):
                candidates.append(dict(dataset=name,channel_index_0based=ch,channel_name='MEG 056 (source-order correspondence)' if name=='MatchWords' and ch==55 else 'F8' if name=='VideoEmotions' and ch==6 else None,
                    train_exact_constant=flat['TRAIN'],test_exact_constant=flat['TEST'],train_effectively_flat=low['TRAIN'],test_effectively_flat=low['TEST'],
                    all_cases_flat=sum(flat.values())==parts['TRAIN']['cases']+parts['TEST']['cases'],
                    proposed_action='Retire whole problem' if name in retired else 'Drop this axis globally in both splits, subject to review'))
        for source in summary['source_files']:
            p=Path(source['path']);assert (p.stat().st_size,p.stat().st_mtime_ns)==(source['bytes'],source['mtime_ns']),str(p)
            snapshots.append(source)
    output.mkdir(parents=True,exist_ok=True)
    for filename,records in [('signal-scale-audit-summary.csv',rows),('signal-scale-audit-channels.csv',details),('signal-scale-audit-removal-candidates.csv',candidates)]:
        with (output/filename).open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,list(records[0]));writer.writeheader();writer.writerows(records)
    report=dict(date=datetime.date.today().isoformat(),status='Review only; no dataset or sidecar modifications performed',
        datasets_audited=len(rows),files_audited=len(snapshots),source_bytes=sum(p['bytes'] for p in snapshots),cases_audited=total_cases,case_channel_pairs=total_pairs,
        nonfinite_values=nonfinite,exact_constant_pairs=sum(r['exact_constant_pairs'] for r in rows),
        aeon_tiny_nonconstant_pairs=sum(r['aeon_tiny_nonconstant_pairs'] for r in rows),
        rules=dict(exact_constant='Fully finite channel with max == min, at least two samples',aeon_tiny='Population nanstd <= 1e-7 AND nanmax - nanmin != 0',
                   effectively_flat_relative='Nonconstant std < 1e-6 times median nonconstant channel std in the same case; diagnostic candidate, not an automatic physical-unit conclusion'),
        proposed_retirements=retired,proposed_remaining_problems=len(rows)-len(retired),removal_candidates=candidates,
        length_metadata_discrepancies=[dict(dataset=r['dataset'],actual_train=r['train_timepoints'],actual_test=r['test_timepoints'],registry=r['registry_timepoints']) for r in rows if r['train_timepoints']!=r['registry_timepoints'] or r['test_timepoints']!=r['registry_timepoints']],
        proposed_threshold_repairs=[dict(dataset='MatchWords',remove_original_channel_indices_0based=[55],gain=1e15,source_unit='T',output_unit='fT',reason='MEG; requested 1e6 gain leaves 25214 varying pairs below threshold'),dict(dataset='VideoEmotions',remove_original_channel_indices_0based=[6],gain=1,source_unit='microvolt scale',output_unit='unchanged',reason='F8 effectively flat for subject 030; source is already scaled by 1e6')],
        voltage_standardisation_candidates=[dict(dataset=r['dataset'],gain=1e6,evidence=r['unit_assessment'],currently_fails_aeon=r['aeon_tiny_nonconstant_pairs']>0) for r in rows if r['unit_standardisation_candidate_gain']==1e6],
        precision_plan=dict(computation='float64 for gains',decimal_output='17 significant digits / exact float64 roundtrip',removal_only='Preserve retained numeric tokens where possible',limitation='Casting cannot recover precision already lost in prior source/float32 conversions'),
        sidecar_plan=['Before/after SHA256 and byte sizes','Gain, source/output units and confidence','Source precision, computation dtype and decimal output precision','Removed original indices/names/reasons and kept-axis mapping','Before/after shapes and class counts; unchanged case/split order','Case metadata hashes updated with explicit dtype; original source hashes retained','Sensor/channel sidecars, manifests and registry counts updated','Versioned transformation history and validation; existing benchmark results left historical'],
        dataset_summaries=rows,source_snapshot=snapshots)
    dump(output/'signal-scale-audit.json',report)
    print(json.dumps({k:v for k,v in report.items() if k in ['datasets_audited','files_audited','source_bytes','cases_audited','case_channel_pairs','nonfinite_values','exact_constant_pairs','aeon_tiny_nonconstant_pairs','removal_candidates','voltage_standardisation_candidates']},indent=2))
    return report


if __name__=='__main__':summarize()
