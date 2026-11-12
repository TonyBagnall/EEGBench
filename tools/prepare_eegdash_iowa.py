"""Iowa PD/control rest: named channel intersection, native500Hz, no extra DSP."""
import json
from pathlib import Path
import re
import warnings

import numpy as np
from scipy.io import loadmat
from tools import prepare_open_moabb as core
from tools.download_eegdash_diagnosis import CONFIG
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]


def participant_plan(cache):
    rows=core.table(cache/'participants.tsv');groups={'Control':[],'PD':[]}
    if len({r['participant_id'] for r in rows})!=len(rows):raise ValueError('Duplicate source participant')
    for r in rows:
        if r['GROUP'] not in groups:raise ValueError('Unreviewed clinical label')
        groups[r['GROUP']].append(r['participant_id'].removeprefix('sub-'))
    train=set()
    for ids in groups.values():
        ids.sort();n=int(np.floor(.75*len(ids)));train.update(ids[:n])
        if n<2 or len(ids)-n<1:raise ValueError('Insufficient group for split')
    return {r['participant_id'].removeprefix('sub-'):r for r in rows},train


def common_channels(cache):
    tables=sorted(cache.glob('sub-*/eeg/*_channels.tsv'))
    if len(tables)!=149:raise ValueError('Expected full149person BIDS channel inventory')
    rows=[core.table(p) for p in tables];names=[[r['name'] for r in t] for t in rows]
    if any(len(n)!=len(set(n)) for n in names):raise ValueError('Ambiguous native channel names')
    shared=set.intersection(*(set(n) for n in names));shared.discard('Resp')
    # Original first-recording order, explicit name-based selection across layouts.
    selected=[n for n in names[0] if n in shared]
    if len(selected)<50:raise ValueError('Unexpectedly small common EEG sensor set')
    return selected,dict(native_layouts=[list(t) for t in sorted({tuple(n) for n in names})],selected_order=selected,
        policy='Intersection of original source BIDS sensor names across all149recordings, excluding Resp. Exact named mapping to native SET indices, no positional assumptions.',
        nonshared_names=sorted(set.union(*(set(n) for n in names))-set(selected)))


def continuous_segments(events,n_samples):
    cuts={0,n_samples}
    for e in events:
        if str(e.get('type','')).lower()!='boundary':continue
        latency=float(e['latency'])
        if latency==1 and str(e.get('code',''))=='New Segment':continue
        boundary=int(np.floor(latency))
        if 0<boundary<n_samples:cuts.add(boundary)
    cuts=sorted(cuts);return list(zip(cuts[:-1],cuts[1:]))


def records(cache,spec):
    import mne
    people,train=participant_plan(cache);canonical,layout=common_channels(cache);spec['metadata_updates']['channel_harmonisation']=layout
    receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    for f in sorted(receipt['files'],key=lambda f:f['name']):
        if not f['name'].endswith('_eeg.set'):continue
        person=re.search(r'(?:^|/)sub-([^/]+)',f['name'])[1]
        if spec.get('subjects') and person not in spec['subjects']:continue
        participant=people[person];label='1' if participant['GROUP']=='Control' else '2';path=cache/f['name'];d=loadmat(path,simplify_cells=True);d=d.get('EEG',d)
        names=[c['labels'] for c in d['chanlocs']];stem=str(path)[:-7];channels=core.table(stem+'channels.tsv');bids=json.loads(Path(stem+'eeg.json').read_text(encoding='utf-8'))
        if names!=[r['name'] for r in channels] or d['srate']!=500 or bids['SamplingFrequency']!=500 or d['trials']!=1:raise ValueError('Native/BIDS recording schema mismatch')
        picks=[names.index(n) for n in canonical];fdt=path.with_suffix('.fdt');count=int(d['pnts']);nch=int(d['nbchan'])
        if fdt.stat().st_size!=nch*count*4 or d['data']!=fdt.name:raise ValueError('Native FDT pointer or byte count mismatch')
        data=np.memmap(fdt,mode='r',dtype='<f4').reshape(count,nch).T
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_eeglab(path,preload=False,verbose=False)
        if raw.ch_names!=names or raw.n_times!=count or raw.info['sfreq']!=500:raise ValueError('Independent reader identity mismatch')
        if not np.allclose(raw.get_data(start=0,stop=min(2000,count))*1e6,np.asarray(data[:,:min(2000,count)],dtype='<f8'),rtol=1e-12,atol=1e-12):raise ValueError('Independent native microvolt calibration mismatch')
        events=d.get('event',[]);events=[events] if isinstance(events,dict) else list(events);segments=continuous_segments(events,count);rows=[];x=[]
        for segment,(a,b) in enumerate(segments):
            for start in range(a,b-2000+1,2000):
                index=len(rows);row=core.base_row(person,'native_session_unspecified','Rest',f['name'],index,start,2000,500,participant['GROUP'],label)
                row.update(source_epoch_index='',source_event_sample='',original_trial_id='',source_window_index=index,continuous_segment_index=segment,source_label_scope='Original participant GROUP',
                    original_participant_id=participant['participant_id'],original_participant_eeg_id=participant['EEG'],original_clinical_id=participant['ID'],
                    age=participant['AGE'],gender=participant['GENDER'],MOCA=participant['MOCA'],UPDRS=participant['UPDRS'],original_TYPE=participant['TYPE'],
                    source_array_index=f'Original float32 FDT channels{picks}, samples[{start}:{start+2000}], float64 cast without scale change',
                    sample_reference='Stored source file samples, zero-based/end-exclusive; original pre-discontinuity acquisition offsets unknown where boundaries exist')
                rows.append(row);x.append(np.ascontiguousarray(data[picks,start:start+2000],dtype='<f8'))
        if not rows:raise ValueError('No complete source rest windows')
        yield np.stack(x),rows,canonical,dict(source_file=f['name'],source_file_sha256=f['sha256'],participant_id=person,participant_metadata=participant,source_eeg_indices=picks,native_channel_names=names,
            native_channel_types=[str(c.get('type','')) for c in d['chanlocs']],native_sensor_fields=core.native_json(d['chanlocs']),native_history=str(d.get('history','')),native_reference=str(d.get('ref','')),
            native_bids_eeg=bids,native_bids_channel_table=channels,native_events=core.native_json(events),continuous_segments=segments,native_samples=count,native_sampling_frequency_hz=500,
            source_case_count=len(rows),excluded_segment_tail_samples=sum((b-a)%2000 for a,b in segments),native_units='Source BIDS units n/a; EEGLAB microvolt storage convention, independently checked against MNE SI decode',
            duration_note='Source README describes2minutes; actual native lengths vary, retained complete windows cover the supplied Rest recording, no invented fixed crop')


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    conf=CONFIG['iowa_rest'];ds=conf['dataset'];cache=Path(cache_root)/'EEGDash'/ds;people,train=participant_plan(cache)
    spec=dict(name='ParkinsonsRestIowa',source='Singh et al./Iowa resting eyes-open / OpenNeuro ds004584',cache='EEGDash/'+ds,hz=500,points=2000,classes=2,train_subjects=len(train),licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',moabb_revision=None,
        doi='10.18112/openneuro.ds004584.v1.0.0',paper='Singh et al., original source ReferencesAndLinks DOI10.1101/2022.07.26.22278079',labels={'1':'control','2':'parkinsons_disease'},splitter=lambda p,c:set(p)&train,
        evidence_files=['eegdash-diagnosis-plan.md','ds004584-diagnosis-source-lock.json'],cache_evidence_files=['participants.tsv','dataset_description.json','README','original-source-lock.json'],conversion_files=['prepare_eegdash_iowa.py','prepare_eegdash_diagnosis.py','download_eegdash_diagnosis.py','requirements-eegdash-diagnosis.txt'],
        intermediate_directory='classification-intermediate-'+('pilot' if pilot else 'full'),note='PD/control diagnostic groups from original participant GROUP; full source Rest recordings,4second windows at500Hz, no added DSP. Exact named sensor intersection across149source layouts; Resp and nonshared electrodes excluded explicitly. Native float32 FDT values castfloat64, interpreted as microvolts by EEGLAB convention; BIDS unit/type fields n/a. Source cohort related to existing Iowa interval-timing tasks, distinct rest recordings, not an independent participant study.',
        metadata_updates=dict(domain='Med',eegdash_id='on004584',original_source_url='https://openneuro.org/datasets/ds004584/versions/1.0.0',paper_reference='Singh et al., DOI10.1101/2022.07.26.22278079',reference='Source BIDS:Pz reference and AFz ground; native SET ref=common',eeg_reference='Original BIDS and SET reference fields retained',
            split_definition='Fixed whole-subject within original GROUP: sorted string IDs, floor0.75*n TRAIN, remainder TEST.149subjects, explicit memberships saved; no validation archive',
            original_sampling_frequency_hz=None,original_frequency_evidence='Native distributed rate500Hz; pre-export acquisition sampling not independently verified',window_overlap_seconds=0,
            unit_evidence='Native EEGLAB numeric microvolt convention verified against MNE SI decoder; BIDS units n/a, interpretation format-based, factor1 export',
            preprocessing='No added filter,resampling,baseline,normalisation or reference change. Native history and boundaries retained; source SoftwareFilters=n/a does not establish absence of earlier processing.',
            shared_cohort='Iowa PD cohort also represented by existing LongIntervalTask/ShortIntervalTask(ds004579); this preparation uses separate source Rest recordings and must not be counted as an independent clinical study',
            metadata_evidence=dict(direct='Original clinical GROUP and demographics/scales, exact SET/BIDS names/order/template positions/events, source sampling and stored numeric values',documented='Original CC0 and resting eyes-open source protocol',inferred='Microvolt format convention because native BIDS units n/a',assigned='Fixed clinical split and4second windows; named channel intersection'),
            missing_or_inconsistent_metadata=['Layouts replaceFT9/PO3/PO4 withIz/I1/I2 in some recordings; only verified common labels selected, exact index mappings retained','Some recordings have an extra Resp input despite BIDS EEG count; auxiliary identity retained, not treated as EEG','README2minute duration differs from native lengths; no fabricated event timing or duration truncation','Source montage positions appear template-like; units/frame/individual measurement not established','Clinical status provided; medication state not recovered, no ON/OFF claim','Original units/type metadata n/a; physical scale interpretation format-based']))
    if pilot:spec.update(name=spec['name']+'Pilot',subjects=conf['pilot']);output=cache/'pilot-output'
    key='iowa_rest';core.SPECS[key]=spec;core.READERS[key]=records;result=core.prepare(key,cache_root,output);folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    for sensor in m['sensors']:sensor.update(native_channel_index=m['recordings'][0]['source_eeg_indices'][sensor['pre_flat_removal_array_index']],identity_evidence='Exact original name intersection, per-recording native index mappings retained',unit_evidence='EEGLAB convention; BIDS units n/a')
    result=finish(result,m,spec['evidence_files'],spec['conversion_files'],dict(label_mapping=spec['labels'],split_definition=m['split_definition'],channel_harmonisation=m['channel_harmonisation'],eegdash_id='on004584'))
    core.dump(ROOT/'docs'/(ds+'-diagnosis-'+('pilot' if pilot else 'conversion')+'-result.json'),result);return result
