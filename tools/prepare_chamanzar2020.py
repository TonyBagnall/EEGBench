"""Interictal migraine versus healthy control resting-state HD-EEG (Chamanzar et al. 2020/2021, KiltHub Figshare 12636731 v1)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import warnings
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

from tools import prepare_open_moabb as core
from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch
from tools.update_dataset_sidecars import finish

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_ID = '12636731'
PILOT_SUBJECTS = ['C1', 'C21', 'M1', 'M17']
EXPECTED_EXTERNAL_CHANNELS = [
    'M1', 'M2', 'LO1', 'LO2', 'IO1', 'SO1', 'IO2',
    'ECG', 'GSR1', 'GSR2', 'Erg1', 'Erg2', 'Resp', 'Plet', 'Temp', 'Status',
]


def parse_demographics_xlsx(xlsx_path):
    """Read sheet1 of Migraine_Control_Demographics.xlsx using stdlib XML/zipfile."""
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with zipfile.ZipFile(xlsx_path) as zf:
        shared = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            sroot = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            for si in sroot:
                shared.append(''.join(t.text or '' for t in si.iter(f'{ns}t')))
        sheet = ET.fromstring(zf.read('xl/worksheets/sheet1.xml'))
        raw_rows = []
        for row in sheet.iter(f'{ns}row'):
            vals = []
            for cell in row:
                ref = cell.attrib.get('r', '')
                col_letters = ''.join(ch for ch in ref if ch.isalpha())
                col_idx = 0
                for ch in col_letters:
                    col_idx = col_idx * 26 + (ord(ch.upper()) - ord('A') + 1)
                while len(vals) < max(0, col_idx - 1):
                    vals.append('')
                ctype = cell.attrib.get('t')
                vnode = cell.find(f'{ns}v')
                if vnode is None or vnode.text is None:
                    vals.append('')
                elif ctype == 's':
                    vals.append(shared[int(vnode.text)].strip())
                else:
                    vals.append(vnode.text.strip())
            if any(vals):
                raw_rows.append(vals)
    header = raw_rows[0]
    records = []
    for vals in raw_rows[1:]:
        padded = vals + [''] * (len(header) - len(vals))
        records.append(dict(zip(header, padded)))
    return records


def subject_sort_key(person):
    m = re.fullmatch(r'([CM])(\d+)', person)
    if not m:
        raise ValueError(f'Unrecognised Chamanzar2020 participant ID: {person}')
    return (m[1], int(m[2]))


def migraine_participant_plan(demographics_rows, article_files):
    """Apply author medication/matching exclusions and compute stratified 75/25 whole-subject split."""
    zip_by_person = {}
    for f in article_files:
        if not f['name'].endswith('.zip') or f['name'] == 'EEG_Stimuli.zip':
            continue
        m = re.match(r'^([CM]\d+)(?:_\d+)?\.zip$', f['name'])
        if not m:
            raise ValueError(f'Unrecognised Figshare zip name: {f["name"]}')
        person = m[1]
        if person in zip_by_person:
            raise ValueError(f'Duplicate Figshare zip for participant {person}')
        zip_by_person[person] = f

    demo_by_person = {}
    for row in demographics_rows:
        person = row['P#'].strip()
        if not person:
            continue
        if person in demo_by_person:
            raise ValueError(f'Duplicate participant in Demographics.xlsx: {person}')
        demo_by_person[person] = row

    groups = {'C': [], 'M': []}
    excluded = []
    eligible = {}

    for person in sorted(zip_by_person, key=subject_sort_key):
        if person not in demo_by_person:
            excluded.append(dict(
                participant_id=person,
                zip_file=zip_by_person[person]['name'],
                reason='Unmatched surplus control subject omitted from Migraine_Control_Demographics.xlsx (README.txt line 90)',
            ))
            continue
        row = demo_by_person[person]
        med = row.get('Medication before the recording session?', '').strip()
        if person.startswith('M') and med.lower() == 'yes':
            excluded.append(dict(
                participant_id=person,
                zip_file=zip_by_person[person]['name'],
                age=row.get('Age', ''),
                gender=row.get('Gender', ''),
                aura=row.get('Aura?', ''),
                medication_before_session=med,
                reason='Excluded per authors (README.txt line 90): took medication before the recording session',
            ))
            continue
        if person.startswith('M') and med.lower() != 'no':
            raise ValueError(f'Unexpected medication field for {person}: {med!r}')
        prefix = person[0]
        groups[prefix].append(person)
        eligible[person] = dict(row, zip_info=zip_by_person[person])

    if set(demo_by_person) - set(zip_by_person):
        raise ValueError('Participant in Demographics.xlsx missing Figshare zip archive')

    train = set()
    for prefix, people in groups.items():
        ordered = sorted(people, key=subject_sort_key)
        count = int(np.floor(0.75 * len(ordered)))
        if count < 2 or len(ordered) - count < 1:
            raise ValueError(f'Insufficient {prefix} group size for split')
        train.update(ordered[:count])
    return eligible, train, excluded


def resting_fixation_blocks(low2_events, n_samples, hz=512, window_points=2048, windows_per_block=30, max_blocks=3):
    """Identify verified 120-second fixation blocks bounded by trigger bit 1 (start) and bit 2 (end)."""
    block_points = window_points * windows_per_block
    max_span = int(round(135 * hz))
    detected = []
    pending_start = None
    for sample, code in low2_events:
        sample = int(sample)
        low2 = int(code) & 3
        if low2 == 1:
            pending_start = sample
        elif low2 == 2 and pending_start is not None:
            span = sample - pending_start
            if block_points <= span <= max_span and 0 <= pending_start and pending_start + block_points <= n_samples:
                detected.append(dict(
                    start_sample=pending_start,
                    end_trigger_sample=sample,
                    span_samples=span,
                    retained_end_sample=pending_start + block_points,
                ))
            pending_start = None
    if not detected:
        raise ValueError('No complete 120-second resting fixation blocks found in Status channel')
    retained = detected[:max_blocks]
    return retained, detected


def md5_file(path):
    h = hashlib.md5()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def lock_and_download(cache_root=Path('D:/Data/EEGSources'), pilot=False):
    cache = Path(cache_root) / 'Chamanzar2020'
    cache.mkdir(parents=True, exist_ok=True)
    article_path = cache / f'figshare-article-{ARTICLE_ID}.json'
    fetch(f'https://api.figshare.com/v2/articles/{ARTICLE_ID}', article_path)
    article = json.loads(article_path.read_text(encoding='utf-8'))
    lic_name = str(article.get('license', {}).get('name', ''))
    if 'CC BY 4.0' not in lic_name:
        raise ValueError(f'Unexpected Figshare licence: {lic_name}')

    by_name = {f['name']: f for f in article['files']}
    meta_names = [
        'README.txt',
        'Migraine_Control_Demographics.xlsx',
        'EEG experiment protocol_Migraine_Brain_KiltHub_vF.pdf',
        'EEG_Stimuli.zip',
    ]
    meta_records = [
        dict(
            name=article_path.name,
            url=f'https://api.figshare.com/v2/articles/{ARTICLE_ID}',
            bytes=article_path.stat().st_size,
            sha256=sha(article_path),
        )
    ]
    for name in meta_names:
        f = by_name[name]
        target = cache / name
        fetch(f['download_url'], target, 'md5:' + f['computed_md5'], f['size'])
        meta_records.append(dict(
            name=name,
            url=f['download_url'],
            bytes=f['size'],
            md5=f['computed_md5'],
            sha256=sha(target),
        ))

    demographics = parse_demographics_xlsx(cache / 'Migraine_Control_Demographics.xlsx')
    eligible, _, excluded = migraine_participant_plan(demographics, article['files'])

    bdf_dir = cache / 'resting_bdf'
    bdf_dir.mkdir(parents=True, exist_ok=True)
    prov_path = cache / 'zip-extraction-provenance.json'
    zip_prov = json.loads(prov_path.read_text(encoding='utf-8')) if prov_path.is_file() else {}

    # Remove earlier ad-hoc pilot_extract folder once verified BDFs are managed cleanly
    pilot_extract = cache / 'pilot_extract'
    if pilot_extract.is_dir():
        shutil.rmtree(pilot_extract)

    target_people = [p for p in sorted(eligible, key=subject_sort_key) if not pilot or p in PILOT_SUBJECTS]
    bdf_records = []
    for person in target_people:
        zinfo = eligible[person]['zip_info']
        rel_bdf = f'resting_bdf/{person}_resting.bdf'
        bdf_path = cache / rel_bdf
        cached_entry = zip_prov.get(person)
        if bdf_path.is_file() and cached_entry and bdf_path.stat().st_size == cached_entry['bdf_bytes'] and sha(bdf_path) == cached_entry['bdf_sha256']:
            bdf_records.append(dict(
                name=rel_bdf,
                url=zinfo['download_url'],
                bytes=cached_entry['bdf_bytes'],
                sha256=cached_entry['bdf_sha256'],
                source_zip_name=zinfo['name'],
                source_zip_bytes=zinfo['size'],
                source_zip_md5=zinfo['computed_md5'],
                source_zip_sha256=cached_entry['zip_sha256'],
                zip_member=cached_entry['zip_member'],
            ))
            continue

        zip_path = cache / zinfo['name']
        fetch(zinfo['download_url'], zip_path, 'md5:' + zinfo['computed_md5'], zinfo['size'])
        zip_sha = sha(zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            candidates = [
                item for item in zf.infolist()
                if not item.is_dir()
                and not Path(item.filename).name.startswith('._')
                and '__MACOSX' not in item.filename
                and re.search(r'rest.*\.bdf$', Path(item.filename).name, re.I)
            ]
            if len(candidates) != 1:
                raise ValueError(f'Expected exactly 1 resting BDF in {zinfo["name"]}, found {[c.filename for c in candidates]}')
            member = candidates[0]
            tmp_bdf = bdf_path.with_suffix('.bdf.tmp')
            with zf.open(member) as src, tmp_bdf.open('wb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            tmp_bdf.replace(bdf_path)
        # Immediately unlink the multi-task subject zip to keep peak scratch disk < 5 GB
        zip_path.unlink()
        bdf_sha = sha(bdf_path)
        entry = dict(
            person=person,
            zip_name=zinfo['name'],
            zip_bytes=zinfo['size'],
            zip_md5=zinfo['computed_md5'],
            zip_sha256=zip_sha,
            zip_member=member.filename,
            bdf_relpath=rel_bdf,
            bdf_bytes=bdf_path.stat().st_size,
            bdf_sha256=bdf_sha,
        )
        zip_prov[person] = entry
        dump(prov_path, zip_prov)
        print(f'Verified & extracted {zinfo["name"]} -> {rel_bdf} (deleted zip)', flush=True)
        bdf_records.append(dict(
            name=rel_bdf,
            url=zinfo['download_url'],
            bytes=entry['bdf_bytes'],
            sha256=bdf_sha,
            source_zip_name=zinfo['name'],
            source_zip_bytes=zinfo['size'],
            source_zip_md5=zinfo['computed_md5'],
            source_zip_sha256=zip_sha,
            zip_member=member.filename,
        ))

    receipt = dict(
        dataset='Chamanzar2020',
        source_record_id=f'figshare:{ARTICLE_ID}',
        source_revision=f'KiltHub CMU / Figshare {ARTICLE_ID} v{article.get("version", 1)} (DOI 10.1184/R1/12636731)',
        licence='CC-BY-4.0',
        licence_evidence=f'Figshare API article {ARTICLE_ID} license="{lic_name}" ({article.get("license", {}).get("url", "")})',
        pilot=pilot,
        files=meta_records + bdf_records,
        excluded_participants=excluded,
        source_urls=[
            f'https://doi.org/10.1184/R1/{ARTICLE_ID}',
            f'https://api.figshare.com/v2/articles/{ARTICLE_ID}',
        ],
    )
    dump(cache / 'download-receipt.json', receipt)
    dump(cache / 'source-record.json', receipt)
    if not pilot or not (ROOT / 'docs/chamanzar2020-source-lock.json').exists():
        dump(ROOT / 'docs/chamanzar2020-source-lock.json', receipt)
    return receipt


def records(cache, spec):
    import mne
    article = json.loads((cache / f'figshare-article-{ARTICLE_ID}.json').read_text(encoding='utf-8'))
    demographics = parse_demographics_xlsx(cache / 'Migraine_Control_Demographics.xlsx')
    eligible, _, excluded = migraine_participant_plan(demographics, article['files'])
    spec['metadata_updates']['excluded_participants'] = excluded
    receipt = json.loads((cache / 'download-receipt.json').read_text(encoding='utf-8'))
    canonical = None

    for f in sorted(receipt['files'], key=lambda item: item['name']):
        if not f['name'].endswith('_resting.bdf'):
            continue
        person = Path(f['name']).name.split('_')[0]
        if spec.get('subjects') and person not in spec['subjects']:
            continue
        participant = eligible[person]
        label = '1' if person.startswith('C') else '2'
        original_group = 'Control' if label == '1' else 'Migraine_Interictal_Unmedicated'
        path = cache / f['name']
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw = mne.io.read_raw_bdf(path, preload=False, verbose=False)
        if raw.info['sfreq'] != 512.0 or len(raw.ch_names) != 144:
            raise ValueError(f'Unexpected BDF sampling rate or channel count in {f["name"]}: {raw.info["sfreq"]}, {len(raw.ch_names)}')
        scalp_names = list(raw.ch_names[:128])
        ext_names = list(raw.ch_names[128:])
        if ext_names != EXPECTED_EXTERNAL_CHANNELS:
            raise ValueError(f'Unexpected external/status channels in {f["name"]}: {ext_names}')
        if canonical is None:
            canonical = scalp_names
        elif scalp_names != canonical:
            raise ValueError(f'Scalp 128-channel layout differs in {f["name"]}')
        evs = mne.find_events(raw, stim_channel='Status', shortest_event=1, initial_event=True, verbose=False)
        low2_events = [(int(e[0]), int(e[2]) & 3) for e in evs if (int(e[2]) & 3) in {1, 2}]
        retained_blocks, all_blocks = resting_fixation_blocks(low2_events, raw.n_times, hz=512, window_points=2048, windows_per_block=30, max_blocks=3)

        picks = list(range(128))
        data_uV = raw.get_data(picks=picks) * 1e6
        points = 2048
        rows = []
        values = []
        for block_idx, blk in enumerate(retained_blocks):
            bstart = blk['start_sample']
            bend = blk['retained_end_sample']
            for win_within, start in enumerate(range(bstart, bend - points + 1, points)):
                seg = np.ascontiguousarray(data_uV[:, start:start + points], dtype='<f8')
                if np.all(seg == 0) or np.all(seg == seg[:, :1]):
                    continue
                index = len(rows)
                row = core.base_row(person, '01', 'Resting', f['name'], index, start, points, 512, original_group, label)
                row.update(
                    source_epoch_index='',
                    source_event_sample=bstart,
                    source_event_sample_1based=bstart + 1,
                    fixation_block_index=block_idx,
                    window_within_block=win_within,
                    original_participant_id=person,
                    age=participant.get('Age', ''),
                    gender=participant.get('Gender', ''),
                    aura=participant.get('Aura?', ''),
                    medication_before_session=participant.get('Medication before the recording session?', ''),
                    source_zip_name=f['source_zip_name'],
                    source_zip_member=f['zip_member'],
                    source_label_scope='Original participant clinical cohort (healthy control vs unmedicated interictal migraine)',
                    source_array_index=f'Native BDF scalp channels[0:128], samples[{start}:{start+points}], MNE SI decode * 1e6 float64 microvolts',
                )
                rows.append(row)
                values.append(seg)
        if not rows:
            raise ValueError(f'No valid resting windows extracted from {f["name"]}')
        yield np.stack(values), rows, canonical, dict(
            source_file=f['name'],
            source_file_sha256=f['sha256'],
            source_zip_name=f['source_zip_name'],
            source_zip_md5=f['source_zip_md5'],
            source_zip_sha256=f['source_zip_sha256'],
            source_zip_member=f['zip_member'],
            participant_id=person,
            participant_metadata={k: v for k, v in participant.items() if k != 'zip_info'},
            source_eeg_indices=picks,
            native_channel_names=list(raw.ch_names),
            excluded_external_channels=ext_names,
            detected_fixation_blocks=len(all_blocks),
            retained_fixation_blocks=retained_blocks,
            native_sampling_frequency_hz=512,
            native_samples=raw.n_times,
            source_case_count=len(rows),
            original_physical_units={k: str(v) for k, v in (raw._orig_units or {}).items() if k in set(scalp_names[:5])},
            unit_evidence='BioSemi 24-bit BDF calibrated header decoded by MNE to volts and multiplied by 1e6 to float64 microvolts',
        )


def prepare(cache_root=Path('D:/Data/EEGSources'), output=Path('D:/Data/EEG'), pilot=False):
    lock_and_download(cache_root, pilot=pilot)
    cache = Path(cache_root) / 'Chamanzar2020'
    article = json.loads((cache / f'figshare-article-{ARTICLE_ID}.json').read_text(encoding='utf-8'))
    demographics = parse_demographics_xlsx(cache / 'Migraine_Control_Demographics.xlsx')
    _, train, excluded = migraine_participant_plan(demographics, article['files'])

    spec = dict(
        name='MigraineRest',
        source='Chamanzar, Haigh, Grover & Behrmann / CMU KiltHub Figshare 12636731 v1',
        cache='Chamanzar2020',
        hz=512,
        points=2048,
        classes=2,
        train_subjects=len(train),
        licence='CC-BY-4.0',
        licence_url='https://creativecommons.org/licenses/by/4.0/',
        moabb_revision=None,
        doi='10.1184/R1/12636731',
        paper='Chamanzar, Haigh, Grover & Behrmann (2021), Abnormalities in cortical pattern of coherence in migraine detected using ultra high-density EEG, Brain Communications 3(2):fcab061, DOI 10.1093/braincomms/fcab061',
        labels={'1': 'healthy_control', '2': 'interictal_migraine'},
        splitter=lambda people, chunks: set(people) & train,
        evidence_files=['eegdash-diagnosis-plan.md', 'chamanzar2020-source-lock.json'],
        cache_evidence_files=['README.txt', 'Migraine_Control_Demographics.xlsx', f'figshare-article-{ARTICLE_ID}.json'],
        conversion_files=['prepare_chamanzar2020.py'],
        intermediate_directory='classification-intermediate-' + ('pilot' if pilot else 'full'),
        note='Unmedicated interictal migraine versus age- and gender-matched healthy controls during eyes-open central-cross resting fixation (CMU KiltHub Figshare 12636731 v1; CC BY 4.0). Retains 33 participants from Migraine_Control_Demographics.xlsx (18 matched controls, 15 unmedicated migraineurs; M2, M6 and M18 excluded per authors due to pre-session medication; unmatched surplus C2, C6, C12 excluded). 128 scalp HD-EEG BioSemi channels at native 512 Hz in float64 microvolts (external M1/M2 mastoids, EOG, ECG, autonomic and Status channels 128..143 excluded). Up to the first 3 verified 120-second fixation blocks (trigger 1 to trigger 2 in Resting_migraine.m = 90 consecutive 4-second windows per participant) retained so protocol block count matches across groups and self-paced breaks are excluded.',
        metadata_updates=dict(
            domain='Med',
            original_source_url='https://doi.org/10.1184/R1/12636731',
            paper_reference='Chamanzar, Haigh, Grover & Behrmann (2021), Brain Communications 3(2):fcab061, DOI 10.1093/braincomms/fcab061',
            reference='BioSemi ActiveTwo CMS/DRL native acquisition reference; external mastoid channels M1/M2 excluded rather than applied offline',
            eeg_reference='Native BioSemi CMS/DRL acquisition; no offline mastoid or average rereferencing applied',
            split_definition='Fixed whole-subject within matched Control (18) and unmedicated Migraine (15) cohorts sorted numerically (C1..C21, M1..M17): floor(0.75*n) TRAIN (13 Control, 11 Migraine = 24), remainder TEST (5 Control, 4 Migraine = 9)',
            window_overlap_seconds=0,
            original_sampling_frequency_hz=512,
            preprocessing='MNE calibrated BioSemi BDF decode to float64 microvolts and selection of the 128 scalp HD-EEG channels only; no filtering, resampling, baseline correction or rereferencing.',
            excluded_participants=excluded,
            metadata_evidence=dict(
                direct='Participant cohort prefix (C/M), Migraine_Control_Demographics.xlsx age/gender/aura/medication fields, BioSemi BDF 128 scalp headers/calibration and Status parallel-port fixation block triggers',
                documented='CC BY 4.0 licence on CMU KiltHub, Resting_migraine.m trigger code (1=start, 2=end of 120 s cross fixation) and README.txt author exclusions',
                assigned='Stratified 75/25 whole-subject split, consecutive 4-second windows inside verified 120 s fixation blocks, and 3-block cap matching control protocol duration',
            ),
            missing_or_inconsistent_metadata=[
                'Migraineurs recorded up to 6 resting blocks (12 min) while controls recorded 3 blocks (6 min); capping at first 3 blocks (90 windows) prevents protocol-length confounding',
                'M13 lacked auditory SSAEP only and is retained here because unmedicated resting-state HD-EEG and demographics are complete',
                'Customised 128-electrode cap uses 10-5 labels without individual digitised coordinates in the BDF files',
            ],
        ),
    )
    if pilot:
        spec.update(name=spec['name'] + 'Pilot', subjects=PILOT_SUBJECTS)
        output = cache / 'pilot-output'
    key = 'chamanzar2020'
    core.SPECS[key] = spec
    core.READERS[key] = records
    result = core.prepare(key, cache_root, output)
    folder = Path(result['path'])
    name = result['dataset']
    m = json.loads((folder / f'{name}_metadata.json').read_text(encoding='utf-8'))
    for sensor in m['sensors']:
        sensor['native_channel_index'] = sensor['pre_flat_removal_array_index']
        sensor['identity_evidence'] = 'Native BioSemi BDF scalp HD-EEG channel (indices 0..127); external channels 128..143 excluded'
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
    core.dump(ROOT / 'docs' / ('chamanzar2020-' + ('pilot' if pilot else 'conversion') + '-result.json'), result)
    return result
