"""Recording-based native adapters for Rozado, Cho and Daly."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import warnings
import zipfile

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core


def nearest_sample(times,stamp):
    """Raw XDF timestamps can have packet jitter and need not be sorted."""
    times=np.asarray(times)
    if not len(times) or not np.isfinite(times).all():raise ValueError('Invalid XDF timestamps')
    index=int(np.argmin(np.abs(times-stamp)))
    if abs(times[index]-stamp)>.05:raise ValueError('Cue not within50ms of native EEG clock')
    return index


def rozado_records(cache,spec):
    import pyxdf
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));root=(cache/'extracted').resolve();root.mkdir(exist_ok=True)
    selected=spec.get('subjects')
    for f in receipt['files']:
        if not f['name'].endswith('.rar'):continue
        # Extract the requested native pilot participants only. Full extraction
        # uses7-Zip's archive-path protection, into this named source directory.
        patterns=[p+'/exp*/experiment.xdf' for p in selected] if selected else ['*/exp*/experiment.xdf']
        subprocess.run(['C:/Program Files/7-Zip/7z.exe','x',str(cache/f['name']),'-o'+str(root),'-y','-bso0',*patterns],check=True)
    paths=sorted(root.glob('*/exp*/experiment.xdf'),key=lambda p:(int(p.parts[-3]),p.parts[-2]))
    for path in paths:
        person=path.parts[-3];run=path.parts[-2]
        if selected and person not in selected:continue
        streams,header=pyxdf.load_xdf(str(path),synchronize_clocks=False,dejitter_timestamps=False)
        eeg=[s for s in streams if s['info']['type']==['EEG']];markers=[s for s in streams if s['info']['type']==['Markers']]
        if len(eeg)!=1 or len(markers)!=1:raise ValueError('Ambiguous native EEG/marker streams')
        eeg=eeg[0];markers=markers[0];ei=eeg['info'];mi=markers['info']
        if ei.get('hostname')!=mi.get('hostname') or not ei.get('hostname'):raise ValueError('Different XDF clock hosts require explicit synchronisation review')
        channels=ei['desc'][0]['channels'][0]['channel'];names=[c.get('label',[''])[0] for c in channels];types=[c.get('type',[''])[0] for c in channels];units=[c.get('unit',[''])[0] for c in channels]
        picks=[i for i,t in enumerate(types) if t=='EEG'];chosen=[names[i] for i in picks]
        if len(names)!=57 or len(picks)!=32 or picks!=list(range(1,33)) or ei['nominal_srate']!=['512']:raise ValueError('Changed native Rozado sensor schema')
        if any(units[i].lower() not in ['microvolts','microvolt','uv','µv','μv'] for i in picks):raise ValueError('Unknown EEG units; cannot calibrate by guess')
        data=np.asarray(eeg['time_series']);times=np.asarray(eeg['time_stamps']);events=[]
        if data.shape!=(len(times),57):raise ValueError('Native XDF sample alignment mismatch')
        for ordinal,(stamp,value) in enumerate(zip(markers['time_stamps'],markers['time_series'],strict=True)):
            code=str(value[0]).lower()
            if code not in ['left','nothing']:continue
            start=nearest_sample(times,stamp)
            if start+3072>len(data):raise ValueError('Incomplete Rozado imagery/rest trial')
            events.append((ordinal,float(stamp),code,start))
        if len(events) not in [25,50]:raise ValueError('Changed native Rozado cue count')
        rows=[];x=[];source=path.relative_to(root).as_posix()
        for ordinal,stamp,code,start in events:
            dt=np.diff(times[start:start+3072]);span=float(times[start+3071]-times[start])
            if abs(span-3071/512)>.25 or np.max(dt)>.25:raise ValueError('Rozado native window has a substantial timing gap; review before harmonisation')
            label='1' if code=='left' else '2';row=core.base_row(person,'single_visit',run,source,ordinal,start,3072,512,code,label)
            row.update(original_trial_id=str(len(rows)+1),native_marker_index=ordinal,source_event_timestamp=stamp,
                       selected_start_timestamp=float(times[start]),selected_last_timestamp=float(times[start+3071]),cue_alignment_error_seconds=float(times[start]-stamp),
                       native_window_timestamp_span_seconds=span,native_window_max_timestamp_step_seconds=float(np.max(dt)),native_window_nonmonotonic_timestamp_steps=int(np.sum(dt<=0)),
                       sample_reference='Native stored EEG stream sample index, zero-based, end exclusive; seconds fields are nominal index/512, XDF timestamps retained separately',
                       clock_alignment='Common native hostname, raw XDF clocks; nearest raw EEG timestamp; no clock correction/dejittering or waveform resampling',
                       source_array_index=f'Native XDF EEG time_series[{start}:{start+3072},1:33], transposed; Trig1 and EX/AUX excluded',
                       original_partition='unsplit',quality_note='Source documents unusually noisy/common-mode signals for participants10/15; retained unless flat-sensor policy excludes a channel' if person in ['10','15'] else '')
            rows.append(row);x.append(np.ascontiguousarray(data[start:start+3072,picks].T,dtype='<f8'))
        yield np.stack(x),rows,chosen,dict(source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id='single_visit',run_id=run,
            native_channel_names=names,native_channel_types=types,native_channel_units=units,source_eeg_indices=picks,native_stream_info=core.native_json(ei),
            native_marker_info=core.native_json(mi),native_sampling_frequency_hz=512,native_units='Explicit XDF microvolts, unchanged after float64 cast',
            native_clock_offsets=core.native_json(eeg.get('clock_values',[])),timestamp_difference_quantiles_seconds=np.quantile(np.diff(times),[0,.01,.5,.99,1]).tolist(),
            nonmonotonic_timestamp_steps=int(np.sum(np.diff(times)<=0)),source_case_count=len(rows),native_marker_codes=sorted({str(v[0]) for v in markers['time_series']}))


def cho_epochs(d,sequence):
    hz=int(d['srate']);e=np.asarray(d['imagery_event']).ravel();onsets=np.flatnonzero((e>0)&np.r_[True,e[1:]!=e[:-1]])
    count=int(d['n_imagery_trials'])
    if hz!=512 or len(onsets)!=count or count not in [100,120] or set(e)!={0,1}:raise ValueError('Changed Cho native event schema')
    events=[]
    for label,field in [('1','imagery_left'),('2','imagery_right')]:
        a=np.asarray(d[field]);seq=np.asarray(sequence[field]).ravel()
        if a.shape!=(68,len(e)) or len(seq)!=count or not np.all(np.diff(seq)>0):raise ValueError('Cho data/event/sequence mismatch')
        for trial,start in enumerate(onsets):
            if start+1536>len(e):raise ValueError('Incomplete native Cho task')
            events.append((int(seq[trial]),label,field,trial,int(start),np.ascontiguousarray(a[:64,start:start+1536],dtype='<f8')))
    if len({v[0] for v in events})!=len(events):raise ValueError('Ambiguous original Cho trial ordering')
    events.sort(key=lambda e:e[0])
    return events


def cho_records(cache,spec):
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(cache/'trial_sequence.zip') as z:
        for f in sorted(receipt['files'],key=lambda f:f['name']):
            m=re.fullmatch(r'mat_data/s(\d{2})\.mat',f['name'])
            if not m:continue
            person=m[1]
            if spec.get('subjects') and person not in spec['subjects']:continue
            d=loadmat(cache/f['name'],simplify_cells=True)['eeg'];seq_name=[n for n in z.namelist() if Path(n).name==f's{int(person)}_trial_sequence_v1.mat']
            if len(seq_name)!=1:raise ValueError('Missing original trial sequence file')
            sequence=loadmat(z.open(seq_name[0]),simplify_cells=True)['trial_sequence'];events=cho_epochs(d,sequence);rows=[]
            for original_position,label,field,trial,start,x in events:
                row=core.base_row(person,'single_visit','source_run_unknown',f['name']+'/'+field,trial,start,1536,512,label,label)
                row.update(source_file=f['name'],original_trial_id=str(original_position),original_trial_id_evidence='Literal original trial_sequence value; its units and relationship to original continuous sample clock not established',
                           original_sequence_file=seq_name[0],source_class_array=field,native_class_trial_index=trial,native_event_value=1,
                           sample_reference='Native class-specific concatenated array sample indices, zero-based, end exclusive; not original interleaved continuous recording',
                           source_array_index=f'Native eeg.{field}[0:64,{start}:{start+1536}], original event onset at{start}',
                           source_epoch_index=trial,original_partition='unsplit')
                rows.append(row)
            names=[f'source_column_{i+1:02d}' for i in range(64)]
            info=dict(source_file=f['name'],source_file_sha256=f['sha256'],participant_id=person,session_id='single_visit',native_subject=d['subject'],
                source_eeg_indices=list(range(64)),native_channel_names=None,native_channel_types=['EEG']*64+['EMG']*4,anatomical_name_status='Original MAT has coordinates but no sensor labels; opaque column IDs, no invented anatomical labels',
                native_senloc=core.native_json(d['senloc']),native_psenloc=core.native_json(d['psenloc']),coordinate_evidence='Original paper: measured3D positions and unit-sphere projection; senloc units/frame not established',
                native_bad_trial_indices=core.native_json(d['bad_trial_indices']),bad_trial_handling='Retained as native quality annotations, no undocumented rejection',
                native_frame=core.native_json(d['frame']),native_sampling_frequency_hz=512,source_case_count=len(rows),native_comment=str(d['comment']))
            yield np.stack([e[-1] for e in events]),rows,names,info


def daly_records(cache,spec):
    import mne
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'));demographics={r['participant_id']:r for r in core.table(cache/'participants.tsv')}
    files=[f for f in receipt['files'] if f['name'].endswith('.edf')]
    files.sort(key=lambda f:(f['name'].split('/')[0],int(re.search(r'_task-run(\d+)_',f['name'])[1])))
    for f in files:
        person=re.search(r'sub-(\d+)',f['name'])[1];run=re.search(r'_task-run(\d+)_',f['name'])[1]
        if run=='1':raise ValueError('Calibration run must not enter conversion')
        if spec.get('subjects') and person not in spec['subjects']:continue
        path=cache/f['name'];stem=str(path)[:-7];channels=core.table(stem+'channels.tsv');events=core.table(stem+'events.tsv');info=json.loads(Path(stem+'eeg.json').read_text(encoding='utf-8'))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_edf(path,preload=True,verbose=False)
        names=[c['name'] for c in channels]
        if raw.ch_names!=names or len(names)!=19 or raw.info['sfreq']!=1000 or info['SamplingFrequency']!=1000:raise ValueError('Daly native BIDS/EDF sensor/frequency mismatch')
        if any(c['type']!='EEG' or c['units']!='microV' for c in channels) or not np.all(np.asarray(raw._raw_extras[0]['units'])==1e-6):raise ValueError('Unexpected native EDF physical units')
        data=raw.get_data().astype('<f8',copy=False)*1e6;rows=[];x=[];excluded=[]
        for i,event in enumerate(events):
            if event['trial_type'] not in ['1','2']:continue
            onset=float(event['onset']);duration=float(event['duration']);start=int(round(onset*1000))
            if duration!=20 or start<0:raise ValueError('Changed native Daly20s trial definition')
            if start+20000>raw.n_times:
                excluded.append(dict(native_event_index=i,event=event,reason='Native EDF ends before the complete20-second event window',available_samples=raw.n_times-start));continue
            row=core.base_row(person,'single_visit',run,f['name'],i,start,20000,1000,event['trial_type'],event['trial_type'])
            row.update(original_trial_id=str(i+1),source_event_onset=event['onset'],source_event_duration=event['duration'],source_event_file=Path(stem+'events.tsv').relative_to(cache).as_posix(),
                       source_array_index=f'Calibrated EDF EEG channels0:19 samples[{start}:{start+20000}], volts multiplied by1e6 in float64',
                       original_partition='unsplit',age=demographics['sub-'+person]['age'],sex=demographics['sub-'+person]['sex'])
            rows.append(row);x.append(np.ascontiguousarray(data[:,start:start+20000]))
        if not rows:raise ValueError('Targetless recording unexpectedly selected')
        yield np.stack(x),rows,names,dict(source_file=f['name'],source_file_sha256=f['sha256'],participant_id=person,session_id='single_visit',run_id=run,
            source_eeg_indices=list(range(19)),native_channel_names=names,native_channel_types=[c['type'] for c in channels],native_bids_channel_table=channels,native_bids_eeg_json=info,
            native_sampling_frequency_hz=1000,native_units='BIDS microV and EDF1e-6 multiplier agree; MNE calibrated volts multiplied by1e6',native_reference=info['EEGReference'],
            source_case_count=len(rows),excluded_incomplete_cases=excluded,original_labelled_event_count=len(rows)+len(excluded),participant_metadata=demographics['sub-'+person])


def extra_specs(common):
    return {
     'rozado':dict(common,name='ImaginedHandPupils',source='Rozado2015',cache='Rozado2015',hz=512,points=3072,train_subjects=22,
        splitter=lambda people,chunks:set(people)&{str(i) for i in list(range(1,12))+list(range(16,27))},
        labels={'1':'imagined_left_hand_grasp','2':'rest'},doi='10.7910/DVN/28932',paper='Rozado,Duenser,Gruen(2015), DOI10.1371/journal.pone.0121262'),
     'cho':dict(common,name='ImaginedHandsPhysiology',source='Cho2017',cache='Cho2017',hz=512,points=1536,train_subjects=39,
        splitter=lambda people,chunks:set(people)&{f'{i:02d}' for i in range(1,40)},
        labels={'1':'imagined_left_hand','2':'imagined_right_hand'},doi='10.5524/100295',paper='Cho,Ahn,Ahn,Kwon,Jun(2017), DOI10.1093/gigascience/gix034'),
     'daly':dict(common,name='ImaginedHandMusicTempo',source='Daly2020',cache='Daly2020',hz=1000,points=20000,train_subjects=13,
        splitter=lambda people,chunks:set(people)&{f'{i:02d}' for i in range(1,14)},licence='CC-BY-4.0',licence_url='https://creativecommons.org/licenses/by/4.0/',
        labels={'1':'lower_alpha_imagined_right_hand_squeezing','2':'raise_alpha_relaxation'},doi='10.18112/openneuro.ds002720.v1.0.1',paper='Daly et al., Brain-Computer Music Interface tempo data, OpenNeuro ds002720 v1.0.1; original Reading README references2018/2014 analyses')}


READERS={'rozado':rozado_records,'cho':cho_records,'daly':daly_records}
