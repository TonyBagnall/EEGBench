"""Export prepared candidates into the local Name/Name_TRAIN.ts EEG layout.

Writes a combined Name_rows.tsv, Name_metadata.json, channels.txt, source evidence
and export validation. Every .ts case is re-read and compared to its HDF5 source
without loading the entire dataset into RAM. Existing dataset folders are never
overwritten. Quarantined data require an explicit flag and go under _quarantine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import h5py
import numpy as np
import pandas as pd

from .prepare import dump, read_json, sha256
from .registry import EXCLUDED_DATASETS


EXPORTS = {
    "bcic2a": ("ImaginedHandFeetTongue", "Four imagined movements: left hand, right hand, feet and tongue"),
    "isruc-sleep": ("ClinicalSleepStages", "Five-stage sleep classification"),
    "faced": ("VideoEmotions", "Eight observed video-elicited emotion classes; Neutral missing upstream"),
    "arithmetic_zyma2019": ("MentalArithmetic", "Mental arithmetic versus eyes-closed rest"),
    "bcic2020-3": ("ImaginedCommands", "Five imagined spoken commands"),
    "chbmit": ("ChildhoodSeizures", "Seizure versus background EEG"),
}


def ts_header(name, channels, timepoints, classes, quarantined=False, class_values=None):
    warning = "# QUARANTINED: exact duplicate signals cross TRAIN/TEST; see QUARANTINED.txt\n" if quarantined else ""
    return (warning + f"# See {name}_metadata.json and {name}_rows.tsv for sensors, provenance and case identities.\n"
            f"@problemName {name}\n@timestamps false\n@missing false\n@univariate false\n"
            f"@dimension {channels}\n@equalLength true\n@seriesLength {timepoints}\n"
            "@classLabel true " + " ".join(map(str, range(classes) if class_values is None else class_values)) + "\n@data\n")


def parse_case(line, channels, timepoints):
    parts = line.rstrip("\r\n").split(":")
    if len(parts) != channels + 1:
        raise ValueError("Incorrect number of channels in exported .ts case")
    data = [np.fromstring(part, dtype=np.float32, sep=",") for part in parts[:-1]]
    if any(len(ch) != timepoints for ch in data):
        raise ValueError("Incorrect timepoint count in exported .ts case")
    return np.stack(data), int(parts[-1])


def validate_ts(path, X, y):
    """Stream every written case back from disk and compare signals and labels."""
    count = 0
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip().lower() == "@data":
                break
        else:
            raise ValueError("No @data marker")
        for line in f:
            if count >= len(X):
                raise ValueError("Extra .ts case")
            case, label = parse_case(line, X.shape[1], X.shape[2])
            if not np.array_equal(case, X[count]) or label != int(y[count]):
                raise ValueError(f"Export differs from source at case {count}")
            count += 1
            if count % 2000 == 0:
                print(f"{Path(path).name}: verified {count}/{len(X)} cases", flush=True)
    if count != len(X):
        raise ValueError("Missing .ts cases")
    return dict(cases=count, shape=list(X.shape), exact_float32_equality=True, labels_equal=True,
                sha256=sha256(path), bytes=Path(path).stat().st_size)


def aeon_smoke(folder, name, metadata):
    """Load representative exported cases with aeon and fit/predict a classifier."""
    from aeon.datasets import load_from_ts_file
    from aeon.classification.feature_based import SummaryClassifier
    examples = {}
    for split in ("TRAIN", "TEST"):
        per_class = {}
        with (folder / f"{name}_{split}.ts").open(encoding="utf-8") as f:
            for line in f:
                if line.strip().lower() == "@data":
                    break
            for line in f:
                label = int(line.rsplit(":", 1)[-1])
                per_class.setdefault(label, [])
                if len(per_class[label]) < 4:
                    per_class[label].append(line)
                if len(per_class) == metadata["classes"] and all(len(rows) == 4 for rows in per_class.values()):
                    break
        examples[split] = [line for label in sorted(per_class) for line in per_class[label]]
    with tempfile.TemporaryDirectory(prefix="aeon-ts-", dir=folder) as temporary:
        loaded = {}
        for split, lines in examples.items():
            path = Path(temporary) / f"{split}.ts"
            path.write_text(ts_header(name, len(metadata["channel_names"]), metadata["shapes"]["train"][2], metadata["classes"], class_values=metadata.get("observed_class_values")) + "".join(lines), encoding="utf-8")
            loaded[split] = load_from_ts_file(path)
        estimator = SummaryClassifier(random_state=0, n_jobs=1)
        estimator.fit(*loaded["TRAIN"])
        predicted = estimator.predict(loaded["TEST"][0])
        if len(predicted) != len(loaded["TEST"][1]):
            raise ValueError("aeon classifier failed on exported data")
    return dict(passed=True, classifier="aeon SummaryClassifier", train_cases=len(examples["TRAIN"]),
                test_cases=len(examples["TEST"]), note="Compatibility check only; no benchmark accuracy is reported.")


def export_dataset(source, destination, dataset, include_quarantined=False, smoke=True):
    if dataset in EXCLUDED_DATASETS:
        raise ValueError(EXCLUDED_DATASETS[dataset])
    source, destination = Path(source) / dataset, Path(destination)
    name, target = EXPORTS[dataset]
    metadata = read_json(source / "dataset.json")
    validation = read_json(source / "validation.json")
    quarantined = not validation["passed"]
    if quarantined and not include_quarantined:
        raise ValueError("Quarantined dataset requires --include-quarantined and is exported under _quarantine")
    marker = source / ("review-manifest.json" if quarantined else "manifest.json")
    if not marker.exists():
        raise ValueError("Source conversion has no completion/review manifest")
    folder = destination / "_quarantine" / name if quarantined else destination / name
    if folder.exists():
        raise FileExistsError(f"Refusing to overwrite existing dataset folder: {folder}")
    # Estimate before creating an output folder. Text plus evidence is larger than
    # float32 HDF5; use a conservative upper bound for nine significant digits.
    required = sum(np.prod(shape, dtype=np.int64) for shape in metadata["shapes"].values()) * 18 + 100_000_000
    if shutil.disk_usage(destination).free < required:
        raise OSError(f"Insufficient output space; reserve {required / 1e9:.1f} GB")
    folder.mkdir(parents=True)
    if metadata["provenance"].get("local_preparation_only"):
        (folder / "LOCAL_RESEARCH_ONLY.txt").write_text(
            "Prepared for local research. This conversion does not grant redistribution rights.\n"
            + "\n".join(metadata["provenance"]["notes"]) + "\n", encoding="utf-8")
    if quarantined:
        (folder / "QUARANTINED.txt").write_text(
            "FOR INVESTIGATION ONLY. Exact duplicate signals cross TRAIN/TEST in the pinned upstream release.\n"
            "Original splits and cases are retained. Do not include this dataset in benchmark results or publish it as a clean split.\n"
            "See cross-split-duplicates.csv, duplicate-origin-verification.json and source-validation.json.\n", encoding="utf-8")
    all_rows = []
    reports = {}
    channels, timepoints = len(metadata["channel_names"]), metadata["shapes"]["train"][2]
    channel_format = ",".join(["%.9g"] * timepoints)
    with h5py.File(source / "arrays.h5", "r") as f:
        if json.loads(f.attrs["channel_names_json"]) != metadata["channel_names"]:
            raise ValueError("Source HDF5 and JSON channel order disagree")
        for split in ("train", "test"):
            X, y = f[f"X_{split}"], f[f"y_{split}"][:]
            cases = pd.read_parquet(source / f"cases_{split}.parquet")
            if len(cases) != len(X) or not np.array_equal(cases.label_encoded, y):
                raise ValueError("Source case metadata and arrays disagree")
            path = folder / f"{name}_{split.upper()}.ts"
            with path.open("x", encoding="utf-8", newline="\n") as out:
                out.write(ts_header(name, channels, timepoints, metadata["classes"], quarantined, metadata.get("observed_class_values")))
                for i in range(len(X)):
                    case = X[i]
                    out.write(":".join(channel_format % tuple(ch.tolist()) for ch in case) + f":{y[i]}\n")
                    if (i + 1) % 2000 == 0:
                        print(f"{name} {split}: wrote {i + 1}/{len(X)} cases", flush=True)
            reports[split.upper()] = validate_ts(path, X, y)
            # Match the common local row schema while retaining all distributed
            # fields. No precomputed validation folds are imposed on classifiers.
            rows = cases.copy()
            rows.insert(0, "split", split.upper())
            rows.insert(1, "row", np.arange(len(rows)))
            rows.insert(2, "example_id", [f"{metadata['provenance']['hf_id']}@{metadata['provenance']['revision']}/{r.recording_id}/epoch-{r.source_epoch_index}" for r in rows.itertuples()])
            group = rows.participant_id.astype("string")
            if metadata["provenance"]["split_key"] == "run":
                group = group + "/run-" + rows.run_id.astype("string")
            rows.insert(3, "group", group)
            rows["label"] = rows.label_encoded
            rows["validation_fold"] = pd.NA
            rows["source_label"] = rows.label_original
            if rows.example_id.duplicated().any():
                raise ValueError("Non-unique source example identifiers")
            leading = ["split", "row", "example_id", "group", "participant_id", "label", "validation_fold"]
            rows = rows[leading + [col for col in rows if col not in leading]]
            all_rows.append(rows)
            shutil.copy2(source / f"cases_{split}.parquet", folder / f"cases_{split}.parquet")
    combined = pd.concat(all_rows, ignore_index=True)
    if combined.example_id.duplicated().any():
        raise ValueError("Source example IDs repeat across partitions")
    combined.to_csv(folder / f"{name}_rows.tsv", sep="\t", index=False, na_rep="")
    reloaded = pd.read_csv(folder / f"{name}_rows.tsv", sep="\t", dtype=str, keep_default_na=False)
    if reloaded.example_id.tolist() != combined.example_id.tolist() or reloaded.subject_id.tolist() != combined.subject_id.tolist():
        raise ValueError("TSV metadata order or string identifiers changed")
    local_channels = metadata["channel_names"]
    if dataset == "isruc-sleep":
        local_channels = [sensor["source_derivation"] for sensor in metadata["sensors"]]
        if any(not name for name in local_channels):
            raise ValueError("ISRUC source derivation mapping is incomplete")
    (folder / "channels.txt").write_text(", ".join(local_channels) + "\n", encoding="utf-8")
    local_metadata = dict(metadata)
    local_metadata.update(name=name, source_dataset_name=dataset, target=target,
        preparation_status="quarantined" if quarantined else "validated local preparation",
        channels=metadata["channel_names"], sampling_frequency_hz=metadata["frequency"],
        samples_per_case=timepoints, seconds_per_case=metadata["window_seconds"],
        units="numeric microvolt scale recorded by upstream multiplication by 1e6; retained MNE unit tags can still say V",
        source_url=metadata["provenance"]["source"], source_doi=metadata["provenance"]["doi"],
        license=metadata["provenance"]["licence"], license_url=metadata["provenance"]["licence_url"],
        paper_url=metadata["provenance"]["reference_url"], dtype="float32", axis_order=["example", "channel", "time"],
        label_map=metadata["label_mapping"], group_unit=metadata["provenance"]["split_key"],
        split_policy=read_json(marker)["split"], validation_fold_policy="Not provided; fitted classifiers own validation/tuning.",
        case_metadata=dict(file=f"{name}_rows.tsv", ordering="TRAIN then TEST; row is zero-based within split", identifiers="strings; preserve leading zeros", label="unchanged encoded source target"),
        local_export_validation=reports)
    if dataset == "arithmetic_zyma2019":
        local_metadata["related_local_dataset"] = dict(name="EEGMAT", relationship="same original PhysioNet EEGmat collection", differences="EEGMAT uses 500 Hz / 2 s windows; Arithmetic uses the pinned OpenEEGBench 200 Hz / 5 s windows and different subject split. Not independent recording collections.")
    if dataset == "isruc-sleep":
        local_metadata["distributed_channel_names"] = metadata["channel_names"]
        local_metadata["channels"] = local_metadata["channel_names"] = local_channels
        local_metadata["sensors"] = [dict(sensor, name=actual, distributed_name=sensor["name"])
                                     for sensor, actual in zip(metadata["sensors"], local_channels)]
        local_metadata["channel_name_correction"] = "Recovered original bipolar derivation labels from serialized upstream rename_channels mapping; array axis order unchanged."
    dump(folder / f"{name}_metadata.json", local_metadata)
    for item in ("ATTRIBUTION.txt", "metadata-completeness.json", "source-chunks.json",
                 "cross-split-duplicates.csv", "duplicate-origin-verification.json", "bibliographic-correction.json"):
        if (source / item).exists():
            shutil.copy2(source / item, folder / item)
    shutil.copy2(marker, folder / "source-manifest.json")
    shutil.copy2(source / "validation.json", folder / "source-validation.json")
    shutil.copytree(source / "source_metadata", folder / "source_metadata")
    shutil.copytree(source / "conversion_code", folder / "conversion_code")
    if smoke:
        reports["aeon"] = aeon_smoke(folder, name, metadata)
    reports["quality_status"] = "quarantined" if quarantined else "passed"
    reports["metadata_rows_verified"] = len(combined)
    reports["channel_order"] = "identical to source arrays and source JSON; no reordering"
    dump(folder / f"{name}_validation.json", reports)
    (folder / f"README_{name}.md").write_text(
        f"# {name}\n\n{target}. {'QUARANTINED: source duplicates cross TRAIN/TEST.' if quarantined else 'Validated local .ts preparation.'}\n\n"
        f"Source: {metadata['provenance']['hf_id']} at `{metadata['provenance']['revision']}`.\n\n"
        f"Use `{name}_TRAIN.ts` and `{name}_TEST.ts`. Original validation is appended to training; test is unchanged. "
        f"`{name}_rows.tsv` records source partitions and zero-based row numbers, ordered TRAIN then TEST. "
        "Read IDs as strings. No validation folds are assigned.\n\n"
        f"`channels.txt` and `{name}_metadata.json` give exact channel order and types. Positions remain unknown; "
        "CHBMIT channel names are upstream renamings of bipolar derivations, not monopolar sensor locations.\n\n"
        f"See `{name}_validation.json`, `source-validation.json`, source metadata and attribution for limitations and checks.\n",
        encoding="utf-8")
    manifest = dict(name=name, source_dataset=dataset, revision=metadata["provenance"]["revision"],
        status="quarantined" if quarantined else "validated", format="aeon multivariate .ts with local EEG sidecars",
        split=read_json(marker)["split"], licence=metadata["provenance"]["licence"],
        exporter_sha256=sha256(__file__), validation=reports,
        artifacts={p.relative_to(folder).as_posix(): dict(sha256=sha256(p), bytes=p.stat().st_size) for p in folder.rglob("*") if p.is_file()})
    dump(folder / f"{name}_manifest.json", manifest)
    print(f"Completed {folder} ({manifest['status']})", flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(".openeegbench/archive"))
    parser.add_argument("--destination", type=Path, default=Path("D:/Data/EEG"))
    parser.add_argument("--dataset", choices=(*EXPORTS, "all"), default="all")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()
    for dataset in EXPORTS if args.dataset == "all" else [args.dataset]:
        if dataset == "mdd_mumtaz2016" and not args.include_quarantined:
            continue
        export_dataset(args.source, args.destination, dataset, args.include_quarantined)


if __name__ == "__main__":
    main()
