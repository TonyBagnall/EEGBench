"""Pinned MartinezPeon2024 source -> ImaginedGripForce .ts and ordered sidecars.

Run from the repo root with the scientific runtime on PYTHONPATH:
    python -m tools.prepare_imagined_grip_force --download-only
    python -m tools.prepare_imagined_grip_force --offline

No MOABB preprocessing is applied. Cue times are inferred from the fixed protocol,
relative to source row zero, as in the pinned loader; not recorded trigger events.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np

from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch, header, validate, overlapping_intervals
from tools.prepare_wang import digest_case, format_case

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'docs/imagined-grip-force-source-lock.json'
REVISION = 'bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5'
CHANNELS = 'AF3 F7 F3 FC5 T7 P7 O1 O2 P8 T8 FC6 F4 F8 AF4'.split()
ONSET_SECONDS = (2.9, 10.9, 18.9, 26.9, 34.9)
LABELS = {'10': '1', '40': '2', '70': '3'}
SPEC = dict(name='ImaginedGripForce', source='MartinezPeon2024 / Figshare 25773342 v1',
            channels=14, points=640, hz=128, classes=3)
CACHE = Path('D:/Data/EEGSources/MartinezPeon2024')


def identify(filename):
    match = re.fullmatch(r'user(\d{3})_(10|40|70)_([12])\.txt', filename)
    if not match or not 1 <= int(match[1]) <= 10:
        raise ValueError(f'Unexpected source filename: {filename}')
    return match.groups()  # Keep original participant zero padding.


def source_files(cache, download=True):
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    if lock['version'] != 1 or lock['licence']['name'] != 'CC BY 4.0':
        raise ValueError('Unexpected source version/licence')
    files = sorted(lock['files'], key=lambda f: identify(f['name']))
    expected = {(f'{p:03d}', level, attempt) for p in range(1, 11)
                for level in LABELS for attempt in ['1', '2']}
    if len(files) != 60 or {identify(f['name']) for f in files} != expected:
        raise ValueError('Source file membership differs from pinned 60 recordings')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)

    def ensure(f):
        path = cache / f['name']
        if download:
            fetch(f['download_url'], path, 'md5:' + f['computed_md5'], f['size'])
        if path.stat().st_size != f['size'] or sha(path, 'md5') != f['computed_md5']:
            raise ValueError(f'Pinned source checksum mismatch: {path}')
        return dict(f, sha256=sha(path))

    inventory = list(ThreadPoolExecutor(6).map(ensure, files))
    for start in range(0, 60, 10):
        print(f'Source files {start+1}-{start+10}: verified', flush=True)
    dump(cache / 'source-receipt.json', inventory)
    return inventory


def windows(data):
    """Select EEG columns in source order and complete protocol-derived epochs."""
    data = np.asarray(data, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] != 23 or not np.isfinite(data).all():
        raise ValueError('Expected finite 23-column native source table')
    for event, onset in enumerate(ONSET_SECONDS):
        start = int(np.rint(onset * SPEC['hz']))
        end = start + SPEC['points']
        if end > len(data):
            raise ValueError('Incomplete protocol-derived epoch; no padding allowed')
        x = np.ascontiguousarray(data[start:end, 2:16].T, dtype='<f8')
        yield x, event, onset, start, end


def aeon_check(folder, spec):
    from aeon.classification.feature_based import SummaryClassifier
    from aeon.datasets import load_from_ts_file
    from aeon.utils.validation.collection import check_collection_variance

    train, ytrain = load_from_ts_file(folder / f'{spec["name"]}_TRAIN.ts')
    test, ytest = load_from_ts_file(folder / f'{spec["name"]}_TEST.ts')
    check_collection_variance(train)
    check_collection_variance(test)
    model = SummaryClassifier(random_state=0, n_jobs=1)
    model.fit(train, ytrain)
    predictions = model.predict(test)
    assert predictions.shape == ytest.shape
    return dict(full_train_load=True, full_test_load=True,
                classifier='aeon.classification.feature_based.SummaryClassifier',
                fitted_cases=len(ytrain), predicted_cases=len(predictions),
                accuracy=float(np.mean(predictions == ytest)),
                purpose='Format compatibility only; not a reported benchmark result')


def convert(cache=CACHE, output=Path('D:/Data/EEG'), download=True):
    cache, output = Path(cache), Path(output)
    final = output / SPEC['name']
    if final.exists():
        raise FileExistsError(f'Refusing to overwrite existing problem: {final}')
    inventory = source_files(cache, download)
    cases = {'TRAIN': [], 'TEST': []}
    recordings = []
    for f in inventory:
        participant, level, attempt = identify(f['name'])
        data = np.loadtxt(cache / f['name'], dtype=np.float64)
        split = 'TRAIN' if int(participant) <= 8 else 'TEST'
        recording_id = f['name'][:-4]
        recordings.append(dict(recording_id=recording_id, participant_id=participant,
                               session_id='0', session_id_evidence='Single session documented; archive ID 0',
                               source_file=f['name'], shape=list(data.shape),
                               sha256=f['sha256'], native_column_count=data.shape[1],
                               source_first_row_time_column_18=float(data[0, 18]),
                               source_last_row_time_column_18=float(data[-1, 18])))
        for x, event, onset, start, end in windows(data):
            row = dict(split=split, row=len(cases[split]),
                       example_id=f'ImaginedGripForce/{recording_id}/{event}',
                       participant_id=participant, session_id='0', run_id=f'level{level}_attempt{attempt}',
                       recording_id=recording_id, source_file=f['name'], source_file_sha256=f['sha256'],
                       source_epoch_index=event, event_index=event,
                       source_array_index=f'rows[{start}:{end}], columns[2:16], transposed',
                       source_event_sample='', source_event_sample_1based='',
                       protocol_onset_seconds=onset, protocol_onset_sample_rounded=start,
                       start_sample=start, end_sample=end,
                       start_time_seconds=start / SPEC['hz'], end_time_seconds=end / SPEC['hz'],
                       sample_reference='Native source table rows; zero-based, exclusive end',
                       timing_evidence='Inferred fixed protocol relative to first source row, not recorded triggers',
                       source_label=level, label=LABELS[level],
                       label_description=f'imagined_right_hand_squeeze_{level}_percent_MVC',
                       label_evidence='Original filename force level', original_partition='unsplit',
                       source_sample_counter_first=float(data[start, 1]),
                       source_sample_counter_last=float(data[end-1, 1]),
                       source_time_column_18_first=float(data[start, 18]),
                       source_time_column_18_last=float(data[end-1, 18]),
                       signal_sha256=digest_case(x), signal_hash_dtype='<f8')
            cases[split].append((x, row))
    if [len(cases[s]) for s in ['TRAIN', 'TEST']] != [240, 60]:
        raise ValueError('Unexpected case counts')

    # Apply the authorised archive-wide constant/effectively-flat sensor policy.
    all_x = np.stack([x for split in cases.values() for x, _ in split])
    constant = (np.ptp(all_x, axis=2) == 0).sum(axis=0)
    effective = (np.std(all_x, axis=2) <= 1e-7).sum(axis=0)
    removed = np.flatnonzero(effective > 0).tolist()
    keep = [i for i in range(14) if i not in removed]
    if not keep:
        raise ValueError('All EEG channels failed variance screening')
    spec = dict(SPEC, channels=len(keep))
    channels = [CHANNELS[i] for i in keep]
    quality = dict(threshold_uV=1e-7, policy='Remove a sensor globally if any case is constant or std <= threshold',
                   source_channel_names=CHANNELS,
                   constant_case_counts_by_source_channel=constant.tolist(),
                   effectively_flat_case_counts_by_source_channel=effective.tolist(),
                   removed_source_channel_indices=removed)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ImaginedGripForce-', dir=output) as tmp:
        stage = Path(tmp)
        arrays = {}
        for split, pairs in cases.items():
            with (stage / f'{spec["name"]}_{split}.ts').open('w', encoding='ascii', newline='\n') as ts, \
                 (stage / f'cases_{split.lower()}.tsv').open('w', encoding='utf-8', newline='') as tsv:
                ts.write(header(spec))
                writer = csv.DictWriter(tsv, fieldnames=list(pairs[0][1]), delimiter='\t', lineterminator='\n')
                writer.writeheader()
                values = []
                for x, row in pairs:
                    x = np.ascontiguousarray(x[keep], dtype='<f8')
                    row['signal_sha256'] = digest_case(x)
                    if removed:
                        row['source_array_index'] += f'; kept EEG axes {keep}'
                    writer.writerow(row)
                    ts.write(format_case(x) + ':' + row['label'] + '\n')
                    values.append(x)
                arrays['X_' + split.lower()] = np.stack(values)
                arrays['y_' + split.lower()] = np.array([r['label'] for _, r in pairs])
        np.savez_compressed(stage / 'classification_arrays.npz', **arrays,
                            channel_names=np.array(channels))
        with np.load(stage / 'classification_arrays.npz', allow_pickle=False) as saved:
            for key, value in arrays.items():
                if not np.array_equal(saved[key], value):
                    raise ValueError('Intermediate NPZ roundtrip mismatch')
        reports, hashes, intervals = {}, {}, {}
        for split in cases:
            reports[split], hashes[split], intervals[split] = validate(stage, spec, split)
        shared = set(reports['TRAIN']['subjects']) & set(reports['TEST']['subjects'])
        duplicates = len(hashes['TRAIN'] & hashes['TEST'])
        overlaps = overlapping_intervals(intervals['TRAIN'], intervals['TEST'])
        if shared or duplicates or overlaps:
            raise ValueError('Cross-partition leakage detected')
        if any(r['within_split_duplicate_cases'] for r in reports.values()):
            raise ValueError('Duplicate cases within partition require review')
        checks = dict(partitions=reports, shared_subjects=sorted(shared),
                      cross_split_duplicate_cases=duplicates, cross_split_overlapping_intervals=overlaps,
                      numeric_column_order_verified_all_60_files=True,
                      sensor_identity_basis='Documented source/loader mapping, not embedded names',
                      npz_exact_roundtrip=True,
                      aeon=aeon_check(stage, spec))
        sensors = [dict(array_index=i, source_table_column=2+old, source_eeg_axis=old,
                        name=CHANNELS[old], type='EEG', units='uV',
                        evidence='Pinned MOABB loader and documented Emotiv EPOC column mapping; source has no header',
                        position=None) for i, old in enumerate(keep)]
        unknown = ['No recorded cue triggers; timing is inferred from the fixed protocol relative to row zero',
                   'Native time columns and wrapping sample counters retained, not treated as absolute acquisition time',
                   'No embedded channel labels or individual sensor coordinates; names/order are documented mapping',
                   'Session ID 0 is archive assigned to the documented single visit; run ID derived from filename',
                   'No separately marked basal/rest class is recovered',
                   'Raw microvolt scale and P3/P4 reference are documented interpretations, not file-header fields']
        metadata = dict(name=spec['name'], source_dataset='MartinezPeon2024', aliases=['EEG Kinesthetic motor imagery levels'],
                        data_doi='10.6084/m9.figshare.25773342.v1', paper_doi='10.1088/1741-2552/ad5f27',
                        paper='Martinez-Peon et al. (2024), Characterization and classification of kinesthetic motor imagery levels, J. Neural Eng. 21, 046024',
                        licence='CC-BY-4.0', source_revision='Figshare article 25773342 version 1',
                        moabb_revision=REVISION, shapes={s.lower(): r['shape'] for s, r in reports.items()},
                        subjects=10, sessions=10, sessions_per_subject=1, recording_count=60,
                        dtype='float64', units='uV', sampling_frequency_hz=128,
                        original_sampling_frequency_hz_documented=128, window_samples=640, window_seconds=5,
                        overlap_seconds=0, channel_names=channels, sensors=sensors,
                        source_channel_names=CHANNELS, kept_source_channel_indices=keep,
                        removed_channels=[dict(source_array_index=i, name=CHANNELS[i], reason='Constant/effectively flat case sensor; global removal') for i in removed],
                        native_table_columns=23, source_eeg_columns=list(range(2,16)),
                        discarded_columns='0 time-like; 1 wrapping sample counter; 16/17 gyroscope; 18 time; 19-22 unused; these are not EEG',
                        reference=dict(documented='P3 and P4 reference locations, as quoted by pinned loader from article', directly_recovered=False),
                        montage=dict(documented='Emotiv EPOC scalp sites', individual_positions_available=False,
                                     template_positions_used=False),
                        label_mapping={LABELS[k]: f'imagined_right_hand_squeeze_{k}_percent_MVC' for k in LABELS},
                        original_to_encoded_labels=LABELS,
                        class_distributions={s.lower(): r['class_counts'] for s, r in reports.items()},
                        split_definition='Deterministic participant split: original 001-008 TRAIN, 009-010 TEST; no official source split',
                        validation_partition=None, source_partition='unsplit',
                        case_order='Participant ascending, numeric force level ascending, attempt ascending, cue ascending; no shuffle',
                        preprocessing='Select columns 2:16 and fixed protocol windows; retain native microvolt values in float64; no filtering, resampling, demeaning or reference change',
                        source_processing_note='Paper reports a 60 Hz notch in its analysis; not applied here and not asserted present in distributed values',
                        channel_quality=quality, unknown_or_inconsistent_metadata=unknown, recordings=recordings)
        dump(stage / f'{spec["name"]}_metadata.json', metadata)
        dump(stage / f'{spec["name"]}_validation.json', checks)
        dump(stage / 'metadata-completeness.json', dict(direct=['source filenames, numerical columns, row indices, hashes, time/sample column values'],
             documented=['channel mapping, units, rate, reference, task protocol'], inferred=['cue times, epoch IDs'],
             assigned=['session/run IDs, encoded labels, participant split'], missing_or_inconsistent=unknown))
        with (stage / 'channels.tsv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, list(sensors[0]), delimiter='\t'); writer.writeheader(); writer.writerows(sensors)
        (stage / 'channels.txt').write_text(', '.join(channels) + '\n', encoding='utf-8')
        evidence = stage / 'source_metadata'; evidence.mkdir()
        shutil.copy2(LOCK, evidence / LOCK.name)
        dump(evidence / 'source-receipt.json', inventory)
        if (cache / 'figshare-25773342-v1.json').exists():
            shutil.copy2(cache / 'figshare-25773342-v1.json', evidence / 'figshare-25773342-v1.json')
        loader = cache / 'moabb-martinezpeon2024.py'
        if download:
            fetch(f'https://raw.githubusercontent.com/NeuroTechX/moabb/{REVISION}/moabb/datasets/martinezpeon2024.py', loader)
        if loader.exists():
            shutil.copy2(loader, evidence / loader.name)
        code = stage / 'conversion_code'; code.mkdir()
        for name in ['prepare_imagined_grip_force.py', 'prepare_small_moabb.py', 'prepare_wang.py', 'prepare_moabb.py', 'requirements-moabb.txt']:
            shutil.copy2(Path(__file__).with_name(name), code / name)
        (stage / 'ATTRIBUTION.txt').write_text('Martinez-Peon, D. (2024). EEG Kinesthetic motor imagery levels. Figshare 25773342 v1. CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nPaper DOI: 10.1088/1741-2552/ad5f27. Changes: EEG selection, protocol-derived epoching, participant split, .ts export; no numerical rescaling.\n', encoding='utf-8')
        (stage / 'README_ImaginedGripForce.md').write_text('# ImaginedGripForce\n\nThree imagined right-hand grip force levels: 10/40/70% MVC. Source Figshare 25773342 v1, CC BY 4.0.\n\n240 training cases (subjects 001-008), 60 test cases (009-010), 5-second windows at 128 Hz, float64 microvolts. No archived validation. Source IDs are strings.\n\nCue onsets are inferred from protocol, not recorded triggers. See metadata for sensor mapping evidence and quality corrections. Case TSV row order equals .ts row order.\n\nclassification_arrays.npz uses numpy.savez_compressed: X_train, y_train, X_test, y_test and channel_names, with numeric X in cases/channels/time order; load with numpy.load(..., allow_pickle=False).\n', encoding='utf-8')
        dump(stage / f'{spec["name"]}_manifest.json', dict(name=spec['name'], source_revision='Figshare 25773342 v1',
             source_url='https://doi.org/10.6084/m9.figshare.25773342.v1', licence='CC-BY-4.0',
             moabb_revision=REVISION, source_files=inventory, split=metadata['split_definition'],
             conversion=metadata['preprocessing'], artifacts={p.relative_to(stage).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in stage.rglob('*') if p.is_file()}))
        stage.rename(final)
    return dict(dataset=spec['name'], path=str(final), train_cases=240, test_cases=60,
                subjects=10, channels=spec['channels'], timepoints=640, classes=3, frequency=128,
                size_GB=sum(p.stat().st_size for p in final.rglob('*') if p.is_file())/1e9,
                licence='CC-BY-4.0', validation=checks, channel_quality=quality)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--output', type=Path, default=Path('D:/Data/EEG'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    if args.download_only:
        source_files(args.cache, not args.offline)
    else:
        result = convert(args.cache, args.output, not args.offline)
        dump(ROOT / 'docs/imagined-grip-force-local-results.json', result)
        print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
