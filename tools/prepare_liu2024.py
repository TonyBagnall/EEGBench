"""Download pinned Figshare Liu2024 EDFs and prepare ImaginedHandsStroke.

python -m tools.prepare_liu2024 [--offline] [--download-only]
Uses the original author's EDF derivative and supplied event/channel tables.
Excludes release IDs 05,15,49 following pinned MOABB gh-1248/1273 provenance,
and ID43 because its native stage sequence is ambiguous.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import warnings

import numpy as np

from tools import prepare_open_moabb as core
from tools.prepare_small_moabb import fetch
from tools.prepare_moabb import sha
from tools.prepare_wang import digest_case

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'docs/liu2024-source-lock.json'
EXCLUDED={'05':'04','15':'11','49':'47'}
MARKER_EXCLUSIONS={'43':'Ambiguous multiple native imagery onsets before a break; shared-schedule class alignment not uniquely supported'}
SPEC=dict(name='ImaginedHandsStroke',source='Liu2024 / EEG datasets of stroke patients',
    cache='Liu2024',hz=500,points=2000,classes=2,train_subjects=35,
    labels={'1':'imagined_left_hand','2':'imagined_right_hand'},
    doi='10.6084/m9.figshare.21679035.v5',
    paper='Liu, Wei, Wang et al. (2024), An EEG motor imagery dataset for brain computer interface in acute stroke patients, Scientific Data 11, 131, DOI 10.1038/s41597-023-02787-8',
    note='46 release IDs retained; 05,15,49 excluded as derived products following pinned MOABB gh-1248/1273, without asserting that clinical patients are identical. Release ID43 additionally excluded because imagery-stage pulses are ambiguous. Fractional interpolated trigger values are not rounded into events; complete native instruction/imagery/break sequences determine trial order and retain an audit of ignored orphan pulses. One documented session/run per release ID. Native EDF EEG names/order matched to author channel table; 29 EEG retained, CPz reference, two EOG and unnamed stage trigger excluded. MNE-calibrated volts multiplied by 1e6 in float64. Four-second windows start at actual native stage-2 triggers; labels come from shared author event schedule, not hand-specific native trigger codes. Shared schedule ideal onset/duration fields are milliseconds and differ from jittered native markers. Publisher documents mean removal and 0.5-40Hz FIR preprocessing; no additional filtering, baseline or resampling. Native electrode coordinates retained as supplied (Other/mm, approximately unit-radius values); no physical coordinate reinterpretation.',
    evidence_files=['liu2024-source-lock.json'],
    cache_evidence_files=['moabb-liu2024.py','derived-release-audit.json','all-retained-trigger-audit.json']+
        [f['name'] for f in json.loads(LOCK.read_text())['files'] if f['name']!='edffile.zip'],
    metadata_updates=dict(released_participant_count=50,upstream_derived_release_ids=EXCLUDED,
        additional_recording_quality_exclusions=MARKER_EXCLUSIONS,
        source_sensor_count=33,reference_channel_excluded='CPz',eog_channels_excluded=['HEOL','HEOR'],
        trigger_channel_excluded='',coordinates_evidence='Shared author table, Other/mm declaration; coordinate scale is uncertain and no individual measured montage is asserted',
        hand_label_evidence='Shared author schedule matched to ordinal of complete native stage triplets; native stage codes do not encode hand',
        source_index_scope='Distributed EDF derivative; original clinical/MAT pre-export sample correspondence unavailable',
        window_overlap_policy='Fixed four-second windows within approximately eight-second trials. Every retained window ends at or before its native break marker; per-case endpoint differences are preserved. No case-window overlap.'),
    conversion_files=['prepare_liu2024.py'])


def ensure_sources(cache,download=True):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    lock=json.loads(LOCK.read_text())
    if lock['article_id']!=21679035 or lock['version']!=5 or lock['licence']['name']!='CC BY 4.0':
        raise ValueError('Source version/licence mismatch')
    inventory=[]
    for f in lock['files']:
        if Path(f['name']).name!=f['name']:raise ValueError('Unsafe source filename')
        p=cache/f['name']
        if download:fetch(f['download_url'],p,'md5:'+f['computed_md5'],f['size'])
        if p.stat().st_size!=f['size'] or sha(p,'md5')!=f['computed_md5']:raise ValueError('Source checksum mismatch')
        inventory.append(dict(name=f['name'],bytes=f['size'],checksum='md5:'+f['computed_md5'],sha256=sha(p),url=f['download_url'],figshare_file_id=f['id']))
    core.dump(cache/'download-receipt.json',dict(dataset='Liu2024',source_record_id=21679035,
        source_revision='Figshare article 21679035 version 5',licence='CC-BY-4.0',files=inventory))
    if download:
        fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{core.REVISION}/moabb/datasets/liu2024.py',cache/'moabb-liu2024.py')
    if not (cache/'moabb-liu2024.py').exists():raise FileNotFoundError('Pinned loader evidence missing')
    return core.extract_selected(cache/'edffile.zip',cache/'extracted',lambda n:n.lower().endswith('.edf'))


def eeg_indices(names,channel_table):
    expected=[r['name'] for r in channel_table if r['type']=='EEG']
    if len(expected)!=29 or len(names)!=33 or len(set(names))!=33:
        raise ValueError('Native sensor schema changed')
    indices=[i for i,n in enumerate(names) if n in expected]
    if [names[i] for i in indices]!=expected:
        raise ValueError('Native EEG channel order differs from author table; no silent reorder')
    if set(names)-set(expected)!={'CPz','HEOL','HEOR',''}:
        raise ValueError('Unexpected auxiliary/reference channels')
    return indices,expected


def imagery_events(stage_signal,schedule,return_audit=False):
    """Use observed native stage markers; shared schedule supplies left/right labels."""
    scaled=np.asarray(stage_signal,dtype=np.float64)*1e6
    nearest=np.rint(scaled).astype(int)
    discrete=np.isclose(scaled,nearest,rtol=0,atol=1e-6)
    if not np.isfinite(scaled).all() or (scaled< -1e-6).any() or (scaled>3+1e-6).any():
        raise ValueError('Trigger calibration differs from reviewed EDF')
    # Publisher artifact interpolation also affected the trigger row. Fractional
    # levels are not events: retain only actual discrete 1/2/3 levels, never
    # manufacture a marker by rounding an interpolated value to a class code.
    marker=np.where(discrete,nearest,0)
    starts=core.pulse_onsets(marker)
    triplets=[];ignored=[];instruction=None;imagery=None
    for sample in starts:
        sample=int(sample);code=int(marker[sample])
        if code==1:
            if imagery is not None:
                ignored.append(dict(sample=sample,code=code,reason='Extra instruction-like pulse during unfinished imagery stage'))
            else:
                if instruction is not None:ignored.append(dict(sample=instruction,code=1,reason='Repeated instruction before imagery'))
                instruction=sample
        elif code==2:
            if imagery is not None:raise ValueError(f'Ambiguous multiple imagery onsets before a break: samples {imagery} and {sample}')
            if instruction is None:ignored.append(dict(sample=sample,code=code,reason='Imagery-like pulse without preceding instruction'))
            else:imagery=sample
        elif code==3:
            if imagery is None:ignored.append(dict(sample=sample,code=code,reason='Break-like pulse without preceding imagery'))
            else:
                triplets.append((instruction,imagery,sample));instruction=imagery=None
        else:raise ValueError('Unknown native stage code')
    if instruction is not None:ignored.append(dict(sample=instruction,code=1,reason='Unfinished trailing instruction'))
    if imagery is not None:ignored.append(dict(sample=imagery,code=2,reason='Unfinished trailing imagery-like pulse without break'))
    if len(triplets)!=40:
        raise ValueError(f'Expected 40 complete native triplets, found {len(triplets)}')
    if len(schedule)!=120 or [int(r['value']) for r in schedule]!=[1,2,3]*40:
        raise ValueError('Author event table protocol differs')
    output=[]
    for trial in range(40):
        event=3*trial+1;entry=schedule[event]
        label=entry['trial_type']
        if label not in ['1','2'] or any(schedule[3*trial+i]['trial_type']!=label for i in range(3)):
            raise ValueError('Inconsistent trial labels in author schedule')
        if int(entry['duration'])!=4000:raise ValueError('Non-four-second imagery schedule')
        _,start,stop=triplets[trial]
        output.append((trial,event,start,stop,entry))
    if Counter(e[-1]['trial_type'] for e in output)!={'1':20,'2':20}:
        raise ValueError('Unexpected source class counts')
    bad=np.flatnonzero(~discrete)
    spans=[]
    if len(bad):
        groups=np.split(bad,np.flatnonzero(np.diff(bad)>1)+1)
        spans=[dict(start_sample=int(g[0]),end_sample=int(g[-1])+1) for g in groups]
    audit=dict(native_stage_pulse_count=len(starts),complete_triplets=len(triplets),ignored_stage_pulses=ignored,
        noninteger_trigger_samples_ignored=len(bad),noninteger_trigger_spans=spans,
        rule='Select only discrete native 1/2/3 code levels (1e-6 code-unit tolerance); fractional interpolated trigger values are background. Match complete instruction->imagery->break sequences in native order; repeated instruction/isolated break and unfinished tail pulses do not advance shared-schedule hand labels; ambiguous multiple imagery onsets fail')
    return (output,audit) if return_audit else output


def read_raw(path):
    import mne
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        raw=mne.io.read_raw_edf(path,preload=True,verbose=False,stim_channel=None)
    if raw.info['sfreq']!=500 or raw.n_times!=160000:
        raise ValueError('Native EDF frequency/length changed')
    if not np.all(np.asarray(raw._raw_extras[0]['units'])==1e-6):
        raise ValueError('Native EDF calibration changed; review units')
    return raw


def audit_derived(cache,root):
    table=core.table(cache/'task-motor-imagery_channels.tsv');report=[]
    def values(person):
        p=root/f'edffile/sub-{person}/eeg/sub-{person}_task-motor-imagery_eeg.edf'
        raw=read_raw(p);indices,_=eeg_indices(raw.ch_names,table)
        return raw.get_data(picks=indices)*1e6
    for derived,source in EXCLUDED.items():
        a,b=values(derived),values(source)
        ac=a-a.mean(axis=1,keepdims=True);bc=b-b.mean(axis=1,keepdims=True)
        corr=(ac*bc).sum(axis=1)/np.sqrt((ac*ac).sum(axis=1)*(bc*bc).sum(axis=1))
        report.append(dict(excluded_release_id=derived,source_release_id=source,
            all_eeg_calibrated_values_equal=bool(np.array_equal(a,b)),
            channel_correlations=corr.tolist(),median_channel_correlation=float(np.median(corr)),
            eeg_signal_sha256_excluded=digest_case(a),eeg_signal_sha256_source=digest_case(b),
            exclusion_basis='Pinned upstream provenance guard, not correlation threshold or clinical-identity inference'))
    core.dump(cache/'derived-release-audit.json',dict(issue='https://github.com/NeuroTechX/moabb/issues/1248',
        moabb_revision=core.REVISION,excluded_release_ids=EXCLUDED,pairs=report,
        scope='Local calibrated EDF numerical comparison; raw MAT generation and patient identity are not inferred'))


def audit_triggers(cache,root):
    schedule=core.table(cache/'task-motor-imagery_events.tsv');out={}
    for path in sorted(root.rglob('*.edf')):
        person=path.parts[-3][4:]
        if person in EXCLUDED:continue
        raw=read_raw(path);signal=raw.get_data(picks=[raw.ch_names.index('')])[0]
        try:
            _,audit=imagery_events(signal,schedule,return_audit=True)
            if person in MARKER_EXCLUSIONS:raise RuntimeError('Previously ambiguous recording now passes; review source version')
            out[person]=dict(status='pass',**audit)
        except ValueError as e:
            if person not in MARKER_EXCLUSIONS:raise
            scaled=signal*1e6;nearest=np.rint(scaled).astype(int)
            discrete=np.isclose(scaled,nearest,rtol=0,atol=1e-6)
            marker=np.where(discrete,nearest,0);starts=core.pulse_onsets(marker)
            out[person]=dict(status='excluded',error=str(e),source_file=path.relative_to(root).as_posix(),
                native_discrete_stage_pulses=[dict(sample=int(s),code=int(marker[s])) for s in starts],
                noninteger_trigger_samples_ignored=int((~discrete).sum()))
    core.dump(cache/'all-retained-trigger-audit.json',out)
    print('Native trigger audit:',sum(r['status']=='pass' for r in out.values()),'pass; 43 excluded with detailed pulse evidence',flush=True)


def records(cache,spec):
    root=cache/'extracted'
    channels=core.table(cache/'task-motor-imagery_channels.tsv')
    schedule=core.table(cache/'task-motor-imagery_events.tsv')
    participants={r['Participant_ID']:r for r in core.table(cache/'participants.tsv')}
    electrodes=core.table(cache/'task-motor-imagery_electrodes.tsv')
    coords=json.loads((cache/'task-motor-imagery_coordsystem.json').read_text())
    props=json.loads((cache/'task-motor-imagery_eeg.json').read_text())
    files=sorted(root.rglob('*.edf'))
    if len(files)!=50:raise ValueError('Expected all 50 released EDFs before exclusions')
    for path in files:
        token=path.parts[-3];person=token[4:]
        if person in EXCLUDED or person in MARKER_EXCLUSIONS:continue
        raw=read_raw(path);indices,names=eeg_indices(raw.ch_names,channels)
        source=path.relative_to(root).as_posix()
        signal=raw.get_data(picks=indices).astype(np.float64)*1e6
        events,stage_audit=imagery_events(raw.get_data(picks=[raw.ch_names.index('')])[0],schedule,return_audit=True)
        rows=[];values=[]
        for trial,event,start,break_start,entry in events:
            if start+2000>break_start:raise ValueError('Four-second epoch would cross native imagery-stage end')
            label=entry['trial_type']
            row=core.base_row(person,'0','0',source,trial,start,2000,500,label,label)
            row.update(source_participant_id=token,source_schedule_row=event,
                sample_reference='Distributed EDF derivative samples; original pre-export continuous offsets unavailable',
                native_stage_marker='2',source_schedule_onset_ms=entry['onset'],
                source_schedule_duration_ms=entry['duration'],native_break_start_sample=break_start,
                epoch_end_minus_native_break_samples=start+2000-break_start,
                source_array_index=f'EDF native channel indices {indices}, samples[{start}:{start+2000}]',
                event_evidence='Actual native stage-2 trigger sample; hand label from ordinal-matched author event schedule')
            rows.append(row);values.append(core.crop(signal,start,2000))
        info=dict(core.mne_info(raw),source_file=source,source_file_sha256=sha(path),participant_id=person,
            source_participant_id=token,session_id='0',run_id='0',source_eeg_indices=indices,
            original_participant_metadata=participants[token],native_channel_table=channels,
            native_stage_event_audit=stage_audit,
            distributed_edf_measurement_date=str(raw.info.get('meas_date')),
            native_electrodes=electrodes,native_coordinate_system=coords,author_eeg_metadata=props,
            excluded_source_channels=[dict(array_index=i,name=n,reason='Documented CPz reference' if n=='CPz' else 'EOG' if n in ['HEOL','HEOR'] else 'Unnamed stage-trigger channel') for i,n in enumerate(raw.ch_names) if i not in indices],
            source_eog_name_discrepancy='Native HEOR is VEOR in the shared author channel table; excluded EOG retained by native name in evidence',
            publisher_preprocessing_documented='EEGLAB mean removal and 0.5-40 Hz FIR filtering; not locally repeated',
            session_id_evidence='One session/run documented; archive assigns 0',
            fixed_window_max_extension_past_break_samples=max(r['epoch_end_minus_native_break_samples'] for r in rows))
        yield np.stack(values),rows,names,info


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,default=Path('D:/Data/EEGSources/Liu2024'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--offline',action='store_true');p.add_argument('--download-only',action='store_true');a=p.parse_args()
    root=ensure_sources(a.cache,not a.offline)
    if a.download_only:return
    audit_derived(a.cache,root)
    audit_triggers(a.cache,root)
    core.SPECS['liu2024']=dict(SPEC,cache=a.cache.name);core.READERS['liu2024']=records
    result=core.prepare('liu2024',a.cache.parent,a.output)
    core.dump(ROOT/'docs/liu2024-local-results.json',result)


if __name__=='__main__':main()
