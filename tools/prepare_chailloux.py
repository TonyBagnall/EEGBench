"""Chailloux2020 native BrainVision -> SymbolAttention .ts with provenance."""
import argparse
import copy
import json
from pathlib import Path
import re
import shutil

import numpy as np
from tools import prepare_open_moabb as core

ROOT=Path(__file__).resolve().parents[1]
CHANNELS=['FZ','Cz','P3','PZ','P4','PO7','PO8','Oz','Timestamp']
REVISION='153d0a1633adbf7d079eeabc866a2ad727bcff46'


def markers(text):
    """Native VMRK positions are one-based; retain marker ordinal and text."""
    result=[]
    for line in text.splitlines():
        match=re.match(r'Mk(\d+)=(.*)',line)
        if not match:continue
        fields=match[2].split(',')
        if fields[0]!='trigger' or len(fields)<5:raise ValueError('Unknown native marker type')
        result.append(dict(marker_number=int(match[1]),code=fields[1],position_1based=int(fields[2]),size=int(fields[3]),channel=int(fields[4])))
    if any(b['position_1based']<=a['position_1based'] for a,b in zip(result,result[1:])):raise ValueError('Unordered/coincident markers require review')
    return result


def flash_labels(events,grid,allow_missing_target=False,strict_grid=True):
    target=None;block=0;result=[]
    for event in events:
        code=event['code']
        if code=='201':block+=1;target=None
        elif code=='200':target=None
        elif code in ['202','203']:continue
        elif re.fullmatch(r'10[1-9]',code):
            target=int(code[-1])
            if (strict_grid and target>grid) or not block:raise ValueError('Target outside block/grid')
        elif re.fullmatch('[1-9]',code):
            if (strict_grid and int(code)>grid) or (target is None and not allow_missing_target):raise ValueError('Flash without valid attended target')
            result.append(dict(event,block_index_1based=block,target_symbol=target,label=None if target is None else '2' if int(code)==target else '1'))
        else:raise ValueError(f'Unknown source marker: {code}')
    if not result and not allow_missing_target:raise ValueError('No labelled flashes')
    return result


def records(cache,spec):
    import mne
    paths=sorted(cache.glob('sub-*/ses-*/eeg/*_eeg.vhdr'),key=lambda p:(int(p.parts[-4][4:]),p.parts[-3],p.name))
    seen_recordings={}
    for path in paths:
        match=re.fullmatch(r'sub-(\d+)_ses-(\d+)_task-(cnos|ctos)_run-([456789](?:F|H)?)_eeg.vhdr',path.name)
        if not match:raise ValueError(f'Unknown source identity {path}')
        person,session,task,run=match.groups()
        if spec.get('subjects') and person not in spec['subjects']:continue
        raw=mne.io.read_raw_brainvision(path,preload=False,verbose=False)
        native=markers(path.with_suffix('.vmrk').read_text(encoding='utf-8-sig'))
        labels=flash_labels(native,int(run[0]),allow_missing_target=True,strict_grid=False)
        if not labels:
            spec['metadata_updates']['excluded_source_recordings'].append(dict(source_file=path.relative_to(cache).as_posix(),
                native_channel_names=raw.ch_names,native_samples=raw.n_times,native_marker_count=len(native),
                reason='No native flash events: no classification cases; placeholder/unknown sensors not assigned scalp names'))
            raw.close();continue
        if raw.ch_names!=CHANNELS or raw.info['sfreq']!=256 or not np.array_equal(raw._cals,np.full(9,1e-6)):raise ValueError('Changed channel order/frequency/default calibration')
        binary_sha=core.sha(path.with_suffix('.eeg'))
        if binary_sha in seen_recordings:
            first=seen_recordings[binary_sha]
            if first['person']!=person or first['markers']!=native:raise ValueError('Identical source waveform with conflicting subject/markers: manual review required')
            spec['metadata_updates']['excluded_source_recordings'].append(dict(source_file=path.relative_to(cache).as_posix(),
                reason='Exact duplicate native EEG binary and marker stream of earlier file for same participant',
                retained_source_file=first['source_file'],native_eeg_sha256=binary_sha,excluded_flash_count=len(labels)))
            raw.close();continue
        seen_recordings[binary_sha]=dict(person=person,markers=native,source_file=path.relative_to(cache).as_posix())
        header=path.read_text(encoding='utf-8-sig')
        if not all(t in header for t in ['DataOrientation=MULTIPLEXED','BinaryFormat=IEEE_FLOAT_32','NumberOfChannels=9']):raise ValueError('Unexpected binary layout')
        binary=path.with_suffix('.eeg')
        if binary.stat().st_size!=raw.n_times*9*4:raise ValueError('Wrong binary length')
        data=np.memmap(binary,dtype='<f4',mode='r',shape=(raw.n_times,9))
        # Keep native numeric values directly, avoiding a V-to-uV round trip.
        probe=np.asarray(data[:min(512,raw.n_times)].T,dtype='<f8')
        if not np.array_equal(probe*1e-6,raw.get_data(start=0,stop=probe.shape[1])):raise ValueError('Direct binary and MNE decoding disagree')
        prefix=path.name[:-9];channel_rows=core.table(path.with_name(prefix+'_channels.tsv'))
        if [r['name'] for r in channel_rows]!=CHANNELS:raise ValueError('BIDS sensor table disagrees with arrays')
        event_rows=core.table(path.with_name(prefix+'_events.tsv'))
        if len(event_rows)!=len(native):raise ValueError('BIDS/native event counts disagree')
        for r,e in zip(event_rows,native,strict=True):
            if r['value']!=e['code'] or int(r['sample'])!=e['position_1based'] or abs(float(r['onset'])*256-(e['position_1based']-1))>1e-5:raise ValueError('BIDS/native event alignment differs')
        rows=[];values=[];excluded=[];source=path.relative_to(cache).as_posix()
        for ordinal,event in enumerate(labels):
            start=event['position_1based']-1;end=start+256
            if event['label'] is None:
                excluded.append(dict(event,reason='Flash has no attended-target marker in current block; never carry a previous block target'));continue
            if end>raw.n_times:
                excluded.append(dict(event,reason='Incomplete one-second epoch at recording end'));continue
            row=core.base_row(person,session,run,source,ordinal,start,256,256,event['code'],event['label'])
            row.update(source_epoch_index='',source_event_sample_1based=event['position_1based'],
                native_marker_number=event['marker_number'],source_array_index=f'BrainVision float32 samples[{start}:{end}], channels[0:8], transposed',
                task_id=task,filename_grid_symbols=int(run[0]),block_index_1based=event['block_index_1based'],target_symbol=event['target_symbol'],
                source_flash_symbol=event['code'],label_evidence='Native target marker10X selects attended symbolX within block; compare native flash1-9',
                native_timestamp_start=float(data[start,8]),native_timestamp_last_sample=float(data[end-1,8]),
                timestamp_evidence='Native Timestamp column, unit/timebase unspecified; float32 quantisation prevents precise event timing; use native sample indices',
                source_epoch_id_evidence='Original recording continuous; event_index is assigned flash ordinal, native_marker_number is recovered',
                stimulus_condition=f'Native condition code {run[-1]}; SF/CF mapping not independently recovered' if run[-1] in ['F','H'] else 'Best-performing stimulation type per protocol; native subtype not encoded',
                exported_native_channel_indices='[0,1,2,3,4,5,6,7]')
            rows.append(row);values.append(np.asarray(data[start:end,:8].T,dtype='<f8'))
        info=dict(core.mne_info(raw),source_file=source,source_file_sha256=core.sha(path),participant_id=person,session_id=session,run_id=run,
            source_eeg_indices=list(range(8)),native_binary_format='Little-endian float32, multiplexed',native_marker_count=len(native),
            source_channels_table=channel_rows,source_eeg_json=json.loads(path.with_name(prefix+'_eeg.json').read_text()),
            channel_types_documented=['EEG']*8+['timestamp'],unit_evidence='Unit omitted in VHDR and unknown in BIDS; MNE assumes microvolts; native numeric values unchanged',
            reference_evidence='Native EEG JSON M2 and original README right mastoid; source loader right-earlobe description is less precise',
            source_metadata_discrepancies=['BIDS types all unknown and EEGChannelCount0 despite documented8EEG','BIDS sample field equals one-based VMRK position; onset uses zero-based position'],
            excluded_incomplete_cases=excluded,source_flash_count=len(labels),epoch_overlap='One-second flash epochs overlap within recordings; entire subjects assigned together')
        info['retained_flash_ordinals']=[r['event_index'] for r in rows]
        info['mne_default_channel_types']=info['native_channel_types'];info['native_channel_types']=[r['type'] for r in channel_rows]
        timestamps=np.asarray(data[:,8]);steps=np.unique(np.diff(timestamps))
        info['source_timestamp']=dict(first=float(timestamps[0]),last=float(timestamps[-1]),distinct_values=int(len(np.unique(timestamps))),
            step_values=steps.tolist(),units='Unspecified; values retained without conversion',
            warning='Large absolute timestamps stored upstream as float32 are coarsely quantised; do not infer exact acquisition times or epoch boundaries from this column')
        info['filename_grid_symbols']=int(run[0]);info['observed_flash_symbols']=sorted({int(e['code']) for e in labels})
        info['filename_grid_disagrees_with_events']=any(i>int(run[0]) for i in info['observed_flash_symbols'])
        raw.close()
        yield np.stack(values) if values else np.empty((0,8,256),dtype='<f8'),rows,CHANNELS[:8],info


SPEC=dict(name='SymbolAttention',source='Chailloux2020 / OpenNeuro ds003190 v1.0.1',cache='Chailloux2020',
    hz=256,points=256,classes=2,train_subjects=14,licence='CC0-1.0',licence_url='https://creativecommons.org/publicdomain/zero/1.0/',
    doi='10.18112/openneuro.ds003190.v1.0.1',labels={'1':'NonTarget','2':'Target'},
    paper='Chailloux Peguero, Mendoza-Montoya and Antelis (2020), Single-Option P300-BCI Performance Is Affected by Visual Stimulation Conditions, Sensors20(24)7198; DOI10.3390/s20247198',
    note='All available cnos/ctos runs, native participant/session/run tokens and EEG order preserved. Derive target/non-target from native block target10X and flash1-9. One-second epochs start at zero-based native VMRK position-1; overlap within recordings, never across subject partitions. Native float32 numeric values cast directly to float64, presumed microvolt scale under BrainVision default; no filter, baseline, rereference or resampling. Timestamp excluded; all8 EEG retained before global flat policy. Native BIDS EEGChannelCount0/types unknown contradict documented sensors; unit field absent. Native M2 reference retained; no invented individual montage.',
    evidence_files=['symbol-attention-preparation.md','symbol-attention-licence-evidence.json','symbol-attention-source-inspection.json','symbol-attention-source-lock.json'],cache_evidence_files=['dataset_description.json','LICENSE','README','participants.tsv','moabb-chailloux2020.py'],
    conversion_files=['prepare_chailloux.py','download_openneuro_release.py','download_chailloux.py'],
    validation_updates=dict(source_sensor_identity='Every included VHDR and BIDS sensor table checked against native arrays; FZ/PZ spelling/order preserved; no-event placeholder files excluded explicitly'),
    metadata_updates=dict(excluded_source_recordings=[],original_source_url='https://openneuro.org/datasets/ds003190/versions/1.0.1',reference_paper_doi='10.3390/s20247198',
        reference='M2 (right mastoid), source EEG JSON and original README',ground='AFz, documented in original README',
        channel_positions=None,montage='Documented 10-20 placement; individual coordinates absent; no synthetic positions assigned',
        unit_evidence='VHDR unit omitted, BIDS unknown; microvolt interpretation inferred from BrainVision default/MNE convention; numerical factor1',
        overlap='One-second flash epochs overlap within source recording; no subject/recording crosses partitions',
        missing_or_inconsistent_metadata=['Source has no fixed TRAIN/TEST: archive uses14 lowest numeric subject IDs train, remaining5 test',
            'Physical units inferred, not explicit; native numeric values preserved',
            'BIDS EEGChannelCount0 and unknown types conflict with original README8EEG and native labels; Timestamp excluded',
            'BIDS sample values use one-based native VMRK positions, despite zero-based onset times; converter explicitly subtracts1',
            'Individual demographics/electrode positions and native acquisition filtering unavailable',
            'Available sessions/runs vary; inventory reports actual files rather than assuming19x3x7'],
        metadata_evidence=dict(direct='Subject/session/run/file tokens, channels, marker ordinals/positions/symbols, EEG JSON M2, fs256 and binary float32 arrays',
            documented='Sensor roles, AFz ground, M2 reference and protocol in original README/paper',
            assigned='Target encoding, one-second epochs and subject-disjoint archive split; source has no epoch IDs or fixed partitions',
            inferred='Microvolt interpretation follows BrainVision default; no synthetic geometry')))


def numeric_split(people,chunks):
    return set(sorted(people,key=int)[:14])


def prepare(cache_root=Path('D:/Data/EEGSources'),output=Path('D:/Data/EEG'),pilot=False):
    spec=copy.deepcopy(SPEC);spec['splitter']=numeric_split
    cache=Path(cache_root)/spec['cache']
    spec['cache_evidence_files'] += [p.relative_to(cache).as_posix() for p in sorted(cache.glob('sub-*/ses-*/eeg/*')) if p.suffix in ['.tsv','.json','.vhdr','.vmrk']]
    if pilot:
        spec['name']='SymbolAttentionPilot';spec['subjects']=['01','019'];spec['splitter']=lambda people,chunks:{'01'}
        spec['metadata_updates']['split_definition']='Pilot only: subject01 train,019 test'
    else:spec['metadata_updates']['split_definition']='Original numeric subject IDs1-14 train,15-19 test; tokens01-09/010-019 preserved as strings; all available sessions/runs per person retained'
    core.SPECS['chailloux']=spec;core.READERS['chailloux']=records
    return finish_sidecars(core.prepare('chailloux',cache_root,output))


def finish_sidecars(result):
    import csv
    folder=Path(result['path']);name=result['dataset'];changed=[]
    path=folder/f'{name}_metadata.json';metadata=json.loads(path.read_text())
    metadata['aliases']=['Chailloux2020','OpenNeuro ds003190 v1.0.1','Single-Option P300-BCI',json.loads((folder/'source_metadata/dataset_description.json').read_text())['Name'],'NEMAR raw mirror on003190 (pinned loader)','NEMAR nm000262 (BIDS derivative of same OpenNeuro source)']
    metadata['preprocessing']='Direct native float32-to-float64 EEG values; presumed microvolt units, factor1. One-second native flash-event crops; Timestamp excluded. No filter, resampling, baseline or rereferencing.'
    metadata['original_partition']='No original fixed classification partition; archive assigns whole participants'
    metadata['case_order']='Participants sorted numerically, then native session token and filename, then native flash-marker order; never shuffled'
    metadata['excluded_case_count']=sum(len(r['excluded_incomplete_cases']) for r in metadata['recordings'])
    metadata['source_flash_count']=sum(r['source_flash_count'] for r in metadata['recordings'])
    if result['train_cases']+result['test_cases']+metadata['excluded_case_count']!=metadata['source_flash_count']:raise ValueError('Source flash/exclusion/export accounting mismatch')
    metadata['excluded_duplicate_recording_flash_count']=sum(r.get('excluded_flash_count',0) for r in metadata['excluded_source_recordings'])
    metadata['distributed_source_flash_count']=metadata['source_flash_count']+metadata['excluded_duplicate_recording_flash_count']
    metadata['source_recording_files_including_no_event_placeholders']=len(metadata['recordings'])+len(metadata['excluded_source_recordings'])
    metadata['filename_grid_discrepancies']=[dict(source_file=r['source_file'],filename_grid_symbols=r['filename_grid_symbols'],observed_flash_symbols=r['observed_flash_symbols']) for r in metadata['recordings'] if r['filename_grid_disagrees_with_events']]
    metadata['source_timestamp_evidence']='Native timestamps retained per case and recording; upstream float32 precision is coarse at large absolute values. Unit/timebase not established; use native sample indices.'
    for sensor in metadata['sensors']:
        sensor.update(native_channel_index=CHANNELS.index(sensor['name']),units_evidence='Unit omitted in native VHDR; microvolt interpretation follows BrainVision default, values unchanged',
            type_evidence='Original dataset README identifies first8 as EEG; source BIDS tables say unknown',position=None,reference='M2 (right mastoid), documented and EEG JSON')
    core.dump(path,metadata);changed.append(path)
    path=folder/'channels.tsv'
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,list(metadata['sensors'][0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(metadata['sensors'])
    changed.append(path)
    path=folder/f'README_{name}.md';s=path.read_text(encoding='utf-8').replace('Float64 microvolts.','Native numerical values cast to float64; microvolt units are inferred, not embedded in the files.');path.write_text(s,encoding='utf-8');changed.append(path)
    path=folder/'metadata-completeness.json';core.dump(path,dict(evidence=metadata['metadata_evidence'],
        direct_fields=['participant_id','session_id','run_id','source_file','native_marker_number','source_event_sample_1based','source_flash_symbol','target_symbol','native_timestamp_start','native_timestamp_last_sample','channel_names','sampling_frequency_hz'],
        inferred=['microvolt interpretation','target/non-target encoding from native target/flash equality','archive-defined whole-subject split'],
        missing=['original pre-BIDS matrix row IDs beyond native files','individual demographics','individual electrode coordinates','native explicit physical unit','native acquisition filter settings','precise original timestamps'],
        inconsistent=metadata['missing_or_inconsistent_metadata'],excluded_recordings=metadata['excluded_source_recordings'],excluded_cases=metadata['excluded_case_count']));changed.append(path)
    for filename in SPEC['evidence_files']:
        path=folder/'source_metadata'/filename;shutil.copy2(ROOT/'docs'/filename,path);changed.append(path)
    path=folder/'conversion_code/prepare_chailloux.py';shutil.copy2(Path(__file__),path);changed.append(path)
    path=folder/f'{name}_manifest.json';manifest=json.loads(path.read_text())
    manifest.update(original_source_url=metadata['original_source_url'],reference_paper_doi=metadata['reference_paper_doi'],licence_url=SPEC['licence_url'],
        label_mapping=SPEC['labels'],split_definition=metadata['split_definition'],unit_evidence=metadata['unit_evidence'])
    for file in changed:manifest['artifacts'][file.relative_to(folder).as_posix()]=dict(bytes=file.stat().st_size,sha256=core.sha(file))
    core.dump(path,manifest)
    result['size_GB']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())/1e9
    p=ROOT/'docs/open-moabb-conversion-results.json';results=json.loads(p.read_text());results['chailloux']=result;core.dump(p,results)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-root',type=Path,default=Path('D:/Data/EEGSources'));p.add_argument('--output',type=Path,default=Path('D:/Data/EEG'));p.add_argument('--pilot',action='store_true');a=p.parse_args();prepare(a.cache_root,a.output,a.pilot)
