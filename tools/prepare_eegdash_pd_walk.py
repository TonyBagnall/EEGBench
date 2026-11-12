"""Parkinson's disease versus healthy control during treadmill walking (OpenNeuro ds007526 v1.0.2)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import warnings
import zipfile

import numpy as np
from scipy.io import loadmat

from tools import prepare_open_moabb as core
from tools.download_eegdash_diagnosis import EVIDENCE, blob_sha
from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch
from tools.update_dataset_sidecars import finish

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'ds007526'
REF = '1.0.2'
COMMIT = '3644d723a59035e0f12bb31eba93fb53e5e4cad6'
PILOT_SUBJECTS = ['002', '028', '029', '144']
AUXILIARY_CHANNELS = {'EOG1', 'EOG2', 'EOG3', 'EOG4', 'VREF'}


def walk_participant_plan(participants, walk_Recording_people):
    """Stratified 75/25 whole-subject split across task-walk participants."""
    if len({r['participant_id'] for r in participants}) != len(participants):
        raise ValueError('Duplicate participant_id in participants.tsv')
    if len({r['subject_id'] for r in participants}) != len(participants):
        raise ValueError('Duplicate original subject_id in participants.tsv')
    walk_set = set(walk_Recording_people)
    groups = {'HC': [], 'PD': []}
    excluded = []
    lookup = {}
    for row in participants:
        person = row['participant_id'].removeprefix('sub-')
        group = row['group']
        if group not in groups:
            raise ValueError(f'Unreviewed diagnostic group: {group}')
        if person not in walk_set:
            excluded.append(dict(
                participant_id=person,
                original_participant_id=row['participant_id'],
                original_subject_id=row['subject_id'],
                group=group,
                reason='No task-walk EEG recording in pinned OpenNeuro v1.0.2 release; only resting-state EEG distributed',
            ))
            continue
        lookup[person] = row
        groups[group].append(person)
    if set(lookup) != walk_set:
        raise ValueError('task-walk recording lacks participants.tsv entry')
    train = set()
    for ids in groups.values():
        ids.sort()
        count = int(np.floor(0.75 * len(ids)))
        if count < 2 or len(ids) - count < 1:
            raise ValueError('Insufficient clinical group membership for split')
        train.update(ids[:count])
    return lookup, train, excluded


def walk_continuous_segments(events, eeg_data):
    """Split continuous recording around interior boundary/break-cnt markers and multi-sample zero dropouts."""
    n_samples = int(eeg_data.shape[1])
    bad = np.zeros(n_samples, dtype=bool)
    zero_mask = np.all(eeg_data == 0, axis=0)
    zero_idx = np.flatnonzero(zero_mask)
    zero_runs = []
    if len(zero_idx):
        splits = np.where(np.diff(zero_idx) > 1)[0] + 1
        for run in np.split(zero_idx, splits):
            if len(run) >= 2:
                a, b = int(run[0]), int(run[-1]) + 1
                bad[a:b] = True
                zero_runs.append((a, b))
    cuts = {0, n_samples}
    discontinuity_events = []
    for ev in events:
        etype = str(ev.get('type', '')).strip().lower()
        if etype not in {'boundary', 'break cnt'}:
            continue
        latency_1based = float(ev['latency'])
        duration = float(ev.get('duration', 0.0) or 0.0)
        if etype == 'boundary' and latency_1based == 1.0:
            continue
        start_0based = int(np.floor(latency_1based - 1.0))
        if 0 < start_0based < n_samples:
            cuts.add(start_0based)
        if etype == 'break cnt' and duration > 0:
            a = max(0, start_0based)
            b = min(n_samples, int(np.ceil(latency_1based - 1.0 + duration)))
            if a < b:
                bad[a:b] = True
                cuts.update({a, b})
        discontinuity_events.append(dict(type=str(ev.get('type', '')), latency_1based=latency_1based, duration=duration))
    for a, b in zero_runs:
        cuts.update({a, b})
    ordered = sorted(cuts)
    segments = [(a, b) for a, b in zip(ordered[:-1], ordered[1:]) if a < b and not bad[a:b].any()]
    return segments, dict(discontinuity_events=discontinuity_events, all_zero_runs=zero_runs)


def lock_and_download(cache_root=Path('D:/Data/EEGSources/EEGDash'), pilot=False):
    cache = Path(cache_root) / DATASET
    cache.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    tree_path = cache / 'original-release-tree.json'
    fetch(f'https://api.github.com/repos/OpenNeuroDatasets/{DATASET}/git/trees/{COMMIT}?recursive=1', tree_path)
    tree = json.loads(tree_path.read_text(encoding='utf-8'))
    if tree.get('truncated'):
        raise ValueError('Incomplete original source tree')
    archive = cache / 'original-metadata.zip'
    fetch(f'https://codeload.github.com/OpenNeuroDatasets/{DATASET}/zip/{COMMIT}', archive)
    files = []
    native = []
    with zipfile.ZipFile(archive) as z:
        prefix = z.namelist()[0]
        for entry in tree['tree']:
            if entry['type'] != 'blob':
                continue
            name = entry['path']
            data = z.read(prefix + name)
            if blob_sha(data) != entry['sha']:
                raise ValueError('Original Git blob differs ' + name)
            if entry['mode'] == '120000':
                if '_task-walk_' not in name or Path(name).suffix not in {'.set', '.fdt'}:
                    continue
                pointer = data.decode()
                m = re.search(r'(SHA256|MD5)E-s(\d+)--([0-9a-f]+)\.[^/]+', pointer)
                if not m or len(m[3]) != {'SHA256': 64, 'MD5': 32}[m[1]]:
                    raise ValueError('Unknown original annex key ' + name)
                native.append(dict(
                    name=name,
                    url=f'https://s3.amazonaws.com/openneuro.org/{DATASET}/{name}',
                    bytes=int(m[2]),
                    checksum=m[1].lower() + ':' + m[3],
                    git_blob_sha1=entry['sha'],
                    git_annex_pointer=pointer,
                ))
            else:
                if name.startswith(('.', 'code/')) or ('/eeg/' in name and '_task-walk_' not in name):
                    continue
                target = (cache / name).resolve()
                if not target.is_relative_to(cache.resolve()):
                    raise ValueError('Unsafe original source path')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                files.append(dict(
                    name=name,
                    url=f'https://raw.githubusercontent.com/OpenNeuroDatasets/{DATASET}/{COMMIT}/{name}',
                    bytes=len(data),
                    checksum='sha256:' + hashlib.sha256(data).hexdigest(),
                    git_blob_sha1=entry['sha'],
                ))
    description = json.loads((cache / 'dataset_description.json').read_text(encoding='utf-8-sig'))
    if description.get('License') != 'CC0':
        raise ValueError('Original data licence needs separate review')
    for name in ['dataset_description.json', 'participants.tsv', 'participants.json', 'README', 'CHANGES']:
        if (cache / name).is_file():
            shutil.copy2(cache / name, EVIDENCE / f'{DATASET}-{name}')
    selected = [
        f for f in native
        if not pilot or re.search(r'(?:^|/)sub-([^/]+)', f['name'])[1] in PILOT_SUBJECTS
    ]

    def download_one(f):
        p = cache / f['name']
        fetch(f['url'], p, f['checksum'], f['bytes'])
        print('Verified', f['name'], flush=True)
        return dict(f, sha256=sha(p))

    with ThreadPoolExecutor(4) as pool:
        downloaded_native = list(pool.map(download_one, selected))
    metadata = [dict(f, sha256=sha(cache / f['name'])) for f in files]
    receipt = dict(
        dataset=DATASET,
        source_record_id=DATASET,
        source_revision=f'OpenNeuro {DATASET} v{REF}, Git {COMMIT}',
        original_ref=REF,
        original_commit=COMMIT,
        licence='CC0-1.0',
        pilot=pilot,
        files=metadata + downloaded_native,
        metadata_archive_sha256=sha(archive),
        licence_evidence='Original pinned dataset_description.json License=CC0',
        source_urls=[f'https://openneuro.org/datasets/{DATASET}/versions/{REF}'],
        selection_scope='Root BIDS metadata plus all task-walk EEG sidecars and single-file .set recordings',
    )
    dump(cache / 'download-receipt.json', receipt)
    dump(cache / 'source-record.json', receipt)
    dump(cache / 'original-source-lock.json', receipt)
    dump(EVIDENCE / f'{DATASET}-original-files.json', receipt)
    if not pilot:
        dump(ROOT / 'docs' / f'{DATASET}-diagnosis-source-lock.json', receipt)
    else:
        lock_doc = ROOT / 'docs' / f'{DATASET}-diagnosis-source-lock.json'
        if not lock_doc.exists():
            dump(lock_doc, receipt)
    return receipt


def records(cache, spec):
    import mne
    receipt = json.loads((cache / 'download-receipt.json').read_text(encoding='utf-8'))
    all_walk_people = sorted({
        re.search(r'(?:^|/)sub-([^/]+)', f['name'])[1]
        for f in receipt['files']
        if f['name'].endswith('_task-walk_channels.tsv')
    })
    people, _, excluded = walk_participant_plan(core.table(cache / 'participants.tsv'), all_walk_people)
    spec['metadata_updates']['excluded_participants'] = excluded
    canonical = None
    for f in sorted(receipt['files'], key=lambda item: item['name']):
        if not f['name'].endswith('_task-walk_eeg.set'):
            continue
        person = re.search(r'(?:^|/)sub-([^/]+)', f['name'])[1]
        if spec.get('subjects') and person not in spec['subjects']:
            continue
        participant = people[person]
        label = '1' if participant['group'] == 'HC' else '2'
        path = cache / f['name']
        stem = str(path)[:-7]
        channels = core.table(stem + 'channels.tsv')
        bids = json.loads(Path(stem + 'eeg.json').read_text(encoding='utf-8-sig'))
        d = loadmat(path, simplify_cells=True)
        eeg = d.get('EEG', d)
        names = [c['labels'] for c in eeg['chanlocs']]
        if names != [r['name'] for r in channels] or float(eeg['srate']) != 250.0 or float(bids['SamplingFrequency']) != 250.0 or int(eeg['trials']) != 1:
            raise ValueError('Native/BIDS recording schema mismatch in ' + f['name'])
        picks = [i for i, row in enumerate(channels) if row['type'] == 'EEG' and row['name'] not in AUXILIARY_CHANNELS]
        selected_names = [names[i] for i in picks]
        if len(picks) != 60 or set(names) - set(selected_names) != AUXILIARY_CHANNELS:
            raise ValueError('Unreviewed ds007526 channel layout in ' + f['name'])
        if canonical is None:
            canonical = selected_names
        elif selected_names != canonical:
            raise ValueError('ds007526 scalp channel order differs across recordings')
        if any(channels[i]['units'] not in {'µV', 'μV', 'uV', 'microV'} for i in picks):
            raise ValueError('Unexpected BIDS physical unit in ' + f['name'])
        arr = eeg['data']
        count = int(eeg['pnts'])
        if not isinstance(arr, np.ndarray) or arr.shape != (65, count):
            raise ValueError('Unexpected embedded EEGLAB data array in ' + f['name'])
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw = mne.io.read_raw_eeglab(path, preload=False, verbose=False)
        if raw.ch_names != names or raw.n_times != count or raw.info['sfreq'] != 250.0:
            raise ValueError('Independent EEGLAB reader mismatch in ' + f['name'])
        probe = min(2000, count)
        if not np.allclose(raw.get_data(start=0, stop=probe) * 1e6, np.asarray(arr[:, :probe], dtype='<f8'), rtol=1e-12, atol=1e-10):
            raise ValueError('Independent microvolt calibration mismatch in ' + f['name'])
        eeg_uV = np.asarray(arr[picks], dtype='<f8')
        events = eeg.get('event', [])
        events = [events] if isinstance(events, dict) else list(events)
        segments, seg_audit = walk_continuous_segments(events, eeg_uV)
        points = 1000
        rows = []
        values = []
        for seg_idx, (seg_a, seg_b) in enumerate(segments):
            for start in range(seg_a, seg_b - points + 1, points):
                index = len(rows)
                row = core.base_row(person, 'native_session_unspecified', 'walk', f['name'], index, start, points, 250, participant['group'], label)
                row.update(
                    source_epoch_index='',
                    source_event_sample='',
                    original_trial_id='',
                    source_window_index=index,
                    continuous_segment_index=seg_idx,
                    source_label_scope='Original participant clinical group (HC vs PD)',
                    original_participant_id=participant['participant_id'],
                    original_subject_id=participant['subject_id'],
                    age=participant['age'],
                    sex=participant['sex'],
                    moca=participant['moca'],
                    updrs_part_iii=participant['updrs_part_iii'],
                    updrs_total=participant['updrs_total'],
                    disease_duration_months=participant['disease_duration'],
                    ledd_mg=participant['ledd'],
                    source_array_index=f'Embedded float32 SET channels{picks}, samples[{start}:{start+points}], cast to float64 microvolts',
                )
                rows.append(row)
                values.append(np.ascontiguousarray(eeg_uV[:, start:start + points], dtype='<f8'))
        if not rows:
            raise ValueError('No complete 4-second walking windows in ' + f['name'])
        yield np.stack(values), rows, canonical, dict(
            source_file=f['name'],
            source_file_sha256=f['sha256'],
            participant_id=person,
            participant_metadata=participant,
            source_eeg_indices=picks,
            native_channel_names=names,
            excluded_auxiliary_channels=sorted(AUXILIARY_CHANNELS),
            native_bids_eeg=bids,
            native_bids_channels=channels,
            native_reference=str(eeg.get('ref', '')),
            continuous_segments=segments,
            discontinuity_audit=seg_audit,
            native_samples=count,
            native_sampling_frequency_hz=250,
            source_case_count=len(rows),
            excluded_segment_tail_samples=sum((b - a) % points for a, b in segments),
            unit_evidence='Explicit BIDS microvolt units (µV) match EEGLAB embedded float32 storage and MNE SI decode * 1e6',
        )


def prepare(cache_root=Path('D:/Data/EEGSources'), output=Path('D:/Data/EEG'), pilot=False):
    eegdash_root = Path(cache_root) / 'EEGDash'
    lock_and_download(eegdash_root, pilot=pilot)
    cache = eegdash_root / DATASET
    receipt = json.loads((cache / 'download-receipt.json').read_text(encoding='utf-8'))
    all_walk_people = sorted({
        re.search(r'(?:^|/)sub-([^/]+)', f['name'])[1]
        for f in receipt['files']
        if f['name'].endswith('_task-walk_channels.tsv')
    })
    _, train, excluded = walk_participant_plan(core.table(cache / 'participants.tsv'), all_walk_people)
    spec = dict(
        name='ParkinsonsWalking',
        source=f'Katzir, Vered & Maidan / Tel Aviv Sourasky Medical Center / OpenNeuro {DATASET} v{REF}',
        cache=f'EEGDash/{DATASET}',
        hz=250,
        points=1000,
        classes=2,
        train_subjects=len(train),
        licence='CC0-1.0',
        licence_url='https://creativecommons.org/publicdomain/zero/1.0/',
        moabb_revision=None,
        doi=f'10.18112/openneuro.{DATASET}.v{REF}',
        paper='Katzir, Vered & Maidan (2025), Electroencephalography-Based Clustering Reveals Robust Neurophysiological Subtypes in Parkinson\'s Disease, Movement Disorders, DOI 10.1002/mds.70348',
        labels={'1': 'healthy_control', '2': 'parkinsons_disease'},
        splitter=lambda people, chunks: set(people) & train,
        evidence_files=['eegdash-diagnosis-plan.md', f'{DATASET}-diagnosis-source-lock.json'],
        cache_evidence_files=[p for p in ['dataset_description.json', 'participants.tsv', 'participants.json', 'original-source-lock.json'] if (cache / p).is_file()],
        conversion_files=['prepare_eegdash_pd_walk.py'],
        intermediate_directory='classification-intermediate-' + ('pilot' if pilot else 'full'),
        note='Parkinson\'s disease versus healthy control diagnosis during active treadmill walking (task-walk) from OpenNeuro ds007526 v1.0.2 (133 participants with walking EEG: 23 HC, 110 PD; 11 rest-only participants lack task-walk files). 60 named scalp EEG channels at native 250 Hz in float64 microvolts (excluding EOG1..EOG4 and flat reference channel VREF); consecutive non-overlapping 4-second windows strictly within continuous segments bounded by interior boundary/break-cnt markers.',
        metadata_updates=dict(
            domain='Med',
            original_source_url=f'https://openneuro.org/datasets/{DATASET}/versions/{REF}',
            paper_reference='Katzir, Vered & Maidan (2025), Movement Disorders, DOI 10.1002/mds.70348',
            reference='Native EEGLAB ref=common; VREF vertex reference channel zero-valued in distributed files, BIDS EEGReference=n/a',
            eeg_reference='Original distributed reference retained; no rereferencing applied',
            split_definition='Fixed whole-subject within HC and PD among the 133 task-walk participants: sorted sub-* numeric string IDs, floor(0.75*n) TRAIN (17 HC, 82 PD = 99), remainder TEST (6 HC, 28 PD = 34)',
            window_overlap_seconds=0,
            original_sampling_frequency_hz=250,
            preprocessing='No conversion filtering, resampling, baseline correction, normalisation or rereferencing. 60 scalp EEG channels selected (excluding EOG1..EOG4 and VREF); embedded float32 microvolts cast to float64 and verified against MNE SI decode.',
            excluded_participants=excluded,
            metadata_evidence=dict(
                direct='Original clinical group (HC/PD), MDS-UPDRS/MoCA/LEDD/demographics, embedded SET arrays, BIDS channel names/units (µV) and discontinuity events',
                documented='OpenNeuro CC0 licence and Movement Disorders subtype study protocol during active walking',
                assigned='Stratified 75/25 whole-subject split and consecutive 4-second non-overlapping windows within continuous segments',
            ),
            missing_or_inconsistent_metadata=[
                'mne-bids export marked EOG1..EOG4 and VREF as type EEG; excluded explicitly by channel identity',
                '11 of 144 participants in participants.tsv only have task-rest files and no task-walk recording',
                'BIDS EEGReference and SoftwareFilters fields are n/a; native break-cnt segments excluded rather than bridged',
            ],
        ),
    )
    if pilot:
        spec.update(name=spec['name'] + 'Pilot', subjects=PILOT_SUBJECTS)
        output = cache / 'pilot-output'
    key = 'pd_walk'
    core.SPECS[key] = spec
    core.READERS[key] = records
    result = core.prepare(key, cache_root, output)
    folder = Path(result['path'])
    name = result['dataset']
    m = json.loads((folder / f'{name}_metadata.json').read_text(encoding='utf-8'))
    picks = m['recordings'][0]['source_eeg_indices']
    for sensor in m['sensors']:
        sensor['native_channel_index'] = picks[sensor['pre_flat_removal_array_index']]
        sensor['identity_evidence'] = 'Original 60 scalp EEG channels in native SET/BIDS order; EOG1..EOG4 and VREF excluded'
    result = finish(
        result,
        m,
        spec['evidence_files'],
        spec['conversion_files'],
        dict(
            label_mapping=spec['labels'],
            split_definition=m['split_definition'],
            excluded_participants=m['excluded_participants'],
        ),
    )
    if not pilot:
        inter = cache / spec['intermediate_directory']
        npz_files = list(inter.glob('*.npz')) if inter.is_dir() else []
        for f in npz_files:
            f.unlink()
        if inter.is_dir() and not any(inter.iterdir()):
            inter.rmdir()
        result['cleaned_intermediate_npz_files'] = len(npz_files)
    core.dump(ROOT / 'docs' / (f'{DATASET}-diagnosis-' + ('pilot' if pilot else 'conversion') + '-result.json'), result)
    return result
