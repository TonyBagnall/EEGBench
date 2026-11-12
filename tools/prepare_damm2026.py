"""Download, verify and convert Damm2026 (OpenNeuro ds008446 v1.0.1) -> ImaginedFingers.

Reads native BIDS EDF recordings directly without MOABB resampling, filtering,
demeaning or synthetic timelines. Cross-verifies the embedded EDF Marker channel
sample-for-sample against BIDS _events.tsv (accounting for the publisher's 512^2
onset divisor), retains the 62 scalp EEG channels in native order (excluding
Ref1, Ref2 and Marker), crops exact 6-second (3,072-sample at 512 Hz) imagined
finger windows, and exports validated float64 microvolt .ts files and sidecars.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import tarfile

import numpy as np

from tools import prepare_open_moabb as core
from tools.prepare_moabb import dump, sha
from tools.prepare_small_moabb import fetch
from tools.update_dataset_sidecars import finish

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "damm2026-source-lock.json"

EXPECTED_62_CHANNELS = [
    "Fp1", "Fpz", "Fp2", "AF7", "AF5", "AF4", "AF8",
    "F7", "F5", "F3", "F1", "Fz", "F2", "F4", "F6", "F8",
    "FT7", "FC5", "FC3", "FC1", "FCz", "FC2", "FC4", "FC6", "FT8",
    "T7", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "T8",
    "TP7", "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6", "TP8",
    "P7", "P5", "P3", "P1", "Pz", "P2", "P4", "P6", "P8",
    "PO7", "PO3", "POz", "PO2", "PO8", "O1", "Oz", "O2", "AF9", "AF10",
]
AUXILIARY_CHANNELS = ["Ref1", "Ref2", "Marker"]

CODE_TO_LABEL = {3: "1", 4: "2", 5: "3", 6: "4", 7: "5"}
LABELS = {
    "1": "imagined_thumb",
    "2": "imagined_index_finger",
    "3": "imagined_middle_finger",
    "4": "imagined_ring_finger",
    "5": "imagined_pinky_finger",
}

# Fixed 75/25 whole-subject split (15 TRAIN / 5 TEST) simultaneously stratified
# across counterbalancing_log.json block-1 order (8S/7R train, 2S/3R test),
# _eeg.json BlockAssignment order (7S/8R train, 3S/2R test), handedness (1L each
# in train and test), gender (3M/10F/2U train, 1M/3F/1U test), and placing the
# single early-terminated recording (sub-18 run-01) in TRAIN so TEST has 1,500
# exact balanced trials (300 per finger).
TRAIN_SUBJECTS = frozenset({
    "01", "02", "03", "04", "05", "06", "07", "08",
    "09", "11", "12", "14", "17", "18", "19",
})
TEST_SUBJECTS = frozenset({"10", "13", "15", "16", "20"})
PILOT_SUBJECTS = ("01", "18")


def subject_of_path(rel_path: str) -> str | None:
    match = re.match(r"^sub-(\d{2})/", rel_path)
    return match.group(1) if match else None


def verify_checksum(path: Path, expected: str, size: int) -> str:
    if not path.is_file() or path.stat().st_size != size:
        raise ValueError(f"Size mismatch for {path}: expected {size}")
    algo, digest = expected.split(":", 1)
    actual = sha(path, algo)
    if actual != digest:
        raise ValueError(f"Checksum mismatch for {path}: expected {digest}, got {actual}")
    return actual if algo == "sha256" else sha(path, "sha256")


def download(
    cache_root: Path = Path("D:/Data/EEGSources"),
    pilot: bool = False,
    workers: int = 6,
) -> dict:
    """Download and cryptographically verify pinned BIDS files for Damm2026."""
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    cache = Path(cache_root) / lock["source_dataset"]
    cache.mkdir(parents=True, exist_ok=True)

    tar_url = f"https://codeload.github.com/OpenNeuroDatasets/{lock['openneuro_id']}/tar.gz/{lock['git_commit']}"
    tar_path = cache / "release-snapshot.tar.gz"
    fetch(tar_url, tar_path, f"sha256:{lock['snapshot_tarball_sha256']}")

    moabb_url = (
        f"https://raw.githubusercontent.com/NeuroTechX/moabb/"
        f"{lock['moabb_reference_commit']}/{lock['moabb_loader']}"
    )
    moabb_ref_path = cache / "moabb-damm2026-reference.py"
    fetch(moabb_url, moabb_ref_path)

    selected_subjects = set(PILOT_SUBJECTS) if pilot else None
    wanted = []
    for entry in lock["files"]:
        sub = subject_of_path(entry["name"])
        if selected_subjects is not None and sub is not None and sub not in selected_subjects:
            continue
        wanted.append(entry)

    non_annex = {e["name"]: e for e in wanted if "annex_key" not in e}
    if non_annex:
        with tarfile.open(tar_path, "r:gz") as tf:
            members = {}
            for member in tf.getmembers():
                if "/" not in member.name or not member.isfile():
                    continue
                rel = member.name.split("/", 1)[1]
                if rel in non_annex:
                    members[rel] = member
            for rel, entry in non_annex.items():
                target = (cache / rel).resolve()
                if not target.is_relative_to(cache.resolve()):
                    raise ValueError(f"Unsafe archive path: {rel}")
                if target.is_file() and target.stat().st_size == entry["bytes"]:
                    try:
                        verify_checksum(target, entry["publisher_checksum"], entry["bytes"])
                        continue
                    except ValueError:
                        pass
                if rel not in members:
                    raise ValueError(f"Missing {rel} in release snapshot tarball")
                data = tf.extractfile(members[rel]).read()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                verify_checksum(target, entry["publisher_checksum"], entry["bytes"])

    annex_entries = [e for e in wanted if "annex_key" in e]

    def fetch_annex(entry: dict) -> dict:
        target = cache / entry["name"]
        fetch(entry["url"], target, entry["publisher_checksum"], entry["bytes"])
        digest = verify_checksum(target, entry["publisher_checksum"], entry["bytes"])
        print(f"Verified {entry['name']} ({entry['bytes'] / 1e6:.2f} MB)", flush=True)
        return dict(entry, sha256=digest)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        verified_annex = {e["name"]: e for e in pool.map(fetch_annex, annex_entries)}

    verified_files = []
    for entry in wanted:
        if entry["name"] in verified_annex:
            verified_files.append(verified_annex[entry["name"]])
        else:
            target = cache / entry["name"]
            digest = verify_checksum(target, entry["publisher_checksum"], entry["bytes"])
            verified_files.append(dict(entry, sha256=digest))

    description = json.loads((cache / "dataset_description.json").read_text(encoding="utf-8"))
    if description.get("License") != "CC0":
        raise ValueError(f"Unexpected native BIDS License: {description.get('License')}")

    receipt = dict(
        dataset=lock["dataset"],
        source_dataset=lock["source_dataset"],
        source_record_id=lock["openneuro_id"],
        source_revision=f"OpenNeuro {lock['openneuro_id']} v{lock['version']}, Git {lock['git_commit']}",
        doi=lock["doi"],
        licence="CC0-1.0",
        licence_evidence="Native pinned dataset_description.json License=CC0 (OpenNeuro ds008446 v1.0.1)",
        moabb_reference_commit=lock["moabb_reference_commit"],
        moabb_reference_sha256=sha(moabb_ref_path),
        snapshot_tarball_sha256=sha(tar_path),
        pilot=pilot,
        excluded_non_bids_sourcedata=lock["excluded_non_bids_sourcedata"],
        source_urls=[
            f"https://openneuro.org/datasets/{lock['openneuro_id']}/versions/{lock['version']}",
            f"https://doi.org/{lock['doi']}",
        ],
        files=verified_files,
    )
    dump(cache / "download-receipt.json", receipt)
    dump(cache / "source-record.json", receipt)
    dump(cache / ("download-receipt-pilot.json" if pilot else "download-receipt-full.json"), receipt)
    return receipt


def parse_events_vector(events_path: Path, n_times: int, sfreq: float = 512.0) -> tuple[np.ndarray, float]:
    """Reconstruct the per-sample trigger vector from BIDS _events.tsv.

    In OpenNeuro ds008446 v1.0.1, _events.tsv stores per-sample trigger rows whose
    onset column was divided by 512 twice (sample = round(onset * 512 * 512)).
    """
    scale = sfreq * sfreq
    vector = np.zeros(n_times, dtype=np.int64)
    prev_sample = -1
    max_residual = 0.0
    with Path(events_path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["onset", "duration", "trial_type"]:
            raise ValueError(f"Unexpected _events.tsv columns in {events_path}: {reader.fieldnames}")
        for row in reader:
            exact = float(row["onset"]) * scale
            sample = int(round(exact))
            residual = abs(exact - sample)
            if residual > 1e-3:
                raise ValueError(f"Non-integer reconstructed sample in {events_path}: {row['onset']} -> {exact}")
            if residual > max_residual:
                max_residual = residual
            if sample <= prev_sample or sample < 0 or sample >= n_times:
                raise ValueError(f"Out-of-order or out-of-bounds event sample {sample} in {events_path}")
            code = int(row["trial_type"])
            if code not in {0, 1, 2, 3, 4, 5, 6, 7}:
                raise ValueError(f"Unexpected trigger code {code} in {events_path}")
            vector[sample] = code
            prev_sample = sample
    return vector, max_residual


def extract_finger_blocks(
    marker: np.ndarray,
    events_vec: np.ndarray,
    points: int = 3072,
    expected_full_blocks: int = 75,
    allow_truncated_final: bool = False,
) -> tuple[list[tuple[int, int, int]], list[dict]]:
    """Verify 100% Marker == events.tsv agreement and return complete finger blocks."""
    if marker.shape != events_vec.shape or not np.array_equal(marker, events_vec):
        diff = np.flatnonzero(marker != events_vec)
        first = int(diff[0]) if len(diff) else -1
        raise ValueError(
            f"EDF Marker channel disagrees with _events.tsv at {len(diff)} samples (first at {first})"
        )
    if not set(np.unique(marker)) <= {0, 1, 2, 3, 4, 5, 6, 7}:
        raise ValueError(f"Unexpected EDF Marker codes: {sorted(set(map(int, np.unique(marker))))}")

    changes = np.flatnonzero(np.r_[True, marker[1:] != marker[:-1]])
    ends = np.r_[changes[1:], len(marker)]
    raw_blocks = [
        (int(start), int(end), int(marker[start]))
        for start, end in zip(changes, ends, strict=True)
        if int(marker[start]) in CODE_TO_LABEL
    ]
    if not raw_blocks:
        raise ValueError("No imagined-finger cue blocks found in recording")

    complete: list[tuple[int, int, int]] = []
    excluded: list[dict] = []
    for idx, (start, end, code) in enumerate(raw_blocks):
        duration = end - start
        if duration == points and end <= len(marker):
            complete.append((start, end, code))
        elif allow_truncated_final and idx == len(raw_blocks) - 1 and 0 < duration < points:
            # Verify recording terminated during this final cue (only trailing zeros remain).
            if np.any(marker[end:] != 0):
                raise ValueError("Non-zero markers follow truncated block; mid-run corruption suspected")
            excluded.append(
                dict(
                    block_ordinal=idx,
                    start_sample=start,
                    end_sample=end,
                    available_samples=duration,
                    required_samples=points,
                    source_event_code=code,
                    label=CODE_TO_LABEL[code],
                    reason="Native EDF recording ended before complete 6-second cue window",
                )
            )
        else:
            raise ValueError(
                f"Unexpected finger block duration {duration} samples at index {idx} (start={start}, code={code})"
            )

    if not allow_truncated_final:
        if len(complete) != expected_full_blocks:
            raise ValueError(f"Expected {expected_full_blocks} finger blocks, got {len(complete)}")
        per_code = Counter(code for _, _, code in complete)
        expected_per_code = {code: expected_full_blocks // 5 for code in CODE_TO_LABEL}
        if dict(per_code) != expected_per_code:
            raise ValueError(f"Unbalanced run finger counts: {dict(per_code)}")
    return complete, excluded


def damm2026_records(cache: Path, spec: dict):
    """Yield per-run (X, rows, channel_names, recording_info) tuples for Damm2026."""
    import mne

    participants = core.table(cache / "participants.tsv")
    by_person = {r["participant_id"].removeprefix("sub-"): r for r in participants}
    if len(by_person) != 20 or set(by_person) != (TRAIN_SUBJECTS | TEST_SUBJECTS):
        raise ValueError("Unexpected participants.tsv membership in Damm2026")

    cb_log = json.loads((cache / "sourcedata" / "counterbalancing_log.json").read_text(encoding="utf-8"))
    cb_assign = cb_log["ParticipantBlockAssignment"]
    if set(cb_assign) != {f"sub-{p}" for p in by_person}:
        raise ValueError("counterbalancing_log.json participant mismatch")

    receipt = json.loads((cache / "download-receipt.json").read_text(encoding="utf-8"))
    by_file = {f["name"]: f for f in receipt["files"]}
    edf_entries = sorted(
        (f for f in receipt["files"] if f["name"].endswith("_eeg.edf")),
        key=lambda f: f["name"],
    )

    all_excluded_incomplete = []
    discrepancies = []

    for entry in edf_entries:
        match = re.fullmatch(
            r"sub-(\d{2})/eeg/sub-(\d{2})_task-(random|sequential)_run-(0[12])_eeg\.edf",
            entry["name"],
        )
        if not match or match.group(1) != match.group(2):
            raise ValueError(f"Unrecognised Damm2026 EDF path: {entry['name']}")
        person, _, task, run = match.groups()
        if spec.get("subjects") and person not in spec["subjects"]:
            continue

        edf_path = cache / entry["name"]
        stem = str(edf_path)[:-8]
        channels_path = Path(stem + "_channels.tsv")
        events_path = Path(stem + "_events.tsv")
        eeg_json_path = Path(stem + "_eeg.json")
        scans_path = cache / f"sub-{person}" / f"sub-{person}_scans.tsv"

        channels = core.table(channels_path)
        eeg_json = json.loads(eeg_json_path.read_text(encoding="utf-8"))
        scans = core.table(scans_path)

        raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
        if raw.info["sfreq"] != 512.0 or eeg_json.get("SamplingFrequency") != 512:
            raise ValueError(f"Unexpected sampling rate in {entry['name']}")
        if len(raw.ch_names) != 65 or raw.ch_names != [c["name"] for c in channels]:
            raise ValueError(f"Channel header/TSV mismatch in {entry['name']}")
        if raw.ch_names[:62] != EXPECTED_62_CHANNELS or raw.ch_names[62:] != AUXILIARY_CHANNELS:
            raise ValueError(f"Unexpected 62+3 channel order in {entry['name']}")
        if [c["type"] for c in channels[:62]] != ["EEG"] * 62 or channels[64]["type"] != "TRIG":
            raise ValueError(f"Unexpected channel types in {channels_path}")
        if [c["units"] for c in channels[:62]] != ["uV"] * 62:
            raise ValueError(f"Unexpected channel units in {channels_path}")

        units = np.asarray(raw._raw_extras[0]["units"], dtype=np.float64)
        if units.shape != (65,) or not np.allclose(units, 1e-6, rtol=0.0, atol=1e-15):
            raise ValueError(f"Unexpected EDF header unit multipliers in {entry['name']}: {units}")

        marker = np.rint(raw.get_data(picks=[64])[0] * 1e6).astype(np.int64)
        events_vec, max_residual = parse_events_vector(events_path, raw.n_times, sfreq=512.0)

        is_known_truncated = entry["name"] == "sub-18/eeg/sub-18_task-random_run-01_eeg.edf"
        if not is_known_truncated and raw.n_times != 468992:
            raise ValueError(f"Unexpected sample count {raw.n_times} in {entry['name']}")

        blocks, excluded = extract_finger_blocks(
            marker,
            events_vec,
            points=spec["points"],
            expected_full_blocks=75,
            allow_truncated_final=is_known_truncated,
        )
        for item in excluded:
            all_excluded_incomplete.append(dict(source_file=entry["name"], participant_id=person, **item))

        cb_first = cb_assign[f"sub-{person}"]["block1_condition"]
        json_block = eeg_json.get("BlockAssignment", {})
        json_first = json_block.get("original_first_condition")
        if cb_first != json_first and (person, cb_first, json_first) not in discrepancies:
            discrepancies.append((person, cb_first, json_first))

        data_uv = raw.get_data(picks=list(range(62))).astype("<f8", copy=False) * 1e6
        participant = by_person[person]
        run_token = f"task-{task}_run-{run}"
        rows = []
        values = []
        for event_idx, (start, end, code) in enumerate(blocks):
            encoded = CODE_TO_LABEL[code]
            row = core.base_row(
                person,
                "1",
                run_token,
                entry["name"],
                event_idx,
                start,
                spec["points"],
                spec["hz"],
                code,
                encoded,
            )
            row.update(
                task_condition=task,
                run_number=run,
                source_event_code=str(code),
                bids_events_onset_raw=f"{start / (512.0 * 512.0):.17g}",
                counterbalancing_log_block1=cb_first,
                bids_eeg_json_which_block=str(json_block.get("which_block_this_was", "")),
                bids_eeg_json_first_condition=str(json_first or ""),
                age=participant["age"],
                gender=participant["gender"],
                handedness=participant["handedness"],
                source_array_index=f"EDF channels[0:62], samples[{start}:{end}], float64 volts*1e6",
                event_evidence=(
                    "Contiguous 3,072-sample pulse on native EDF Marker channel (codes 3..7), "
                    "100% sample-by-sample verified against BIDS _events.tsv (onset * 512^2)"
                ),
            )
            rows.append(row)
            values.append(core.crop(data_uv, start, spec["points"]))

        ev_rel = entry["name"].replace("_eeg.edf", "_events.tsv")
        info = dict(
            core.mne_info(raw),
            source_file=entry["name"],
            source_file_sha256=entry["sha256"],
            events_file=ev_rel,
            events_file_sha256=by_file[ev_rel]["sha256"],
            participant_id=person,
            session_id="1",
            run_id=run_token,
            task_condition=task,
            participant_metadata=participant,
            counterbalancing_log_entry=cb_assign[f"sub-{person}"],
            bids_eeg_json=eeg_json,
            bids_scans=scans,
            native_bids_channels=channels,
            source_eeg_indices=list(range(62)),
            excluded_auxiliary_channels=dict(Ref1=62, Ref2=63, Marker=64),
            marker_events_tsv_exact_match=True,
            events_tsv_onset_divisor_bug="BIDS _events.tsv onset was divided by 512 twice (sample = onset * 512 * 512)",
            events_tsv_max_sample_rounding_residual=max_residual,
            source_case_count=len(rows),
            excluded_incomplete_cases=excluded,
        )
        yield np.stack(values), rows, list(EXPECTED_62_CHANNELS), info

    spec["metadata_updates"]["excluded_incomplete_cases"] = all_excluded_incomplete
    spec["metadata_updates"]["counterbalancing_sidecar_discrepancy_subjects"] = [
        dict(participant_id=p, counterbalancing_log_block1=cb, bids_eeg_json_first_condition=jb)
        for p, cb, jb in discrepancies
    ]


def build_spec(pilot: bool = False) -> dict:
    split_desc = (
        "Fixed whole-subject 75/25 split (15 TRAIN: 01-09,11,12,14,17,18,19; "
        "5 TEST: 10,13,15,16,20), stratified simultaneously across counterbalancing_log.json "
        "and _eeg.json block-order assignments, handedness (1 L each in TRAIN and TEST), and "
        "gender, with sub-18's single early-terminated run in TRAIN so TEST has 1,500 exact "
        "balanced trials (300 per finger)"
    )
    note = (
        "All four BIDS runs per participant (two random-order, two sequential-order) combined. "
        "Select 62 scalp EEG channels in native EDF order (exclude Ref1, Ref2, Marker). "
        "Calibrated EDF volts multiplied by 1e6 in float64 to recover native microvolts; "
        "no filtering, resampling, demeaning, baseline correction or rereferencing applied. "
        "Six-second (3,072-sample at 512 Hz) finger-imagery blocks (codes 3..7 -> labels 1..5) "
        "verified 100% sample-for-sample between native EDF Marker channel and BIDS _events.tsv "
        "(whose onset column was divided by 512 twice in ds008446 v1.0.1). One incomplete final "
        "cue in sub-18 task-random run-01 (2,858/3,072 samples) is explicitly excluded."
    )
    return dict(
        name="ImaginedFingersPilot" if pilot else "ImaginedFingers",
        source="Damm2026 / OpenNeuro ds008446 v1.0.1",
        cache="Damm2026",
        hz=512,
        points=3072,
        classes=5,
        train_subjects=1 if pilot else 15,
        licence="CC0-1.0",
        licence_url="https://creativecommons.org/publicdomain/zero/1.0/",
        doi="10.18112/openneuro.ds008446.v1.0.1",
        paper=(
            "Damm, L. M., Jiang, D., and Demosthenous, A. (2026), "
            "Random and Sequential Order Finger Motor Imagery, OpenNeuro ds008446 v1.0.1"
        ),
        labels=dict(LABELS),
        splitter=(lambda people, chunks: {"01"} if pilot else (set(people) & TRAIN_SUBJECTS)),
        subjects=list(PILOT_SUBJECTS) if pilot else None,
        intermediate_directory="classification-intermediate-" + ("pilot" if pilot else "full"),
        evidence_files=["damm2026-source-lock.json", "scalp-mi-candidates.md"],
        cache_evidence_files=[
            "CHANGES",
            "README.md",
            "dataset_description.json",
            "participants.json",
            "participants.tsv",
            "sourcedata/counterbalancing_log.json",
            "moabb-damm2026-reference.py",
        ],
        conversion_files=["prepare_damm2026.py"],
        note=note,
        validation_updates=dict(
            source_sensor_identity="All 62 native EDF EEG labels, types, units and order verified against BIDS _channels.tsv",
            marker_events_cross_verified_all_recordings=True,
        ),
        metadata_updates=dict(
            domain="BCI",
            paper_reference="Damm, Jiang and Demosthenous (2026), OpenNeuro ds008446 v1.0.1, DOI 10.18112/openneuro.ds008446.v1.0.1",
            eeg_reference="Linked Mastoids (BIDS EEGReference); Ref1 and Ref2 recorded separately and excluded from 62 scalp channels",
            reference="Linked Mastoids",
            original_source_url="https://openneuro.org/datasets/ds008446/versions/1.0.1",
            split_definition=split_desc,
            preprocessing=(
                "Native BIDS raw EDF acquisition (g.tec GmbH, 512 Hz, hardware passband 0-100 Hz, "
                "SoftwareFilters n/a, Linked Mastoids reference). Select 62 scalp EEG channels, "
                "multiply calibrated SI volts by 1e6 in float64, crop exact 3,072-sample (6 s) "
                "cue windows; no added DSP."
            ),
            unit_evidence="EDF header physical units uV (MNE SI multiplier 1e-6) and BIDS _channels.tsv units=uV agree across all 62 EEG channels",
            channel_identity_status="Directly verified native ordered 10-05 scalp EEG channel labels across all 80 EDF headers and BIDS _channels.tsv files",
            metadata_evidence=dict(
                direct=(
                    "Native EDF signal arrays, embedded EDF Marker channel, BIDS _events.tsv, "
                    "_channels.tsv, _eeg.json, _scans.tsv, participants.tsv and counterbalancing_log.json"
                ),
                secondary="Pinned MOABB Damm2026 adapter (commit bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5) confirming 5-finger imagery codes 3..7 and 512^2 onset scaling",
                assigned="Encoded labels 1..5 for native finger codes 3..7 and stratified 15/5 whole-subject benchmark split",
            ),
            missing_or_inconsistent_metadata=[
                "BIDS _events.tsv onset values were divided by 512 twice (sample = onset * 512^2); verified 100% sample-for-sample against native EDF Marker channel",
                "sourcedata/counterbalancing_log.json and per-run _eeg.json BlockAssignment invert which condition came first for 12/20 participants; both fields are preserved per case and the 15/5 subject split is balanced under both",
                "sub-18 task-random run-01 ends at 693.58 s (355,328 samples), truncating the 57th cue to 2,858/3,072 samples; the 56 complete cues are retained and the incomplete final cue is excluded",
                "README.md mentions a root LICENSE file not present in the Git tree; dataset_description.json explicitly declares License=CC0",
                "Individual digitised electrode coordinates are not included in ds008446; standard 10-05 channel names are preserved without inventing coordinates",
                "Redundant 27.15 GB sourcedata/Raw CSV Dataset and Visual Stimuli PNGs outside BIDS sub-* EDFs are excluded from source cache (recorded in damm2026-source-lock.json)",
            ],
        ),
    )


def prepare(
    cache_root: Path = Path("D:/Data/EEGSources"),
    output: Path = Path("D:/Data/EEG"),
    pilot: bool = False,
    cleanup_intermediates: bool = True,
) -> dict:
    """Download (if needed), convert, validate and enrich ImaginedFingers."""
    download(cache_root=cache_root, pilot=pilot)
    spec = build_spec(pilot=pilot)
    cache = Path(cache_root) / spec["cache"]
    if pilot:
        output = cache / "pilot-output"
        if (output / spec["name"]).exists():
            import shutil
            shutil.rmtree(output / spec["name"])

    conversion_report = ROOT / "docs" / "open-moabb-conversion-results.json"
    prior_report_bytes = conversion_report.read_bytes() if conversion_report.exists() else None

    try:
        core.SPECS["damm2026"] = spec
        core.READERS["damm2026"] = damm2026_records
        result = core.prepare("damm2026", cache_root=cache_root, output=output)
        folder = Path(result["path"])
        name = result["dataset"]
        metadata = json.loads((folder / f"{name}_metadata.json").read_text(encoding="utf-8"))
        for sensor in metadata["sensors"]:
            sensor["native_channel_index"] = sensor["pre_flat_removal_array_index"]
        manifest_fields = dict(
            label_mapping=spec["labels"],
            split_definition=metadata["split_definition"],
            licence_url=spec["licence_url"],
            original_source_url=metadata["original_source_url"],
            excluded_incomplete_cases=metadata["excluded_incomplete_cases"],
        )
        result = finish(
            result,
            metadata,
            spec["evidence_files"],
            spec["conversion_files"],
            manifest_fields,
        )
    finally:
        if prior_report_bytes is not None:
            conversion_report.write_bytes(prior_report_bytes)
        elif conversion_report.exists():
            conversion_report.unlink()

    removed_npz = 0
    if not pilot and cleanup_intermediates:
        inter_dir = cache / spec["intermediate_directory"]
        if inter_dir.is_dir():
            for npz_file in inter_dir.glob("recording-*.npz"):
                npz_file.unlink()
                removed_npz += 1
            try:
                inter_dir.rmdir()
            except OSError:
                pass
    result["cleaned_intermediate_npz_files"] = removed_npz

    out_json = ROOT / "docs" / f"damm2026-{'pilot' if pilot else 'conversion'}-result.json"
    core.dump(out_json, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=Path("D:/Data/EEGSources"))
    parser.add_argument("--output", type=Path, default=Path("D:/Data/EEG"))
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--keep-intermediates", action="store_true")
    args = parser.parse_args()
    prepare(
        cache_root=args.cache_root,
        output=args.output,
        pilot=args.pilot,
        cleanup_intermediates=not args.keep_intermediates,
    )
