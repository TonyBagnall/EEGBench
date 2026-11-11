"""Export test-set acc, balacc, logloss and AUROC as dataset x classifier CSVs."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

root = Path("D:/Results/EEG")
out = Path(sys.argv[1])
probs = list(pd.read_csv(root / "paper_tables/problem_families.csv").dataset)
skip_est = {"STC", "FreshPRINCE", "MiniROCKET", "ROCKET"}
keep_hybrid = {"HC2-500-pc", "HC2-noTDE-500-pc"}

def read(f):
    L = f.read_text().splitlines()
    m = re.search(r"Encoder dictionary: \{(.*?)\}", L[0])
    rows = [l.split(",") for l in L[3:] if l.strip()]
    y = np.array([r[0] for r in rows]); p = np.array([r[1] for r in rows])
    acc = np.mean(y == p)
    bal = np.mean([np.mean(p[y == c] == c) for c in np.unique(y)])
    ll = auc = np.nan
    try:
        P = np.array([[float(x) for x in r[3:] if x != ""] for r in rows])
        enc = {k: int(v) for k, v in re.findall(r"(?:np\.str_\()?'([^']*)'\)?:\s*(\d+)", m.group(1))} if m else {}
        if not all(t in enc for t in y):
            enc = {l: i for i, l in enumerate(sorted(set(y) | set(p)))}
        idx = np.array([enc[t] for t in y])
        ll = -np.mean(np.log(np.clip(P[np.arange(len(idx)), idx], 1e-15, 1)))
        present = np.unique(idx)
        if len(present) == 2 and P.shape[1] == 2:
            auc = roc_auc_score(idx == present[1], P[:, present[1]])
        elif len(present) > 2:
            Q = P[:, present]; Q = Q / np.clip(Q.sum(1, keepdims=True), 1e-15, None)
            auc = roc_auc_score(idx, Q, multi_class="ovr", average="macro", labels=present)
    except Exception:
        pass
    return acc, bal, ll, auc

recs = []
for f in root.glob("*/*/Predictions/*/testResample0.csv"):
    cat, est, _, ds = f.parts[-5:-1]
    if cat.startswith("_") or cat == "NBack" or ds not in probs or est in skip_est: continue
    if cat == "Hybrid" and est not in keep_hybrid: continue
    try: recs.append((cat, est, ds, *read(f)))
    except Exception as e: print("bad", f, e)
df = pd.DataFrame(recs, columns=["family", "classifier", "dataset", "accuracy", "balacc", "logloss", "auroc"])
assert not df.duplicated(["classifier", "dataset"]).any()
out.mkdir(parents=True, exist_ok=True)
for met in ["accuracy", "balacc", "logloss", "auroc"]:
    w = df.pivot(index="dataset", columns="classifier", values=met).reindex(probs)
    w = w[sorted(w.columns, key=str.lower)]
    w.to_csv(out / f"{met}.csv", float_format="%.6f")
df[["classifier", "family"]].drop_duplicates().sort_values("classifier", key=lambda s: s.str.lower()).to_csv(out / "classifiers.csv", index=False)
pd.read_csv(root / "paper_tables/problem_families.csv").to_csv(out / "datasets.csv", index=False)
print(len(df), "results,", df.classifier.nunique(), "classifiers,", len(probs), "datasets")
print("missing logloss", df.logloss.isna().sum(), "missing auroc", df.auroc.isna().sum())
print(df[df.auroc.isna()].groupby("classifier").size().to_string())
