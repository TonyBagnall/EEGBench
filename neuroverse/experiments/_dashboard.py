"""Interactive HTML dashboard and Markdown summary builders for Neuroverse.

Generates three self-contained pages sharing a common navigation bar and
visual design inspired by modern ML benchmark suites (such as ``eeg.fm``):

- ``leaderboard.html`` (and ``index.html``): algorithm leaderboard across all
  77 scalp EEG problems and split by problem type (BCI, Motor Imagery, Motor
  Execution, ERP, VEP, Speech, Clinical, Cognitive), ranking the 72 distinct
  canonical classifiers by default with an option to include all 90
  configurations.
- ``matrix.html``: interactive 77-problem by 72-classifier (or 90-configuration)
  heatmap score matrix grouped by problem type and algorithm paradigm, with
  metric switching, row-normalised or baseline-gain shading, and per-cell
  multi-metric tooltips.
- ``datasets.html``: interactive problem explorer showing test-majority floor,
  median, ceiling, winning algorithm, gain over baseline, and completion count.
"""

from __future__ import annotations

import json
import math
from datetime import date
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

from neuroverse.datasets import (
    PROBLEM_TYPE_TABS,
    STUDY_TAXONOMY,
    by_type,
    metadata as dataset_metadata,
    neuroverse_study,
)
from neuroverse.estimators import PARADIGMS, TSML_FAMILIES, estimator_info

PRIMARY_METRICS = ("balacc", "accuracy", "auroc", "logloss")
LOWER_IS_BETTER = frozenset({"logloss"})

PARADIGM_ORDER = ("TSML", "EEG-Classical", "EEG-DL", "EEG-FM", "Tabular")


def compute_league_table(
    datasets: list[str],
    frames: dict[str, pd.DataFrame],
    primary_metric: str = "balacc",
    min_coverage_ratio: float = 0.8,
    mode: str = "common_block",
    exclude: tuple[str, ...] = ("Default",),
    canonical_only: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    """Compute an algorithm league table on ``datasets``.

    Parameters
    ----------
    datasets : list of str
        Selected problem names defining the scope of the table.
    frames : dict of str -> pd.DataFrame
        Metric matrices indexed by dataset with one column per estimator.
    primary_metric : str, default="balacc"
        Metric used for coverage admission, mean rank, wins, and top-5 counts.
    min_coverage_ratio : float, default=0.8
        Minimum fraction of ``datasets`` an estimator must cover in
        ``"common_block"`` mode (e.g. ``0.8`` requires ``ceil(0.8 * N)``).
    mode : {"common_block", "available"}, default="common_block"
        - ``"common_block"``: admit estimators meeting ``min_coverage_ratio``
          and evaluate every admitted estimator strictly on their shared
          completed intersection so ranks and means are paired.
        - ``"available"``: include every estimator with at least one result on
          ``datasets``, ranking within each problem across available estimators
          and normalising ranks to ``[1, M]``.
    exclude : tuple of str, default=("Default",)
        Estimator columns to exclude from the competitive league.
    canonical_only : bool, default=False
        When True, restrict the league to the 72 canonical distinct classifiers
        (excluding non-canonical preprocessing, tree-count, and random-weight
        ablation variants).

    Returns
    -------
    table : pd.DataFrame
        Ranked summary table with columns ``position``, ``estimator``,
        ``paradigm``, ``paradigm_label``, ``tsml_family``, ``base_method``,
        ``is_ablation``, ``is_canonical``, ``coverage``, ``scope_problems``,
        ``common_problems``, ``mean_rank``, ``wins``, ``top5``, and one column
        per available metric.
    common : list of str
        Problems in the shared evaluation block (all scoped problems with at
        least one score when ``mode="available"``).
    """
    if primary_metric not in frames:
        raise ValueError(f"primary_metric={primary_metric!r} not in frames")

    excluded = set(exclude)
    primary = frames[primary_metric].reindex(datasets)
    keep_cols = [
        c
        for c in primary.columns
        if c not in excluded and (not canonical_only or bool(estimator_info(c)["is_canonical"]))
    ]
    primary = primary[keep_cols]

    n_scope = len(datasets)
    if n_scope == 0 or primary.empty:
        return pd.DataFrame(), []

    coverage = primary.notna().sum(axis=0)
    lower_better = primary_metric in LOWER_IS_BETTER

    if mode == "common_block":
        min_cov = math.ceil(min_coverage_ratio * n_scope) if min_coverage_ratio > 0 else 1
        panel = [c for c in keep_cols if int(coverage[c]) >= min_cov]
        if not panel:
            return pd.DataFrame(), []
        common = primary[panel].dropna().index.tolist()
        if not common:
            return pd.DataFrame(), []
        block = primary.loc[common, panel]
        ranks = block.rank(axis=1, ascending=lower_better, method="average")
        row_best = block.min(axis=1) if lower_better else block.max(axis=1)
        wins = pd.Series(
            np.isclose(block.to_numpy(), row_best.to_numpy()[:, None], rtol=0.0, atol=1e-12).sum(axis=0),
            index=panel,
        )
        top5 = (ranks <= 5.0).sum(axis=0)
        mean_rank = ranks.mean(axis=0)
        metric_means = {
            m: frames[m].reindex(index=common, columns=panel).mean(axis=0)
            for m in frames
        }
        n_common = len(common)
    elif mode == "available":
        panel = [c for c in keep_cols if int(coverage[c]) >= 1]
        if not panel:
            return pd.DataFrame(), []
        sub = primary[panel]
        active_rows = sub.notna().any(axis=1)
        common = sub.index[active_rows].tolist()
        if not common:
            return pd.DataFrame(), []
        sub = sub.loc[common]
        raw_ranks = sub.rank(axis=1, ascending=lower_better, method="average")
        row_counts = sub.notna().sum(axis=1)
        m_panel = len(panel)
        norm_ranks = raw_ranks.copy()
        for ds in common:
            cnt = int(row_counts[ds])
            if cnt > 1 and m_panel > 1:
                norm_ranks.loc[ds] = 1.0 + (raw_ranks.loc[ds] - 1.0) * (m_panel - 1.0) / (cnt - 1.0)
            else:
                norm_ranks.loc[ds] = 1.0
        row_best = sub.min(axis=1) if lower_better else sub.max(axis=1)
        is_best = np.isclose(sub.to_numpy(), row_best.to_numpy()[:, None], rtol=0.0, atol=1e-12) & sub.notna().to_numpy()
        wins = pd.Series(is_best.sum(axis=0), index=panel)
        top5 = (raw_ranks <= 5.0).sum(axis=0)
        mean_rank = norm_ranks.mean(axis=0)
        metric_means = {
            m: frames[m].reindex(index=common, columns=panel).mean(axis=0)
            for m in frames
        }
        n_common = len(common)
    else:
        raise ValueError(f"mode must be 'common_block' or 'available', not {mode!r}")

    rows = []
    for est in panel:
        info = estimator_info(est)
        rec: dict[str, object] = {
            "estimator": est,
            "paradigm": info["paradigm"],
            "paradigm_label": info["paradigm_label"],
            "tsml_family": info["tsml_family"],
            "base_method": info["base_method"],
            "library": info["library"],
            "is_ablation": bool(info["is_ablation"]),
            "is_canonical": bool(info["is_canonical"]),
            "description": info["description"],
            "coverage": int(coverage[est]),
            "scope_problems": n_scope,
            "common_problems": n_common,
            "mean_rank": float(mean_rank[est]),
            "wins": int(wins[est]),
            "top5": int(top5[est]),
        }
        for m, series in metric_means.items():
            val = series[est]
            rec[m] = float(val) if pd.notna(val) else float("nan")
        rows.append(rec)

    result = pd.DataFrame(rows)
    tie_asc = primary_metric in LOWER_IS_BETTER
    result = result.sort_values(
        ["mean_rank", primary_metric], ascending=[True, tie_asc]
    ).reset_index(drop=True)
    result.insert(0, "position", np.arange(1, len(result) + 1))
    return result, common


def study_leaderboard_markdown(
    frames: dict[str, pd.DataFrame],
    top_n: int = 15,
    min_coverage_ratio: float = 0.8,
    canonical_only: bool = True,
) -> str:
    """Build the concise Overall + By-Problem-Type Markdown summary for README.md."""
    n_study = len(neuroverse_study)
    overall, common_all = compute_league_table(
        neuroverse_study,
        frames,
        primary_metric="balacc",
        min_coverage_ratio=min_coverage_ratio,
        canonical_only=canonical_only,
    )
    if overall.empty:
        return "No common-block results available."

    # Include top_n plus the top representative of any paradigm outside top_n
    top_slice = overall.head(top_n)
    represented = set(top_slice["paradigm"])
    extras = []
    for par in PARADIGM_ORDER:
        if par not in represented:
            cand = overall[(overall["paradigm"] == par) & (~overall["is_ablation"])]
            if cand.empty:
                cand = overall[overall["paradigm"] == par]
            if not cand.empty:
                extras.append(cand.iloc[0])
    shown = pd.concat([top_slice, pd.DataFrame(extras)], ignore_index=True) if extras else top_slice

    lines = [
        f"#### Overall Performance Leaderboard ({n_study} Scalp EEG Problems)",
        "",
        "| # | Algorithm | Paradigm | Cov. | Mean Rank | Balanced Acc | Accuracy | AUROC | Log Loss &darr; | Wins |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    best_vals = {
        "mean_rank": overall["mean_rank"].min(),
        "balacc": overall["balacc"].max(),
        "accuracy": overall["accuracy"].max(),
        "auroc": overall["auroc"].max(),
        "logloss": overall["logloss"].min(),
    }

    def fmt_pct(val: float, best: float) -> str:
        if pd.isna(val):
            return "&mdash;"
        txt = f"{100.0 * val:.2f}%"
        return f"**{txt}**" if np.isclose(val, best, atol=1e-6) else txt

    for idx, row in shown.iterrows():
        if idx == top_n and extras:
            lines.append("| &vellip; | *Best remaining paradigm representatives* | | | | | | | | |")
        rk = f"{row['mean_rank']:.2f}"
        if np.isclose(row["mean_rank"], best_vals["mean_rank"], atol=1e-6):
            rk = f"**{rk}**"
        auroc_txt = "&mdash;" if pd.isna(row.get("auroc")) else (
            f"**{row['auroc']:.4f}**"
            if np.isclose(row["auroc"], best_vals["auroc"], atol=1e-6)
            else f"{row['auroc']:.4f}"
        )
        ll_txt = "&mdash;" if pd.isna(row.get("logloss")) else (
            f"**{row['logloss']:.3f}**"
            if np.isclose(row["logloss"], best_vals["logloss"], atol=1e-6)
            else f"{row['logloss']:.3f}"
        )
        lines.append(
            f"| {int(row['position'])} | `{row['estimator']}` | {row['paradigm_label']} "
            f"| {int(row['coverage'])}/{int(row['scope_problems'])} | {rk} "
            f"| {fmt_pct(row['balacc'], best_vals['balacc'])} "
            f"| {fmt_pct(row['accuracy'], best_vals['accuracy'])} "
            f"| {auroc_txt} | {ll_txt} | {int(row['wins'])} |"
        )

    total_pool = sum(
        1
        for c in frames["balacc"].columns
        if c != "Default" and (not canonical_only or bool(estimator_info(c)["is_canonical"]))
    )
    pool_noun = "distinct classifiers" if canonical_only else "configurations"
    min_cov_all = math.ceil(min_coverage_ratio * n_study)
    lines.extend(
        [
            "",
            f"*{len(overall)} of {total_pool} {pool_noun} meet &ge;80% coverage ({min_cov_all}/{n_study} problems), "
            f"evaluated on their {len(common_all)} shared completed problems (resample 0, ordered by "
            "mean balanced-accuracy rank).*",
            "",
            "#### Leaderboard by Problem Type",
            "",
            "| Problem Type | Problems (Common) | #1 Overall | #2 Overall | #3 Overall | Best EEG-Specific Classifier |",
            "|---|---:|---|---|---|---|",
        ]
    )

    for tab_key, tab_label in PROBLEM_TYPE_TABS.items():
        probs = by_type(tab_key)
        tbl, com = compute_league_table(
            probs,
            frames,
            primary_metric="balacc",
            min_coverage_ratio=min_coverage_ratio,
            canonical_only=canonical_only,
        )
        if tbl.empty:
            continue
        medals = []
        for pos in range(min(3, len(tbl))):
            r = tbl.iloc[pos]
            medals.append(f"`{r['estimator']}` ({100.0 * r['balacc']:.1f}%)")
        while len(medals) < 3:
            medals.append("&mdash;")
        eeg_only = tbl[tbl["paradigm"].isin(["EEG-Classical", "EEG-DL", "EEG-FM"])]
        best_eeg = (
            f"`{eeg_only.iloc[0]['estimator']}` (#{int(eeg_only.iloc[0]['position'])}, "
            f"{100.0 * eeg_only.iloc[0]['balacc']:.1f}%)"
            if not eeg_only.empty
            else "&mdash;"
        )
        lines.append(
            f"| **{tab_label}** | {len(probs)} ({len(com)}) | {medals[0]} "
            f"| {medals[1]} | {medals[2]} | {best_eeg} |"
        )

    return "\n".join(lines)


def full_domain_tables_markdown(
    frames: dict[str, pd.DataFrame],
    top_n: int = 15,
    min_coverage_ratio: float = 0.8,
    canonical_only: bool = True,
) -> str:
    """Build per-domain Top-N Markdown tables for ``docs/leaderboard.md``."""
    blocks: list[str] = []
    for tab_key, tab_label in PROBLEM_TYPE_TABS.items():
        probs = by_type(tab_key)
        tbl, com = compute_league_table(
            probs,
            frames,
            primary_metric="balacc",
            min_coverage_ratio=min_coverage_ratio,
            canonical_only=canonical_only,
        )
        if tbl.empty:
            continue
        min_cov = math.ceil(min_coverage_ratio * len(probs))
        blocks.extend(
            [
                f"### {tab_label} ({len(probs)} problems; {len(com)} common; {len(tbl)} classifiers &ge;{min_cov}/{len(probs)})",
                "",
                "| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |",
                "|---:|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in tbl.head(top_n).itertuples():
            blocks.append(
                f"| {row.position} | `{row.estimator}` | {row.paradigm_label} "
                f"| {row.coverage}/{row.scope_problems} | {row.mean_rank:.2f} "
                f"| {100.0 * row.balacc:.2f}% | {100.0 * row.accuracy:.2f}% "
                f"| {row.wins} | {row.top5} |"
            )
        blocks.append("")
    return "\n".join(blocks).rstrip()


def _build_payload(
    frames: dict[str, pd.DataFrame],
    cd_png_fn=None,
    cd_top_k: int = 10,
) -> dict[str, object]:
    """Assemble compact JSON payload shared by the interactive HTML pages."""
    meta_df = dataset_metadata().reindex(neuroverse_study)
    estimators = [c for c in frames["balacc"].columns if c != "Default"]

    datasets_info = []
    for ds in neuroverse_study:
        fam, bci = STUDY_TAXONOMY[ds]
        row = meta_df.loc[ds]
        datasets_info.append(
            {
                "name": ds,
                "family": fam,
                "bci_type": bci,
                "type": bci if bci else fam,
                "channels": int(row["channels"]),
                "length": int(row["length"]),
                "classes": int(row["classes"]),
                "subjects": None if pd.isna(row["subjects"]) else int(row["subjects"]),
                "train_size": int(row["train_size"]),
                "test_size": int(row["test_size"]),
                "hz": None if pd.isna(row["frequency"]) else float(row["frequency"]),
                "availability": str(row["availability"]),
                "in_paper": bool(row["published_benchmark"]),
            }
        )

    estimators_info = []
    for est in estimators:
        info = estimator_info(est)
        estimators_info.append(
            {
                "name": est,
                "paradigm": info["paradigm"],
                "paradigm_label": info["paradigm_label"],
                "tsml_family": info["tsml_family"],
                "base_method": info["base_method"],
                "library": info["library"],
                "is_ablation": bool(info["is_ablation"]),
                "is_canonical": bool(info["is_canonical"]),
                "description": info["description"],
            }
        )

    def serialise_matrix(metric: str, decimals: int = 5) -> list[list[float | None]]:
        if metric not in frames:
            return [[None] * len(estimators) for _ in neuroverse_study]
        mat = frames[metric].reindex(index=neuroverse_study, columns=estimators).to_numpy(dtype=float)
        out: list[list[float | None]] = []
        for r in range(mat.shape[0]):
            out.append(
                [
                    None if not np.isfinite(mat[r, c]) else round(float(mat[r, c]), decimals)
                    for c in range(mat.shape[1])
                ]
            )
        return out

    default_floor: dict[str, list[float | None]] = {}
    for m in PRIMARY_METRICS:
        if m in frames and "Default" in frames[m].columns:
            ser = frames[m].reindex(neuroverse_study)["Default"].to_numpy(dtype=float)
            default_floor[m] = [
                None if not np.isfinite(v) else round(float(v), 5) for v in ser
            ]
        else:
            default_floor[m] = [None] * len(neuroverse_study)

    tabs_meta = []
    cd_images: dict[str, dict[str, object]] = {}
    for tab_key, tab_label in PROBLEM_TYPE_TABS.items():
        probs = by_type(tab_key)
        tabs_meta.append({"key": tab_key, "label": tab_label, "datasets": probs})
        if cd_png_fn is not None:
            tbl, com = compute_league_table(
                probs,
                frames,
                primary_metric="balacc",
                min_coverage_ratio=0.8,
                canonical_only=True,
            )
            if not tbl.empty and len(com) >= 2:
                top_ests = list(tbl["estimator"].head(cd_top_k))
                cd_scores = frames["balacc"].loc[com, top_ests]
                png = cd_png_fn(cd_scores, False, 0.05)
                if png:
                    cd_images[tab_key] = {
                        "png": png,
                        "n_estimators": len(top_ests),
                        "n_common": len(com),
                        "alpha": 0.05,
                    }

    return {
        "built": date.today().isoformat(),
        "datasets": datasets_info,
        "estimators": estimators_info,
        "paradigms": PARADIGMS,
        "tsml_families": TSML_FAMILIES,
        "tabs": tabs_meta,
        "scores": {
            "balacc": serialise_matrix("balacc", 5),
            "accuracy": serialise_matrix("accuracy", 5),
            "auroc": serialise_matrix("auroc", 5),
            "logloss": serialise_matrix("logloss", 4),
        },
        "default_floor": default_floor,
        "cd_diagrams": cd_images,
    }


_SHARED_CSS = """
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --fg: #0f172a;
  --fg-secondary: #334155;
  --muted: #64748b;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --accent: #2563eb;
  --accent-soft: rgba(37, 99, 235, 0.10);
  --best-bg: rgba(16, 185, 129, 0.14);
  --best-fg: #065f46;
  --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);

  --p-tsml-bg: #dbeafe; --p-tsml-fg: #1e40af; --p-tsml-bd: #93c5fd;
  --p-class-bg: #dcfce7; --p-class-fg: #166534; --p-class-bd: #86efac;
  --p-dl-bg: #f3e8ff; --p-dl-fg: #6b21a8; --p-dl-bd: #d8b4fe;
  --p-fm-bg: #ffedd5; --p-fm-fg: #9a3412; --p-fm-bd: #fdba74;
  --p-tab-bg: #f1f5f9; --p-tab-fg: #475569; --p-tab-bd: #cbd5e1;
}
html[data-theme="dark"] {
  --bg: #0b1120;
  --surface: #111827;
  --surface-alt: #1e293b;
  --fg: #f1f5f9;
  --fg-secondary: #cbd5e1;
  --muted: #94a3b8;
  --border: #1f2937;
  --border-strong: #334155;
  --accent: #60a5fa;
  --accent-soft: rgba(96, 165, 250, 0.16);
  --best-bg: rgba(16, 185, 129, 0.22);
  --best-fg: #6ee7b7;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.35);

  --p-tsml-bg: rgba(59, 130, 246, 0.20); --p-tsml-fg: #93c5fd; --p-tsml-bd: rgba(96, 165, 250, 0.4);
  --p-class-bg: rgba(34, 197, 94, 0.18); --p-class-fg: #86efac; --p-class-bd: rgba(74, 222, 128, 0.4);
  --p-dl-bg: rgba(168, 85, 247, 0.20); --p-dl-fg: #d8b4fe; --p-dl-bd: rgba(192, 132, 252, 0.4);
  --p-fm-bg: rgba(249, 115, 22, 0.22); --p-fm-fg: #fdba74; --p-fm-bd: rgba(251, 146, 60, 0.45);
  --p-tab-bg: rgba(148, 163, 184, 0.16); --p-tab-fg: #cbd5e1; --p-tab-bd: rgba(148, 163, 184, 0.35);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 40;
}
.topbar-inner {
  max-width: 1480px;
  margin: 0 auto;
  padding: 0.7rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 700;
  font-size: 1.08rem;
  color: var(--fg);
  text-decoration: none;
}
.brand:hover { text-decoration: none; }
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-weight: 800;
  font-size: 0.85rem;
  letter-spacing: -0.03em;
}
.brand-tag {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  background: var(--surface-alt);
  color: var(--muted);
  border: 1px solid var(--border);
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.nav-link {
  padding: 0.42rem 0.8rem;
  border-radius: 7px;
  font-weight: 600;
  font-size: 0.88rem;
  color: var(--fg-secondary);
  transition: background 0.15s, color 0.15s;
}
.nav-link:hover {
  background: var(--surface-alt);
  color: var(--fg);
  text-decoration: none;
}
.nav-link.active {
  background: var(--accent-soft);
  color: var(--accent);
}
.theme-btn {
  border: 1px solid var(--border);
  background: var(--surface-alt);
  color: var(--fg-secondary);
  border-radius: 7px;
  padding: 0.38rem 0.68rem;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}
.theme-btn:hover { border-color: var(--border-strong); color: var(--fg); }

.container {
  max-width: 1480px;
  margin: 0 auto;
  padding: 1.5rem 1.5rem 4rem;
}
.hero {
  margin-bottom: 1.25rem;
}
.hero h1 {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0 0 0.3rem;
}
.hero p {
  margin: 0;
  color: var(--muted);
  max-width: 920px;
  font-size: 0.94rem;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 0.85rem;
  margin: 1.15rem 0 1.35rem;
}
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1.05rem;
  box-shadow: var(--shadow);
}
.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin-bottom: 0.3rem;
}
.kpi-value {
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--fg);
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}
.kpi-sub {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 0.22rem;
}

.tab-strip {
  display: flex;
  gap: 0.35rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.tab-btn {
  border: none;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-weight: 600;
  font-size: 0.88rem;
  padding: 0.55rem 0.85rem;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.tab-btn:hover { color: var(--fg); }
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.tab-count {
  font-size: 0.74rem;
  padding: 0.06rem 0.42rem;
  border-radius: 999px;
  background: var(--surface-alt);
  color: var(--muted);
}
.tab-btn.active .tab-count {
  background: var(--accent-soft);
  color: var(--accent);
}

.toolbar {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.1rem;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow);
}
.pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}
.pill-btn {
  border: 1px solid var(--border);
  background: var(--surface-alt);
  color: var(--fg-secondary);
  border-radius: 999px;
  padding: 0.28rem 0.72rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.12s;
}
.pill-btn:hover { border-color: var(--border-strong); color: var(--fg); }
.pill-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}
.control-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
}
select.ctrl, input.ctrl {
  background: var(--surface-alt);
  color: var(--fg);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 0.36rem 0.65rem;
  font: inherit;
  font-size: 0.83rem;
}
select.ctrl:focus, input.ctrl:focus {
  outline: 2px solid var(--accent);
  outline-offset: -1px;
}
label.chk {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: var(--fg-secondary);
  cursor: pointer;
  user-select: none;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.48rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  border: 1px solid transparent;
  white-space: nowrap;
}
.badge-TSML { background: var(--p-tsml-bg); color: var(--p-tsml-fg); border-color: var(--p-tsml-bd); }
.badge-EEG-Classical { background: var(--p-class-bg); color: var(--p-class-fg); border-color: var(--p-class-bd); }
.badge-EEG-DL { background: var(--p-dl-bg); color: var(--p-dl-fg); border-color: var(--p-dl-bd); }
.badge-EEG-FM { background: var(--p-fm-bg); color: var(--p-fm-fg); border-color: var(--p-fm-bd); }
.badge-Tabular { background: var(--p-tab-bg); color: var(--p-tab-fg); border-color: var(--p-tab-bd); }

.rank-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.55rem;
  padding: 0 0.35rem;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.8rem;
}
.rank-1 { background: #fef3c7; color: #92400e; border: 1px solid #f59e0b; }
.rank-2 { background: #e2e8f0; color: #334155; border: 1px solid #94a3b8; }
.rank-3 { background: #ffedd5; color: #9a3412; border: 1px solid #fb923c; }
html[data-theme="dark"] .rank-1 { background: rgba(245, 158, 11, 0.24); color: #fcd34d; border-color: rgba(245, 158, 11, 0.55); }
html[data-theme="dark"] .rank-2 { background: rgba(148, 163, 184, 0.24); color: #e2e8f0; border-color: rgba(148, 163, 184, 0.5); }
html[data-theme="dark"] .rank-3 { background: rgba(251, 146, 60, 0.24); color: #fdba74; border-color: rgba(251, 146, 60, 0.5); }

.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
  max-height: 76vh;
}
table.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-variant-numeric: tabular-nums;
}
table.data-table th, table.data-table td {
  padding: 0.52rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: right;
  white-space: nowrap;
}
table.data-table thead th {
  background: var(--surface-alt);
  color: var(--fg-secondary);
  font-weight: 700;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  position: sticky;
  top: 0;
  z-index: 10;
  user-select: none;
}
table.data-table thead th.sortable { cursor: pointer; }
table.data-table thead th.sortable:hover { color: var(--accent); }
table.data-table th.col-pos, table.data-table td.col-pos {
  text-align: center;
  width: 3.1rem;
  position: sticky;
  left: 0;
  z-index: 11;
  background: var(--surface);
}
table.data-table thead th.col-pos { background: var(--surface-alt); z-index: 15; }
table.data-table th.col-name, table.data-table td.col-name {
  text-align: left;
  position: sticky;
  left: 3.1rem;
  z-index: 11;
  background: var(--surface);
  box-shadow: 2px 0 5px -2px rgba(15, 23, 42, 0.12);
}
table.data-table thead th.col-name { background: var(--surface-alt); z-index: 15; }
table.data-table tbody tr:hover td { background: var(--surface-alt); }
table.data-table td.best-cell {
  background: var(--best-bg) !important;
  color: var(--best-fg);
  font-weight: 700;
}
.alg-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.alg-main {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.alg-name { font-weight: 700; color: var(--fg); font-size: 0.9rem; }
.alg-sub { font-size: 0.74rem; color: var(--muted); }
.cov-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.cov-bar {
  width: 44px;
  height: 6px;
  border-radius: 999px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  overflow: hidden;
}
.cov-fill {
  height: 100%;
  background: var(--accent);
}
.section-card {
  margin-top: 1.35rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.1rem 1.25rem;
  box-shadow: var(--shadow);
}
.section-card h2 {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
}
.note {
  color: var(--muted);
  font-size: 0.84rem;
  margin: 0.5rem 0 0;
}
.banner-warn {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: var(--fg);
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  margin-bottom: 0.9rem;
  font-size: 0.84rem;
  display: none;
}
.cd-img {
  max-width: 100%;
  height: auto;
  background: #ffffff;
  border-radius: 8px;
  padding: 0.5rem;
  border: 1px solid var(--border);
}
.action-btn {
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--fg);
  border-radius: 7px;
  padding: 0.36rem 0.72rem;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
tr.clickable-row { cursor: pointer; }
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  z-index: 80;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
}
.modal-backdrop.open { display: flex; }
.modal-card {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  max-width: 880px;
  width: 100%;
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
}
.modal-head {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.modal-body {
  padding: 1rem 1.25rem 1.25rem;
  overflow-y: auto;
}
.modal-close {
  border: 1px solid var(--border);
  background: var(--surface-alt);
  color: var(--fg);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-weight: 700;
  cursor: pointer;
}
.dom-bar-grid {
  display: grid;
  grid-template-columns: 135px 1fr 125px;
  gap: 0.45rem 0.75rem;
  align-items: center;
  margin: 0.65rem 0 1rem;
}
.dom-track {
  height: 10px;
  border-radius: 999px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  overflow: hidden;
}
.dom-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #10b981);
}
"""


def _topbar_html(active_page: str) -> str:
    links = [
        ("leaderboard", "leaderboard.html", "Algorithm Leaderboard"),
        ("matrix", "matrix.html", "Overall Score Matrix"),
        ("datasets", "datasets.html", "Problem Explorer"),
        ("paper", "../neuroverse_paper_2026/leaderboard.html", "2026 Paper Archive (30)"),
    ]
    nav = "".join(
        f'<a class="nav-link{" active" if key == active_page else ""}" href="{href}">{escape(label)}</a>'
        for key, href, label in links
    )
    return (
        '<header class="topbar"><div class="topbar-inner">'
        '<div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap">'
        '<a class="brand" href="leaderboard.html">'
        '<span class="brand-mark">NV</span>'
        '<span>Neuroverse</span>'
        '</a>'
        f'<span class="brand-tag">{len(neuroverse_study)} Scalp EEG Problems &middot; 72 Classifiers</span>'
        "</div>"
        f'<nav class="nav-links">{nav}'
        '<button type="button" class="theme-btn" id="themeToggle" title="Switch colour theme">Theme</button>'
        "</nav></div></header>"
    )


_THEME_JS = r"""
(function(){
  var root = document.documentElement;
  var saved = localStorage.getItem("neuroverse-theme");
  if (saved === "dark" || saved === "light") {
    root.setAttribute("data-theme", saved);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    root.setAttribute("data-theme", "dark");
  }
  var btn = document.getElementById("themeToggle");
  function syncBtn() {
    if (!btn) return;
    btn.textContent = root.getAttribute("data-theme") === "dark" ? "Light mode" : "Dark mode";
  }
  syncBtn();
  if (btn) {
    btn.addEventListener("click", function(){
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("neuroverse-theme", next);
      syncBtn();
    });
  }
  window.eegDownloadCsv = function(filename, rows) {
    var lines = rows.map(function(r) {
      return r.map(function(cell) {
        var s = cell === null || cell === undefined ? "" : String(cell);
        if (s.indexOf(",") !== -1 || s.indexOf('"') !== -1 || s.indexOf("\n") !== -1) {
          return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
      }).join(",");
    });
    var blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
})();
"""


def write_interactive_leaderboard(
    payload: dict[str, object],
    output_path: Path,
    also_index: bool = True,
) -> Path:
    """Write ``leaderboard.html`` (and optionally ``index.html``)."""
    data_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neuroverse &mdash; Algorithm Leaderboard</title>
<style>{_SHARED_CSS}
.champ-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
  gap: 0.7rem;
  margin-top: 0.75rem;
}}
.champ-item {{
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem 0.8rem;
  background: var(--surface-alt);
}}
.champ-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }}
.champ-name {{ font-weight: 700; font-size: 0.9rem; }}
.champ-meta {{ font-size: 0.78rem; color: var(--muted); }}
</style>
</head>
<body>
{_topbar_html("leaderboard")}
<main class="container">
  <section class="hero">
    <h1>EEG Classification Algorithm Leaderboard</h1>
    <p>Systematic comparison of 72 distinct classification algorithms (90 total configurations including band-pass and random-weight controls) across {len(payload["datasets"])} scalp EEG classification problems (fixed train/test resample 0).</p>
  </section>

  <div class="tab-strip" id="tabStrip" role="tablist"></div>

  <div class="kpi-grid" id="kpiGrid"></div>

  <div class="toolbar">
    <div class="pill-group" id="paradigmPills"></div>
    <div class="control-group">
      <select class="ctrl" id="viewSelect" aria-label="Column layout">
        <option value="metrics" selected>Columns: Standard Metrics</option>
        <option value="domains">Columns: Split by Problem Type</option>
      </select>
      <select class="ctrl" id="familySelect" aria-label="Filter by tsml-eval family">
        <option value="ALL">All tsml-eval families</option>
      </select>
      <select class="ctrl" id="modeSelect" aria-label="Coverage and ranking mode">
        <option value="block80" selected>Common Block (&ge;80% coverage)</option>
        <option value="block90">Common Block (&ge;90% coverage)</option>
        <option value="block100">Complete Only (100% coverage)</option>
        <option value="available">All Available (No coverage gate &middot; normalised rank)</option>
      </select>
      <label class="chk"><input type="checkbox" id="includeVariants"> Include 18 variants &amp; controls (all 90 configs)</label>
      <input type="search" class="ctrl" id="searchInput" placeholder="Search classifier or library...">
      <button type="button" class="action-btn" id="exportLbCsv">Export CSV</button>
    </div>
  </div>

  <div class="banner-warn" id="modeBanner"></div>

  <div class="table-card">
    <div class="table-scroll">
      <table class="data-table" id="lbTable">
        <thead id="lbHead"></thead>
        <tbody id="lbBody"></tbody>
      </table>
    </div>
  </div>
  <p class="note" id="tableFootnote"></p>

  <section class="section-card">
    <h2>Best Representative per Paradigm (<span id="champTabLabel">All Scalp EEG</span>)</h2>
    <div class="champ-grid" id="champGrid"></div>
  </section>

  <section class="section-card" id="cdSection">
    <h2>Critical Difference Diagram (<span id="cdTabLabel">All Scalp EEG</span>)</h2>
    <div id="cdContainer"></div>
    <p class="note" id="cdNote"></p>
  </section>
</main>
<div class="modal-backdrop" id="algModal">
  <div class="modal-card">
    <div class="modal-head">
      <div id="algModalTitle"></div>
      <button type="button" class="modal-close" id="algModalClose">&times; Close</button>
    </div>
    <div class="modal-body" id="algModalBody"></div>
  </div>
</div>
<script id="benchData" type="application/json">{data_json}</script>
<script>{_THEME_JS}
(function(){{
  var DATA = JSON.parse(document.getElementById("benchData").textContent);
  var dsIndex = {{}};
  DATA.datasets.forEach(function(d, idx) {{ dsIndex[d.name] = idx; }});
  var tabByKey = {{}};
  DATA.tabs.forEach(function(t) {{ tabByKey[t.key] = t; }});
  var DOMAIN_COLS = ["MI", "ME", "ERP", "VEP", "Speech", "Clinical", "Cognitive"];

  var state = {{
    tab: "All",
    view: "metrics",
    paradigm: "ALL",
    family: "ALL",
    mode: "block80",
    includeVariants: false,
    search: "",
    sortBy: "mean_rank",
    sortDir: "asc"
  }};
  var lastExport = {{ filename: "neuroverse_leaderboard.csv", rows: [] }};

  // Populate tabs
  var tabStrip = document.getElementById("tabStrip");
  DATA.tabs.forEach(function(t) {{
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tab-btn" + (t.key === state.tab ? " active" : "");
    btn.dataset.tab = t.key;
    btn.innerHTML = t.label + ' <span class="tab-count">' + t.datasets.length + "</span>";
    btn.addEventListener("click", function() {{
      state.tab = t.key;
      Array.prototype.forEach.call(tabStrip.children, function(c) {{
        c.classList.toggle("active", c.dataset.tab === state.tab);
      }});
      render();
    }});
    tabStrip.appendChild(btn);
  }});

  // Populate paradigm pills
  var paradigmPills = document.getElementById("paradigmPills");
  var pillDefs = [["ALL", "All Paradigms"]];
  ["TSML", "EEG-Classical", "EEG-DL", "EEG-FM", "Tabular"].forEach(function(k) {{
    if (DATA.paradigms[k]) pillDefs.push([k, DATA.paradigms[k]]);
  }});
  pillDefs.forEach(function(pair) {{
    var b = document.createElement("button");
    b.type = "button";
    b.className = "pill-btn" + (pair[0] === state.paradigm ? " active" : "");
    b.dataset.par = pair[0];
    b.textContent = pair[1];
    b.addEventListener("click", function() {{
      state.paradigm = pair[0];
      Array.prototype.forEach.call(paradigmPills.children, function(c) {{
        c.classList.toggle("active", c.dataset.par === state.paradigm);
      }});
      render();
    }});
    paradigmPills.appendChild(b);
  }});

  var viewSel = document.getElementById("viewSelect");
  viewSel.addEventListener("change", function() {{
    state.view = viewSel.value;
    if (state.view === "metrics" && state.sortBy.indexOf("dom_") === 0) {{
      state.sortBy = "mean_rank";
      state.sortDir = "asc";
    }} else if (state.view === "domains" && ["accuracy", "auroc", "logloss", "wins", "top5", "coverage"].indexOf(state.sortBy) !== -1) {{
      state.sortBy = "mean_rank";
      state.sortDir = "asc";
    }}
    render();
  }});

  // Populate tsml-eval family dropdown
  var famSel = document.getElementById("familySelect");
  Object.keys(DATA.tsml_families).forEach(function(f) {{
    var opt = document.createElement("option");
    opt.value = f;
    opt.textContent = f;
    famSel.appendChild(opt);
  }});
  famSel.addEventListener("change", function() {{ state.family = famSel.value; render(); }});

  var modeSel = document.getElementById("modeSelect");
  modeSel.addEventListener("change", function() {{ state.mode = modeSel.value; render(); }});

  document.getElementById("includeVariants").addEventListener("change", function(e) {{
    state.includeVariants = e.target.checked; render();
  }});
  document.getElementById("searchInput").addEventListener("input", function(e) {{
    state.search = e.target.value.trim().toLowerCase(); render();
  }});
  document.getElementById("exportLbCsv").addEventListener("click", function() {{
    if (window.eegDownloadCsv && lastExport.rows.length) {{
      window.eegDownloadCsv(lastExport.filename, lastExport.rows);
    }}
  }});

  // Delegated sort headers
  document.getElementById("lbHead").addEventListener("click", function(e) {{
    var th = e.target.closest("th.sortable");
    if (!th) return;
    var col = th.dataset.sort;
    if (state.sortBy === col) {{
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    }} else {{
      state.sortBy = col;
      state.sortDir = th.dataset.dir || "asc";
    }}
    render();
  }});

  function rankRowDescending(vals) {{
    var present = [];
    for (var i = 0; i < vals.length; i++) {{
      if (vals[i] !== null && !isNaN(vals[i])) present.push({{ idx: i, v: vals[i] }});
    }}
    present.sort(function(a, b) {{ return b.v - a.v; }});
    var ranks = new Array(vals.length).fill(null);
    var p = 0;
    while (p < present.length) {{
      var q = p;
      while (q + 1 < present.length && Math.abs(present[q + 1].v - present[p].v) <= 1e-12) q++;
      var avg = (p + 1 + q + 1) / 2.0;
      for (var k = p; k <= q; k++) ranks[present[k].idx] = avg;
      p = q + 1;
    }}
    return {{ ranks: ranks, count: present.length, maxVal: present.length ? present[0].v : null }};
  }}

  function computeLeague(tabObj, includeAll) {{
    var dIdxs = tabObj.datasets.map(function(n) {{ return dsIndex[n]; }});
    var nScope = dIdxs.length;
    var nEst = DATA.estimators.length;
    var bal = DATA.scores.balacc;
    var acc = DATA.scores.accuracy;
    var auc = DATA.scores.auroc;
    var ll = DATA.scores.logloss;

    var cov = new Array(nEst).fill(0);
    for (var j = 0; j < nEst; j++) {{
      for (var r = 0; r < dIdxs.length; r++) {{
        if (bal[dIdxs[r]][j] !== null) cov[j]++;
      }}
    }}

    var isAvail = state.mode === "available";
    var ratio = state.mode === "block100" ? 1.0 : (state.mode === "block90" ? 0.9 : 0.8);
    var minCov = isAvail ? 1 : Math.ceil(ratio * nScope);

    var panel = [];
    var nPool = 0;
    for (var j2 = 0; j2 < nEst; j2++) {{
      if (!includeAll && !DATA.estimators[j2].is_canonical) continue;
      nPool++;
      if (cov[j2] >= minCov) panel.push(j2);
    }}
    if (!panel.length) return {{ rows: [], byName: {{}}, nScope: nScope, nCommon: 0, minCov: minCov, nAdmitted: 0, nPool: nPool }};

    var evalRows = [];
    for (var r2 = 0; r2 < dIdxs.length; r2++) {{
      var di = dIdxs[r2];
      if (isAvail) {{
        var any = false;
        for (var pIdx = 0; pIdx < panel.length; pIdx++) {{
          if (bal[di][panel[pIdx]] !== null) {{ any = true; break; }}
        }}
        if (any) evalRows.push(di);
      }} else {{
        var all = true;
        for (var pIdx2 = 0; pIdx2 < panel.length; pIdx2++) {{
          if (bal[di][panel[pIdx2]] === null) {{ all = false; break; }}
        }}
        if (all) evalRows.push(di);
      }}
    }}
    if (!evalRows.length) return {{ rows: [], byName: {{}}, nScope: nScope, nCommon: 0, minCov: minCov, nAdmitted: panel.length, nPool: nPool }};

    var mPanel = panel.length;
    var sumRank = new Array(mPanel).fill(0);
    var cntRank = new Array(mPanel).fill(0);
    var wins = new Array(mPanel).fill(0);
    var top5 = new Array(mPanel).fill(0);

    for (var er = 0; er < evalRows.length; er++) {{
      var rowIdx = evalRows[er];
      var slice = panel.map(function(col) {{ return bal[rowIdx][col]; }});
      var rkObj = rankRowDescending(slice);
      for (var k = 0; k < mPanel; k++) {{
        var rk = rkObj.ranks[k];
        if (rk !== null) {{
          var adj = rk;
          if (isAvail && rkObj.count > 1 && mPanel > 1) {{
            adj = 1.0 + (rk - 1.0) * (mPanel - 1.0) / (rkObj.count - 1.0);
          }} else if (isAvail) {{
            adj = 1.0;
          }}
          sumRank[k] += adj;
          cntRank[k]++;
          if (rk <= 5.0) top5[k]++;
          if (rkObj.maxVal !== null && Math.abs(slice[k] - rkObj.maxVal) <= 1e-12) wins[k]++;
        }}
      }}
    }}

    function colMean(mat, col) {{
      var s = 0, c = 0;
      for (var i = 0; i < evalRows.length; i++) {{
        var v = mat[evalRows[i]][col];
        if (v !== null && !isNaN(v)) {{ s += v; c++; }}
      }}
      return c > 0 ? s / c : null;
    }}

    var rows = [];
    for (var k2 = 0; k2 < mPanel; k2++) {{
      var cIdx = panel[k2];
      var meta = DATA.estimators[cIdx];
      rows.push({{
        estIdx: cIdx,
        meta: meta,
        name: meta.name,
        coverage: cov[cIdx],
        scope: nScope,
        mean_rank: cntRank[k2] ? sumRank[k2] / cntRank[k2] : null,
        balacc: colMean(bal, cIdx),
        accuracy: colMean(acc, cIdx),
        auroc: colMean(auc, cIdx),
        logloss: colMean(ll, cIdx),
        wins: wins[k2],
        top5: top5[k2]
      }});
    }}

    rows.sort(function(a, b) {{
      if (a.mean_rank !== b.mean_rank) return a.mean_rank - b.mean_rank;
      return (b.balacc || 0) - (a.balacc || 0);
    }});
    var byName = {{}};
    rows.forEach(function(r, idx) {{
      r.leagueRank = idx + 1;
      byName[r.name] = r;
    }});

    return {{
      rows: rows,
      byName: byName,
      nScope: nScope,
      nCommon: evalRows.length,
      minCov: minCov,
      nAdmitted: mPanel,
      nPool: nPool
    }};
  }}

  function esc(s) {{
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}

  function fmtPct(v) {{ return v === null || isNaN(v) ? "&mdash;" : (100.0 * v).toFixed(2) + "%"; }}
  function fmtDec(v, d) {{ return v === null || isNaN(v) ? "&mdash;" : v.toFixed(d); }}
  function sortMark(col) {{
    if (state.sortBy !== col) return "";
    return state.sortDir === "asc" ? " &uarr;" : " &darr;";
  }}

  // Modal inspection logic
  var modal = document.getElementById("algModal");
  var modalTitle = document.getElementById("algModalTitle");
  var modalBody = document.getElementById("algModalBody");
  function closeAlgModal() {{ modal.classList.remove("open"); }}
  document.getElementById("algModalClose").addEventListener("click", closeAlgModal);
  modal.addEventListener("click", function(e) {{ if (e.target === modal) closeAlgModal(); }});
  document.addEventListener("keydown", function(e) {{ if (e.key === "Escape" && modal.classList.contains("open")) closeAlgModal(); }});

  function openAlgModal(estIdx) {{
    var meta = DATA.estimators[estIdx];
    modalTitle.innerHTML =
      '<div style="display:flex;align-items:center;gap:0.55rem;flex-wrap:wrap">' +
        '<strong style="font-size:1.12rem">' + esc(meta.name) + '</strong>' +
        '<span class="badge badge-' + esc(meta.paradigm) + '">' + esc(meta.paradigm_label) + '</span>' +
        '<span class="brand-tag">' + esc(meta.tsml_family) + '</span>' +
        '<span class="brand-tag">' + esc(meta.library) + '</span>' +
      '</div>' +
      '<div style="color:var(--muted);font-size:0.83rem;margin-top:0.25rem">' + esc(meta.description) + '</div>';

    var domBars = '<h3 style="margin:0 0 0.4rem;font-size:0.95rem">Rank &amp; Balanced Accuracy by Problem Type</h3>' +
      '<div class="dom-bar-grid">';
    var modalIncAll = state.includeVariants || !meta.is_canonical;
    DATA.tabs.forEach(function(t) {{
      var lg = computeLeague(t, modalIncAll);
      var rec = lg.byName[meta.name];
      if (rec) {{
        var pct = Math.max(4, Math.min(100, Math.round(100.0 * (rec.balacc || 0))));
        domBars +=
          '<div style="font-weight:600;font-size:0.82rem">' + esc(t.key) + ' <span style="color:var(--muted);font-weight:400">(' + rec.coverage + '/' + t.datasets.length + ')</span></div>' +
          '<div class="dom-track"><div class="dom-fill" style="width:' + pct + '%"></div></div>' +
          '<div style="text-align:right;font-size:0.8rem;font-variant-numeric:tabular-nums"><strong>#' + rec.leagueRank + '</strong>/' + lg.nAdmitted + ' &middot; ' + fmtPct(rec.balacc) + '</div>';
      }} else {{
        var rawCov = 0;
        t.datasets.forEach(function(dn) {{ if (DATA.scores.balacc[dsIndex[dn]][estIdx] !== null) rawCov++; }});
        domBars +=
          '<div style="font-weight:600;font-size:0.82rem">' + esc(t.key) + ' <span style="color:var(--muted);font-weight:400">(' + rawCov + '/' + t.datasets.length + ')</span></div>' +
          '<div class="dom-track"></div>' +
          '<div style="text-align:right;font-size:0.78rem;color:var(--muted)">Below coverage gate</div>';
      }}
    }});
    domBars += '</div>';

    // Per-problem breakdown (top 8 gains + missing list)
    var perProb = [];
    var missing = [];
    for (var ri = 0; ri < DATA.datasets.length; ri++) {{
      var d = DATA.datasets[ri];
      var ba = DATA.scores.balacc[ri][estIdx];
      if (ba === null) {{
        missing.push(d.name);
        continue;
      }}
      var fl = DATA.default_floor.balacc[ri];
      var rowBa = DATA.scores.balacc[ri];
      var cnt = 0, better = 0;
      for (var k = 0; k < rowBa.length; k++) {{
        if (!modalIncAll && !DATA.estimators[k].is_canonical) continue;
        if (rowBa[k] !== null) {{
          cnt++;
          if (rowBa[k] > ba + 1e-12) better++;
        }}
      }}
      perProb.push({{
        name: d.name,
        type: d.type,
        rk: better + 1,
        cnt: cnt,
        balacc: ba,
        floor: fl,
        gain: fl !== null ? (ba - fl) : 0
      }});
    }}
    perProb.sort(function(a, b) {{ return a.rk !== b.rk ? a.rk - b.rk : b.gain - a.gain; }});
    var topSlice = perProb.slice(0, 8);
    var tblHtml = '<h3 style="margin:0.8rem 0 0.45rem;font-size:0.95rem">Strongest Benchmark Tasks (Best Within-Problem Ranks)</h3>' +
      '<div class="table-scroll"><table class="data-table"><thead><tr>' +
      '<th class="col-name">Problem</th><th>Type</th><th>Rank</th><th>Balanced Acc</th><th>Default Floor</th><th>Gain</th>' +
      '</tr></thead><tbody>';
    topSlice.forEach(function(p) {{
      tblHtml += '<tr><td class="col-name"><strong>' + esc(p.name) + '</strong></td>' +
        '<td><span class="brand-tag">' + esc(p.type) + '</span></td>' +
        '<td>#' + p.rk + ' / ' + p.cnt + '</td>' +
        '<td>' + fmtPct(p.balacc) + '</td>' +
        '<td>' + fmtPct(p.floor) + '</td>' +
        '<td>' + (p.gain >= 0 ? "+" : "") + fmtPct(p.gain) + '</td></tr>';
    }});
    tblHtml += '</tbody></table></div>';

    var missHtml = missing.length
      ? ('<p class="note" style="margin-top:0.85rem"><strong>Pending / unsupported tasks (' + missing.length + ' of ' + DATA.datasets.length + '):</strong> ' + esc(missing.join(", ")) + '.</p>')
      : ('<p class="note" style="margin-top:0.85rem"><strong>Full coverage:</strong> Completed all ' + DATA.datasets.length + ' scalp EEG benchmark tasks.</p>');

    modalBody.innerHTML = domBars + tblHtml + missHtml;
    modal.classList.add("open");
  }}

  document.getElementById("lbBody").addEventListener("click", function(e) {{
    var tr = e.target.closest("tr[data-est-idx]");
    if (!tr) return;
    openAlgModal(parseInt(tr.dataset.estIdx, 10));
  }});

  function render() {{
    var tabObj = tabByKey[state.tab] || DATA.tabs[0];
    var league = computeLeague(tabObj, state.includeVariants);
    var allRows = league.rows;

    var domLeagues = {{}};
    if (state.view === "domains") {{
      DOMAIN_COLS.forEach(function(dk) {{
        if (tabByKey[dk]) domLeagues[dk] = computeLeague(tabByKey[dk], state.includeVariants);
      }});
      allRows.forEach(function(r) {{
        DOMAIN_COLS.forEach(function(dk) {{
          var rec = domLeagues[dk] && domLeagues[dk].byName[r.name];
          r["dom_" + dk] = rec ? rec.mean_rank : null;
          r["domPos_" + dk] = rec ? rec.leagueRank : null;
          r["domBal_" + dk] = rec ? rec.balacc : null;
        }});
      }});
    }}

    // KPI cards (always reflect full admitted league of the selected tab)
    var leader = allRows[0] || null;
    var bestEeg = allRows.filter(function(r) {{
      return r.meta.paradigm === "EEG-Classical" || r.meta.paradigm === "EEG-DL" || r.meta.paradigm === "EEG-FM";
    }})[0] || null;
    var bestFm = allRows.filter(function(r) {{
      return r.meta.paradigm === "EEG-FM" && !r.meta.is_ablation;
    }})[0] || null;

    var poolLabel = state.includeVariants ? "configurations" : "distinct classifiers";
    var kpiHtml = "";
    kpiHtml += '<div class="kpi-card"><div class="kpi-label">Evaluation Scope</div>' +
      '<div class="kpi-value">' + league.nScope + ' Problems <span class="brand-tag">' + league.nCommon + ' shared</span></div>' +
      '<div class="kpi-sub">' + league.nAdmitted + ' of ' + league.nPool + ' ' + poolLabel + ' admitted (min ' + league.minCov + '/' + league.nScope + ')</div></div>';

    if (leader) {{
      kpiHtml += '<div class="kpi-card"><div class="kpi-label">#1 Overall on ' + esc(tabObj.label) + '</div>' +
        '<div class="kpi-value">' + esc(leader.name) + ' <span class="badge badge-' + esc(leader.meta.paradigm) + '">' + esc(leader.meta.paradigm_label) + '</span></div>' +
        '<div class="kpi-sub">Mean rank ' + fmtDec(leader.mean_rank, 2) + ' &middot; BalAcc ' + fmtPct(leader.balacc) + ' &middot; ' + leader.wins + ' wins</div></div>';
    }}
    if (bestEeg) {{
      kpiHtml += '<div class="kpi-card"><div class="kpi-label">Best EEG-Specific Pipeline</div>' +
        '<div class="kpi-value">' + esc(bestEeg.name) + ' <span class="badge badge-' + esc(bestEeg.meta.paradigm) + '">#' + bestEeg.leagueRank + '</span></div>' +
        '<div class="kpi-sub">' + esc(bestEeg.meta.paradigm_label) + ' &middot; BalAcc ' + fmtPct(bestEeg.balacc) + '</div></div>';
    }}
    if (bestFm) {{
      kpiHtml += '<div class="kpi-card"><div class="kpi-label">Leading EEG Foundation Model</div>' +
        '<div class="kpi-value">' + esc(bestFm.name) + ' <span class="badge badge-EEG-FM">#' + bestFm.leagueRank + '</span></div>' +
        '<div class="kpi-sub">Coverage ' + bestFm.coverage + '/' + bestFm.scope + ' &middot; BalAcc ' + fmtPct(bestFm.balacc) + '</div></div>';
    }} else {{
      kpiHtml += '<div class="kpi-card"><div class="kpi-label">EEG Foundation Coverage</div>' +
        '<div class="kpi-value">Switch to All Available</div>' +
        '<div class="kpi-sub">LaBraM covers 57/' + DATA.datasets.length + ' problems (10-20 channel metadata required)</div></div>';
    }}
    document.getElementById("kpiGrid").innerHTML = kpiHtml;

    // Mode warning banner
    var banner = document.getElementById("modeBanner");
    if (state.mode === "available") {{
      banner.style.display = "block";
      banner.innerHTML = "<strong>All-Available Mode:</strong> Showing all algorithms with &ge;1 result on this tab (including montage- or binary-restricted pipelines such as <code>LaBraM</code> and <code>TRCSP-LDA-MOABB</code>). Ranks are normalised per problem and means are over each algorithm's available subset, so treat scores as descriptive rather than paired.";
    }} else {{
      banner.style.display = "none";
    }}

    // Filter rows
    var filtered = allRows.filter(function(r) {{
      if (state.paradigm !== "ALL" && r.meta.paradigm !== state.paradigm) return false;
      if (state.family !== "ALL" && r.meta.tsml_family !== state.family) return false;
      if (state.search) {{
        var hay = (r.name + " " + r.meta.paradigm_label + " " + r.meta.tsml_family + " " + r.meta.library + " " + r.meta.description).toLowerCase();
        if (hay.indexOf(state.search) === -1) return false;
      }}
      return true;
    }});

    // Best values among visible rows for highlighting
    var best = {{ mean_rank: Infinity, balacc: -Infinity, accuracy: -Infinity, auroc: -Infinity, logloss: Infinity }};
    DOMAIN_COLS.forEach(function(dk) {{ best["dom_" + dk] = Infinity; }});
    filtered.forEach(function(r) {{
      if (r.mean_rank !== null && r.mean_rank < best.mean_rank) best.mean_rank = r.mean_rank;
      if (r.balacc !== null && r.balacc > best.balacc) best.balacc = r.balacc;
      if (r.accuracy !== null && r.accuracy > best.accuracy) best.accuracy = r.accuracy;
      if (r.auroc !== null && r.auroc > best.auroc) best.auroc = r.auroc;
      if (r.logloss !== null && r.logloss < best.logloss) best.logloss = r.logloss;
      if (state.view === "domains") {{
        DOMAIN_COLS.forEach(function(dk) {{
          var dv = r["dom_" + dk];
          if (dv !== null && dv !== undefined && dv < best["dom_" + dk]) best["dom_" + dk] = dv;
        }});
      }}
    }});

    // Sort visible rows
    var dir = state.sortDir === "asc" ? 1 : -1;
    filtered.sort(function(a, b) {{
      if (state.sortBy === "name") {{
        return a.name.toLowerCase().localeCompare(b.name.toLowerCase()) * dir;
      }}
      var va = a[state.sortBy], vb = b[state.sortBy];
      if ((va === null || va === undefined) && (vb === null || vb === undefined)) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (va !== vb) return (va - vb) * dir;
      return a.leagueRank - b.leagueRank;
    }});

    // Render table header & body for active column view
    var headHtml = "";
    var bodyHtml = "";
    var csvRows = [];

    function cls(val, target) {{
      return val !== null && val !== undefined && Math.abs(val - target) <= 1e-9 ? ' class="best-cell"' : "";
    }}

    if (state.view === "metrics") {{
      headHtml = '<tr>' +
        '<th class="col-pos">#</th>' +
        '<th class="col-name sortable" data-sort="name" data-dir="asc">Algorithm' + sortMark("name") + '</th>' +
        '<th class="sortable" data-sort="mean_rank" data-dir="asc">Mean Rank' + sortMark("mean_rank") + '</th>' +
        '<th class="sortable" data-sort="balacc" data-dir="desc">Balanced Acc' + sortMark("balacc") + '</th>' +
        '<th class="sortable" data-sort="accuracy" data-dir="desc">Accuracy' + sortMark("accuracy") + '</th>' +
        '<th class="sortable" data-sort="auroc" data-dir="desc">AUROC' + sortMark("auroc") + '</th>' +
        '<th class="sortable" data-sort="logloss" data-dir="asc">Log Loss' + sortMark("logloss") + '</th>' +
        '<th class="sortable" data-sort="wins" data-dir="desc">Wins' + sortMark("wins") + '</th>' +
        '<th class="sortable" data-sort="top5" data-dir="desc">Top-5' + sortMark("top5") + '</th>' +
        '<th class="sortable" data-sort="coverage" data-dir="desc">Coverage' + sortMark("coverage") + '</th>' +
        '</tr>';
      csvRows.push(["Position", "League_Rank", "Algorithm", "Paradigm", "TSML_Family", "Library", "Coverage", "Scope", "Mean_Rank", "Balanced_Acc", "Accuracy", "AUROC", "LogLoss", "Wins", "Top5"]);

      filtered.forEach(function(r, idx) {{
        var dispPos = idx + 1;
        var rkBadge = dispPos <= 3 ? '<span class="rank-pill rank-' + dispPos + '">' + dispPos + "</span>" : String(dispPos);
        var globalHint = (state.paradigm !== "ALL" || state.family !== "ALL" || state.search)
          ? ' <span class="alg-sub">(#' + r.leagueRank + " overall)</span>" : "";
        var pctCov = Math.round((100.0 * r.coverage) / Math.max(1, r.scope));

        bodyHtml += '<tr class="clickable-row" data-est-idx="' + r.estIdx + '" title="Click to inspect per-domain profile &amp; top tasks">' +
          '<td class="col-pos">' + rkBadge + '</td>' +
          '<td class="col-name"><div class="alg-cell"><div class="alg-main">' +
            '<span class="alg-name">' + esc(r.name) + '</span>' +
            '<span class="badge badge-' + esc(r.meta.paradigm) + '">' + esc(r.meta.paradigm_label) + '</span>' +
            globalHint +
          '</div><div class="alg-sub">' + esc(r.meta.tsml_family) + " &middot; " + esc(r.meta.library) + " &middot; " + esc(r.meta.description) + '</div></div></td>' +
          "<td" + cls(r.mean_rank, best.mean_rank) + ">" + fmtDec(r.mean_rank, 2) + "</td>" +
          "<td" + cls(r.balacc, best.balacc) + ">" + fmtPct(r.balacc) + "</td>" +
          "<td" + cls(r.accuracy, best.accuracy) + ">" + fmtPct(r.accuracy) + "</td>" +
          "<td" + cls(r.auroc, best.auroc) + ">" + fmtDec(r.auroc, 4) + "</td>" +
          "<td" + cls(r.logloss, best.logloss) + ">" + fmtDec(r.logloss, 3) + "</td>" +
          "<td>" + r.wins + "</td>" +
          "<td>" + r.top5 + "</td>" +
          '<td><div class="cov-wrap"><span>' + r.coverage + "/" + r.scope + '</span><span class="cov-bar"><span class="cov-fill" style="width:' + pctCov + '%"></span></span></div></td>' +
          "</tr>";

        csvRows.push([
          dispPos, r.leagueRank, r.name, r.meta.paradigm_label, r.meta.tsml_family, r.meta.library,
          r.coverage, r.scope,
          r.mean_rank === null ? "" : r.mean_rank.toFixed(4),
          r.balacc === null ? "" : r.balacc.toFixed(5),
          r.accuracy === null ? "" : r.accuracy.toFixed(5),
          r.auroc === null ? "" : r.auroc.toFixed(5),
          r.logloss === null ? "" : r.logloss.toFixed(4),
          r.wins, r.top5
        ]);
      }});
    }} else {{
      headHtml = '<tr>' +
        '<th class="col-pos">#</th>' +
        '<th class="col-name sortable" data-sort="name" data-dir="asc">Algorithm' + sortMark("name") + '</th>' +
        '<th class="sortable" data-sort="mean_rank" data-dir="asc">' + esc(state.tab) + ' Rank' + sortMark("mean_rank") + '</th>' +
        '<th class="sortable" data-sort="balacc" data-dir="desc">' + esc(state.tab) + ' BalAcc' + sortMark("balacc") + '</th>';
      DOMAIN_COLS.forEach(function(dk) {{
        var nDom = tabByKey[dk] ? tabByKey[dk].datasets.length : 0;
        headHtml += '<th class="sortable" data-sort="dom_' + dk + '" data-dir="asc">' + esc(dk) + ' (' + nDom + ')' + sortMark("dom_" + dk) + '</th>';
      }});
      headHtml += '</tr>';

      var hdrCsv = ["Position", "League_Rank", "Algorithm", "Paradigm", state.tab + "_MeanRank", state.tab + "_BalAcc"];
      DOMAIN_COLS.forEach(function(dk) {{ hdrCsv.push(dk + "_Pos", dk + "_MeanRank", dk + "_BalAcc"); }});
      csvRows.push(hdrCsv);

      filtered.forEach(function(r, idx) {{
        var dispPos = idx + 1;
        var rkBadge = dispPos <= 3 ? '<span class="rank-pill rank-' + dispPos + '">' + dispPos + "</span>" : String(dispPos);
        bodyHtml += '<tr class="clickable-row" data-est-idx="' + r.estIdx + '" title="Click to inspect per-domain profile &amp; top tasks">' +
          '<td class="col-pos">' + rkBadge + '</td>' +
          '<td class="col-name"><div class="alg-cell"><div class="alg-main">' +
            '<span class="alg-name">' + esc(r.name) + '</span>' +
            '<span class="badge badge-' + esc(r.meta.paradigm) + '">' + esc(r.meta.paradigm_label) + '</span>' +
          '</div><div class="alg-sub">' + esc(r.meta.tsml_family) + " &middot; " + esc(r.meta.library) + '</div></div></td>' +
          "<td" + cls(r.mean_rank, best.mean_rank) + ">" + fmtDec(r.mean_rank, 2) + "</td>" +
          "<td" + cls(r.balacc, best.balacc) + ">" + fmtPct(r.balacc) + "</td>";

        var rowCsv = [
          dispPos, r.leagueRank, r.name, r.meta.paradigm_label,
          r.mean_rank === null ? "" : r.mean_rank.toFixed(4),
          r.balacc === null ? "" : r.balacc.toFixed(5)
        ];

        DOMAIN_COLS.forEach(function(dk) {{
          var dMr = r["dom_" + dk], dPos = r["domPos_" + dk], dBa = r["domBal_" + dk];
          if (dMr === null || dMr === undefined) {{
            bodyHtml += '<td style="color:var(--muted)">&mdash;</td>';
            rowCsv.push("", "", "");
          }} else {{
            bodyHtml += "<td" + cls(dMr, best["dom_" + dk]) + ">#" + dPos +
              ' <span style="color:var(--muted);font-size:0.74rem">(' + fmtDec(dMr, 1) + ')</span>' +
              '<div style="font-size:0.74rem;color:var(--fg-secondary)">' + fmtPct(dBa) + '</div></td>';
            rowCsv.push(dPos, dMr.toFixed(4), dBa === null ? "" : dBa.toFixed(5));
          }}
        }});
        bodyHtml += "</tr>";
        csvRows.push(rowCsv);
      }});
    }}

    if (!filtered.length) {{
      bodyHtml = '<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--muted)">No algorithms match the current filter settings.</td></tr>';
    }}
    document.getElementById("lbHead").innerHTML = headHtml;
    document.getElementById("lbBody").innerHTML = bodyHtml;
    lastExport = {{
      filename: "neuroverse_leaderboard_" + state.tab.toLowerCase() + "_" + state.view + ".csv",
      rows: csvRows
    }};

    document.getElementById("tableFootnote").innerHTML =
      "Showing <strong>" + filtered.length + "</strong> of <strong>" + league.nAdmitted + "</strong> admitted algorithms on <strong>" +
      esc(tabObj.label) + "</strong> (" + league.nCommon + " shared problems from " + league.nScope +
      " in scope; built " + esc(DATA.built) + "). Click any algorithm row for its full cross-domain profile.";

    // Paradigm champions strip
    document.getElementById("champTabLabel").textContent = tabObj.label;
    var champHtml = "";
    ["TSML", "EEG-Classical", "EEG-DL", "EEG-FM", "Tabular"].forEach(function(par) {{
      var top = allRows.filter(function(r) {{ return r.meta.paradigm === par && !r.meta.is_ablation; }})[0];
      if (!top) return;
      champHtml += '<div class="champ-item">' +
        '<div class="champ-head"><span class="badge badge-' + par + '">' + esc(DATA.paradigms[par]) + '</span><span class="alg-sub">#' + top.leagueRank + ' overall</span></div>' +
        '<div class="champ-name">' + esc(top.name) + '</div>' +
        '<div class="champ-meta">Rank ' + fmtDec(top.mean_rank, 2) + ' &middot; BalAcc ' + fmtPct(top.balacc) + ' &middot; ' + top.wins + ' wins</div>' +
        '</div>';
    }});
    document.getElementById("champGrid").innerHTML = champHtml;

    // Critical difference diagram
    document.getElementById("cdTabLabel").textContent = tabObj.label;
    var cdObj = DATA.cd_diagrams[state.tab];
    var cdCont = document.getElementById("cdContainer");
    var cdNote = document.getElementById("cdNote");
    if (cdObj && cdObj.png) {{
      cdCont.innerHTML = '<img class="cd-img" alt="Critical difference diagram for ' + esc(tabObj.label) + '" src="data:image/png;base64,' + cdObj.png + '">';
      cdNote.textContent = "Top " + cdObj.n_estimators + " admitted distinct classifiers on " + tabObj.label + " over their " + cdObj.n_common +
        " shared problems (72-classifier canonical pool, balanced accuracy, pairwise Wilcoxon signed-rank tests with Holm correction, alpha=" + cdObj.alpha + "). Connected bars indicate cliques that are not statistically distinguishable.";
    }} else {{
      cdCont.innerHTML = '<p class="note">No critical difference diagram rendered for this subset.</p>';
      cdNote.textContent = "";
    }}
  }}

  render();
}})();
</script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    if also_index:
        (output_path.parent / "index.html").write_text(html, encoding="utf-8")
    return output_path


def write_score_matrix_page(payload: dict[str, object], output_path: Path) -> Path:
    """Write ``matrix.html`` (interactive problem-by-classifier score heatmap)."""
    data_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neuroverse &mdash; Overall Performance Score Matrix</title>
<style>{_SHARED_CSS}
.matrix-wrap {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow);
  overflow: auto;
  max-height: 78vh;
}}
table.matrix-table {{
  border-collapse: separate;
  border-spacing: 0;
  font-variant-numeric: tabular-nums;
  font-size: 0.76rem;
}}
table.matrix-table th, table.matrix-table td {{
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 0.28rem 0.42rem;
  white-space: nowrap;
  text-align: center;
}}
table.matrix-table thead tr.banner-row th {{
  position: sticky;
  top: 0;
  z-index: 22;
  font-size: 0.73rem;
  font-weight: 700;
  padding: 0.35rem 0.5rem;
}}
table.matrix-table thead tr.alg-row th {{
  position: sticky;
  top: 28px;
  z-index: 20;
  background: var(--surface-alt);
  height: 128px;
  vertical-align: bottom;
  padding: 0.35rem 0.22rem;
}}
.rot-label {{
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  display: inline-block;
  font-weight: 600;
  font-size: 0.74rem;
  color: var(--fg);
  max-height: 118px;
  overflow: hidden;
  text-overflow: ellipsis;
}}
table.matrix-table th.sticky-ds, table.matrix-table td.sticky-ds {{
  position: sticky;
  left: 0;
  z-index: 15;
  background: var(--surface);
  text-align: left;
  font-weight: 600;
  min-width: 190px;
}}
table.matrix-table th.sticky-type, table.matrix-table td.sticky-type {{
  position: sticky;
  left: 190px;
  z-index: 15;
  background: var(--surface);
  min-width: 78px;
  box-shadow: 2px 0 5px -2px rgba(15, 23, 42, 0.14);
}}
table.matrix-table thead th.sticky-ds, table.matrix-table thead th.sticky-type {{
  z-index: 30;
  background: var(--surface-alt);
}}
tr.summary-row td {{
  background: var(--surface-alt);
  font-weight: 700;
}}
td.cell-missing {{
  color: var(--muted);
  background: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 4px,
    rgba(148, 163, 184, 0.10) 4px,
    rgba(148, 163, 184, 0.10) 8px
  );
}}
td.cell-win {{
  font-weight: 800;
  box-shadow: inset 0 0 0 1.6px var(--fg);
}}
#cellTooltip {{
  position: fixed;
  pointer-events: none;
  z-index: 100;
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--border-strong);
  border-radius: 9px;
  padding: 0.65rem 0.85rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.22);
  font-size: 0.8rem;
  min-width: 240px;
  display: none;
}}
.tt-title {{ font-weight: 700; font-size: 0.88rem; margin-bottom: 0.15rem; }}
.tt-sub {{ color: var(--muted); font-size: 0.74rem; margin-bottom: 0.45rem; }}
.tt-grid {{ display: grid; grid-template-columns: 1fr auto; gap: 0.18rem 0.8rem; }}
</style>
</head>
<body>
{_topbar_html("matrix")}
<main class="container">
  <section class="hero">
    <h1>Overall Performance Score Matrix</h1>
    <p>Problem-by-classifier score heatmap across all {len(payload["datasets"])} scalp EEG tasks and 72 distinct classifiers (90 total configurations). Hover over any cell to inspect all four metrics, within-problem rank, and gain over the constant majority-class floor.</p>
  </section>

  <div class="tab-strip" id="matrixTabStrip"></div>

  <div class="toolbar">
    <div class="control-group">
      <label><strong>Metric:</strong>
        <select class="ctrl" id="metricSelect">
          <option value="balacc" selected>Balanced Accuracy (%)</option>
          <option value="accuracy">Accuracy (%)</option>
          <option value="auroc">AUROC</option>
          <option value="logloss">Log Loss &darr;</option>
        </select>
      </label>
      <label><strong>Columns:</strong>
        <select class="ctrl" id="colScopeSelect">
          <option value="top35" selected>Top 35 Distinct on Selected Tab</option>
          <option value="canonical72">All 72 Distinct Classifiers</option>
          <option value="all90">All 90 Configurations (incl. variants)</option>
          <option value="TSML">General TSML Only (11)</option>
          <option value="EEG-Classical">EEG Classical Only (23)</option>
          <option value="EEG-DL">EEG Supervised DL Only (32)</option>
          <option value="EEG-FM">EEG Foundation Only (2)</option>
          <option value="Tabular">Tabular Only (4)</option>
        </select>
      </label>
      <label><strong>Grouping:</strong>
        <select class="ctrl" id="colOrderSelect">
          <option value="paradigm" selected>Group by Paradigm Banner</option>
          <option value="rank">Order by Overall Mean Score</option>
        </select>
      </label>
      <label><strong>Shading:</strong>
        <select class="ctrl" id="shadeSelect">
          <option value="rownorm" selected>Row-Normalised (min &rarr; max)</option>
          <option value="gain">Gain over Default Floor</option>
          <option value="abs">Absolute Score</option>
        </select>
      </label>
    </div>
    <div class="control-group">
      <input type="search" class="ctrl" id="dsFilter" placeholder="Filter problems...">
      <input type="search" class="ctrl" id="estFilter" placeholder="Filter algorithms...">
      <button type="button" class="action-btn" id="exportMatrixCsv">Export CSV</button>
    </div>
  </div>

  <div class="matrix-wrap">
    <table class="matrix-table" id="matrixTable"></table>
  </div>
  <p class="note" id="matrixNote"></p>
</main>
<div id="cellTooltip"></div>
<script id="benchData" type="application/json">{data_json}</script>
<script>{_THEME_JS}
(function(){{
  var DATA = JSON.parse(document.getElementById("benchData").textContent);
  var dsMap = {{}};
  DATA.datasets.forEach(function(d, i) {{ dsMap[d.name] = i; }});

  var state = {{
    tab: "All",
    metric: "balacc",
    colScope: "top35",
    colOrder: "paradigm",
    shade: "rownorm",
    dsQuery: "",
    estQuery: ""
  }};
  var lastMatrixCsv = {{ filename: "neuroverse_matrix.csv", rows: [] }};

  var strip = document.getElementById("matrixTabStrip");
  DATA.tabs.forEach(function(t) {{
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tab-btn" + (t.key === state.tab ? " active" : "");
    b.dataset.tab = t.key;
    b.innerHTML = t.label + ' <span class="tab-count">' + t.datasets.length + "</span>";
    b.addEventListener("click", function() {{
      state.tab = t.key;
      Array.prototype.forEach.call(strip.children, function(c) {{
        c.classList.toggle("active", c.dataset.tab === state.tab);
      }});
      render();
    }});
    strip.appendChild(b);
  }});

  document.getElementById("metricSelect").addEventListener("change", function(e) {{ state.metric = e.target.value; render(); }});
  document.getElementById("colScopeSelect").addEventListener("change", function(e) {{ state.colScope = e.target.value; render(); }});
  document.getElementById("colOrderSelect").addEventListener("change", function(e) {{ state.colOrder = e.target.value; render(); }});
  document.getElementById("shadeSelect").addEventListener("change", function(e) {{ state.shade = e.target.value; render(); }});
  document.getElementById("dsFilter").addEventListener("input", function(e) {{ state.dsQuery = e.target.value.trim().toLowerCase(); render(); }});
  document.getElementById("estFilter").addEventListener("input", function(e) {{ state.estQuery = e.target.value.trim().toLowerCase(); render(); }});
  document.getElementById("exportMatrixCsv").addEventListener("click", function() {{
    if (window.eegDownloadCsv && lastMatrixCsv.rows.length) {{
      window.eegDownloadCsv(lastMatrixCsv.filename, lastMatrixCsv.rows);
    }}
  }});

  function esc(s) {{
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}

  function cellColour(t) {{
    // t in [0, 1]: 0 = weak (cool slate/rose), 0.5 = neutral amber/sky, 1 = strong emerald
    if (t === null || isNaN(t)) return "";
    var clamped = Math.max(0, Math.min(1, t));
    var isDark = document.documentElement.getAttribute("data-theme") === "dark";
    var hue = Math.round(12 + clamped * 138); // 12 (coral) -> 150 (emerald)
    var sat = isDark ? 58 : 72;
    var light = isDark ? (20 + clamped * 18) : (95 - clamped * 26);
    return "background-color:hsl(" + hue + "," + sat + "%," + light + "%);";
  }}

  function render() {{
    var tabObj = DATA.tabs.filter(function(t) {{ return t.key === state.tab; }})[0] || DATA.tabs[0];
    var mat = DATA.scores[state.metric];
    var lowerBetter = state.metric === "logloss";
    var isPct = state.metric === "balacc" || state.metric === "accuracy";

    var rowIdxs = tabObj.datasets.map(function(n) {{ return dsMap[n]; }}).filter(function(ri) {{
      if (!state.dsQuery) return true;
      var d = DATA.datasets[ri];
      return (d.name + " " + d.type + " " + d.family).toLowerCase().indexOf(state.dsQuery) !== -1;
    }});

    // Sort rows by type then name for clean visual blocks
    var typeOrder = {{ "MI": 1, "ME": 2, "ERP": 3, "VEP": 4, "Speech": 5, "Clinical": 6, "Cognitive": 7 }};
    rowIdxs.sort(function(a, b) {{
      var da = DATA.datasets[a], db = DATA.datasets[b];
      var ta = typeOrder[da.type] || 9, tb = typeOrder[db.type] || 9;
      if (ta !== tb) return ta - tb;
      return da.name.localeCompare(db.name);
    }});

    // Compute mean score per estimator across rowIdxs to rank columns
    var nEst = DATA.estimators.length;
    var colMeans = new Array(nEst).fill(null);
    var colCov = new Array(nEst).fill(0);
    for (var j = 0; j < nEst; j++) {{
      var s = 0, c = 0;
      for (var r = 0; r < rowIdxs.length; r++) {{
        var v = mat[rowIdxs[r]][j];
        if (v !== null) {{ s += v; c++; }}
      }}
      colCov[j] = c;
      colMeans[j] = c > 0 ? s / c : null;
    }}

    var allCols = [];
    for (var j2 = 0; j2 < nEst; j2++) {{
      if (state.estQuery) {{
        var em = DATA.estimators[j2];
        if ((em.name + " " + em.paradigm_label + " " + em.tsml_family).toLowerCase().indexOf(state.estQuery) === -1) continue;
      }}
      allCols.push(j2);
    }}

    allCols.sort(function(a, b) {{
      var ma = colMeans[a], mb = colMeans[b];
      if (ma === null && mb === null) return 0;
      if (ma === null) return 1;
      if (mb === null) return -1;
      return lowerBetter ? (ma - mb) : (mb - ma);
    }});

    var cols = allCols;
    if (state.colScope === "top35") {{
      var canonCols = allCols.filter(function(c) {{ return DATA.estimators[c].is_canonical; }});
      cols = canonCols.filter(function(c) {{ return colCov[c] >= Math.ceil(0.6 * Math.max(1, rowIdxs.length)); }}).slice(0, 35);
      if (!cols.length) cols = canonCols.slice(0, 35);
    }} else if (state.colScope === "canonical72") {{
      cols = allCols.filter(function(c) {{ return DATA.estimators[c].is_canonical; }});
    }} else if (state.colScope !== "all90") {{
      cols = allCols.filter(function(c) {{ return DATA.estimators[c].is_canonical && DATA.estimators[c].paradigm === state.colScope; }});
    }}

    var parOrder = {{ "TSML": 1, "EEG-FM": 2, "EEG-DL": 3, "EEG-Classical": 4, "Tabular": 5 }};
    if (state.colOrder === "paradigm") {{
      cols.sort(function(a, b) {{
        var pa = parOrder[DATA.estimators[a].paradigm] || 9;
        var pb = parOrder[DATA.estimators[b].paradigm] || 9;
        if (pa !== pb) return pa - pb;
        var ma = colMeans[a], mb = colMeans[b];
        if (ma === null) return 1;
        if (mb === null) return -1;
        return lowerBetter ? (ma - mb) : (mb - ma);
      }});
    }}

    // Build paradigm banner spans
    var bannerRow = '<tr><th class="sticky-ds" rowspan="2">Problem (' + rowIdxs.length + ')</th>' +
      '<th class="sticky-type" rowspan="2">Type</th>';
    if (state.colOrder === "paradigm" && cols.length > 0) {{
      var i = 0;
      while (i < cols.length) {{
        var pCode = DATA.estimators[cols[i]].paradigm;
        var span = 1;
        while (i + span < cols.length && DATA.estimators[cols[i + span]].paradigm === pCode) span++;
        bannerRow += '<th colspan="' + span + '" class="badge-' + esc(pCode) + '">' + esc(DATA.paradigms[pCode] || pCode) + " (" + span + ")</th>";
        i += span;
      }}
    }} else if (cols.length > 0) {{
      bannerRow += '<th colspan="' + cols.length + '" style="background:var(--surface-alt)">Algorithms Ordered by Mean Score (' + cols.length + ')</th>';
    }}
    bannerRow += "</tr>";

    var algRow = '<tr class="alg-row">';
    cols.forEach(function(c) {{
      var em = DATA.estimators[c];
      algRow += '<th title="' + esc(em.name + " (" + em.paradigm_label + "): " + em.description) + '"><span class="rot-label">' + esc(em.name) + "</span></th>";
    }});
    algRow += "</tr>";

    // Summary mean row
    var sumRow = '<tr class="summary-row"><td class="sticky-ds">Mean (' + rowIdxs.length + ' problems)</td><td class="sticky-type"><span class="alg-sub">Coverage</span></td>';
    cols.forEach(function(c) {{
      var m = colMeans[c];
      var txt = m === null ? "&mdash;" : (isPct ? (100 * m).toFixed(1) : m.toFixed(2));
      sumRow += '<td title="Completed ' + colCov[c] + ' of ' + rowIdxs.length + ' visible problems">' + txt + '<div style="font-size:0.65rem;color:var(--muted)">' + colCov[c] + "/" + rowIdxs.length + "</div></td>";
    }});
    sumRow += "</tr>";

    // Precompute full-90 within-problem ranks for rich tooltips & CSV export
    var csvRows = [["Problem", "Type", "Default_Floor"].concat(cols.map(function(c) {{ return DATA.estimators[c].name; }}))];
    csvRows.push(["Mean", "Coverage", ""].concat(cols.map(function(c) {{
      return colMeans[c] === null ? "" : colMeans[c].toFixed(5);
    }})));

    var bodyRows = "";
    rowIdxs.forEach(function(ri) {{
      var d = DATA.datasets[ri];
      var fullRow = mat[ri];
      var visVals = cols.map(function(c) {{ return fullRow[c]; }}).filter(function(v) {{ return v !== null; }});
      var rMin = visVals.length ? Math.min.apply(null, visVals) : null;
      var rMax = visVals.length ? Math.max.apply(null, visVals) : null;
      var winVal = lowerBetter ? rMin : rMax;
      var floorVal = DATA.default_floor[state.metric][ri];

      bodyRows += '<tr><td class="sticky-ds" title="' + esc(d.channels + " ch, length " + d.length + ", " + d.classes + " classes, test N=" + d.test_size) + '">' + esc(d.name) + '</td>' +
        '<td class="sticky-type"><span class="brand-tag">' + esc(d.type) + '</span></td>';

      var rowCsv = [d.name, d.type, floorVal === null ? "" : floorVal.toFixed(5)];
      cols.forEach(function(c) {{
        var v = fullRow[c];
        if (v === null) {{
          bodyRows += '<td class="cell-missing" data-ri="' + ri + '" data-ci="' + c + '">&mdash;</td>';
          rowCsv.push("");
          return;
        }}
        rowCsv.push(v.toFixed(5));
        var t = 0.5;
        if (state.shade === "rownorm" && rMax !== null && rMin !== null && rMax > rMin) {{
          t = lowerBetter ? (rMax - v) / (rMax - rMin) : (v - rMin) / (rMax - rMin);
        }} else if (state.shade === "gain" && floorVal !== null) {{
          var g = lowerBetter ? (floorVal - v) : (v - floorVal);
          t = Math.max(0, Math.min(1, 0.35 + g * 1.8));
        }} else {{
          t = lowerBetter ? Math.max(0, Math.min(1, 1 - v / 2.5)) : v;
        }}
        var isWin = winVal !== null && Math.abs(v - winVal) <= 1e-9;
        var disp = isPct ? (100 * v).toFixed(1) : v.toFixed(2);
        bodyRows += '<td' + (isWin ? ' class="cell-win"' : '') + ' style="' + cellColour(t) + '" data-ri="' + ri + '" data-ci="' + c + '">' + disp + "</td>";
      }});
      bodyRows += "</tr>";
      csvRows.push(rowCsv);
    }});

    document.getElementById("matrixTable").innerHTML =
      '<thead class="matrix-head"><tr class="banner-row">' + bannerRow.slice(4) + algRow + "</thead>" +
      "<tbody>" + sumRow + bodyRows + "</tbody>";
    lastMatrixCsv = {{
      filename: "neuroverse_matrix_" + state.tab.toLowerCase() + "_" + state.metric + ".csv",
      rows: csvRows
    }};

    document.getElementById("matrixNote").textContent =
      "Displaying " + rowIdxs.length + " problems x " + cols.length +
      " algorithms. Bold bordered cells mark the best score among displayed columns on each problem. Hatched cells indicate runs not yet completed or unsupported by the estimator.";
  }}

  // Floating tooltip delegation
  var tt = document.getElementById("cellTooltip");
  var tbl = document.getElementById("matrixTable");
  tbl.addEventListener("mousemove", function(e) {{
    var td = e.target.closest("td[data-ri]");
    if (!td) {{ tt.style.display = "none"; return; }}
    var ri = parseInt(td.dataset.ri, 10), ci = parseInt(td.dataset.ci, 10);
    var d = DATA.datasets[ri], em = DATA.estimators[ci];
    var ba = DATA.scores.balacc[ri][ci];
    var ac = DATA.scores.accuracy[ri][ci];
    var au = DATA.scores.auroc[ri][ci];
    var ll = DATA.scores.logloss[ri][ci];
    var fl = DATA.default_floor.balacc[ri];

    // Compute rank among all 90 on balacc
    var rowBa = DATA.scores.balacc[ri];
    var cnt = 0, better = 0;
    for (var k = 0; k < rowBa.length; k++) {{
      if (rowBa[k] !== null) {{
        cnt++;
        if (ba !== null && rowBa[k] > ba + 1e-12) better++;
      }}
    }}
    var rkStr = ba === null ? "Pending / unsupported" : ("#" + (better + 1) + " of " + cnt + " completed");
    var gainStr = (ba !== null && fl !== null) ? (((ba - fl) >= 0 ? "+" : "") + (100 * (ba - fl)).toFixed(2) + "% vs Default") : "&mdash;";

    tt.innerHTML =
      '<div class="tt-title">' + esc(d.name) + " &times; " + esc(em.name) + '</div>' +
      '<div class="tt-sub">' + esc(d.type) + " (" + d.channels + " ch, " + d.classes + " classes, N=" + d.test_size + ") &middot; " + esc(em.paradigm_label) + '</div>' +
      '<div class="tt-grid">' +
        '<span>Within-problem rank (BalAcc):</span><strong>' + rkStr + '</strong>' +
        '<span>Balanced Accuracy:</span><strong>' + (ba === null ? "&mdash;" : (100 * ba).toFixed(2) + "%") + '</strong>' +
        '<span>Gain over floor:</span><strong>' + gainStr + '</strong>' +
        '<span>Accuracy:</span><strong>' + (ac === null ? "&mdash;" : (100 * ac).toFixed(2) + "%") + '</strong>' +
        '<span>AUROC:</span><strong>' + (au === null ? "&mdash;" : au.toFixed(4)) + '</strong>' +
        '<span>Log Loss:</span><strong>' + (ll === null ? "&mdash;" : ll.toFixed(4)) + '</strong>' +
      '</div>';
    tt.style.display = "block";
    var x = Math.min(window.innerWidth - 280, e.clientX + 16);
    var y = Math.min(window.innerHeight - 190, e.clientY + 16);
    tt.style.left = x + "px";
    tt.style.top = y + "px";
  }});
  tbl.addEventListener("mouseleave", function() {{ tt.style.display = "none"; }});

  render();
}})();
</script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def write_problem_explorer_page(payload: dict[str, object], output_path: Path) -> Path:
    """Write ``datasets.html`` (interactive per-problem summary explorer)."""
    data_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neuroverse &mdash; Problem Explorer</title>
<style>{_SHARED_CSS}
tr.row-nosignal td {{ background: rgba(245, 158, 11, 0.10); }}
tr.row-saturated td {{ background: rgba(16, 185, 129, 0.09); }}
</style>
</head>
<body>
{_topbar_html("datasets")}
<main class="container">
  <section class="hero">
    <h1>EEG Problem Explorer ({len(payload["datasets"])} Scalp EEG Benchmark Tasks)</h1>
    <p>Turns the benchmark question around: for each classification problem, inspect the majority-class Default floor, the median and ceiling across the 72 distinct classifiers (or all 90 configurations), which paradigm wins, and how much signal was found beyond chance.</p>
  </section>

  <div class="tab-strip" id="dsTabStrip"></div>

  <div class="kpi-grid" id="dsKpiGrid"></div>

  <div class="toolbar">
    <div class="control-group">
      <label><strong>Metric:</strong>
        <select class="ctrl" id="dsMetricSelect">
          <option value="balacc" selected>Balanced Accuracy (%)</option>
          <option value="accuracy">Accuracy (%)</option>
          <option value="auroc">AUROC</option>
        </select>
      </label>
      <label><strong>Signal filter:</strong>
        <select class="ctrl" id="signalSelect">
          <option value="ALL" selected>All problems</option>
          <option value="nosignal">Low signal (&le; +5% over floor)</option>
          <option value="mid">Discriminative (+5% to 99%)</option>
          <option value="sat">Near ceiling (&ge; 99%)</option>
        </select>
      </label>
      <label class="chk"><input type="checkbox" id="dsIncludeVariants"> Include 18 variants (all 90 configs)</label>
    </div>
    <div class="control-group">
      <input type="search" class="ctrl" id="dsSearch" placeholder="Search problem or winner...">
      <button type="button" class="action-btn" id="exportDsCsv">Export CSV</button>
    </div>
  </div>

  <div class="table-card">
    <div class="table-scroll">
      <table class="data-table" id="dsTable">
        <thead>
          <tr>
            <th class="col-pos">#</th>
            <th class="col-name sortable" data-sort="name" data-dir="asc">Problem</th>
            <th class="sortable" data-sort="type" data-dir="asc">Type</th>
            <th class="sortable" data-sort="channels" data-dir="desc">Ch</th>
            <th class="sortable" data-sort="length" data-dir="desc">Length</th>
            <th class="sortable" data-sort="hz" data-dir="desc">Hz</th>
            <th class="sortable" data-sort="classes" data-dir="desc">Classes</th>
            <th class="sortable" data-sort="test_size" data-dir="desc">Test N</th>
            <th class="sortable" data-sort="floor" data-dir="asc">Default Floor</th>
            <th class="sortable" data-sort="median" data-dir="desc">Median</th>
            <th class="sortable" data-sort="best" data-dir="desc">Best</th>
            <th class="sortable" data-sort="winner" data-dir="asc">Best Algorithm</th>
            <th class="sortable" data-sort="gain" data-dir="asc">Gain over Floor</th>
            <th class="sortable" data-sort="spread" data-dir="desc">Spread</th>
            <th class="sortable" data-sort="completed" data-dir="desc">Done</th>
          </tr>
        </thead>
        <tbody id="dsBody"></tbody>
      </table>
    </div>
  </div>
  <p class="note">Click any problem row to inspect all completed classifiers ranked on that task. Amber rows mark problems where the best classifier gains &le;5 percentage points over the constant Default floor; green rows mark problems reaching &ge;99%.</p>
</main>
<div class="modal-backdrop" id="dsModal">
  <div class="modal-card">
    <div class="modal-head">
      <div id="dsModalTitle"></div>
      <button type="button" class="modal-close" id="dsModalClose">&times; Close</button>
    </div>
    <div class="modal-body" id="dsModalBody"></div>
  </div>
</div>
<script id="benchData" type="application/json">{data_json}</script>
<script>{_THEME_JS}
(function(){{
  var DATA = JSON.parse(document.getElementById("benchData").textContent);
  var dsMap = {{}};
  DATA.datasets.forEach(function(d, i) {{ dsMap[d.name] = i; }});

  var state = {{
    tab: "All",
    metric: "balacc",
    signal: "ALL",
    includeVariants: false,
    search: "",
    sortBy: "gain",
    sortDir: "asc"
  }};
  var lastDsCsv = {{ filename: "neuroverse_problems.csv", rows: [] }};

  var strip = document.getElementById("dsTabStrip");
  DATA.tabs.forEach(function(t) {{
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tab-btn" + (t.key === state.tab ? " active" : "");
    b.dataset.tab = t.key;
    b.innerHTML = t.label + ' <span class="tab-count">' + t.datasets.length + "</span>";
    b.addEventListener("click", function() {{
      state.tab = t.key;
      Array.prototype.forEach.call(strip.children, function(c) {{
        c.classList.toggle("active", c.dataset.tab === state.tab);
      }});
      render();
    }});
    strip.appendChild(b);
  }});

  document.getElementById("dsMetricSelect").addEventListener("change", function(e) {{ state.metric = e.target.value; render(); }});
  document.getElementById("signalSelect").addEventListener("change", function(e) {{ state.signal = e.target.value; render(); }});
  document.getElementById("dsIncludeVariants").addEventListener("change", function(e) {{ state.includeVariants = e.target.checked; render(); }});
  document.getElementById("dsSearch").addEventListener("input", function(e) {{ state.search = e.target.value.trim().toLowerCase(); render(); }});
  document.getElementById("exportDsCsv").addEventListener("click", function() {{
    if (window.eegDownloadCsv && lastDsCsv.rows.length) {{
      window.eegDownloadCsv(lastDsCsv.filename, lastDsCsv.rows);
    }}
  }});

  Array.prototype.forEach.call(document.querySelectorAll("#dsTable th.sortable"), function(th) {{
    th.addEventListener("click", function() {{
      var col = th.dataset.sort;
      if (state.sortBy === col) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      else {{ state.sortBy = col; state.sortDir = th.dataset.dir || "asc"; }}
      render();
    }});
  }});

  function esc(s) {{
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}

  function median(arr) {{
    if (!arr.length) return null;
    var s = arr.slice().sort(function(a, b) {{ return a - b; }});
    var mid = Math.floor(s.length / 2);
    return s.length % 2 ? s[mid] : 0.5 * (s[mid - 1] + s[mid]);
  }}

  // Per-problem leaderboard modal
  var dsModal = document.getElementById("dsModal");
  var dsModalTitle = document.getElementById("dsModalTitle");
  var dsModalBody = document.getElementById("dsModalBody");
  function closeDsModal() {{ dsModal.classList.remove("open"); }}
  document.getElementById("dsModalClose").addEventListener("click", closeDsModal);
  dsModal.addEventListener("click", function(e) {{ if (e.target === dsModal) closeDsModal(); }});
  document.addEventListener("keydown", function(e) {{ if (e.key === "Escape" && dsModal.classList.contains("open")) closeDsModal(); }});

  function openDsModal(ri) {{
    var d = DATA.datasets[ri];
    var flBa = DATA.default_floor.balacc[ri];
    dsModalTitle.innerHTML =
      '<div style="display:flex;align-items:center;gap:0.55rem;flex-wrap:wrap">' +
        '<strong style="font-size:1.12rem">' + esc(d.name) + '</strong>' +
        '<span class="brand-tag">' + esc(d.type) + '</span>' +
        '<span class="brand-tag">' + esc(d.availability) + '</span>' +
      '</div>' +
      '<div style="color:var(--muted);font-size:0.83rem;margin-top:0.25rem">' +
        d.channels + ' channels &middot; length ' + d.length + (d.hz ? ' (' + d.hz + ' Hz)' : '') +
        ' &middot; ' + d.classes + ' classes &middot; train N=' + d.train_size + ', test N=' + d.test_size +
        ' &middot; Default BalAcc floor: ' + (flBa === null ? '&mdash;' : (100 * flBa).toFixed(2) + '%') +
      '</div>';

    var entries = [];
    for (var ci = 0; ci < DATA.estimators.length; ci++) {{
      if (!state.includeVariants && !DATA.estimators[ci].is_canonical) continue;
      var ba = DATA.scores.balacc[ri][ci];
      if (ba === null) continue;
      entries.push({{
        meta: DATA.estimators[ci],
        balacc: ba,
        accuracy: DATA.scores.accuracy[ri][ci],
        auroc: DATA.scores.auroc[ri][ci],
        logloss: DATA.scores.logloss[ri][ci]
      }});
    }}
    entries.sort(function(a, b) {{
      var va = a[state.metric], vb = b[state.metric];
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return vb - va;
    }});

    var tHtml = '<div class="table-scroll"><table class="data-table"><thead><tr>' +
      '<th class="col-pos">#</th><th class="col-name">Algorithm</th><th>Balanced Acc</th><th>Gain vs Floor</th><th>Accuracy</th><th>AUROC</th><th>Log Loss</th>' +
      '</tr></thead><tbody>';
    entries.forEach(function(e, i) {{
      var g = flBa !== null ? (e.balacc - flBa) : null;
      tHtml += '<tr><td class="col-pos">' + (i + 1) + '</td>' +
        '<td class="col-name"><div class="alg-main"><span class="alg-name">' + esc(e.meta.name) + '</span> ' +
          '<span class="badge badge-' + esc(e.meta.paradigm) + '">' + esc(e.meta.paradigm_label) + '</span></div></td>' +
        '<td>' + (100 * e.balacc).toFixed(2) + '%</td>' +
        '<td>' + (g === null ? '&mdash;' : ((g >= 0 ? '+' : '') + (100 * g).toFixed(2) + '%')) + '</td>' +
        '<td>' + (e.accuracy === null ? '&mdash;' : (100 * e.accuracy).toFixed(2) + '%') + '</td>' +
        '<td>' + (e.auroc === null ? '&mdash;' : e.auroc.toFixed(4)) + '</td>' +
        '<td>' + (e.logloss === null ? '&mdash;' : e.logloss.toFixed(3)) + '</td></tr>';
    }});
    tHtml += '</tbody></table></div>';
    dsModalBody.innerHTML = tHtml;
    dsModal.classList.add("open");
  }}

  document.getElementById("dsBody").addEventListener("click", function(e) {{
    var tr = e.target.closest("tr[data-ri]");
    if (!tr) return;
    openDsModal(parseInt(tr.dataset.ri, 10));
  }});

  function render() {{
    var tabObj = DATA.tabs.filter(function(t) {{ return t.key === state.tab; }})[0] || DATA.tabs[0];
    var mat = DATA.scores[state.metric];
    var floors = DATA.default_floor[state.metric];
    var isPct = state.metric !== "auroc";

    var poolTotal = 0;
    for (var p0 = 0; p0 < DATA.estimators.length; p0++) {{
      if (state.includeVariants || DATA.estimators[p0].is_canonical) poolTotal++;
    }}

    var rows = tabObj.datasets.map(function(name) {{
      var ri = dsMap[name];
      var d = DATA.datasets[ri];
      var vals = [], best = -Infinity, worst = Infinity, winIdx = -1;
      for (var c = 0; c < DATA.estimators.length; c++) {{
        if (!state.includeVariants && !DATA.estimators[c].is_canonical) continue;
        var v = mat[ri][c];
        if (v !== null) {{
          vals.push(v);
          if (v > best) {{ best = v; winIdx = c; }}
          if (v < worst) worst = v;
        }}
      }}
      var fl = floors[ri];
      var med = median(vals);
      var bVal = vals.length ? best : null;
      var wEst = winIdx >= 0 ? DATA.estimators[winIdx] : null;
      return {{
        ri: ri,
        name: d.name,
        type: d.type,
        channels: d.channels,
        length: d.length,
        hz: d.hz,
        classes: d.classes,
        test_size: d.test_size,
        floor: fl,
        median: med,
        best: bVal,
        winner: wEst ? wEst.name : "",
        winnerMeta: wEst,
        gain: (bVal !== null && fl !== null) ? (bVal - fl) : null,
        spread: vals.length ? (best - worst) : null,
        completed: vals.length
      }};
    }});

    var lowSig = rows.filter(function(r) {{ return r.gain !== null && r.gain <= 0.05; }}).length;
    var satCnt = rows.filter(function(r) {{ return r.best !== null && r.best >= 0.99; }}).length;
    var parWins = {{}};
    rows.forEach(function(r) {{
      if (r.winnerMeta) parWins[r.winnerMeta.paradigm_label] = (parWins[r.winnerMeta.paradigm_label] || 0) + 1;
    }});
    var parSummary = Object.keys(parWins).map(function(k) {{ return k + ": " + parWins[k]; }}).join(" &middot; ");

    document.getElementById("dsKpiGrid").innerHTML =
      '<div class="kpi-card"><div class="kpi-label">Problems in Scope</div><div class="kpi-value">' + rows.length + '</div><div class="kpi-sub">Up to ' + poolTotal + (state.includeVariants ? ' configurations' : ' distinct classifiers') + ' evaluated per problem</div></div>' +
      '<div class="kpi-card"><div class="kpi-label">Winning Paradigm Breakdown</div><div class="kpi-value" style="font-size:0.95rem">' + (parSummary || "&mdash;") + '</div><div class="kpi-sub">Count of problem ceilings held by each paradigm</div></div>' +
      '<div class="kpi-card"><div class="kpi-label">Low-Signal Tasks (&le;+5%)</div><div class="kpi-value">' + lowSig + '</div><div class="kpi-sub">Shaded amber &mdash; hardest open EEG problems</div></div>' +
      '<div class="kpi-card"><div class="kpi-label">Near-Ceiling Tasks (&ge;99%)</div><div class="kpi-value">' + satCnt + '</div><div class="kpi-sub">Shaded green &mdash; saturated benchmarks</div></div>';

    var filtered = rows.filter(function(r) {{
      if (state.signal === "nosignal" && !(r.gain !== null && r.gain <= 0.05)) return false;
      if (state.signal === "sat" && !(r.best !== null && r.best >= 0.99)) return false;
      if (state.signal === "mid" && ((r.gain !== null && r.gain <= 0.05) || (r.best !== null && r.best >= 0.99))) return false;
      if (state.search) {{
        var hay = (r.name + " " + r.type + " " + r.winner + " " + (r.winnerMeta ? r.winnerMeta.paradigm_label : "")).toLowerCase();
        if (hay.indexOf(state.search) === -1) return false;
      }}
      return true;
    }});

    var dir = state.sortDir === "asc" ? 1 : -1;
    filtered.sort(function(a, b) {{
      var va = a[state.sortBy], vb = b[state.sortBy];
      if (typeof va === "string") return va.localeCompare(vb) * dir;
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return (va - vb) * dir;
    }});

    function fmt(v) {{
      if (v === null || isNaN(v)) return "&mdash;";
      return isPct ? (100 * v).toFixed(2) + "%" : v.toFixed(4);
    }}

    var csvRows = [["Problem", "Type", "Channels", "Length", "Hz", "Classes", "Test_N", "Default_Floor", "Median", "Best", "Best_Algorithm", "Best_Paradigm", "Gain_over_Floor", "Spread", "Completed"]];
    var html = "";
    filtered.forEach(function(r, idx) {{
      var sigCls = (r.gain !== null && r.gain <= 0.05) ? " row-nosignal" : ((r.best !== null && r.best >= 0.99) ? " row-saturated" : "");
      var winCell = r.winnerMeta
        ? ('<span style="font-weight:600">' + esc(r.winner) + '</span> <span class="badge badge-' + esc(r.winnerMeta.paradigm) + '">' + esc(r.winnerMeta.paradigm_label) + "</span>")
        : "&mdash;";
      html += '<tr class="clickable-row' + sigCls + '" data-ri="' + r.ri + '" title="Click to inspect all ' + r.completed + ' completed algorithms on ' + esc(r.name) + '">' +
        '<td class="col-pos">' + (idx + 1) + '</td>' +
        '<td class="col-name"><strong>' + esc(r.name) + '</strong></td>' +
        '<td><span class="brand-tag">' + esc(r.type) + '</span></td>' +
        '<td>' + r.channels + '</td>' +
        '<td>' + r.length + '</td>' +
        '<td>' + (r.hz === null ? "&mdash;" : r.hz) + '</td>' +
        '<td>' + r.classes + '</td>' +
        '<td>' + r.test_size + '</td>' +
        '<td>' + fmt(r.floor) + '</td>' +
        '<td>' + fmt(r.median) + '</td>' +
        '<td class="best-cell">' + fmt(r.best) + '</td>' +
        '<td style="text-align:left">' + winCell + '</td>' +
        '<td>' + (r.gain === null ? "&mdash;" : ((r.gain >= 0 ? "+" : "") + fmt(r.gain))) + '</td>' +
        '<td>' + fmt(r.spread) + '</td>' +
        '<td>' + r.completed + "/" + DATA.estimators.length + '</td>' +
        '</tr>';
      csvRows.push([
        r.name, r.type, r.channels, r.length, r.hz === null ? "" : r.hz, r.classes, r.test_size,
        r.floor === null ? "" : r.floor.toFixed(5),
        r.median === null ? "" : r.median.toFixed(5),
        r.best === null ? "" : r.best.toFixed(5),
        r.winner, r.winnerMeta ? r.winnerMeta.paradigm_label : "",
        r.gain === null ? "" : r.gain.toFixed(5),
        r.spread === null ? "" : r.spread.toFixed(5),
        r.completed
      ]);
    }});
    document.getElementById("dsBody").innerHTML = html;
    lastDsCsv = {{
      filename: "neuroverse_problems_" + state.tab.toLowerCase() + "_" + state.metric + ".csv",
      rows: csvRows
    }};
  }}

  render();
}})();
</script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
