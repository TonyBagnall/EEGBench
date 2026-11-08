"""Prepare source-pinned MOABB collections as .ts plus ordered EEG sidecars.

The first adapter is BI2014a (VisualSubjects). Downloads original Zenodo files;
does not execute MOABB's filtering, relabelling or incorrect F3/F4 channel aliases.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time
import urllib.request
import zipfile

import numpy as np
from scipy.io import loadmat

NAME = "VisualSubjects"
RECORD = 3266223
CHANNELS = ["Fp1", "Fp2", "F5", "AFZ", "F6", "T7", "Cz", "T8", "P7", "P3", "PZ", "P4", "P8", "O1", "Oz", "O2"]
MOABB_REVISION = "bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5"
AUTHOR_REVISION = "15d9ddd1a9322cce2b70b2a9ba41485047262ddd"
SFREQ, POINTS = 512, 512
FIELDS = ["split", "row", "example_id", "group", "participant_id", "session_id", "run_id",
          "loader_session_id", "loader_run_id", "recording_id", "source_file", "source_archive",
          "source_epoch_index", "start_sample", "end_sample", "start_time_seconds", "end_time_seconds",
          "source_event_code", "source_label", "label", "label_description", "original_partition",
          "signal_sha256"]


def sha(path, algorithm="sha256"):
    result = hashlib.new(algorithm)
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def fetch(url, path, checksum=None, size=None):
    """Download atomically with retries; validate pinned publisher checksums."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def valid():
        return path.is_file() and (size is None or path.stat().st_size == size) and (
            checksum is None or checksum == "md5:" + sha(path, "md5"))
    if valid():
        return path
    for attempt in range(5):
        try:
            part = path.with_name(path.name + ".part")
            request = urllib.request.Request(url, headers={"User-Agent": "EEGBench source-pinned dataset preparation"})
            with urllib.request.urlopen(request, timeout=180) as response, part.open("wb") as file:
                shutil.copyfileobj(response, file, length=1024 * 1024)
            part.replace(path)
            if not valid():
                raise ValueError(f"Publisher checksum/size mismatch: {path.name}")
            return path
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def sources(cache, subjects, download=True):
    cache = Path(cache)
    record_path = cache / f"zenodo-record-{RECORD}.json"
    if download:
        fetch(f"https://zenodo.org/api/records/{RECORD}", record_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record["id"] != RECORD or record["metadata"]["license"]["id"] != "cc-by-4.0":
        raise ValueError("Unexpected source release or data licence")
    files = {item["key"]: item for item in record["files"]}
    needed = ["Header.csv", *[f"subject_{subject:02d}.zip" for subject in subjects]]
    def ensure(name):
        item = files[name]
        path = cache / name
        if download:
            fetch(item["links"]["self"], path, item["checksum"], item["size"])
        if not path.exists() or path.stat().st_size != item["size"] or "md5:" + sha(path, "md5") != item["checksum"]:
            raise ValueError(f"Missing or modified source file: {name}")
        return name
    with ThreadPoolExecutor(max_workers=3) as pool:
        for name in pool.map(ensure, needed):
            print(f"Source verified: {name}", flush=True)
    header = [field.strip() for field in (cache / "Header.csv").read_text().strip().split(",")]
    if header != ["Time", *CHANNELS, "Event", "Target"]:
        raise ValueError("Original channel header changed; channel order must be reviewed")
    for label, repo, revision, filename in [
        ("moabb", "NeuroTechX/moabb", MOABB_REVISION, "moabb/datasets/braininvaders.py"),
        ("author", "plcrodrigues/py.BI.EEG.2014a-GIPSA", AUTHOR_REVISION, "braininvaders2014a/dataset.py"),
    ]:
        url = f"https://raw.githubusercontent.com/{repo}/{revision}/{filename}"
        if download:
            fetch(url, cache / f"{label}-loader.py")
        if not (cache / f"{label}-loader.py").exists():
            raise ValueError("Pinned source-loader evidence is missing")
        dump(cache / f"{label}-revision.json", dict(repository=repo, revision=revision, file=filename, url=url))
    return record, files


def read_recording(archive, subject):
    member = f"subject_{subject:02d}.mat"
    with zipfile.ZipFile(archive) as zipped:
        # Read an exact member; never extract untrusted paths.
        with zipped.open(member) as file:
            array = loadmat(file)["samples"]
    if array.ndim != 2 or array.shape[1] != 19 or len(array) < POINTS:
        raise ValueError("Unexpected samples matrix schema")
    if not np.isfinite(array).all() or not np.allclose(np.diff(array[:, 0]), 1 / SFREQ, atol=1e-8, rtol=0):
        raise ValueError("Missing signal values or inconsistent source timebase")
    stim = array[:, 18]
    if not set(np.unique(stim)) <= {0, 1, 2}:
        raise ValueError("Unknown target codes")
    return array, member


def event_onsets(array):
    """One epoch per target-marker onset; held pulses do not duplicate cases."""
    stim = array[:, 18]
    starts = np.flatnonzero((stim != 0) & np.r_[True, stim[1:] != stim[:-1]])
    if not len(starts):
        raise ValueError("No target/non-target markers")
    return starts


def header(name=NAME):
    return (f"# BI2014a / Zenodo {RECORD}, CC BY 4.0. See metadata and case sidecars.\n"
            "# Original Header.csv sensor names retained, including F5/F6; no channel reordering.\n"
            f"@problemName {name}\n@timestamps false\n@missing false\n@univariate false\n"
            f"@dimensions 16\n@equalLength true\n@seriesLength {POINTS}\n@classLabel true 1 2\n@data\n")


def signal_hash(array):
    return hashlib.sha256(np.asarray(array, dtype="<f4").tobytes()).hexdigest()


def lines(path):
    with Path(path).open(encoding="ascii") as file:
        for line in file:
            if line.strip().lower() == "@data":
                break
        else:
            raise ValueError("Missing @data marker")
        yield from file


def validate_split(folder, split):
    counts, people, hashes = Counter(), set(), set()
    count = 0
    last = (-1, -1)
    path = folder / f"{NAME}_{split}.ts"
    with (folder / f"cases_{split.lower()}.tsv").open(newline="", encoding="utf-8") as file:
        rows = iter(csv.DictReader(file, delimiter="\t"))
        for count, line in enumerate(lines(path), 1):
            row = next(rows, None)
            if row is None or row["split"] != split or int(row["row"]) != count - 1:
                raise ValueError("Case metadata row alignment failed")
            parts = line.strip().split(":")
            if len(parts) != 17:
                raise ValueError("Incorrect exported channel count")
            array = np.stack([np.fromstring(ch, dtype="<f4", sep=",") for ch in parts[:-1]])
            label = int(parts[-1])
            hashed = signal_hash(array)
            if array.shape != (16, POINTS) or hashed != row["signal_sha256"] or label != int(row["label"]) or str(label) != row["source_label"]:
                raise ValueError("Exported signal/label differs from source epoch")
            start, end = int(row["start_sample"]), int(row["end_sample"])
            key = (int(row["participant_id"]), start)
            if end - start != POINTS or key <= last:
                raise ValueError("Epoch bounds or deterministic ordering changed")
            last = key
            people.add(row["participant_id"])
            counts[label] += 1
            hashes.add(hashed)
        if next(rows, None) is not None:
            raise ValueError("Extra metadata rows")
    return dict(cases=count, shape=[count, 16, POINTS], class_counts=dict(sorted(counts.items())),
                subjects=sorted(people), exact_float32_roundtrip=True, metadata_rows_verified=True,
                sha256=sha(path), bytes=path.stat().st_size), hashes


def smoke_test(folder):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier

    loaded = {}
    with tempfile.TemporaryDirectory(dir=folder, prefix="aeon-check-") as tmp:
        for split in ("TRAIN", "TEST"):
            samples = {1: [], 2: []}
            for line in lines(folder / f"{NAME}_{split}.ts"):
                label = int(line.rsplit(":", 1)[1])
                if len(samples[label]) < 4:
                    samples[label].append(line)
                if all(len(items) == 4 for items in samples.values()):
                    break
            path = Path(tmp) / f"{split}.ts"
            path.write_text(header() + "".join(line for label in samples for line in samples[label]), encoding="ascii")
            loaded[split] = load_from_ts_file(path)
        model = SummaryClassifier(random_state=0, n_jobs=1)
        model.fit(*loaded["TRAIN"])
        predicted = model.predict(loaded["TEST"][0])
        if len(predicted) != len(loaded["TEST"][1]):
            raise ValueError("Classifier compatibility failed")
    return dict(passed=True, aeon_version=aeon.__version__, classifier="SummaryClassifier",
                train_cases=len(loaded["TRAIN"][1]), test_cases=len(predicted),
                note="Representative compatibility check; full case readback checked separately, no benchmark scores.")


def convert(cache, output, subjects=tuple(range(1, 65)), train=tuple(range(1, 49)), download=True, smoke=True):
    cache, output = Path(cache).resolve(), Path(output).resolve()
    subjects, train = tuple(sorted(subjects)), set(train)
    if len(subjects) != len(set(subjects)) or not set(subjects) <= set(range(1, 65)) or not train or not train < set(subjects):
        raise ValueError("Invalid participant split")
    folder = output / NAME
    if folder.exists():
        raise FileExistsError(f"Refusing to overwrite {folder}")
    if smoke:
        from aeon.datasets import load_from_ts_file  # noqa: F401
        from aeon.classification.feature_based import SummaryClassifier  # noqa: F401
    record, files = sources(cache, subjects, download)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{NAME}-", dir=output) as tmp:
        stage = Path(tmp)
        handles, tables, writers = {}, {}, {}
        counts = Counter()
        recordings, discarded = [], []
        all_rows = []
        fmt = ",".join(["%.9g"] * POINTS)
        max_cast_error = 0.0
        try:
            for split in ("TRAIN", "TEST"):
                handles[split] = (stage / f"{NAME}_{split}.ts").open("w", encoding="ascii", newline="\n")
                handles[split].write(header())
                tables[split] = (stage / f"cases_{split.lower()}.tsv").open("w", encoding="utf-8", newline="")
                writers[split] = csv.DictWriter(tables[split], FIELDS, delimiter="\t", lineterminator="\n")
                writers[split].writeheader()
            for subject in subjects:
                archive = cache / f"subject_{subject:02d}.zip"
                samples, member = read_recording(archive, subject)
                onsets = event_onsets(samples)
                split = "TRAIN" if subject in train else "TEST"
                subject_counts = Counter()
                previous_end, overlap_cases = -1, 0
                for event_index, onset in enumerate(onsets):
                    onset = int(onset)
                    end = onset + POINTS
                    if end > len(samples):
                        discarded.append(dict(participant_id=f"{subject:02d}", source_epoch_index=event_index,
                                              onset_sample=onset, reason="incomplete one-second epoch at recording end"))
                        continue
                    raw = samples[onset:end, 1:17].T
                    case = np.asarray(raw, dtype="<f4")
                    max_cast_error = max(max_cast_error, float(np.max(np.abs(raw - case))))
                    label = int(samples[onset, 18])
                    if onset < previous_end:
                        overlap_cases += 1
                    previous_end = end
                    row = dict.fromkeys(FIELDS, "")
                    row.update(split=split, row=counts[split], example_id=f"zenodo:{RECORD}/subject_{subject:02d}/event-{event_index}",
                               group=f"{subject:02d}", participant_id=f"{subject:02d}",
                               loader_session_id="0", loader_run_id="0", recording_id=f"subject_{subject:02d}",
                               source_file=member, source_archive=archive.name, source_epoch_index=event_index,
                               start_sample=onset, end_sample=end, start_time_seconds=float(samples[onset, 0]),
                               end_time_seconds=float(samples[end - 1, 0] + 1 / SFREQ),
                               source_event_code=float(samples[onset, 17]), source_label=label, label=label,
                               label_description="NonTarget" if label == 1 else "Target", original_partition="unpartitioned",
                               signal_sha256=signal_hash(case))
                    writers[split].writerow(row)
                    all_rows.append(row)
                    handles[split].write(":".join(fmt % tuple(channel.tolist()) for channel in case) + f":{label}\n")
                    counts[split] += 1
                    subject_counts[label] += 1
                if set(subject_counts) != {1, 2}:
                    raise ValueError(f"Missing a class for participant {subject:02d}")
                recordings.append(dict(participant_id=f"{subject:02d}", recording_id=f"subject_{subject:02d}",
                                       samples=len(samples), source_events=len(onsets), exported_cases=sum(subject_counts.values()),
                                       class_counts=dict(sorted(subject_counts.items())), overlapping_previous_epoch=overlap_cases,
                                       mat_member=member, source_archive=archive.name, source_sha256=sha(archive),
                                       source_md5=files[archive.name]["checksum"],
                                       raw_first_time_seconds=float(samples[0, 0]), raw_last_time_seconds=float(samples[-1, 0]),
                                       source_marker_codes=np.unique(samples[:, 17]).tolist(),
                                       target_marker_codes=np.unique(samples[:, 18]).tolist()))
                print(f"{subject:02d}: {sum(subject_counts.values())} {split} epochs", flush=True)
        finally:
            for file in [*handles.values(), *tables.values()]:
                file.close()
        reports, hashes = {}, {}
        for split in ("TRAIN", "TEST"):
            reports[split], hashes[split] = validate_split(stage, split)
            print(f"Full {split} readback passed: {reports[split]['cases']} cases", flush=True)
        duplicate_count = len(hashes["TRAIN"] & hashes["TEST"])
        if duplicate_count or set(reports["TRAIN"]["subjects"]) & set(reports["TEST"]["subjects"]):
            raise ValueError("Signal duplicates or participants cross TRAIN/TEST")
        if set(reports["TRAIN"]["subjects"]) != {f"{s:02d}" for s in train} or set(reports["TEST"]["subjects"]) != {f"{s:02d}" for s in set(subjects) - train}:
            raise ValueError("Unexpected participant membership")
        all_rows.sort(key=lambda r: (r["split"] != "TRAIN", int(r["row"])))
        if len({r["example_id"] for r in all_rows}) != len(all_rows):
            raise ValueError("Duplicate example identifiers")
        with (stage / f"{NAME}_rows.tsv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(all_rows)
        aeon_check = smoke_test(stage) if smoke else {"passed": False, "status": "not run"}
        validation = dict(quality_status="passed" if smoke else "signal validation passed; aeon not run",
                          partitions=reports, aeon=aeon_check, metadata_rows_verified=len(all_rows),
                          cross_split_duplicate_signal_hashes=duplicate_count, subject_overlap=[],
                          cross_split_recording_overlap=False, within_recording_epoch_overlap=True,
                          channel_order="All files use the global original Header.csv schema; axes copied without reordering. No per-subject sensor headers supplied.",
                          dropped_events=discarded, max_float32_cast_absolute_error_source_units=max_cast_error)
        split_definition = dict(unit="participant", train=[f"{s:02d}" for s in sorted(train)],
                                test=[f"{s:02d}" for s in sorted(set(subjects) - train)], validation="none",
                                origin="EEGBench-defined fixed split; MOABB supplies no universal fixed TRAIN/TEST split.")
        metadata = dict(name=NAME, source_dataset_name="BI2014a", source_aliases=["BrainInvaders2014a", "bi2014a", "BI.EEG.2014a-GIPSA", "nm000244"],
                        target="Visual P300 attended-target versus non-target flash", domain="BCI",
                        source_url=f"https://zenodo.org/records/{RECORD}", source_doi=f"10.5281/zenodo.{RECORD}",
                        source_version="v1", source_concept_doi="10.5281/zenodo.3266222",
                        paper_url="https://hal.science/hal-02171575", reference="Korczowski et al. (2019), Brain Invaders calibration-less P300-based BCI using dry EEG electrodes Dataset (bi2014a).",
                        authors=record["metadata"]["creators"], license="CC-BY-4.0", license_url="https://creativecommons.org/licenses/by/4.0/",
                        license_evidence=f"https://zenodo.org/api/records/{RECORD}", licence_applicability="Original dataset record explicitly licenses EEG data under CC BY 4.0; attribution and conversion details retained.",
                        subjects=len(subjects), recruited_subjects_reported=71, distributed_subjects=64,
                        sessions=None, distributed_recordings=len(subjects), loader_sessions_per_subject=1, loader_runs_per_session=1,
                        session_note="One distributed recording per person, exposed as loader session/run 0/0. Original game session boundaries not recovered; source describes up to three game sessions.",
                        frequency=SFREQ, sampling_frequency_hz=SFREQ, original_sampling_frequency_hz=SFREQ,
                        channels=CHANNELS, channel_names=CHANNELS, channel_count=16, timepoints=POINTS,
                        sensors=[dict(array_index=i, name=n, type="EEG", name_evidence="original Header.csv", position=None) for i,n in enumerate(CHANNELS)],
                        channel_order_evidence="Original release Header.csv applies to every samples matrix; all records have 19 columns with 16 EEG axes in columns 1:17.",
                        channel_name_discrepancy=dict(original_header=["F5", "F6"], loader_aliases=["F3", "F4"],
                                                      decision="Use original F5/F6; preserve exact AFZ/PZ spelling. No signal reordering.",
                                                      moabb_revision=MOABB_REVISION, author_revision=AUTHOR_REVISION),
                        montage="10-10/10-20 layout described by source; individual positions unavailable",
                        channel_reference="right earlobe (source/MOABB acquisition description)", positions=None,
                        acquisition=dict(hardware="g.USBamp", electrodes="g.Sahara dry gold-alloy electrodes",
                                         ground="FZ, as reported in MOABB acquisition metadata; not verified from the numeric files",
                                         line_frequency_hz=50, online_digital_filter="none reported",
                                         evidence="Source/MOABB acquisition description; not directly recovered from MAT values"),
                        units="microvolts, following MOABB's source-to-volts multiplication by 1e-6; no scale change here",
                        dtype="float32", axis_order=["case", "channel", "time"],
                        shapes={s.lower():reports[s]["shape"] for s in reports}, classes=2,
                        label_map={"1":"NonTarget", "2":"Target"}, class_counts={s.lower():reports[s]["class_counts"] for s in reports},
                        window_seconds=1, epoch_interval="[event_onset, event_onset+512) original samples; end exclusive",
                        overlap="Naturally overlapping epochs within a recording; no recording/subject crosses partitions.",
                        preprocessing=dict(epoching="target-marker onset, one second, no baseline correction",
                                           filtering="none added", resampling="none", referencing="unchanged", units="unchanged source scale",
                                           dtype_conversion="MAT float64 numeric values cast to float32; .ts uses 9 significant digits, exact float32 roundtrip",
                                           acquisition="Original online filtering/reference information is publication/loader evidence, not encoded by the numeric matrix."),
                        split_policy=split_definition, case_metadata=dict(file=f"{NAME}_rows.tsv", ordering="TRAIN then TEST, row zero-based within split", identifiers="strings, preserve 01-09"),
                        metadata_evidence=dict(distributed_files=["global channel order", "participant filename", "sample timestamps", "event and target codes", "matrix dimensions", "licence record"],
                                               loader_or_publication=["EEG type", "hardware/reference", "source signal units", "game sessions"],
                                               locally_defined=["TRAIN/TEST split", "epoch IDs and bounds", "encoded labels equal original target codes"]),
                        missing_metadata=["individual sensor positions", "physical session/run boundaries", "original block/selection IDs (event codes retained without unverified decoding)", "subject demographics per retained person"])
        dump(stage / f"{NAME}_metadata.json", metadata)
        dump(stage / f"{NAME}_validation.json", validation)
        dump(stage / "recordings.json", recordings)
        dump(stage / "dropped-events.json", discarded)
        dump(stage / "metadata-completeness.json", dict(evidence=metadata["metadata_evidence"], missing=metadata["missing_metadata"]))
        (stage / "channels.txt").write_text(", ".join(CHANNELS) + "\n", encoding="utf-8")
        (stage / "channels.tsv").write_text("array_index\tname\ttype\tposition\n" + "".join(f"{i}\t{n}\tEEG\t\n" for i,n in enumerate(CHANNELS)), encoding="utf-8")
        (stage / "ATTRIBUTION.txt").write_text(
            "Korczowski, Louis; Ostaschenko, Ekaterina; Andreev, Anton; Cattan, Grégoire; Coelho Rodrigues, Pedro Luis; Gautheret, Violette; Congedo, Marco (2019).\n"
            "Brain Invaders calibration-less P300-based BCI using dry EEG electrodes Dataset (bi2014a), v1. DOI: 10.5281/zenodo.3266223.\n"
            "Data licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n"
            "EEGBench conversion: subject split, one-second onset epochs, float32 conversion and .ts export. Original F5/F6 names retained; no filtering/resampling/re-referencing.\n", encoding="utf-8")
        (stage / f"README_{NAME}.md").write_text(
            f"# {NAME}\n\nBI2014a: visual attended-target (2) versus non-target (1) flash EEG.\n\n"
            "Use the TRAIN/TEST .ts files; per-split case TSVs have exactly matching rows. "
            "The combined rows TSV is TRAIN then TEST. Read IDs as strings. Original samples/time "
            "and event codes are retained; end_sample is exclusive. One-second epochs may overlap "
            "within a person, while people and recordings are disjoint across partitions.\n\n"
            "Source Header.csv gives F5/F6, conflicting with F3/F4 loader aliases. We retain source names "
            "and array order. Physical session boundaries and individual positions are unavailable; "
            "loader 0/0 identifiers are separate from unknown physical session/run IDs.\n\n"
            "No filters, resampling or reference changes are added. Float32 conversion is documented; "
            "all exported cases pass numeric readback. See attribution, metadata, validation and "
            "manifest for source pins and CC BY 4.0 terms. No benchmark results are included.\n", encoding="utf-8")
        evidence = stage / "source_metadata"
        evidence.mkdir()
        for filename in [f"zenodo-record-{RECORD}.json", "Header.csv", "moabb-loader.py", "author-loader.py", "moabb-revision.json", "author-revision.json"]:
            shutil.copy2(cache / filename, evidence / filename)
        code = stage / "conversion_code"
        code.mkdir()
        shutil.copy2(__file__, code / Path(__file__).name)
        manifest = dict(name=NAME, status=validation["quality_status"], source=dict(record=RECORD, version="v1",
                        url=metadata["source_url"], doi=metadata["source_doi"], licence="CC-BY-4.0",
                        record_json_sha256=sha(cache / f"zenodo-record-{RECORD}.json"),
                        files=[dict(filename=r["source_archive"], sha256=r["source_sha256"], checksum=r["source_md5"],
                                    url=files[r["source_archive"]]["links"]["self"]) for r in recordings]),
                        moabb_revision=MOABB_REVISION, author_loader_revision=AUTHOR_REVISION, split=split_definition,
                        conversion=metadata["preprocessing"], validation=validation,
                        artifacts={p.relative_to(stage).as_posix():dict(sha256=sha(p), bytes=p.stat().st_size) for p in stage.rglob("*") if p.is_file()})
        dump(stage / f"{NAME}_manifest.json", manifest)
        stage.rename(folder)
    print(json.dumps(dict(dataset=NAME, output=str(folder), train=counts["TRAIN"], test=counts["TEST"], validation=validation["quality_status"])), flush=True)
    return metadata, validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["bi2014a", "kalunga2016", "erpcore_n400"], default="bi2014a")
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("D:/Data/EEG"))
    parser.add_argument("--subjects", default=None)
    parser.add_argument("--train-subjects", default=None)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.dataset == "erpcore_n400":
        from tools.prepare_erpcore import convert as convert_erpcore
        selected_convert, cache, n_subjects, n_train = convert_erpcore, ".openeegbench/erpcore-source", 40, 30
    elif args.dataset == "kalunga2016":
        from tools.prepare_kalunga import convert as convert_kalunga
        selected_convert, cache, n_subjects, n_train = convert_kalunga, ".openeegbench/kalunga-source", 12, 9
    else:
        selected_convert, cache, n_subjects, n_train = convert, ".openeegbench/bi2014a-source", 64, 48
    subjects = tuple(map(int,args.subjects.split(","))) if args.subjects else tuple(range(1,n_subjects+1))
    train = tuple(map(int,args.train_subjects.split(","))) if args.train_subjects else tuple(range(1,n_train+1))
    selected_convert(args.cache or Path(cache), args.output, subjects, train, not args.offline)


if __name__ == "__main__":
    main()
