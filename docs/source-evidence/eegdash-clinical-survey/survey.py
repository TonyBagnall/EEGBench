"""Survey clinical EEG datasets in EEGDash: groups per subject, tasks, shape."""
import collections, json, re, sys, time
from pathlib import Path
import requests

out = Path(sys.argv[1])
API = "https://data.eegdash.org/api/eegdash"
docs = json.load(open(out / "all_datasets.json", encoding="utf-8"))["data"]
SKIP = {"Healthy", "Unknown"}
GROUPISH = re.compile(r"group|diagnos|dx|type|status|condition|patient|control|"
                      r"label|class|cohort|disease|clinical|population|subgroup|"
                      r"category|arm|phenotype|pathology", re.I)
NOT_GROUP = re.compile(r"^(participant_id|age|sex|gender|hand|handedness|weight|"
                       r"height|session|ses|run|date|time|bmi|years?)$", re.I)

def pick(doc):
    mods = set(doc.get("recording_modality") or doc.get("datatypes") or [])
    path = set((doc.get("tags") or {}).get("pathology") or [])
    return "eeg" in mods and bool(path - SKIP) and path != {"NONE"}

cands = [d for d in docs if pick(d)]
# drop OpenNeuro ids that have a NEMAR twin in the list (same dataset twice)
ids = {d["dataset_id"] for d in cands}
cands = [d for d in cands if not (d["dataset_id"].startswith("ds")
                                  and "on" + d["dataset_id"][2:] in ids)]
print(len(cands), "candidates", flush=True)

sess = requests.Session()
def records(ds):
    allr, skip = [], 0
    while True:
        r = sess.get(f"{API}/records", params={"filter": json.dumps({"dataset": ds}),
                     "limit": 1000, "skip": skip}, timeout=120)
        r.raise_for_status()
        page = r.json().get("data", [])
        allr += page
        if len(page) < 1000:
            return allr
        skip += 1000

rows = []
for i, d in enumerate(cands):
    ds = d["dataset_id"]
    try:
        recs = records(ds)
    except Exception as e:  # keep going; note the failure
        print(ds, "FAILED", e, flush=True)
        recs = []
    subj = {}
    tasks = collections.Counter()
    nch, sf, dur = collections.Counter(), collections.Counter(), []
    for r in recs:
        if r.get("datatype") not in (None, "eeg"):
            continue
        s = r.get("subject")
        subj.setdefault(s, r.get("participant_tsv") or {})
        tasks[r.get("task")] += 1
        nch[r.get("nchans")] += 1
        sf[r.get("sampling_frequency")] += 1
        if r.get("duration_seconds"):
            dur.append(r["duration_seconds"])
    # candidate group columns: categorical, 2..8 levels, name looks group-like
    cols = collections.defaultdict(collections.Counter)
    for p in subj.values():
        for k, v in p.items():
            if v is None or NOT_GROUP.match(k):
                continue
            cols[k][str(v)] += 1
    groups = {k: dict(c) for k, c in cols.items()
              if 2 <= len(c) <= 8 and (GROUPISH.search(k) or len(c) <= 4)}
    # subject-id prefixes (e.g. HS01 / MDD01) as a fallback group signal
    pref = collections.Counter(re.match(r"[A-Za-z]*", str(s)).group(0) or "<num>"
                               for s in subj)
    tg = d.get("tags") or {}
    rows.append({
        "dataset": ds, "name": d.get("name") or d.get("computed_title"),
        "pathology": tg.get("pathology"), "type": tg.get("type"),
        "modality": tg.get("modality"), "n_subjects": len(subj),
        "n_records": len(recs), "tasks": dict(tasks.most_common(8)),
        "nchans": dict(nch.most_common(3)), "sfreq": dict(sf.most_common(3)),
        "median_dur_s": sorted(dur)[len(dur) // 2] if dur else None,
        "group_columns": groups, "subject_prefixes": dict(pref.most_common(6)),
        "paper_doi": d.get("associated_paper_doi"),
        "dataset_doi": d.get("dataset_doi"),
        "source_doi": [s.get("DOI") for s in d.get("source_datasets") or []],
        "how_to_acknowledge": (d.get("how_to_acknowledge") or "")[:400],
        "references": (d.get("references_and_links") or [])[:3],
        "license": d.get("license"),
        "readme": (d.get("readme") or "")[:1500],
    })
    print(i, ds, len(subj), "subj", list(groups)[:4], flush=True)
    time.sleep(0.2)

json.dump(rows, open(out / "survey.json", "w", encoding="utf-8"), indent=1,
          ensure_ascii=False)
