"""Summarize converted candidates and metadata-only inspections without networking."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

import pandas as pd

from .prepare import FIELDS, dump, read_json, sha256
from .registry import CONFIG_URL, DATASETS, EXCLUDED_DATASETS


def quarantine_manifest(folder, config):
    """Document a complete but duplicate-contaminated conversion for review.

    Does not create the success marker manifest.json, modify splits, or permit .ts
    export. The exact failed converter must have been retained and match its
    checkpoint; never attribute a historical run to newer source code.
    """
    report = read_json(folder / "validation.json")
    if report["passed"] or not report["cross_split_duplicate_hashes"]:
        raise ValueError("Only a fully checked duplicate-contaminated conversion can be quarantined here")
    if any(not value for key, value in report["checks"].items() if key != "duplicate_cases"):
        raise ValueError("Other validation checks failed; inspect the incomplete conversion")
    checkpoint = read_json(folder / "checkpoint.json")
    code = folder / "conversion_code/prepare.py"
    if sha256(code) != checkpoint["script_sha256"] or checkpoint["revision"] != config["revision"]:
        raise ValueError("Missing or mismatched failed-converter snapshot")
    train = pd.read_parquet(folder / "cases_train.parquet")
    test = pd.read_parquet(folder / "cases_test.parquet")
    duplicates = train.merge(test, on="signal_sha256", suffixes=("_train", "_test"))
    pair_columns = ["signal_sha256"] + [field + "_" + split for field in (
        "case_index", "subject_id", "recording_id", "source_file", "source_epoch_index",
        "label_encoded", "original_partition") for split in ("train", "test")]
    duplicates[pair_columns].to_csv(folder / "cross-split-duplicates.csv", index=False)
    dump(folder / "source-chunks.json", checkpoint["chunks"])
    (folder / "ATTRIBUTION.txt").write_text(
        f"Contains information from {config['source']} under {config['licence']} ({config['licence_url']}).\n"
        f"{config['reference']} {config['reference_url']}\n"
        "Processed by Braindecode/OpenEEGBench; lossless HDF5 conversion; validation appended to training; original test retained.\n"
        "QUARANTINED: exact duplicate signals cross train/test. Not approved for benchmark use or release.\n",
        encoding="utf-8")
    manifest = dict(status="quarantined", dataset=config["hf_id"], revision=config["revision"],
                    provenance=config, validation=report,
                    source_urls=[f"https://huggingface.co/datasets/{config['hf_id']}/resolve/{config['revision']}/", config["source"], config["licence_evidence"], CONFIG_URL],
                    licence=dict(name=config["licence"], url=config["licence_url"], evidence=config["licence_evidence"], hf_card="unknown"),
                    environment={p: importlib.metadata.version(p) for p in ("numpy", "pandas", "h5py", "pyarrow")},
                    split=dict(key=config["split_key"], values=config["partitions"], order="train followed by validation; source recording and case order unchanged"),
                    conversion=dict(script_sha256=sha256(code), registry_sha256=sha256(folder / "conversion_code/registry.py"), signal_changes="none"),
                    artifacts={p.relative_to(folder).as_posix(): dict(sha256=sha256(p), bytes=p.stat().st_size)
                               for p in folder.rglob("*") if p.is_file() and p.name != "review-manifest.json"})
    dump(folder / "review-manifest.json", manifest)
    return manifest


def build_report(cache, output):
    cache, output = Path(cache), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    candidates, completeness = [], {}
    findings = []
    for name, config in DATASETS.items():
        if name in EXCLUDED_DATASETS:
            findings.append(f"{name}: excluded and signal arrays/export removed. 121 distinct upstream windows crossed train/test (726 affected training cases, 484 test cases, 2904 matching pairs). Only diagnostic evidence remains; see docs/issues/mdd-duplicate-windows.md.")
            continue
        source = cache / name / config["revision"]
        folder = output / name
        inspection_path = source / "inspection.json"
        if not inspection_path.exists():
            candidates.append(dict(dataset=name, status="not inspected"))
            continue
        inspected = read_json(inspection_path)
        cases = pd.read_parquet(source / "inspected_cases.parquet")
        selected = cases[cases.original_partition != "excluded"]
        observed = sorted(selected.label_encoded.unique().tolist())
        complete = (folder / "manifest.json").exists()
        quarantined = (folder / "review-manifest.json").exists()
        metadata_path = folder / "dataset.json"
        status = "converted and validated" if complete else "converted; quarantined for cross-split duplicates" if quarantined else (
            "metadata only; original licence unresolved" if name == "faced" else "not converted or incomplete")
        row = dict(dataset=name,
                   train_cases=inspected["partitions"]["train"] + inspected["partitions"]["validation"],
                   test_cases=inspected["partitions"]["test"],
                   subjects=int(selected.participant_id.nunique()),
                   source_subject_ids=int(selected.subject_id.nunique()),
                   channels=inspected["shape"][0], timepoints=inspected["shape"][1],
                   classes=len(observed), frequency=inspected["frequency"],
                   size_GB=None, licence=("unverified (NEMAR: CC-BY-4.0)" if name == "faced" else config["licence"]),
                   claimed_licence=config["licence"], status=status,
                   counts_evidence="converted arrays" if complete or quarantined else "source metadata only",
                   participants=int(selected.participant_id.nunique()),
                   declared_classes=config["classes"], observed_labels=observed,
                   excluded_cases=inspected.get("excluded_cases", 0), revision=config["revision"])
        if len(observed) != config["classes"]:
            findings.append(f"{name}: source metadata contains {len(observed)} classes {observed}, while OpenEEGBench declares {config['classes']}. No missing class was invented or relabelled.")
        if complete or quarantined:
            m = read_json(metadata_path)
            for field in ("train", "test"):
                if m["shapes"][field][0] != row[field + "_cases"]:
                    raise ValueError(f"Converted counts disagree with inspected protocol: {name}")
            row["size_GB"] = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / 1e9
            report = read_json(folder / "validation.json")
            row["subject_overlap"] = report["subject_overlap"]
            row["duplicate_cases_cross_split"] = len(report["cross_split_duplicate_hashes"])
            if complete and not report["passed"]:
                raise ValueError(f"Manifest exists but validation failed: {name}")
            completeness[name] = read_json(folder / "metadata-completeness.json")
            # Earlier successful runs can have a smaller completeness-report
            # schema while already retaining the fields in their case tables.
            actual_cases = pd.concat([pd.read_parquet(folder / f"cases_{s}.parquet") for s in ("train", "test")], ignore_index=True)
            for field in FIELDS:
                completeness[name][field] = dict(available=int(actual_cases[field].notna().sum()) if field in actual_cases else 0,
                                                total=len(actual_cases))
            if quarantined:
                duplicates = pd.read_csv(folder / "cross-split-duplicates.csv", dtype={"subject_id_train": str, "subject_id_test": str})
                row["affected_train_cases"] = int(duplicates.case_index_train.nunique())
                row["affected_test_cases"] = int(duplicates.case_index_test.nunique())
                row["matching_case_pairs"] = len(duplicates)
                detail = ""
                if name == "mdd_mumtaz2016" and (folder / "duplicate-origin-verification.json").exists():
                    detail = " These are repeated healthy-control P300 windows under six training IDs and four test IDs. An independent checksum-verified re-download of HS1/HS29 confirmed identical (121, 19, 1000) source arrays before conversion."
                findings.append(f"{name}: {row['duplicate_cases_cross_split']} distinct signal hashes occur across splits, affecting {row['affected_train_cases']} training cases and {row['affected_test_cases']} test cases ({len(duplicates)} matching pairs)." + detail + " No cases were removed or reassigned; this dataset is quarantined.")
        else:
            completeness[name] = inspected["completeness"]
        candidates.append(row)
    findings.extend([
        "BCI 2020-3 intentionally uses a within-subject run split. Its 15 subjects are shared across merged training and test.",
        "CHB-MIT's chb24 is excluded by the upstream fixed masks (861 metadata windows). chb01 and chb21 are one physical participant; 23 retained case IDs correspond to 22 known participants.",
        "CHB-MIT's 17 distributed channel names are renamed bipolar derivations. Their original pairs are retained; no monopolar positions are invented.",
        "No dataset provides explicit session IDs. Distributed window/epoch row indices and processed-recording sample intervals are available, but original acquisition trial IDs and sample indices are generally unavailable.",
        "All five inspected releases lack usable stored XYZ sensor positions, and the consulted original BIDS metadata contain no electrode-position sidecars. Channel names and FIFF types are known; positions remain unknown and no synthetic montage was added.",
        "FACED provides video identifiers. Original acquisition frequency is matched from separate BIDS sidecars for Arithmetic, BCI 2020-3 and FACED; 120 MDD cases have no exact original-sidecar match. CHB-MIT's original 256 Hz is source-reported, not recovered per example.",
        "FACED signals were not downloaded: original Synapse redistribution terms could not be verified, despite CC-BY-4.0 on the NEMAR derivative. The HF cards all declare licence unknown.",
    ])
    pilot_path = output.parent / "pilot-ts-roundtrip.json"
    if pilot_path.exists():
        pilot = read_json(pilot_path)
        if (all(pilot[s].get("exact_float32_equality") and pilot[s].get("labels_equal") for s in ("train", "test"))
                and pilot.get("aeon_classifier_on_loaded_ts")):
            findings.append("Arithmetic .ts pilot: all converted examples reload with identical float32 values and labels; an aeon SummaryClassifier fit/predict check passed on reloaded arrays. Evidence: pilot-ts-roundtrip.json in the local data root.")
    result = dict(candidates=candidates, completeness=completeness, findings=findings)
    dump(output / "candidate-report.json", result)
    pd.DataFrame(candidates).to_csv(output / "candidate-summary.csv", index=False)
    columns = ["dataset", "train_cases", "test_cases", "subjects", "channels", "timepoints", "classes", "frequency", "size_GB", "licence"]
    lines = ["# OpenEEGBench candidate preparation results", "",
        "Pinned inputs and commands are documented in `docs/openeegbench-import.md` in the repository.",
        "The existing 30 datasets and results are unchanged. No data were uploaded.", "",
        "Counts for an unconverted candidate are from inspected source metadata, not verified signal arrays.",
        "Sizes are decimal GB for complete converted directories, excluding source cache and separate .ts exports.", "",
        "| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in candidates:
        values = []
        for col in columns:
            value = row.get(col)
            values.append("-" if value is None else f"{value:.3f}" if col == "size_GB" else str(value))
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## Conversion status", ""]
    lines += [f"- `{r['dataset']}`: {r['status']}." for r in candidates]
    lines += ["", "## Metadata completeness", "",
        "Available case counts; a dash means absent. All inspected recordings have ordered channel names and FIFF channel kinds.", "",
        "| Dataset | Subject | Session | Run | Recording/source file | Distributed epoch index | Original trial/video ID | Processed sample bounds | Original sample bounds | Original Hz from BIDS |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for name, fields in completeness.items():
        values = [name]
        for field in ("subject_id", "session_id", "run_id", "recording_id", "source_epoch_index", "original_trial_id", "start_sample_processed", "original_start_sample", "original_frequency_from_bids"):
            value = fields.get(field, {}).get("available", 0)
            values.append(str(value) if value else "-")
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## Findings and exceptions", ""]
    lines += ["- " + f for f in findings]
    lines += ["", "Metadata values are directly recovered unless labelled as derived or inferred. Per-recording MNE Info and original source sidecars retain position/reference information where present; null positions remain unknown. See each dataset's JSON, case tables and validation report for full details. Depression/MDD is excluded from download/export choices; its signal arrays were removed and only diagnostic reports remain. See docs/additional-datasets.md for local names and descriptions.", ""]
    (output / "candidate-report.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path(".openeegbench/source"))
    parser.add_argument("--output", type=Path, default=Path(".openeegbench/archive"))
    parser.add_argument("--quarantine", choices=DATASETS, help="Write a review manifest for a complete conversion rejected only for cross-split duplicates")
    args = parser.parse_args()
    if args.quarantine:
        quarantine_manifest(args.output / args.quarantine, DATASETS[args.quarantine])
    report = build_report(args.cache, args.output)
    print(json.dumps(report["candidates"], indent=2))


if __name__ == "__main__":
    main()
