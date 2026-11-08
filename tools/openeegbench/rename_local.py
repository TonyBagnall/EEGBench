"""Rename local exports to task names without rewriting their signal data blocks."""

import argparse
from pathlib import Path
import shutil

from .prepare import dump, read_json, sha256


RENAMES = {"Arithmetic": "MentalArithmetic", "BCIC2020Speech": "ImaginedCommands", "CHBMIT": "ChildhoodSeizures"}
RENAMES.update(BCIIV2a="ImaginedHandFeetTongue", ISRUCSleep="ClinicalSleepStages", FACED="VideoEmotions")
RENAMES["Weibo2014"] = "ImaginedLeftRightHand"
RENAMES["AlexMI"] = "ImaginedRightHandFeet"


def replace_header(path, old, new, channels, timepoints, classes, class_values=None):
    """Keep the exact @data byte offset by padding a short comment line."""
    path = Path(path)
    size = path.stat().st_size
    with path.open("r+b") as f:
        old_header = b""
        while len(old_header) < 8192:
            line = f.readline()
            if not line:
                raise ValueError("Missing @data header")
            old_header += line
            if line.strip().lower() == b"@data":
                break
        else:
            raise ValueError("Unexpectedly large .ts header")
        directives = [line for line in old_header.splitlines(keepends=True) if line.startswith(b"@")]
        if not any(line.strip() == f"@problemName {old}".encode() for line in directives):
            raise ValueError("Input problem name differs")
        # Preserve source label tokens verbatim, including sparse codes and text labels.
        header = b"# See accompanying metadata and case sidecars.\n" + b"".join(
            f"@problemName {new}\n".encode() if line.strip() == f"@problemName {old}".encode() else line
            for line in directives)
        padding = len(old_header) - len(header)
        if padding < 0:
            raise ValueError("New header does not fit; no data changed")
        header = header.replace(b"\n", b" " * padding + b"\n", 1)
        if len(header) != len(old_header):
            raise ValueError("Header length mismatch")
        f.seek(0)
        f.write(header)
        if f.tell() != len(old_header):
            raise ValueError("Write crossed the data boundary")
    if path.stat().st_size != size:
        raise ValueError("File length changed")
    return dict(data_offset=len(old_header), file_bytes=size,
                method="Only the fixed-length header prefix was written; signal/label bytes after @data were untouched.")


def rename_dataset(root, old, new):
    root = Path(root).resolve()
    source, destination = root / old, root / new
    if source.parent != root or destination.parent != root:
        raise ValueError("Dataset rename is outside the requested EEG root")
    if destination.exists():
        raise FileExistsError(destination)
    m = read_json(source / f"{old}_metadata.json")
    manifest_path = source / f"{old}_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        validation = read_json(source / f"{old}_validation.json")
    else:
        validation = m["validation"]
        if not all(validation[s].get("exact_float32_roundtrip") and validation[s].get("aeon_full_roundtrip_passed") for s in ("TRAIN", "TEST")):
            raise ValueError("Legacy export lacks recorded roundtrip validation")
        manifest = dict(name=old, status="validated", revision=m.get("source_version"),
                        historical_validation_evidence=f"{old}_metadata.json.validation")
        dump(manifest_path, manifest)
    if manifest["status"] != "validated":
        raise ValueError("Only completed validated exports can be renamed here")
    exporter = Path(__file__).with_name("export_local.py")
    (source / "conversion_code").mkdir(exist_ok=True)
    if sha256(exporter) == manifest.get("exporter_sha256"):
        shutil.copy2(exporter, source / "conversion_code/export_local.py")
    headers = {}
    for split in ("TRAIN", "TEST"):
        file = source / f"{old}_{split}.ts"
        headers[split] = replace_header(file, old, new, len(m["channels"]), m["samples_per_case"], m.get("classes", len(m["label_map"])), m.get("observed_class_values"))
        file.rename(source / f"{new}_{split}.ts")
        validation[split]["sha256"] = sha256(source / f"{new}_{split}.ts")
    validation["task_name_update"] = dict(previous=old, current=new, headers=headers,
        note="Earlier full signal/label round-trip checks still apply; only the header prefix and file names changed.")
    m["name"] = new
    m.setdefault("source_dataset_name", old)
    m["aliases"] = list(dict.fromkeys(m.get("aliases", []) + [old, m["source_dataset_name"]] + ([m["provenance"]["hf_id"]] if "provenance" in m else [])))
    m.setdefault("case_metadata", {})["file"] = f"{new}_rows.tsv"
    m["local_export_validation"] = {key: validation[key] for key in ("TRAIN", "TEST")}
    dump(source / f"{old}_metadata.json", m)
    dump(source / f"{old}_validation.json", validation)
    readme = source / f"README_{old}.md"
    text = readme.read_text(encoding="utf-8").replace(old, new) if readme.exists() else f"# {new}\n\n{m['target']}.\n\nUse {new}_TRAIN.ts and {new}_TEST.ts; see {new}_metadata.json and {new}_rows.tsv.\n"
    readme.write_text(text + f"\nPrevious local name / source alias: {old}. Signal and label data blocks were preserved during renaming.\n", encoding="utf-8")
    for suffix in ("_metadata.json", "_rows.tsv", "_validation.json"):
        (source / f"{old}{suffix}").rename(source / f"{new}{suffix}")
    readme.rename(source / f"README_{new}.md")
    # Keep the old manifest as a historical record, clearly distinguished from
    # the current manifest whose artifact names and hashes are regenerated.
    (source / f"{old}_manifest.json").rename(source / "previous-name-manifest.json")
    manifest.update(name=new, previous_local_name=old, aliases=m["aliases"], validation=validation,
                    naming_update=dict(renamer_sha256=sha256(__file__), data_blocks="unchanged"))
    shutil.copy2(__file__, source / "conversion_code/rename_local.py")
    ts_hashes = {f"{new}_{split}.ts": validation[split]["sha256"] for split in ("TRAIN", "TEST")}
    manifest["artifacts"] = {p.relative_to(source).as_posix(): dict(sha256=ts_hashes[p.name] if p.name in ts_hashes else sha256(p), bytes=p.stat().st_size)
                             for p in source.rglob("*") if p.is_file()}
    dump(source / f"{new}_manifest.json", manifest)
    source.rename(destination)
    print(f"Renamed {old} -> {destination}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("D:/Data/EEG"))
    parser.add_argument("--dataset", choices=(*RENAMES, "all"), default="all")
    args = parser.parse_args()
    for old, new in RENAMES.items():
        if args.dataset != "all" and args.dataset != old:
            continue
        if not (args.root / old).exists() and (args.root / new).exists():
            continue
        rename_dataset(args.root, old, new)


if __name__ == "__main__":
    main()
