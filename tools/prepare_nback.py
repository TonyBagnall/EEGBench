"""Prepare Christoph Tremmel's local N-back/audio data as .ts plus sidecars.

Run python -m tools.prepare_nback --help. No network access or signal processing.
Source subject blocks and exclusions were confirmed by the archive owner.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np

NAME = "NBackAudioCondition"
LABELS = [10 * audio + nback for audio in range(4) for nback in range(3)]


@dataclass(frozen=True)
class Layout:
    subjects: int = 25
    rows_per_subject: int = 720
    channels: int = 16
    timepoints: int = 600
    excluded: tuple[int, ...] = (10, 16)
    train: tuple[int, ...] = (1, 3, 4, 5, 6, 7, 8, 11, 12, 13, 17, 20, 21, 22, 23, 24)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def signal_hash(array):
    return hashlib.sha256(np.asarray(array, dtype="<f8").tobytes()).hexdigest()


def parse_source(line, layout):
    """Keep decimal signal tokens unchanged; validate every value and joint code."""
    parts = line.replace(b"\x00", b"").strip().decode("ascii").split(":")
    if len(parts) != layout.channels + 1:
        raise ValueError("Incorrect source channel count or blank row")
    fields = parts[-1].split()
    if len(fields) != 3:
        raise ValueError("Expected nback, audio and combined source labels")
    nback, audio, combined = map(int, fields)
    if nback not in range(3) or audio not in range(4) or combined != audio * 10 + nback:
        raise ValueError("Inconsistent joint source label")
    values = []
    for channel in parts[:-1]:
        tokens = channel.strip().split(",")
        if len(tokens) != layout.timepoints:
            raise ValueError("Incorrect source timepoint count")
        values.append([float(value) for value in tokens])
    array = np.asarray(values, dtype="<f8")
    if not np.isfinite(array).all():
        raise ValueError("Missing or non-finite source signal")
    payload = ":".join(channel.strip() for channel in parts[:-1])
    return payload, array, nback, audio, combined


def header(layout):
    return (
        "# Data attributed to Christoph Tremmel. More information to follow.\n"
        "# Joint class = 10 * audio_condition + nback_level. See metadata sidecars.\n"
        f"@problemName {NAME}\n@timestamps false\n@missing false\n"
        f"@univariate false\n@dimensions {layout.channels}\n@equalLength true\n"
        f"@seriesLength {layout.timepoints}\n@classLabel true "
        + " ".join(map(str, LABELS)) + "\n@data\n"
    )


def read_cases(path):
    with Path(path).open(encoding="ascii") as file:
        for line in file:
            if line.strip().lower() == "@data":
                break
        else:
            raise ValueError("No @data marker")
        yield from file


def validate_partition(folder, split, layout):
    """Check every exported numeric signal against its source hash and case row."""
    count = 0
    observed = Counter()
    path = folder / f"{NAME}_{split}.ts"
    with (folder / f"cases_{split.lower()}.tsv").open(newline="", encoding="utf-8") as file:
        rows = iter(csv.DictReader(file, delimiter="\t"))
        for count, line in enumerate(read_cases(path), 1):
            row = next(rows, None)
            if row is None or row["row"] != str(count - 1) or row["split"] != split:
                raise ValueError("Metadata row alignment failed")
            parts = line.strip().split(":")
            array = np.asarray([[float(v) for v in ch.split(",")] for ch in parts[:-1]], dtype="<f8")
            label = int(parts[-1])
            if array.shape != (layout.channels, layout.timepoints):
                raise ValueError("Exported array shape changed")
            if signal_hash(array) != row["signal_sha256"] or label != int(row["label"]):
                raise ValueError("Signal or label differs from source")
            if label != 10 * int(row["audio_condition"]) + int(row["nback_level"]):
                raise ValueError("Joint label differs from metadata")
            if int(row["source_row_index"]) // layout.rows_per_subject + 1 != int(row["participant_id"]):
                raise ValueError("Subject identity differs from confirmed source block")
            observed[label] += 1
        if next(rows, None) is not None:
            raise ValueError("Extra metadata rows")
    return dict(cases=count, shape=[count, layout.channels, layout.timepoints],
                class_counts=dict(sorted(observed.items())), exact_float64_signal_hashes=True,
                metadata_rows_verified=True, sha256=digest(path), bytes=path.stat().st_size)


def smoke_test(folder, layout):
    import aeon
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier

    loaded = {}
    with tempfile.TemporaryDirectory(dir=folder, prefix="aeon-check-") as tmp:
        for split in ("TRAIN", "TEST"):
            examples = {label: [] for label in LABELS}
            for line in read_cases(folder / f"{NAME}_{split}.ts"):
                label = int(line.rsplit(":", 1)[1])
                if len(examples[label]) < 2:
                    examples[label].append(line)
                if all(len(value) >= 2 for value in examples.values()):
                    break
            path = Path(tmp) / f"{split}.ts"
            path.write_text(header(layout) + "".join(line for label in LABELS for line in examples[label]), encoding="ascii")
            loaded[split] = load_from_ts_file(path)
        classifier = SummaryClassifier(random_state=0, n_jobs=1)
        classifier.fit(*loaded["TRAIN"])
        predicted = classifier.predict(loaded["TEST"][0])
        if len(predicted) != len(loaded["TEST"][1]) or not set(predicted) <= set(loaded["TRAIN"][1]):
            raise ValueError("aeon compatibility check failed")
    return dict(passed=True, classifier="aeon SummaryClassifier", aeon_version=aeon.__version__, all_12_classes_loaded=True,
                train_cases=len(loaded["TRAIN"][1]), test_cases=len(predicted),
                note="Representative cases; full numeric readback is checked separately. No benchmark scores.")


def prepare(source, output, layout=Layout(), smoke=True):
    if smoke:
        # Fail before scanning the large source if the verification environment is broken.
        from aeon.datasets import load_from_ts_file  # noqa: F401
        from aeon.classification.feature_based import SummaryClassifier  # noqa: F401

    source, output = Path(source).resolve(), Path(output).resolve()
    folder = output / NAME
    if folder.exists():
        raise FileExistsError(f"Refusing to overwrite {folder}")
    people = set(range(1, layout.subjects + 1)) - set(layout.excluded)
    train = set(layout.train)
    if not train or not train < people or len(train) != len(layout.train):
        raise ValueError("Invalid subject split")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{NAME}-", dir=output) as tmp:
        stage = Path(tmp)
        fields = ["split", "row", "example_id", "group", "participant_id", "session_id",
                  "run_id", "label", "source_label", "nback_level", "audio_condition",
                  "source_row_index", "trial_index_within_subject", "source_file",
                  "original_partition", "recording_id", "start_sample", "end_sample",
                  "signal_sha256"]
        handles, tables, writers = {}, {}, {}
        counts = Counter()
        hashes = {"TRAIN": set(), "TEST": set()}
        by_subject = Counter()
        per_subject_class = Counter()
        source_hash = hashlib.sha256()
        null_bytes = 0
        try:
            for split in hashes:
                handles[split] = (stage / f"{NAME}_{split}.ts").open("w", encoding="ascii", newline="\n")
                handles[split].write(header(layout))
                tables[split] = (stage / f"cases_{split.lower()}.tsv").open("w", encoding="utf-8", newline="")
                writers[split] = csv.DictWriter(tables[split], fields, delimiter="\t", lineterminator="\n")
                writers[split].writeheader()
            source_rows = 0
            with source.open("rb") as file:
                for index, line in enumerate(file):
                    source_hash.update(line)
                    null_bytes += line.count(b"\x00")
                    payload, array, nback, audio, label = parse_source(line, layout)
                    subject = index // layout.rows_per_subject + 1
                    if subject > layout.subjects:
                        raise ValueError("Unexpected extra source subjects/rows")
                    source_rows += 1
                    by_subject[subject] += 1
                    per_subject_class[subject, label] += 1
                    if subject in layout.excluded:
                        continue
                    split = "TRAIN" if subject in train else "TEST"
                    hashed = signal_hash(array)
                    hashes[split].add(hashed)
                    row = dict.fromkeys(fields, "")
                    row.update(split=split, row=counts[split],
                               example_id=f"ChristophTremmelNBack:source-row-{index}",
                               group=str(subject), participant_id=str(subject), label=label,
                               source_label=label, nback_level=nback, audio_condition=audio,
                               source_row_index=index, trial_index_within_subject=index % layout.rows_per_subject,
                               source_file=source.name, original_partition="unpartitioned",
                               signal_sha256=hashed)
                    writers[split].writerow(row)
                    handles[split].write(f"{payload}:{label}\n")
                    counts[split] += 1
                    if source_rows % 3000 == 0:
                        print(f"Read {source_rows} source rows", flush=True)
        finally:
            for file in [*handles.values(), *tables.values()]:
                file.close()
        if source_rows != layout.subjects * layout.rows_per_subject:
            raise ValueError("Incorrect source row count")
        expected = layout.rows_per_subject // 12
        if layout.rows_per_subject % 12 or any(per_subject_class[s, c] != expected for s in by_subject for c in LABELS):
            raise ValueError("Unexpected class distribution within subject")
        duplicates = hashes["TRAIN"] & hashes["TEST"]
        if duplicates:
            raise ValueError(f"{len(duplicates)} exact duplicate signal hashes cross TRAIN/TEST")
        reports = {split: validate_partition(stage, split, layout) for split in hashes}
        with (stage / f"{NAME}_rows.tsv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for split in hashes:
                with (stage / f"cases_{split.lower()}.tsv").open(encoding="utf-8", newline="") as part:
                    writer.writerows(csv.DictReader(part, delimiter="\t"))
        with (stage / f"{NAME}_rows.tsv").open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file, delimiter="\t"))
        if len(rows) != sum(counts.values()) or len({row["example_id"] for row in rows}) != len(rows):
            raise ValueError("Combined metadata count or identifiers invalid")
        actual_train = {row["participant_id"] for row in rows if row["split"] == "TRAIN"}
        actual_test = {row["participant_id"] for row in rows if row["split"] == "TEST"}
        if actual_train & actual_test or actual_train != {str(s) for s in train} or actual_test != {str(s) for s in people - train}:
            raise ValueError("Subject membership validation failed")
        aeon = smoke_test(stage, layout) if smoke else {"passed": False, "status": "not run"}
        validation = dict(quality_status="passed" if smoke else "signal validation passed; aeon not run",
                          partitions=reports, aeon=aeon, source_rows=source_rows,
                          metadata_rows_verified=len(rows), subject_overlap=[],
                          cross_split_duplicate_signal_hashes=len(duplicates),
                          channel_order="Source array axes retained unchanged; sensor identities unknown.",
                          overlapping_recording_intervals="Unknown: original recording identifiers/bounds unavailable.",
                          null_bytes_removed=null_bytes)
        sensors = [dict(array_index=i, name=None, type="EEG", type_evidence="local formatter; not independently verified",
                        position=None) for i in range(layout.channels)]
        metadata = dict(name=NAME, domain="Psy", target="Joint audio condition and N-back level",
                        attribution="Christoph Tremmel", description="More information to follow.",
                        source_collection="Christoph Tremmel N-back/audio working-memory data",
                        source_aliases=["Christoph EEG", "NBack", "NBackR", "ClassificationData"],
                        source_file=source.name, source_url=None, source_doi=None, paper_url=None,
                        license=None, license_status="Not supplied; local preparation, redistribution not established.",
                        source_subjects=layout.subjects, subjects=len(people), sessions=None, recordings=None,
                        excluded_participant_ids=[str(s) for s in layout.excluded],
                        exclusion_reason="Exclusions confirmed by archive owner; scientific reason to follow.",
                        train_participant_ids=[str(s) for s in sorted(train)],
                        test_participant_ids=[str(s) for s in sorted(people - train)],
                        participant_identity_evidence="Archive owner confirmed contiguous 720-row subject blocks and exclusions on 4 November 2026; original source IDs unavailable.",
                        channels=layout.channels, channel_names=[None] * layout.channels, sensors=sensors,
                        channel_order_consistent="All cases have the same source array-axis layout; anatomical identity/order cannot be independently verified.",
                        channel_reference=None, montage=None, sampling_frequency_hz=None, original_sampling_frequency_hz=None,
                        timepoints=layout.timepoints, samples_per_case=layout.timepoints, window_seconds=None,
                        overlap=None, units=None, axis_order=["case", "channel", "time"],
                        shapes={s.lower(): reports[s]["shape"] for s in hashes},
                        classes=12, class_values=LABELS,
                        label_map={str(c): dict(nback_level=c % 10, audio_condition=c // 10) for c in LABELS},
                        class_counts={s.lower(): reports[s]["class_counts"] for s in hashes},
                        audio_condition_definitions="Codes 0-3 supplied; descriptions to follow.",
                        preprocessing="None added. Remove stray NUL bytes and replace final three-field source segment with unchanged combined label; signal decimal tokens and channel order preserved. Original preprocessing unknown.",
                        split_policy="Reuse original NBack formatter's subject split; source order preserved within each partition. No separate validation partition.",
                        original_partition="Source text is unpartitioned; TRAIN/TEST assigned locally.",
                        case_metadata=dict(file=f"{NAME}_rows.tsv", ordering="TRAIN then TEST; zero-based row within split; read identifiers as strings"),
                        related_preparations="NBack, NBackR and noise subsets use the same source collection; not independent recording collections.",
                        missing_metadata=["original sensor names and verified sensor types", "sampling frequency", "sessions", "recording/run IDs", "original trial IDs", "recording sample/time bounds", "units", "audio descriptions", "montage/reference", "original preprocessing", "publication/source URL/DOI", "data licence"])
        dump(stage / f"{NAME}_metadata.json", metadata)
        dump(stage / f"{NAME}_validation.json", validation)
        dump(stage / "metadata-completeness.json", dict(available=["confirmed participant blocks", "local source row/trial index", "joint and component labels", "array dimensions/order", "fixed split"], missing=metadata["missing_metadata"]))
        (stage / "channels.txt").write_text("Original sensor names are unknown. The source's channel array order is preserved; see sensors in metadata JSON.\n", encoding="utf-8")
        with (stage / "channels.tsv").open("w", encoding="utf-8", newline="") as file:
            file.write("array_index\tname\ttype\ttype_evidence\n")
            for sensor in sensors:
                file.write(f"{sensor['array_index']}\t\tEEG\tlocal formatter; not independently verified\n")
        (stage / "ATTRIBUTION.txt").write_text("Data attributed to Christoph Tremmel. More information to follow.\nOriginal publication, source licence and audio-condition descriptions have not yet been supplied.\n", encoding="utf-8")
        (stage / f"README_{NAME}.md").write_text(
            f"# {NAME}\n\nData attributed to Christoph Tremmel. More information to follow.\n\n"
            "Twelve joint classes: label = 10 * audio condition (0-3) + N-back level (0-2). "
            "Signal values are unchanged. Subject blocks/exclusions were confirmed by the archive owner; "
            "the existing subject split is preserved. Read participant IDs as strings.\n\n"
            "Use the TRAIN/TEST .ts files and corresponding cases_train.tsv / cases_test.tsv; "
            "the combined rows TSV is TRAIN then TEST. Row numbers are zero-based within each split. "
            "Source-row and within-subject indices are local indices, not recovered acquisition trial IDs.\n\n"
            "Sensor names, sampling frequency, sessions and original recording bounds are unknown. "
            "Channel indices do not imply anatomical identities. The licence is pending; this local "
            "preparation does not establish redistribution permission. See metadata and validation JSON.\n",
            encoding="utf-8")
        code = stage / "conversion_code"
        code.mkdir()
        shutil.copy2(__file__, code / Path(__file__).name)
        manifest = dict(name=NAME, status=validation["quality_status"], source=dict(path=str(source),
                        bytes=source.stat().st_size, sha256=source_hash.hexdigest(), attribution="Christoph Tremmel", revision="SHA-256 of supplied local source", urls=[], licence=None),
                        conversion=dict(script="conversion_code/prepare_nback.py", signal_processing="none",
                                        labels="original combined code = 10 * audio + nback", order="source order within split"),
                        split=dict(unit="participant", train=metadata["train_participant_ids"], test=metadata["test_participant_ids"], excluded=metadata["excluded_participant_ids"], validation="none"),
                        artifacts={p.relative_to(stage).as_posix(): dict(bytes=p.stat().st_size, sha256=digest(p)) for p in stage.rglob("*") if p.is_file()})
        dump(stage / f"{NAME}_manifest.json", manifest)
        stage.rename(folder)
    print(json.dumps(dict(dataset=NAME, folder=str(folder), train=counts["TRAIN"], test=counts["TEST"], validation=validation["quality_status"])), flush=True)
    return metadata, validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("C:/Data/ChristophEEG/ClassificationData/ClassificationData.txt"))
    parser.add_argument("--output", type=Path, default=Path("D:/Data/EEG"))
    args = parser.parse_args()
    prepare(args.source, args.output)


if __name__ == "__main__":
    main()
