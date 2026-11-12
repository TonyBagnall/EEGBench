"""Native BrainVision/BIDS first-episode psychosis diagnostic cohorts."""
import configparser
import json
from pathlib import Path
import re
import warnings

import numpy as np
from tools import prepare_open_moabb as core
from tools.download_eegdash_diagnosis import CONFIG
from tools.update_dataset_sidecars import finish

ROOT=Path(__file__).resolve().parents[1]


def harmonise_rate(data, source_hz, target_hz=1000):
    """Anti-alias the whole continuous recording before extracting windows."""
    # Native header division can differ from the JSON/literal by one float ULP.
    # Only recognise the reviewed rates here; retain the exact native ratio below.
    if not any(np.isclose(source_hz, known, rtol=1e-12, atol=0)
               for known in (1000, 3000.00030000003)):
        raise ValueError('Unreviewed native sampling frequency')
    values=np.asarray(data,dtype='<f8')
    if source_hz==target_hz:
        return values
    from mne.filter import resample
    # Use the recorded interval, including its small rounding discrepancy.
    return resample(values,up=target_hz,down=source_hz,npad='auto',
                    method='fft',window='auto',pad='reflect_limited',n_jobs=1,
                    verbose=False)


def nonzero_segments(eeg_data, source_hz):
    """Split native recordings around multi-sample all-channel zero dropouts."""
    zero_mask=np.all(eeg_data==0,axis=0);n_samples=eeg_data.shape[1]
    idx=np.flatnonzero(zero_mask)
    if not len(idx):
        return [(0,n_samples)],[]
    splits=np.where(np.diff(idx)>1)[0]+1
    zero_runs=[(int(r[0]),int(r[-1])+1) for r in np.split(idx,splits) if len(r)>=2]
    if not zero_runs:
        return [(0,n_samples)],[]
    if source_hz!=1000:
        raise ValueError('All-zero dropout in resampled recording requires per-segment anti-alias review')
    segments=[];cursor=0
    for a,b in zero_runs:
        if cursor<a:segments.append((cursor,a))
        cursor=b
    if cursor<n_samples:segments.append((cursor,n_samples))
    return segments,zero_runs


def group_split(participants):
    if len({r['participant_id'] for r in participants})!=len(participants):raise ValueError('Duplicate participant identity')
    groups={'Control':[],'Psychosis':[]}
    for row in participants:
        if row['type'] not in groups:raise ValueError('Unreviewed diagnostic label')
        groups[row['type']].append(row['participant_id'].removeprefix('sub-'))
    train=set()
    for ids in groups.values():
        ids.sort();count=int(np.floor(.75*len(ids)))
        if count<2 or len(ids)-count<1:raise ValueError('Insufficient diagnostic group membership')
        train.update(ids[:count])
    return train


def vectorized_brainvision(path):
    text=Path(path).read_text(encoding='utf-8-sig');config=configparser.ConfigParser(interpolation=None);config.optionxform=str
    config.read_string(text[text.index('[Common Infos]'):]);common=config['Common Infos'];binary=config['Binary Infos']
    if common['DataFormat']!='BINARY' or common['DataOrientation']!='VECTORIZED' or binary['BinaryFormat']!='IEEE_FLOAT_32':raise ValueError('Unreviewed native BrainVision encoding')
    if binary.get('UseBigEndianOrder','NO')!='NO':raise ValueError('Unreviewed byte order')
    channels=int(common['NumberOfChannels']);samples=int(common['DataPoints']);hz=1e6/float(common['SamplingInterval']);native_names=[];resolutions=[];declared_units=[]
    for i in range(channels):
        fields=config['Channel Infos'][f'Ch{i+1}'].split(',');native_names.append(fields[0]);resolution=fields[2].strip() if len(fields)>2 else '';unit=fields[3].strip() if len(fields)>3 else ''
        if unit not in ['', 'µV','μV','uV']:raise ValueError('Unreviewed native physical unit')
        resolutions.append(float(resolution) if resolution else 1.0);declared_units.append(unit or 'Unspecified; BrainVision microvolt default')
    source=Path(path).parent/common['DataFile']
    if source.resolve().parent!=Path(path).parent.resolve() or source.stat().st_size!=channels*samples*4:raise ValueError('Native binary path or byte count mismatch')
    data=np.memmap(source,dtype='<f4',mode='r').reshape(channels,samples)
    return data,dict(native_channel_names=native_names,source_eeg_indices=None,native_resolutions_uV=resolutions,native_declared_units=declared_units,native_sampling_frequency_hz=hz,native_samples=samples,native_channels=channels,native_data_file=source.name,native_header=text)


def records(cache,spec):
    import mne
    participants=core.table(cache/'participants.tsv');lookup={r['participant_id'].removeprefix('sub-'):r for r in participants};receipt=json.loads((cache/'download-receipt.json').read_text(encoding='utf-8'))
    for file in sorted(receipt['files'],key=lambda f:f['name']):
        if not file['name'].endswith('_eeg.vhdr'):continue
        person=re.search(r'(?:^|/)sub-([^/]+)',file['name'])[1]
        if spec.get('subjects') and person not in spec['subjects']:continue
        participant=lookup[person];label='1' if participant['type']=='Control' else '2';path=cache/file['name'];stem=str(path)[:-8]
        channels=core.table(stem+'channels.tsv');bids=json.loads(Path(stem+'eeg.json').read_text(encoding='utf-8'));data,info=vectorized_brainvision(path)
        hz=info['native_sampling_frequency_hz']
        if len(channels)!=info['native_channels'] or not np.isclose(bids['SamplingFrequency'],hz,rtol=1e-12):raise ValueError('Native/BIDS shape or frequency mismatch')
        picks=[i for i,c in enumerate(channels) if c['type']=='EEG'];names=[channels[i]['name'] for i in picks]
        if len(picks)!=61 or len(set(names))!=len(names) or len(channels)!=64:raise ValueError('Unreviewed source sensor layout')
        if any(channels[i]['units'] not in ['microV','µV','uV'] for i in picks):raise ValueError('BIDS physical units unknown')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=mne.io.read_raw_brainvision(path,preload=False,verbose=False)
        if raw.ch_names!=info['native_channel_names'] or raw.n_times!=info['native_samples'] or not np.isclose(raw.info['sfreq'],hz,rtol=1e-12):raise ValueError('Independent native decoder disagreement')
        scale=np.asarray(info['native_resolutions_uV'],dtype='<f8')
        first=np.asarray(data[:,:2000],dtype='<f8')*scale[:,None]
        if not np.allclose(raw.get_data(start=0,stop=2000)*1e6,first,rtol=1e-12,atol=1e-12):raise ValueError('Native microvolt calibration disagreement')
        eeg_uV=np.asarray(data[picks],dtype='<f8')*scale[picks,None]
        segments,zero_runs=nonzero_segments(eeg_uV,hz)
        processed=harmonise_rate(eeg_uV,hz)
        rows=[];x=[];points=4000
        if zero_runs:
            window_bounds=[(seg_idx,start,start,start+points) for seg_idx,(seg_a,seg_b) in enumerate(segments) for start in range(seg_a,seg_b-points+1,points)]
            trailing_samples=sum((seg_b-seg_a)%points for seg_a,seg_b in segments)
        else:
            # Never let rounded resampling length create a window beyond source time.
            count=min(processed.shape[1]//points,int(np.floor(info['native_samples']/hz/4)))
            window_bounds=[(0,idx*points,round(idx*4*hz),round((idx+1)*4*hz)) for idx in range(count)]
            trailing_samples=info['native_samples']-round(count*4*hz)
        for index,(seg_idx,start,native_start,native_end) in enumerate(window_bounds):
            row=core.base_row(person,'native_session_unspecified','Rest',file['name'],index,native_start,native_end-native_start,hz,participant['type'],label)
            row.update(source_epoch_index='',source_event_sample='',original_trial_id='',source_window_index=index,continuous_segment_index=seg_idx,source_label_scope='Original participant diagnostic type',
                source_array_index=f'Native channels{picks}; whole-recording calibrated float64 resampling before output samples[{start}:{start+points}]',
                original_sampling_frequency_hz=hz,processed_sampling_frequency_hz=1000,
                processed_start_sample=start,processed_end_sample=start+points,
                resampling_applied=hz!=1000,
                resampling_support='Whole continuous recording; native bounds describe corresponding time interval, not exclusive filter support',
                original_participant_id=participant['participant_id'],age=participant.get('age',''),gender=participant.get('gender',''),race=participant.get('race',''),ethnicity=participant.get('ethnicity',''),
                channel_label_decision='Use author-provided BIDS channel names in original row order; generic native EEG001..EEG064 names preserved in recording metadata. No array reordering.',
                original_session_id='',original_partition='unsplit')
            rows.append(row);x.append(np.ascontiguousarray(processed[:,start:start+points]))
        if not x:raise ValueError('No complete diagnostic window')
        info.update(source_file=file['name'],source_file_sha256=file['sha256'],participant_id=person,participant_metadata=participant,source_eeg_indices=picks,
            bids_channel_names=[c['name'] for c in channels],native_channel_types=[c['type'] for c in channels],native_bids_channels=channels,native_bids_eeg=bids,
            nonzero_segments=segments,excluded_all_zero_runs=zero_runs,
            source_case_count=len(rows),excluded_trailing_native_samples=trailing_samples,processed_samples=processed.shape[1],
            processed_sampling_frequency_hz=1000,resampling_applied=hz!=1000,
            resampling_method='MNE FFT, recorded source frequency to1000Hz, npad=auto, window=auto, pad=reflect_limited, n_jobs=1; spectral anti-alias truncation; whole recording before windows' if hz!=1000 else 'Identity; original1000Hz samples retained',
            original_event_timing='No event table supplied; windows cover the source continuous recording labelled as resting fixation, no fabricated acquisition trial IDs',
            channel_label_evidence='Native headers use generic EEG001..EEG064. Official BIDS channel table supplies physical names/types in matching64-row order; explicit source metadata mapping, not invented standard electrodes',
            units_evidence='BIDS EEG channels explicitly microV; native BrainVision resolution blank implies1 in default microvolt convention, checked against independent MNE calibrated decode')
        yield np.stack(x),rows,names,info


def prepare(key,cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    conf=CONFIG[key];ds=conf['dataset'];cache=Path(cache_root)/'EEGDash'/ds;train=group_split(core.table(cache/'participants.tsv'));sample='First' if key=='psychosis1' else 'Second'
    spec=dict(name='PsychosisRest'+sample,source=f'PhalenFEP / OpenNeuro {ds} / EEGDash {conf["eegdash"]}',cache='EEGDash/'+ds,hz=1000,points=4000,classes=2,train_subjects=len(train),
        licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',moabb_revision=None,doi=f'10.18112/openneuro.{ds}.v{conf["ref"]}',
        paper='Phalen,Coffman,Ghuman,Sejdic,Salisbury(2020), Non-negative matrix factorization reveals resting-state cortical alpha network abnormalities in the first-episode schizophrenia spectrum, Biol Psychiatry Cogn Neurosci Neuroimaging5(10),961-970; PMID31451387',
        labels={'1':'control','2':'first_episode_psychosis'},splitter=lambda people,chunks:set(people)&train,
        evidence_files=['eegdash-diagnosis-plan.md',ds+'-diagnosis-source-lock.json'],cache_evidence_files=[p for p in ['dataset_description.json','participants.tsv','participants.json','README','original-source-lock.json'] if (cache/p).is_file()],
        conversion_files=['prepare_eegdash_psychosis.py','prepare_eegdash_diagnosis.py','download_eegdash_diagnosis.py','requirements-eegdash-diagnosis.txt'],intermediate_directory='classification-intermediate-resampled-v1-'+('pilot' if pilot else 'full'),
        note='First-episode psychosis versus control using original diagnostic participant labels. All complete non-overlapping4second windows; retain all participants. Original1000Hz recordings unchanged; original3000.00030000003Hz recordings anti-aliased with whole-recording MNE FFT resampling to1000Hz before windowing, authorised9November2026.61BIDS-labelledEEG channels before flat review. Float64 microvolt calibration; BIDS names mapped by original row position, no array reordering.',
        metadata_updates=dict(domain='Med',eegdash_id=conf['eegdash'],original_source_url=f'https://openneuro.org/datasets/{ds}/versions/{conf["ref"]}',
            paper_reference='Phalen et al.(2020), PMID31451387, original dataset ReferencesAndLinks',eeg_reference='TP9, source BIDS EEGReference',reference='TP9, original BIDS',
            split_definition='Fixed within each clinical group: sorted native string IDs, floor0.75*n TRAIN, remainder TEST; whole subjects, no validation export',
            window_overlap_seconds=0,preprocessing='Float64 native microvolt calibration, source EEG selection, whole-recording anti-alias FFT resampling from recorded3000.00030000003Hz to1000Hz where required; native1000Hz unchanged. MNE npad=auto, window=auto, pad=reflect_limited, n_jobs=1. No added reference, baseline or normalisation. BIDS SoftwareFilters=n/a does not prove absence of earlier processing.',
            sampling_frequency_policy='Native rate retained per recording/case; processed1000Hz. Use exact recorded interval rather than silently rounding3000.00030000003 to3000. Resample full recordings before cutting4s windows; native interval bounds are timing provenance, not finite filter support.',
            unit_evidence='Original BIDS microV agrees with BrainVision default microvolt resolution; independent MNE SI decode checked',
            metadata_evidence=dict(direct='Original diagnostic participant type and demographics, native binary/header and BIDS channel names/types/units/order, source recording bounds and reference',assigned='Clinical class encoding and whole-subject split; consecutive4second windows, no original trial IDs invented',documented='Original source CC0, FEP cohort/resting fixation protocol and related paper'),
            missing_or_inconsistent_metadata=['Native headers have generic channel labels; BIDS table supplies explicit positional physical labels, both retained','M2 labelled EEG by source; excluded only if global flat rule triggers, no guessed role for MISC channel','No measured electrode geometry or original event-level rest onset recovered','Two source cohorts native participant lists are disjoint; originalREADME says10people were already reassigned, do not drop them twice; binary identity gate still required across sources','Small-group generalisation is a research benchmark, not evidence of clinical diagnostic performance']))
    if pilot:spec.update(name=spec['name']+'ResampledPilot',subjects=conf['pilot']);output=cache/'pilot-output'
    core.SPECS[key]=spec;core.READERS[key]=records;result=core.prepare(key,cache_root,output);folder=Path(result['path']);name=result['dataset'];m=json.loads((folder/(name+'_metadata.json')).read_text(encoding='utf-8'))
    picks=m['recordings'][0]['source_eeg_indices']
    for sensor in m['sensors']:
        sensor['native_channel_index']=picks[sensor['pre_flat_removal_array_index']];sensor['native_header_name']=m['recordings'][0]['native_channel_names'][sensor['native_channel_index']];sensor['identity_evidence']='Official BIDS channel row at native array index; generic native header label retained'
    result=finish(result,m,spec['evidence_files'],spec['conversion_files'],dict(label_mapping=spec['labels'],split_definition=m['split_definition'],eegdash_id=conf['eegdash'],channel_label_mapping='Original BIDS row positions, no physical array reordering'))
    if not pilot:
        inter=cache/spec['intermediate_directory']
        npz_files=list(inter.glob('*.npz')) if inter.is_dir() else []
        for f in npz_files:f.unlink()
        if inter.is_dir() and not any(inter.iterdir()):inter.rmdir()
        result['cleaned_intermediate_npz_files']=len(npz_files)
    core.dump(ROOT/'docs'/(ds+'-diagnosis-'+('pilot' if pilot else 'conversion')+'-result.json'),result)
    return result
