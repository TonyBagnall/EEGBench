"""3-class Traumatic Brain Injury during 3-stimulus auditory oddball (OpenNeuro ds003522 v1.1.0, Session 1)."""
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
DATASET = 'ds003522'
REF = '1.1.0'
COMMIT = 'fdec2faaa03172eaf40439d7f87437080c266770'
PILOT_SUBJECTS = ['001', '002', '070', '071', '072', '096']
NON_EEG_CHANNELS = {'VEOG', 'EKG'}
GROUP_TO_LABEL = {
    '1': ('1', 'control'),
    '0': ('2', 'subacute_mild_tbi'),
    '2': ('3', 'chronic_tbi'),
}
AUTHOR_AND_INTEGRITY_EXCLUSIONS = {
    '028': 'Exact duplicate BIDS export of sub-027 (both Original_ID=3013, identical .fdt annex object e3102bd58675b74fdeeb97934f4cb25a)',
    '081': 'Cross-cohort duplicate human participant: Quinn Original_ID=35957 is Cavanagh sub-021 Original_ID=3032 (code/manuscript code/s2_Kill_Data_s2.m)',
    '086': 'Cross-cohort duplicate human participant: Quinn Original_ID=48880 is Cavanagh sub-048 Original_ID=3004 (code/manuscript code/s2_Kill_Data_s2.m)',
    '048': 'Author clinical exclusion in s2_Kill_Data_s2.m: Original_ID=3004 had no loss of consciousness (no LOC)',
    '065': 'Author clinical exclusion in s2_Kill_Data_s2.m: Original_ID=3056 had no loss of consciousness (no LOC)',
    '052': 'Author clinical exclusion in s2_Kill_Data_s2.m: Original_ID=3024 had pre-existing head injury',
    '077': 'Author validity exclusion in s2_Kill_Data_s2.m: Original_ID=14000 had TOMM < 45',
    '040': 'BIDS events.tsv lacks S200/S202 oddball stimulus labels (raw split parallel-port STATUS codes S 8/9/10; Convert2BIDS omitted PATCH.m)',
    '060': 'BIDS events.tsv lacks S200/S202 oddball stimulus labels (raw split parallel-port STATUS codes S 8/9/10; Convert2BIDS omitted PATCH.m)',
}


def tbi_participant_plan(participants):
    """Apply author/integrity exclusions, check disjoint human identities, and compute stratified 75/25 split."""
    if len({r['participant_id'] for r in participants}) != len(participants):
        raise ValueError('Duplicate participant_id in ds003522 participants.tsv')
    groups = {'1': [], '2': [], '3': []}
    excluded = []
    lookup = {}
    seen_original_ids = set()
    seen_ursi = set()
    for row in participants:
        person = row['participant_id'].removeprefix('sub-')
        raw_group = str(row['Group']).strip()
        if raw_group not in GROUP_TO_LABEL:
            raise ValueError(f'Unreviewed ds003522 Group code: {raw_group}')
        if person in AUTHOR_AND_INTEGRITY_EXCLUSIONS:
            excluded.append(dict(
                participant_id=person,
                original_participant_id=row['participant_id'],
                original_id=row['Original_ID'],
                ursi=row['URSI'],
                original_group=raw_group,
                reason=AUTHOR_AND_INTEGRITY_EXCLUSIONS[person],
            ))
            continue
        if row['Original_ID'] in seen_original_ids or row['URSI'] in seen_ursi:
            raise ValueError(f'Unresolved duplicate Original_ID/URSI in retained cohort: {row}')
        seen_original_ids.add(row['Original_ID'])
        seen_ursi.add(row['URSI'])
        encoded, _ = GROUP_TO_LABEL[raw_group]
        lookup[person] = row
        groups[encoded].append(person)
    train = set()
    for ids in groups.values():
        ids.sort()
        count = int(np.floor(0.75 * len(ids)))
        if count < 2 or len(ids) - count < 1:
            raise ValueError('Insufficient TBI class count for split')
        train.update(ids[:count])
    return lookup, train, excluded


def common_scalp_channels(cache, eligible_people):
    """Compute named scalp-EEG channel intersection across all eligible ses-01 recordings."""
    tables = [
        cache / f'sub-{person}/ses-01/eeg/sub-{person}_ses-01_task-ThreeStimAuditoryOddball_channels.tsv'
        for person in sorted(eligible_people)
    ]
    rows = [core.table(p) for p in tables]
    names = [[r['name'] for r in t if r['name'] not in NON_EEG_CHANNELS] for t in rows]
    if any(len(n) != len(set(n)) for n in names):
        raise ValueError('Duplicate channel name within ds003522 channels.tsv')
    shared = set.intersection(*(set(n) for n in names))
    selected = [n for n in names[0] if n in shared]
    if len(selected) != 61:
        raise ValueError(f'Expected 61 shared scalp channels in ds003522, got {len(selected)}')
    return selected, dict(
        selected_order=selected,
        excluded_auxiliary_channels=sorted(NON_EEG_CHANNELS),
        nonshared_scalp_channels=sorted(set.union(*(set(n) for n in names)) - set(selected)),
        policy='Exact named intersection across all 87 eligible ses-01 recordings in sub-001 order, excluding VEOG and EKG',
    )


def oddball_epochs(events, native_events, hz, n_samples, pre_samples=100, post_samples=400):
    """Extract non-overlapping [-0.2, +0.8] s deviant oddball epochs (S200 Target and S202 Novel)."""
    points = pre_samples + post_samples
    interior_boundaries = set()
    for ev in native_events:
        if str(ev.get('type', '')).strip().lower() == 'boundary':
            lat = float(ev['latency'])
            if lat == 1.0:
                continue
            cut = int(np.floor(lat - 1.0))
            if 0 < cut < n_samples:
                interior_boundaries.add(cut)
    for row in events:
        if row['value'].strip().lower() == 'boundary':
            onset = float(row['onset'])
            if onset > 0:
                cut = int(round(onset * hz))
                if 0 < cut < n_samples:
                    interior_boundaries.add(cut)
    native_stim = [
        (int(round(float(ev['latency']) - 1.0)), str(ev.get('type', '')).strip())
        for ev in native_events
        if str(ev.get('type', '')).strip() in {'S200', 'S202'}
    ]
    bids_stim = [
        (idx, row)
        for idx, row in enumerate(events)
        if row['value'].strip() in {'S200', 'S202'}
    ]
    if len(bids_stim) != len(native_stim):
        raise ValueError(f'BIDS vs native deviant oddball count mismatch: {len(bids_stim)} vs {len(native_stim)}')
    retained = []
    skipped = []
    prev_end = -1
    for (ordinal, row), (nat_sample0, nat_code) in zip(bids_stim, native_stim, strict=True):
        code = row['value'].strip()
        trial_type = row['trial_type'].strip()
        expected_type = 'Target Tone' if code == 'S200' else 'Novel Tone'
        if trial_type != expected_type or nat_code != code:
            raise ValueError(f'Oddball trigger mismatch at row {ordinal}: {row} vs {nat_code}')
        ev_sample = int(round(float(row['onset']) * hz))
        if abs(nat_sample0 - ev_sample) > 1:
            raise ValueError(f'Native latency differs from BIDS onset by >1 sample at row {ordinal}')
        start = ev_sample - pre_samples
        end = ev_sample + post_samples
        crosses_boundary = any(start < cut < end for cut in interior_boundaries)
        if start < 0 or end > n_samples:
            skipped.append(dict(event_row=ordinal, code=code, start=start, end=end, reason='Epoch extends beyond recording bounds'))
            continue
        if crosses_boundary:
            skipped.append(dict(event_row=ordinal, code=code, start=start, end=end, reason='Epoch crosses interior boundary discontinuity'))
            continue
        if start < prev_end:
            skipped.append(dict(event_row=ordinal, code=code, start=start, end=end, reason='Epoch overlaps preceding retained deviant epoch'))
            continue
        retained.append(dict(
            event_row=ordinal,
            code=code,
            trial_type=trial_type,
            onset_seconds=float(row['onset']),
            event_sample_0based=ev_sample,
            native_sample_0based=nat_sample0,
            start_sample=start,
            end_sample=end,
            points=points,
        ))
        prev_end = end
    if not retained:
        raise ValueError('No complete deviant oddball epochs retained')
    return retained, skipped, sorted(interior_boundaries)


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
                if '/ses-01/eeg/' not in name or Path(name).suffix not in {'.set', '.fdt'}:
                    continue
                person = re.search(r'(?:^|/)sub-([^/]+)/ses-01/', name)[1]
                if person in AUTHOR_AND_INTEGRITY_EXCLUSIONS:
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
                if name.startswith(('.', 'code/', 'stimuli/')) or ('/ses-' in name and '/ses-01/' not in name):
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

    with ThreadPoolExecutor(3) as pool:
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
        eegdash_id='on003522',
        files=metadata + downloaded_native,
        metadata_archive_sha256=sha(archive),
        licence_evidence='Original pinned dataset_description.json License=CC0',
        source_urls=[f'https://openneuro.org/datasets/{DATASET}/versions/{REF}', 'https://data.eegdash.org/api/eegdash/datasets/on003522'],
        selection_scope='Root BIDS metadata plus Session 1 (ses-01) ThreeStimAuditoryOddball sidecars and eligible native .set/.fdt recordings',
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
    people, _, excluded = tbi_participant_plan(core.table(cache / 'participants.tsv'))
    canonical, layout = common_scalp_channels(cache, people)
    spec['metadata_updates']['excluded_participants'] = excluded
    spec['metadata_updates']['channel_harmonisation'] = layout
    receipt = json.loads((cache / 'download-receipt.json').read_text(encoding='utf-8'))
    for f in sorted(receipt['files'], key=lambda item: item['name']):
        if not f['name'].endswith('_eeg.set'):
            continue
        person = re.search(r'(?:^|/)sub-([^/]+)/ses-01/', f['name'])[1]
        if person not in people:
            continue
        if spec.get('subjects') and person not in spec['subjects']:
            continue
        participant = people[person]
        raw_group = str(participant['Group']).strip()
        label, group_desc = GROUP_TO_LABEL[raw_group]
        path = cache / f['name']
        stem = str(path)[:-7]
        channels = core.table(stem + 'channels.tsv')
        events = core.table(stem + 'events.tsv')
        bids = json.loads(Path(stem + 'eeg.json').read_text(encoding='utf-8-sig'))
        d = loadmat(path, simplify_cells=True)
        eeg = d.get('EEG', d)
        names = [c['labels'] for c in eeg['chanlocs']]
        if names != [r['name'] for r in channels] or float(eeg['srate']) != 500.0 or float(bids['SamplingFrequency']) != 500.0 or int(eeg['trials']) != 1:
            raise ValueError('Native/BIDS schema mismatch in ' + f['name'])
        picks = [names.index(n) for n in canonical]
        fdt = path.with_suffix('.fdt')
        count = int(eeg['pnts'])
        nch = int(eeg['nbchan'])
        if fdt.stat().st_size != nch * count * 4 or str(eeg['data']) != fdt.name:
            raise ValueError('Native FDT pointer or byte count mismatch in ' + f['name'])
        data = np.memmap(fdt, mode='r', dtype='<f4').reshape(count, nch).T
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw = mne.io.read_raw_eeglab(path, preload=False, verbose=False)
        if raw.ch_names != names or raw.n_times != count or raw.info['sfreq'] != 500.0:
            raise ValueError('Independent EEGLAB reader mismatch in ' + f['name'])
        probe = min(2000, count)
        if not np.allclose(raw.get_data(start=0, stop=probe) * 1e6, np.asarray(data[:, :probe], dtype='<f8'), rtol=1e-12, atol=1e-10):
            raise ValueError('Independent microvolt calibration mismatch in ' + f['name'])
        native_ev = eeg.get('event', [])
        native_ev = [native_ev] if isinstance(native_ev, dict) else list(native_ev)
        retained, skipped, boundaries = oddball_epochs(events, native_ev, 500, count)
        rows = []
        values = []
        for index, ep in enumerate(retained):
            row = core.base_row(person, '01', 'ThreeStimAuditoryOddball', f['name'], index, ep['start_sample'], 500, 500, group_desc, label)
            row.update(
                source_epoch_index='',
                source_event_row=ep['event_row'],
                source_event_code=ep['code'],
                source_stimulus_type=ep['trial_type'],
                source_event_onset=ep['onset_seconds'],
                source_event_sample=ep['event_sample_0based'],
                source_event_sample_1based=ep['event_sample_0based'] + 1,
                native_marker_sample_0based=ep['native_sample_0based'],
                epoch_window_relative_seconds='[-0.2, 0.8]',
                source_label_scope='Original participant clinical Group (Control vs sub-acute mTBI vs Chronic TBI), distinct from S200/S202 tone code',
                original_participant_id=participant['participant_id'],
                original_id=participant['Original_ID'],
                ursi=participant['URSI'],
                original_group_code=raw_group,
                age=participant['age'],
                sex=participant['sex'],
                source_array_index=f'Native float32 FDT channels{picks}, samples[{ep["start_sample"]}:{ep["end_sample"]}], cast to float64 microvolts',
            )
            rows.append(row)
            values.append(np.ascontiguousarray(data[picks, ep['start_sample']:ep['end_sample']], dtype='<f8'))
        yield np.stack(values), rows, canonical, dict(
            source_file=f['name'],
            source_file_sha256=f['sha256'],
            source_fdt=f['name'][:-4] + '.fdt',
            participant_id=person,
            participant_metadata=participant,
            source_eeg_indices=picks,
            native_channel_names=names,
            native_bids_eeg=bids,
            native_bids_channels=channels,
            interior_boundaries_0based=boundaries,
            skipped_deviant_epochs=skipped,
            native_samples=count,
            native_sampling_frequency_hz=500,
            source_case_count=len(rows),
            unit_evidence='EEGLAB float32 microvolt storage convention verified against MNE SI decode * 1e6; BIDS channel units field n/a',
        )


def prepare(cache_root=Path('D:/Data/EEGSources'), output=Path('D:/Data/EEG'), pilot=False):
    eegdash_root = Path(cache_root) / 'EEGDash'
    lock_and_download(eegdash_root, pilot=pilot)
    cache = eegdash_root / DATASET
    _, train, excluded = tbi_participant_plan(core.table(cache / 'participants.tsv'))
    spec = dict(
        name='TBIAuditoryOddball',
        source=f'Cavanagh & Quinn / UNM Center for Brain Recovery and Repair / OpenNeuro {DATASET} v{REF}',
        cache=f'EEGDash/{DATASET}',
        hz=500,
        points=500,
        classes=3,
        train_subjects=len(train),
        licence='CC0-1.0',
        licence_url='https://creativecommons.org/publicdomain/zero/1.0/',
        moabb_revision=None,
        doi=f'10.18112/openneuro.{DATASET}.v{REF}',
        paper='Cavanagh, Wilson, Rieger, Gill, Mayer & Quinn (2019), ERPs predict symptomatic distress and recovery in sub-acute mild traumatic brain injury, Neuropsychologia 132:107125, DOI 10.1016/j.neuropsychologia.2019.107125; PMID 31228481',
        labels={'1': 'control', '2': 'subacute_mild_tbi', '3': 'chronic_tbi'},
        splitter=lambda people, chunks: set(people) & train,
        evidence_files=['eegdash-diagnosis-plan.md', f'{DATASET}-diagnosis-source-lock.json'],
        cache_evidence_files=[p for p in ['dataset_description.json', 'participants.tsv', 'participants.json', 'README', 'original-source-lock.json'] if (cache / p).is_file()],
        conversion_files=['prepare_eegdash_tbi.py'],
        intermediate_directory='classification-intermediate-' + ('pilot' if pilot else 'full'),
        note='3-class Traumatic Brain Injury diagnosis (Control vs sub-acute mild TBI 3-14 days post-injury vs Chronic TBI) during Session 1 3-stimulus auditory oddball (OpenNeuro ds003522 v1.1.0). Retains 87 strictly disjoint, clinically validated participants after excluding exact BIDS duplicate sub-028 (Original_ID=3013), cross-study shared humans sub-081/sub-086 and clinical/TOMM exclusions documented in authors\' s2_Kill_Data_s2.m, plus 2 unpatched raw trigger files (sub-040, sub-060). Non-overlapping 1.0 s (500-sample @ 500 Hz, [-0.2, +0.8] s) deviant oddball epochs around Target (S200) and Novel (S202) tones across 61 shared scalp EEG channels in float64 microvolts, without baseline subtraction or filtering.',
        metadata_updates=dict(
            domain='Med',
            eegdash_id='on003522',
            original_source_url=f'https://openneuro.org/datasets/{DATASET}/versions/{REF}',
            paper_reference='Cavanagh et al. (2019), Neuropsychologia 132:107125, DOI 10.1016/j.neuropsychologia.2019.107125; PMID 31228481',
            reference='Source BIDS EEGReference=CPz, EEGGround=AFz (Brain Vision ActiChamp)',
            eeg_reference='Original CPz hardware reference retained; no average rereferencing or baseline subtraction applied',
            split_definition='Fixed whole-subject within each of the 3 diagnostic classes across 87 retained participants: sorted sub-* IDs, floor(0.75*n) TRAIN (18 Control, 30 mTBI, 16 Chronic TBI = 64), remainder TEST (7 Control, 10 mTBI, 6 Chronic TBI = 23)',
            window_overlap_seconds=0,
            original_sampling_frequency_hz=500,
            preprocessing='No conversion filtering, resampling, rereferencing or baseline correction. 61 named scalp EEG channels shared across all 87 Session 1 recordings selected (VEOG and EKG excluded); float32 FDT values cast to float64 microvolts.',
            excluded_participants=excluded,
            metadata_evidence=dict(
                direct='Original participant Group (0=mTBI, 1=Control, 2=Chronic TBI), Original_ID/URSI/demographics, Session 1 SET/FDT waveforms and S200/S202 BIDS/native oddball triggers',
                documented='OpenNeuro CC0 licence, Cavanagh et al. (2019) oddball protocol, and author MATLAB scripts Convert2BIDS_mTBICoBRE_3AOB.m, PATCH.m and s2_Kill_Data_s2.m',
                inferred='EEGLAB microvolt storage convention verified against MNE SI decode * 1e6 because BIDS channel units are n/a',
                assigned='1.0 s [-0.2, +0.8] s non-overlapping deviant oddball windowing, 61-channel scalp intersection, and stratified 75/25 whole-subject split',
            ),
            missing_or_inconsistent_metadata=[
                'Upstream Convert2BIDS_mTBICoBRE_3AOB.m exported Original_ID=3013 twice (sub-027 and sub-028 pointing to identical .fdt); sub-028 excluded',
                'Author script s2_Kill_Data_s2.m documents two individuals enrolled in both sub-acute mTBI and Quinn Chronic TBI cohorts (3032=35957, 3004=48880) plus no-LOC/pre-existing-injury/TOMM<45 exclusions; all applied so zero humans cross classes or splits',
                'sub-040 and sub-060 (Original_ID 3002, 3001) have unpatched split parallel-port STATUS triggers (S 8/9/10 + R 12) in BIDS events.tsv; excluded rather than relabelling triggers',
                'Sessions 2 and 3 exist only for longitudinal mTBI/Control subsets with high attrition and not for Chronic TBI; restricted strictly to baseline Session 1',
            ],
        ),
    )
    if pilot:
        spec.update(name=spec['name'] + 'Pilot', subjects=PILOT_SUBJECTS)
        output = cache / 'pilot-output'
    key = 'tbi_oddball'
    core.SPECS[key] = spec
    core.READERS[key] = records
    result = core.prepare(key, cache_root, output)
    folder = Path(result['path'])
    name = result['dataset']
    m = json.loads((folder / f'{name}_metadata.json').read_text(encoding='utf-8'))
    for sensor in m['sensors']:
        sensor['native_channel_index'] = m['recordings'][0]['source_eeg_indices'][sensor['pre_flat_removal_array_index']]
        sensor['identity_evidence'] = 'Exact named scalp-EEG intersection across 87 eligible ses-01 recordings; per-recording native index mapping retained'
        sensor['unit_evidence'] = 'EEGLAB microvolt storage convention verified against MNE SI decode; BIDS units n/a'
    result = finish(
        result,
        m,
        spec['evidence_files'],
        spec['conversion_files'],
        dict(
            label_mapping=spec['labels'],
            split_definition=m['split_definition'],
            excluded_participants=m['excluded_participants'],
            channel_harmonisation=m['channel_harmonisation'],
            eegdash_id='on003522',
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
