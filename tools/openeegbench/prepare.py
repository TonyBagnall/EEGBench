"""Import pinned OpenEEGBench WindowsDataset Zarr v3 releases.

Run ``python -m tools.openeegbench.prepare --help``. No upstream Python code is
executed. This adapter reads the serialized MNE Info directly and implements only
the audited float32 / bytes / gzip Zarr schema; other schemas fail explicitly.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.metadata
import io
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import ssl
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import urllib.error

import h5py
import certifi
import numpy as np
import pandas as pd

from .registry import CONFIG_URL, DATASETS, EXCLUDED_DATASETS, OPENEEGBENCH_REVISION

ZROOT = "sourcedata/braindecode/dataset.zarr"
VERSION = 1
SCRIPT_BYTES = Path(__file__).read_bytes()
REGISTRY_BYTES = Path(__file__).with_name("registry.py").read_bytes()
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
FIELDS = [
    "subject_id", "participant_id", "session_id", "run_id", "recording_id",
    "source_file", "original_trial_id", "source_epoch_index",
    "start_sample_processed", "stop_sample_processed", "start_time_seconds",
    "stop_time_seconds", "original_start_sample", "original_stop_sample",
    "label_original", "label_encoded", "original_partition",
    "label_name", "label_name_evidence", "original_frequency_from_bids",
]


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_bytes(path, data):
    """Publish complete cache files, including when separate commands share cache."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".download-", delete=False) as f:
        temporary = Path(f.name)
        f.write(data)
    temporary.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request_bytes(url):
    for attempt in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "EEGBench-source-audit/1"}), timeout=120, context=TLS_CONTEXT) as response:
                return response.read(), response.headers
        except urllib.error.HTTPError as error:
            if error.code not in (429, 499, 500, 502, 503, 504) or attempt == 11:
                raise
            retry = error.headers.get("Retry-After", "30")
            wait = min(60, max(5, int(retry) if retry.isdigit() else 30))
            print(f"HTTP {error.code} at {urllib.parse.urlsplit(url).netloc}; retrying in {wait}s", flush=True)
            time.sleep(wait)
        except (OSError, TimeoutError):
            if attempt == 11:
                raise
            time.sleep(min(2 ** attempt, 8))


def safe_path(root, relative):
    parts = PurePosixPath(relative).parts
    if not parts or any(p in ("..", ".") or ":" in p or "\\" in p for p in parts) or PurePosixPath(relative).is_absolute():
        raise ValueError(f"Unsafe source path: {relative}")
    return Path(root).joinpath(*parts)


def check_blob(data, entry):
    if len(data) != entry["size"]:
        raise ValueError(f"Size mismatch: {entry['path']}")
    lfs = entry.get("lfs")
    if lfs:
        expected = lfs.get("oid", lfs.get("sha256"))
        actual = hashlib.sha256(data).hexdigest()
    else:
        expected = entry.get("oid", entry.get("sha"))
        actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if not expected or actual != expected:
        raise ValueError(f"Source checksum mismatch: {entry['path']}")


class Source:
    """Pinned, verified HF metadata cache; signal chunks are temporary only."""

    def __init__(self, config, cache):
        self.config = config
        self.cache = Path(cache) / config["name"] / config["revision"]
        self.base = f"https://huggingface.co/datasets/{config['hf_id']}/resolve/{config['revision']}/"
        self.files = {}
        self.blob_cache = Path(cache) / ".metadata-blobs"
        self._blob_locks = defaultdict(threading.Lock)

    def inventory(self):
        path = self.cache / "inventory.json"
        if path.exists():
            entries = read_json(path)
        else:
            entries = []
            url = f"https://huggingface.co/api/datasets/{self.config['hf_id']}/tree/{self.config['revision']}?recursive=true&limit=1000"
            while url:
                body, headers = request_bytes(url)
                entries.extend(json.loads(body))
                url = next((s.split(">", 1)[0].strip(" <") for s in headers.get("Link", "").split(",") if 'rel="next"' in s), None)
            dump(path, entries)
        self.files = {v["path"]: v for v in entries if v["type"] == "file"}
        return self.files

    def fetch(self, name, target=None):
        entry = self.files[name]
        path = safe_path(self.cache, name) if target is None else Path(target)
        if path.exists():
            check_blob(path.read_bytes(), entry)
        elif target is None:
            # Repeated sidecars often have identical git blob IDs. Avoid an HTTP
            # request for every copy, but still verify every destination.
            oid = entry.get("lfs", {}).get("oid", entry["oid"])
            blob = self.blob_cache / oid
            with self._blob_locks[oid]:
                if blob.exists():
                    data = blob.read_bytes()
                else:
                    data, _ = request_bytes(self.base + urllib.parse.quote(name))
                    check_blob(data, entry)
                    atomic_bytes(blob, data)
                check_blob(data, entry)
                atomic_bytes(path, data)
        else:
            data, _ = request_bytes(self.base + urllib.parse.quote(name))
            check_blob(data, entry)
            atomic_bytes(path, data)
        return path

    def metadata(self, workers=8):
        self.inventory()
        names = [p for p in self.files if not "/data/c/" in p]
        # The reviewed releases contain EEG only under data/c. Fail closed if
        # future revisions introduce new large binary files or media.
        if any(self.files[p]["size"] > 10_000_000 for p in names):
            raise ValueError("Unexpected large metadata file; inspect source schema")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(self.fetch, names))
        return self


def partition(value, config):
    matches = [name for name, values in config["partitions"].items() if value in values]
    if not matches and value in config.get("excluded_values", []):
        return "excluded"
    if len(matches) != 1:
        raise ValueError(f"Unassigned or ambiguous split value {value!r}")
    return matches[0]


def sensor_info(info, shape):
    names = info.get("ch_names")
    channels = info.get("chs")
    if not names or not channels or len(names) != shape[1] or len(channels) != shape[1]:
        raise ValueError("Missing channel identities or channel/array dimension mismatch")
    if len(set(names)) != len(names) or [v.get("ch_name") for v in channels] != names:
        raise ValueError("Inconsistent channel names/order in serialized MNE Info")
    return [dict(array_index=i, name=name, **{k: ch.get(k) for k in
        ("kind", "coil_type", "unit", "unit_mul", "loc", "coord_frame", "cal", "range")})
        for i, (name, ch) in enumerate(zip(names, channels))]


def decoded_parameter(value):
    return json.loads(value) if isinstance(value, str) else value


def label_definitions(attrs):
    mappings = []
    for name, kwargs in decoded_parameter(attrs.get("window_kwargs", [])):
        if isinstance(kwargs, dict) and kwargs.get("mapping"):
            mappings.append(kwargs["mapping"])
    if mappings and any(m != mappings[0] for m in mappings):
        raise ValueError("Conflicting distributed label mappings")
    return {str(v): k for k, v in mappings[0].items()} if mappings else {}


def load_records(source):
    root = read_json(source.cache / ZROOT / "zarr.json")
    attrs = root["attributes"]
    if root.get("zarr_format") != 3 or attrs.get("dataset_type") != "WindowsDataset":
        raise ValueError("Expected audited WindowsDataset Zarr v3 release")
    records = []
    first_sensors = None
    first_shape = None
    first_frequency = None
    offset = 0
    for index in range(attrs["n_datasets"]):
        relative = f"{ZROOT}/recording_{index}"
        group = read_json(source.cache / relative / "zarr.json")["attributes"]
        array = read_json(source.cache / relative / "data/zarr.json")
        shape = array["shape"]
        if len(shape) != 3 or min(shape) <= 0 or array["data_type"] != "float32":
            raise ValueError(f"Unsupported shape/type in recording {index}")
        info = group["info"]
        sensors = sensor_info(info, shape)
        # Positions can be absent or differ by participant. Names, kind, units and
        # order must agree; participant-specific locations are retained per record.
        signature = [{k: c[k] for k in ("name", "kind", "unit", "unit_mul")} for c in sensors]
        if first_sensors is None:
            first_sensors, first_shape, first_frequency = signature, shape[1:], info["sfreq"]
        if signature != first_sensors or shape[1:] != first_shape or info["sfreq"] != first_frequency:
            raise ValueError(f"Channel order/type/units, frequency or shape differs in recording {index}; no reordering performed")
        table = pd.read_csv(source.cache / relative / "metadata.tsv", sep="\t", dtype=str, keep_default_na=False)
        table = table.rename(columns={table.columns[0]: "source_metadata_index"})
        if len(table) != shape[0] or not {"target", "i_window_in_trial", "i_start_in_trial", "i_stop_in_trial"} <= set(table):
            raise ValueError(f"Case metadata length/schema mismatch in recording {index}")
        if group.get("target_name") not in (None, "target"):
            raise ValueError("Unsupported alternate target_name")
        desc = group["description"]
        split = partition(desc.get(source.config["split_key"]), source.config)
        records.append(dict(index=index, relative=relative, group=group, array=array,
                            shape=shape, table=table, partition=split, global_offset=offset))
        offset += shape[0]
    if not records:
        raise ValueError("Empty source dataset")
    return attrs, records


def enrich_source(source):
    """Cache original licence evidence and optional original BIDS sidecars.

    Original sidecars are matched by BIDS source basenames, never guessed from
    array shape. Their repository revision is separate from the HF revision.
    """
    config = source.config
    evidence = source.cache / "original-source"
    evidence.mkdir(exist_ok=True)
    for name, expected in (("default_configs/datasets.py", "fcbe878832e343f615cbd9f3c87470a3dd657f75"),
                           ("dataset.py", "b4c4cf6b352eca3bd5cbd1f175ea79f62a1c868a")):
        path = safe_path(evidence / "OpenEEGBench", name)
        if not path.exists():
            data, _ = request_bytes(f"https://raw.githubusercontent.com/braindecode/OpenEEGBench/{OPENEEGBENCH_REVISION}/open_eeg_bench/" + name)
            check_blob(data, dict(path=name, size=len(data), oid=expected))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    evidence_urls = [config["licence_evidence"]]
    if config["name"] == "bcic2020-3":
        evidence_urls.append("https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/")
    for i, url in enumerate(evidence_urls):
        path = evidence / f"licence-evidence-{i}.txt"
        if not path.exists():
            path.write_bytes(request_bytes(url)[0])
    if "bids_repo" in config:
        repo, revision = config["bids_repo"], config["bids_revision"]
        url = f"https://api.github.com/repos/nemarDatasets/{repo}/git/trees/{revision}?recursive=1"
        treefile = evidence / "tree.json"
        if not treefile.exists():
            treefile.write_bytes(request_bytes(url)[0])
        tree = read_json(treefile)
        # Preserve all original recording sidecars (small, no EEG payload), so
        # varying source sampling rates and reference information remain usable.
        files = [v for v in tree["tree"] if v["type"] == "blob" and (
            v["path"] in ("README.md", "dataset_description.json", "participants.tsv")
            or v["path"].endswith(("_eeg.json", "_channels.tsv", "_electrodes.tsv", "_coordsystem.json"))) ]
        def get(entry):
            path = safe_path(evidence / "bids", entry["path"])
            if not path.exists():
                data, _ = request_bytes(f"https://raw.githubusercontent.com/nemarDatasets/{repo}/{revision}/" + entry["path"])
                check_blob(data, entry)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(get, files))
    dump(evidence / "provenance.json", dict(
        evidence_urls=evidence_urls,
        bids_repo=config.get("bids_repo"), bids_revision=config.get("bids_revision"),
        note="Original-source metadata are independent evidence; the HF release does not pin this BIDS conversion revision.",
    ))
    return evidence


def verify_licence(source):
    config = source.config
    if config["name"] in EXCLUDED_DATASETS:
        raise ValueError(EXCLUDED_DATASETS[config["name"]])
    # Reviewed local research preparations are not authorization to redistribute.
    if config.get("local_preparation_only"):
        evidence = source.cache / "original-source/licence-evidence-0.txt"
        if not evidence.exists() or not evidence.stat().st_size:
            raise ValueError("Missing original-source access evidence")
        return
    if config["name"] == "faced":
        raise ValueError("FACED EEG download disabled: NEMAR declares CC-BY-4.0 but original Synapse redistribution terms remain unverified")
    text = (source.cache / "original-source/licence-evidence-0.txt").read_text(encoding="utf-8")
    if config["licence"] == "ODC-By-1.0":
        valid = "Open Data Commons Attribution" in text
    elif config["name"] == "mdd_mumtaz2016":
        valid = json.loads(text)["license"]["name"] == "CC BY 4.0"
    elif config["name"] == "bcic2020-3":
        licence_id = json.loads(text)["data"]["relationships"]["license"]["data"]["id"]
        resolved = read_json(source.cache / "original-source/licence-evidence-1.txt")
        valid = licence_id == resolved["data"]["id"] and resolved["data"]["attributes"]["name"] == "CC-By Attribution 4.0 International"
    else:
        valid = False
    if not valid:
        raise ValueError("Data licence evidence changed or is not recognized; inspect before downloading")


def metadata_rows(record, source, definitions):
    table = record["table"].copy()
    desc = record["group"]["description"]
    n = len(table)
    table["case_in_recording"] = np.arange(n)
    table["source_global_index"] = np.arange(record["global_offset"], record["global_offset"] + n)
    for target, key in [("subject_id", "subject"), ("session_id", "session"), ("run_id", "run")]:
        value = desc.get(key)
        table[target] = str(value) if value is not None else pd.NA
    table["participant_id"] = table["subject_id"].replace({"chb21": "chb01"}) if source.config["name"] == "chbmit" else table["subject_id"]
    table["recording_id"] = f"recording_{record['index']}"
    table["source_file"] = desc.get("path")
    table["source_epoch_index"] = table["source_metadata_index"].astype("string")
    # i_window_in_trial is a window ordinal, not a trial identifier. Keep unknown
    # original IDs null. Preserve original fields and BIDS event sidecars verbatim.
    table["original_trial_id"] = table["video_index"].astype("string") if "video_index" in table else pd.NA
    for out, key in [("start_sample_processed", "i_start_in_trial"), ("stop_sample_processed", "i_stop_in_trial")]:
        table[out] = pd.to_numeric(table[key], errors="raise").astype("int64")
    if not np.all(table.stop_sample_processed - table.start_sample_processed == record["shape"][2]):
        raise ValueError("Window lengths disagree with source array")
    sfreq = record["group"]["info"]["sfreq"]
    table["start_time_seconds"] = table.start_sample_processed / sfreq
    table["stop_time_seconds"] = table.stop_sample_processed / sfreq
    table["coordinate_system"] = "processed_recording; stop exclusive; BIDS-concatenated trials for BCIC2020-3"
    table["original_start_sample"] = pd.NA
    table["original_stop_sample"] = pd.NA
    table["label_original"] = table["target"].astype("string")
    table["label_name"] = table.label_original.map(definitions).astype("string")
    table["label_name_evidence"] = "distributed window_kwargs.mapping" if definitions else pd.NA
    if not definitions and source.config["name"] == "arithmetic_zyma2019":
        table["label_name"] = desc.get("task")
        table["label_name_evidence"] = "distributed recording description.task; observed association with numeric target"
    if not definitions and source.config["name"] == "mdd_mumtaz2016":
        subject = desc.get("subject", "")
        interpretation = "healthy control" if subject.startswith("HS") else (
            "major depressive disorder" if subject.startswith("MDDS") else None)
        table["label_name"] = interpretation
        table["label_name_evidence"] = "inferred from original-source HS/MDDS subject naming and source dataset description; numeric target retained unchanged"
    table["label_encoded"] = pd.to_numeric(table["target"], errors="raise").astype("int64")
    if not table.label_encoded.between(0, source.config["classes"] - 1).all():
        raise ValueError("Labels outside declared source mapping")
    table["original_partition"] = record["partition"]
    table["task"] = desc.get("task")
    # Match original BIDS metadata by the exact source-file basename.
    basename = PurePosixPath(desc.get("path", "")).name
    stem = basename.rsplit(".", 1)[0]
    candidates = list((source.cache / "original-source/bids").rglob(stem + ".json"))
    table["original_frequency_from_bids"] = pd.NA
    table["original_frequency_evidence"] = pd.NA
    if len(candidates) == 1:
        original = read_json(candidates[0])
        table["original_frequency_from_bids"] = original.get("SamplingFrequency", pd.NA)
        table["original_frequency_evidence"] = candidates[0].relative_to(source.cache).as_posix()
    table["original_frequency_from_bids"] = table["original_frequency_from_bids"].astype("Float64")
    for col in ("subject_id", "participant_id", "session_id", "run_id", "recording_id", "source_file",
                "original_trial_id", "source_epoch_index", "label_original", "label_name",
                "label_name_evidence", "original_partition", "original_frequency_evidence"):
        table[col] = table[col].astype("string")
    return table


def read_array(record, source):
    """Decode the audited Zarr schema, including multiple/padded edge chunks."""
    meta = record["array"]
    codecs = meta.get("codecs", [])
    if codecs != [{"name": "bytes", "configuration": {"endian": "little"}},
                  {"name": "gzip", "configuration": {"level": 5}}]:
        raise ValueError("Unreviewed Zarr codecs; use an explicit adapter")
    if meta.get("chunk_key_encoding") != {"name": "default", "configuration": {"separator": "/"}}:
        raise ValueError("Unreviewed chunk key encoding")
    chunk = meta["chunk_grid"]["configuration"]["chunk_shape"]
    shape = record["shape"]
    data = np.empty(shape, dtype="<f4")
    hashes = []
    for coord in itertools.product(*(range(math.ceil(n / c)) for n, c in zip(shape, chunk))):
        name = record["relative"] + "/data/c/" + "/".join(map(str, coord))
        if name not in source.files:
            raise ValueError(f"Missing signal chunk {name}; refusing implicit fill values")
        with tempfile.TemporaryDirectory(prefix="chunk-", dir=source.cache) as tmp:
            path = source.fetch(name, Path(tmp) / "chunk.gz")
            block = np.frombuffer(gzip.decompress(path.read_bytes()), dtype="<f4")
            if block.size != math.prod(chunk):
                raise ValueError("Unexpected decoded chunk length")
            block = block.reshape(chunk)
            destination = tuple(slice(i * c, min((i + 1) * c, n)) for i, c, n in zip(coord, chunk, shape))
            valid = tuple(slice(0, s.stop - s.start) for s in destination)
            data[destination] = block[valid]
            hashes.append(dict(path=name, sha256=sha256(path), bytes=path.stat().st_size))
    if not np.isfinite(data).all():
        raise ValueError("Non-finite signal values")
    return data, hashes


def case_hash(case):
    # Canonical little-endian float32, C order, normalized signed zero.
    data = np.array(case, dtype="<f4", order="C", copy=True)
    data[data == 0] = 0
    return hashlib.sha256(data.tobytes()).hexdigest()


def validate_arrays(folder, config, records=None):
    """Re-read every output case; check metadata hashes, source alignment and splits."""
    folder = Path(folder)
    if records is None:
        local_source = Source(config, folder)
        local_source.cache = folder / "source_metadata"
        _, records = load_records(local_source)
    tables = {s: pd.read_parquet(folder / f"cases_{s}.parquet") for s in ("train", "test")}
    report = {"checks": {}, "warnings": []}
    hashes = {}
    with h5py.File(folder / "arrays.h5", "r") as f:
        for split, table in tables.items():
            X, y = f[f"X_{split}"], f[f"y_{split}"][:]
            if len(table) != len(X) or not np.array_equal(y, table.label_encoded):
                raise ValueError("Metadata/array/label alignment mismatch")
            if table.case_index.tolist() != list(range(len(table))):
                raise ValueError("Case order/index mismatch")
            if records is not None:
                expected = []
                expected_targets = []
                expected_starts = []
                expected_subjects = []
                expected_partitions = []
                for original in (["train", "validation"] if split == "train" else ["test"]):
                    for record in records:
                        if record["partition"] == original:
                            expected.extend(range(record["global_offset"], record["global_offset"] + record["shape"][0]))
                            expected_targets.extend(record["table"].target.astype(int).tolist())
                            expected_starts.extend(record["table"].i_start_in_trial.astype(int).tolist())
                            subject = record["group"]["description"].get("subject")
                            expected_subjects.extend([str(subject) if subject is not None else pd.NA] * record["shape"][0])
                            expected_partitions.extend([original] * record["shape"][0])
                if expected != table.source_global_index.tolist():
                    raise ValueError("Output does not preserve source partition order")
                if (expected_targets != y.tolist() or expected_starts != table.start_sample_processed.tolist()
                        or expected_subjects != table.subject_id.tolist()
                        or expected_partitions != table.original_partition.tolist()):
                    raise ValueError("Output case metadata disagrees with distributed source rows")
            computed = []
            for start in range(0, len(X), 64):
                block = X[start:start + 64]
                if not np.isfinite(block).all():
                    raise ValueError("Non-finite output values")
                computed.extend(case_hash(x) for x in block)
            if computed != table.signal_sha256.tolist():
                raise ValueError("Case hash/metadata correspondence failure")
            hashes[split] = set(computed)
            if set(y) != set(config.get("observed_class_values", range(config["classes"]))):
                raise ValueError(f"Missing class in {split}")
            report[split] = dict(shape=list(X.shape), class_counts={str(k): int(v) for k, v in Counter(y.tolist()).items()})
    overlap = sorted(set(tables["train"].participant_id.dropna()) & set(tables["test"].participant_id.dropna()))
    report["subject_overlap"] = overlap
    report["subject_overlap_intentional"] = config["split_key"] == "run"
    if overlap and config["split_key"] != "run":
        raise ValueError(f"Unexpected participant leakage: {overlap}")
    if overlap:
        report["warnings"].append("Intentional run-based split: subjects occur in train and test")
    duplicates = sorted(hashes["train"] & hashes["test"])
    report["cross_split_duplicate_hashes"] = duplicates
    report["checks"] = dict(shapes=True, labels=True, metadata_alignment=True,
        partition_order=records is not None, channel_order_all_recordings=records is not None,
        duplicate_cases=not duplicates, subject_split=not overlap or config["split_key"] == "run")
    report["passed"] = not duplicates
    dump(folder / "validation.json", report)
    if duplicates:
        pairs = tables["train"].merge(tables["test"], on="signal_sha256", suffixes=("_train", "_test"))
        columns = ["signal_sha256"] + [field + "_" + split for field in (
            "case_index", "subject_id", "recording_id", "source_file", "source_epoch_index",
            "label_encoded", "original_partition") for split in ("train", "test")]
        pairs[columns].to_csv(folder / "cross-split-duplicates.csv", index=False)
        raise ValueError(f"{len(duplicates)} identical signal cases cross train/test; see validation.json")
    return report


def smoke_classifier(folder, seed=0):
    """Fit a cheap aeon classifier on bounded subsets of actual converted arrays."""
    from aeon.classification.feature_based import SummaryClassifier
    with h5py.File(Path(folder) / "arrays.h5", "r") as f:
        y = f["y_train"][:]
        indices = np.sort(np.concatenate([np.flatnonzero(y == c)[:8] for c in np.unique(y)]))
        X = f["X_train"][indices]
        y_test = f["y_test"][:]
        test_indices = np.sort(np.concatenate([np.flatnonzero(y_test == c)[:2] for c in np.unique(y_test)]))
        test = f["X_test"][test_indices]
    estimator = SummaryClassifier(random_state=seed, n_jobs=1)
    estimator.fit(X, y[indices])
    predictions = estimator.predict(test)
    if len(predictions) != len(test) or not set(predictions) <= set(y):
        raise ValueError("aeon classifier smoke test failed")
    result = dict(classifier="aeon.classification.feature_based.SummaryClassifier", seed=seed,
                  train_cases=len(X), test_cases=len(test), passed=True,
                  note="Compatibility check only; not an accuracy benchmark or full-data fit.")
    dump(Path(folder) / "aeon-smoke.json", result)
    return result


def convert(source, output, smoke=True, resume=False):
    verify_licence(source)  # before fetching any EEG chunks
    config = source.config
    attrs, records = load_records(source)
    definitions = label_definitions(attrs)
    folder = Path(output) / config["name"]
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "manifest.json").exists():
        raise FileExistsError(f"Completed output exists: {folder}; choose a new output root")
    arrays = folder / "arrays.h5"
    checkpoint_path = folder / "checkpoint.json"
    checkpoint = read_json(checkpoint_path) if checkpoint_path.exists() else None
    if arrays.exists() and not (resume and checkpoint):
        raise FileExistsError(f"Partial output exists: {arrays}; inspect or choose a new output root")
    code_hash = hashlib.sha256(SCRIPT_BYTES).hexdigest()
    registry_hash = hashlib.sha256(REGISTRY_BYTES).hexdigest()
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if checkpoint and (checkpoint["revision"] != config["revision"] or checkpoint["script_sha256"] != code_hash
                       or checkpoint.get("registry_sha256") != registry_hash
                       or checkpoint.get("config_sha256") != config_hash):
        raise ValueError("Checkpoint source/converter differs; choose a new output root")
    (folder / "conversion_code").mkdir(exist_ok=True)
    (folder / "conversion_code/prepare.py").write_bytes(SCRIPT_BYTES)
    (folder / "conversion_code/registry.py").write_bytes(REGISTRY_BYTES)
    # Full source metadata is copied, excluding signal chunks, before conversion.
    # It retains original channel tables, MNE Info, dig, projectors, references,
    # recording-specific positions, preprocessing logs and source metadata rows.
    shutil.copytree(source.cache, folder / "source_metadata", ignore=shutil.ignore_patterns("chunk-*"), dirs_exist_ok=True)
    raw_bytes = sum(math.prod(r["shape"]) * 4 for r in records if r["partition"] != "excluded")
    if shutil.disk_usage(folder).free < raw_bytes * 1.1 + 256_000_000:
        raise OSError(f"Insufficient disk headroom: up to {raw_bytes / 1e9:.2f} GB uncompressed output plus staging required")
    counts = {s: sum(r["shape"][0] for r in records if r["partition"] in
                    (["train", "validation"] if s == "train" else ["test"])) for s in ("train", "test")}
    if min(counts.values()) <= 0:
        raise ValueError("Empty train or test partition")
    tables = {"train": [], "test": []}
    receipts = checkpoint["chunks"] if checkpoint else []
    completed = checkpoint["completed"] if checkpoint else []
    (folder / "progress").mkdir(exist_ok=True)
    c, t = records[0]["shape"][1:]
    with h5py.File(arrays, "r+" if resume and checkpoint else "x") as f:
        f.attrs["schema_version"] = VERSION
        f.attrs["channel_names_json"] = json.dumps(records[0]["group"]["info"]["ch_names"])
        if checkpoint is None:
            for split, n in counts.items():
                f.create_dataset(f"X_{split}", shape=(n, c, t), dtype="<f4", chunks=(1, c, t), compression="gzip", compression_opts=4, shuffle=True)
                f.create_dataset(f"y_{split}", shape=(n,), dtype="<i8")
            dump(checkpoint_path, dict(revision=config["revision"], script_sha256=code_hash,
                                      registry_sha256=registry_hash, config_sha256=config_hash, completed=[], chunks=[]))
        offsets = dict(train=0, test=0)
        for original in ("train", "validation", "test"):
            for r in records:
                if r["partition"] != original:
                    continue
                split = "test" if original == "test" else "train"
                progress_path = folder / "progress" / f"recording_{r['index']}.parquet"
                if r["index"] in completed:
                    table = pd.read_parquet(progress_path)
                    tables[split].append(table)
                    offsets[split] += len(table)
                    continue
                X, chunk_receipts = read_array(r, source)
                table = metadata_rows(r, source, definitions)
                start, n = offsets[split], len(table)
                table["case_index"] = np.arange(start, start + n)
                table["signal_sha256"] = [case_hash(case) for case in X]
                f[f"X_{split}"][start:start + n] = X
                f[f"y_{split}"][start:start + n] = table.label_encoded.to_numpy()
                tables[split].append(table)
                offsets[split] += n
                receipts.extend(chunk_receipts)
                f.flush()
                table.to_parquet(progress_path, index=False, compression="zstd")
                completed.append(r["index"])
                temporary_checkpoint = checkpoint_path.with_suffix(".partial")
                dump(temporary_checkpoint, dict(revision=config["revision"], script_sha256=code_hash,
                                                registry_sha256=registry_hash, config_sha256=config_hash,
                                                completed=completed, chunks=receipts))
                temporary_checkpoint.replace(checkpoint_path)
                print(f"{config['name']} {original}: recording_{r['index']} ({n} cases)", flush=True)
        for split, parts in tables.items():
            tables[split] = pd.concat(parts, ignore_index=True)
            for col in ("subject_id", "participant_id", "session_id", "run_id", "source_epoch_index", "source_metadata_index", "original_trial_id"):
                tables[split][col] = tables[split][col].astype("string")
            tables[split].to_parquet(folder / f"cases_{split}.parquet", index=False, compression="zstd")
    all_cases = pd.concat(list(tables.values()), ignore_index=True)
    sensors = sensor_info(records[0]["group"]["info"], records[0]["shape"])
    preprocessing = {key: decoded_parameter(attrs[key]) for key in ("raw_preproc_kwargs", "window_kwargs", "window_preproc_kwargs") if key in attrs}
    inverse = {}
    for step in preprocessing.get("raw_preproc_kwargs", []):
        if step["fn"] == "rename_channels":
            inverse.update({v: k for k, v in step["kwargs"].get("mapping", {}).items()})
    for sensor in sensors:
        sensor["source_derivation"] = inverse.get(sensor["name"])
    if not definitions:
        associations = all_cases.groupby("label_original")["label_name"].unique()
        if any(len(v) != 1 or pd.isna(v[0]) for v in associations):
            raise ValueError("Numeric targets do not have a consistent recovered label interpretation")
        definitions = {str(k): v[0] for k, v in associations.items()}
    metadata = dict(
        schema_version=VERSION, name=config["name"], provenance=config,
        shapes={s: [counts[s], c, t] for s in counts}, classes=int(all_cases.label_encoded.nunique()),
        declared_source_classes=config["classes"], observed_class_values=sorted(all_cases.label_encoded.unique().tolist()),
        subjects=int(all_cases.subject_id.nunique()), participants=int(all_cases.participant_id.nunique()),
        sessions=int(all_cases.dropna(subset=["session_id"])[["subject_id", "session_id"]].drop_duplicates().shape[0]),
        session_count_note="Only explicit distributed session identifiers counted; zero means not recorded in metadata.",
        recordings=sum(r["partition"] != "excluded" for r in records), source_recordings=len(records),
        excluded_recordings=[dict(recording_id=f"recording_{r['index']}", description=r["group"]["description"], cases=r["shape"][0])
                             for r in records if r["partition"] == "excluded"],
        frequency=records[0]["group"]["info"]["sfreq"],
        original_frequency_from_bids=sorted(all_cases.original_frequency_from_bids.dropna().unique().tolist()),
        original_frequency_publication=config["original_frequency_publication"],
        channel_names=[v["name"] for v in sensors], sensors=sensors,
        sensor_evidence="Serialized MNE Info in each recording_N/zarr.json; array channel axis unchanged; positions remain per recording.",
        standard_montage_added=False, preprocessing=preprocessing,
        overlap=dict(
            coordinate_system="processed recording samples",
            adjacent_overlapping_pairs=sum(int((r["table"]["i_start_in_trial"].astype(int).sort_values().to_numpy()[1:]
                < np.maximum.accumulate(r["table"].sort_values("i_start_in_trial", key=lambda s: s.astype(int))["i_stop_in_trial"].astype(int).to_numpy())[:-1]).sum()) for r in records),
            note="Computed from retained window intervals within each recording; nominal stride parameters are retained separately.",
        ),
        window_seconds=t / records[0]["group"]["info"]["sfreq"],
        label_mapping=definitions,
        label_mapping_evidence=all_cases.label_name_evidence.dropna().unique().tolist(),
        class_distributions={s: tables[s].label_encoded.value_counts().sort_index().to_dict() for s in tables},
        notes=config["notes"] + ["Original acquisition trial IDs/sample indices are unknown unless explicitly present. Processed-recording indices are not relabelled as original indices.",
                                 "No model-specific normalization, montage injection, channel reordering, filtering or resampling is applied by this converter.",
                                 "MNE unit tags may still say volts after the recorded 1e6 scaling; consult raw_preproc_kwargs for numeric signal units."],
    )
    dump(folder / "dataset.json", metadata)
    completeness = {field: dict(available=int(all_cases[field].notna().sum()), total=len(all_cases)) for field in FIELDS}
    completeness["sensors"] = dict(
        channel_names_and_order="verified for every recording",
        channel_kinds="serialized FIFF kind retained for every recording",
        recordings_with_any_position=sum(any(
            any(v is not None and v != 0 for v in ch.get("loc", [])[:3])
            for ch in r["group"]["info"]["chs"]) for r in records),
        total_recordings=len(records),
        synthetic_montage_added=False,
    )
    dump(folder / "metadata-completeness.json", completeness)
    dump(folder / "source-chunks.json", receipts)
    report = validate_arrays(folder, config, records)
    if smoke:
        smoke_classifier(folder)
    (folder / "ATTRIBUTION.txt").write_text(
        f"Contains information from {config['source']} under {config['licence']} ({config['licence_url']}).\n"
        f"{config['reference']} {config['reference_url']}\n"
        f"Processed by Braindecode/OpenEEGBench. Converted to HDF5; validation appended to training; test unchanged.\n"
        "Retain this attribution, original-source notices and source_metadata when redistributing.\n", encoding="utf-8")
    artifacts = {p.relative_to(folder).as_posix(): dict(sha256=sha256(p), bytes=p.stat().st_size) for p in folder.rglob("*") if p.is_file()}
    manifest = dict(
        schema_version=VERSION, dataset=config["hf_id"], revision=config["revision"],
        source_urls=[source.base, config["source"], config["licence_evidence"], CONFIG_URL],
        licence=dict(name=config["licence"], url=config["licence_url"], evidence=config["licence_evidence"], hf_card="unknown"),
        split=dict(key=config["split_key"], values=config["partitions"], excluded_values=config.get("excluded_values", []),
                   order="numeric recording index, then source metadata row order within each original partition; train followed by validation; test unchanged"),
        conversion=dict(version=VERSION, source_revision=OPENEEGBENCH_REVISION,
                        adapter="audited Zarr v3 WindowsDataset float32/bytes/gzip", signal_changes="none",
                        script_sha256=hashlib.sha256(SCRIPT_BYTES).hexdigest(), registry_sha256=hashlib.sha256(REGISTRY_BYTES).hexdigest()),
        environment={p: importlib.metadata.version(p) for p in ("numpy", "pandas", "h5py", "pyarrow")},
        validation=report, artifacts=artifacts,
    )
    dump(folder / "manifest.json", manifest)  # completion marker written last
    return metadata


def load_prepared(folder):
    """Return X_train, y_train, X_test, y_test as aeon-compatible NumPy arrays."""
    with h5py.File(Path(folder) / "arrays.h5", "r") as f:
        return tuple(f[name][:] for name in ("X_train", "y_train", "X_test", "y_test"))


def export_ts(folder, destination):
    """Stream standard equal-length multivariate .ts, preserving float32 values."""
    folder, destination = Path(folder), Path(destination)
    metadata = read_json(folder / "dataset.json")
    if not read_json(folder / "validation.json")["passed"]:
        raise ValueError("Validation failed; refusing .ts export")
    destination.mkdir(parents=True, exist_ok=True)
    with h5py.File(folder / "arrays.h5", "r") as f:
        for split in ("train", "test"):
            target = destination / f"{metadata['name']}_{split.upper()}.ts"
            if target.exists():
                raise FileExistsError(target)
            X, y = f[f"X_{split}"], f[f"y_{split}"][:]
            # Conservative upper bound for 9 significant digits plus delimiters.
            if shutil.disk_usage(destination).free < math.prod(X.shape) * 18:
                raise OSError("Insufficient disk space for uncompressed .ts export; choose another volume")
            with target.open("x", encoding="utf-8", newline="\n") as out:
                class_values = metadata.get("observed_class_values", range(metadata["classes"]))
                out.write(f"# See accompanying dataset.json, case tables and ATTRIBUTION.txt\n@problemName {metadata['name']}\n@timestamps false\n@missing false\n@univariate false\n@dimensions {X.shape[1]}\n@equalLength true\n@seriesLength {X.shape[2]}\n@classLabel true " + " ".join(map(str, class_values)) + "\n@data\n")
                for i in range(len(X)):
                    out.write(":".join(",".join(format(float(v), ".9g") for v in channel) for channel in X[i]) + ":" + str(y[i]) + "\n")
    for name in ("dataset.json", "cases_train.parquet", "cases_test.parquet", "ATTRIBUTION.txt", "metadata-completeness.json", "validation.json"):
        shutil.copy2(folder / name, destination / name)
    shutil.copy2(folder / "manifest.json", destination / "source-manifest.json")
    dump(destination / "ts-manifest.json", {p.name: dict(sha256=sha256(p), bytes=p.stat().st_size) for p in destination.glob("*.ts")})
    dump(destination / "manifest.json", dict(
        format="aeon multivariate .ts", source_manifest="source-manifest.json",
        dataset=metadata["name"], revision=metadata["provenance"]["revision"],
        split=read_json(folder / "manifest.json")["split"],
        conversion=dict(source_dtype="float32", decimal_significant_digits=9, channel_order="unchanged",
                        exporter_sha256=hashlib.sha256(SCRIPT_BYTES).hexdigest()),
        artifacts={p.name: dict(sha256=sha256(p), bytes=p.stat().st_size)
                   for p in destination.iterdir() if p.is_file() and p.name != "manifest.json"},
    ))


def summarize(output):
    rows = []
    for folder in sorted(Path(output).iterdir()):
        if not folder.is_dir() or not (folder / "manifest.json").exists():
            continue
        m = read_json(folder / "dataset.json")
        rows.append(dict(dataset=m["name"], train_cases=m["shapes"]["train"][0],
                         test_cases=m["shapes"]["test"][0], subjects=m["participants"],
                         channels=len(m["channel_names"]), timepoints=m["shapes"]["train"][2],
                         classes=m["classes"], frequency=m["frequency"],
                         size_GB=sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / 1e9,
                         licence=m["provenance"]["licence"]))
    frame = pd.DataFrame(rows)
    frame.to_csv(Path(output) / "summary.csv", index=False)
    print(frame.to_string(index=False), flush=True)
    return frame


def inspect_report(source, attrs, records):
    """Metadata-only assessment, never presented as a converted dataset."""
    definitions = label_definitions(attrs)
    cases = pd.concat([metadata_rows(r, source, definitions) for r in records], ignore_index=True)
    cases.to_parquet(source.cache / "inspected_cases.parquet", index=False)
    report = dict(name=source.config["name"], revision=source.config["revision"],
        recordings=len(records), cases=len(cases), subjects=int(cases.subject_id.nunique()),
        participants=int(cases.participant_id.nunique()),
        partitions={p: int((cases.original_partition == p).sum()) for p in source.config["partitions"]},
        excluded_cases=int((cases.original_partition == "excluded").sum()),
        shape=records[0]["shape"][1:], frequency=records[0]["group"]["info"]["sfreq"],
        original_frequencies_from_bids=sorted(cases.original_frequency_from_bids.dropna().unique().tolist()),
        channel_order_verified_all_recordings=True,
        declared_classes=source.config["classes"], observed_labels=sorted(cases.label_encoded.unique().tolist()),
        class_counts={str(k): int(v) for k, v in cases.label_encoded.value_counts().sort_index().items()},
        class_count_matches_config=cases.label_encoded.nunique() == source.config["classes"],
        signal_validation="not performed by metadata inspection",
        completeness={field: dict(available=int(cases[field].notna().sum()), total=len(cases)) for field in FIELDS},
        licence_status="original licence unresolved; EEG download disabled" if source.config["name"] == "faced" else "upstream data terms verified",
        config=source.config)
    dump(source.cache / "inspection.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "convert", "validate", "export-ts", "summary"))
    active = {k: v for k, v in DATASETS.items() if k not in EXCLUDED_DATASETS}
    parser.add_argument("--dataset", choices=(*active, "all"), default="arithmetic_zyma2019")
    parser.add_argument("--cache", type=Path, default=Path(".openeegbench/source"))
    parser.add_argument("--output", type=Path, default=Path(".openeegbench/archive"))
    parser.add_argument("--ts-output", type=Path)
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted conversion from recording checkpoints using the same converter")
    args = parser.parse_args()
    if args.command == "summary":
        summarize(args.output)
        return
    for name in (active if args.dataset == "all" else [args.dataset]):
        config = DATASETS[name]
        if args.command in ("inspect", "convert"):
            source = Source(config, args.cache).metadata()
            enrich_source(source)
            attrs, records = load_records(source)
            report = inspect_report(source, attrs, records)
            print(json.dumps(report, indent=2), flush=True)
            if args.command == "convert":
                convert(source, args.output, resume=args.resume)
                summarize(args.output)
        elif args.command == "validate":
            validate_arrays(args.output / name, config)
            smoke_classifier(args.output / name)
        elif args.command == "export-ts":
            if args.ts_output is None:
                parser.error("export-ts requires --ts-output")
            export_ts(args.output / name, args.ts_output / name)


if __name__ == "__main__":
    main()
