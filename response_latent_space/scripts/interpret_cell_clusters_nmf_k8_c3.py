from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


RUN_TAG = "nmf_k8_c3"
TOP_NS = (10, 20)


@dataclass(frozen=True)
class Paths:
    root: Path
    cell_clusters: Path
    marker_drugs: Path
    cell_sensitivity_summary: Path
    cell_metadata: Path
    drug_metadata: Path
    outdir: Path


def bh_fdr(pvals: pd.Series) -> pd.Series:
    """Benjamini-Hochberg FDR without external dependencies."""
    if pvals.empty:
        return pvals.copy()
    n = len(pvals)
    order = np.argsort(pvals.values)
    ranked = pvals.values[order]
    q = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = ranked[i] * n / rank
        prev = min(prev, val)
        q[i] = prev
    q = np.minimum(q, 1.0)
    out = np.empty(n, dtype=float)
    out[order] = q
    return pd.Series(out, index=pvals.index)


def split_tokens(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [t.strip() for t in str(value).split("|") if t and t.strip()]


def normalize_gs_id(value: object) -> str | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.startswith("GS."):
        return s
    if s.isdigit():
        return f"GS.{int(s):04d}"
    return None


def resolve_paths(repo_root: Path) -> Paths:
    rls = repo_root / "response_latent_space"
    outdir = rls / "results" / "biovalidation" / RUN_TAG
    outdir.mkdir(parents=True, exist_ok=True)
    return Paths(
        root=rls,
        cell_clusters=rls / "results" / "clustering" / "cell_clusters_nmf_k8_c3.csv",
        marker_drugs=rls / "results" / "interpretation" / "cell_cluster_marker_drugs_nmf_k8_c3.csv",
        cell_sensitivity_summary=rls / "results" / "interpretation" / "cell_cluster_sensitivity_summary_nmf_k8_c3.csv",
        cell_metadata=rls / "data" / "metadata" / "cell_metadata.csv",
        drug_metadata=rls / "data" / "metadata" / "drug_metadata.csv",
        outdir=outdir,
    )


def enrich_terms(
    marker_df: pd.DataFrame,
    universe_drugs: set[str],
    drug_meta: pd.DataFrame,
    label_col: str,
) -> pd.DataFrame:
    rows = []
    label_map = {}
    for _, r in drug_meta.iterrows():
        label_map[r["drug_id"]] = set(split_tokens(r[label_col]))

    all_terms = sorted(set(t for terms in label_map.values() for t in terms))
    if not all_terms:
        return pd.DataFrame(columns=["cluster", "top_n", "label_type", "term", "a", "b", "c", "d", "odds_ratio", "p_value", "q_value"])

    for cluster, cdf in marker_df.groupby("cluster"):
        for top_n in TOP_NS:
            selected = set(cdf.loc[cdf["rank"] <= top_n, "drug_id"].tolist())
            selected &= universe_drugs
            non_selected = universe_drugs - selected
            if not selected:
                continue

            block = []
            for term in all_terms:
                in_sel = sum(1 for d in selected if term in label_map.get(d, set()))
                out_sel = len(selected) - in_sel
                in_bg = sum(1 for d in non_selected if term in label_map.get(d, set()))
                out_bg = len(non_selected) - in_bg

                if in_sel == 0:
                    continue

                odds_ratio, p_value = fisher_exact([[in_sel, out_sel], [in_bg, out_bg]], alternative="greater")
                block.append(
                    {
                        "cluster": int(cluster),
                        "top_n": int(top_n),
                        "label_type": label_col,
                        "term": term,
                        "a": int(in_sel),
                        "b": int(out_sel),
                        "c": int(in_bg),
                        "d": int(out_bg),
                        "odds_ratio": float(odds_ratio) if np.isfinite(odds_ratio) else np.inf,
                        "p_value": float(p_value),
                    }
                )

            if block:
                bdf = pd.DataFrame(block)
                bdf["q_value"] = bh_fdr(bdf["p_value"])
                rows.append(bdf)

    if not rows:
        return pd.DataFrame(columns=["cluster", "top_n", "label_type", "term", "a", "b", "c", "d", "odds_ratio", "p_value", "q_value"])
    return pd.concat(rows, ignore_index=True).sort_values(["cluster", "top_n", "q_value", "p_value", "term"])


def top_terms(enrich_df: pd.DataFrame, cluster: int, top_n: int, label_type: str, n: int = 3) -> list[str]:
    sdf = enrich_df[
        (enrich_df["cluster"] == cluster)
        & (enrich_df["top_n"] == top_n)
        & (enrich_df["label_type"] == label_type)
        & (enrich_df["q_value"] <= 0.1)
    ].sort_values(["q_value", "p_value", "odds_ratio"], ascending=[True, True, False])
    return sdf["term"].head(n).tolist()


def robust_jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    p = resolve_paths(repo_root)

    cell_clusters = pd.read_csv(p.cell_clusters, index_col=0).rename_axis("cell_line_id").reset_index()
    marker = pd.read_csv(p.marker_drugs)
    sens = pd.read_csv(p.cell_sensitivity_summary)
    cell_meta = pd.read_csv(p.cell_metadata)
    drug_meta = pd.read_csv(p.drug_metadata)

    # TODO 1: audit cluster sizes
    cluster_size = sens[["cluster", "n_cells", "mean_sensitivity_overall"]].copy()
    cluster_size["singleton_cluster"] = cluster_size["n_cells"] < 2
    cluster_size["interpretation_mode"] = np.where(cluster_size["singleton_cluster"], "narrative_only_case_report", "full_program_interpretation")
    cluster_size.to_csv(p.outdir / "cluster_size_audit_nmf_k8_c3.csv", index=False)

    # TODO 2: join cell metadata
    meta = cell_meta.copy()
    if "cell_line_id" not in meta.columns:
        meta["cell_line_id"] = None
    meta["cell_line_id_norm"] = meta["cell_line_id"].map(normalize_gs_id)
    if "tbl2GS.GsID" in meta.columns:
        from_tbl = meta["tbl2GS.GsID"].map(normalize_gs_id)
        meta["cell_line_id_norm"] = meta["cell_line_id_norm"].fillna(from_tbl)
    meta = meta.dropna(subset=["cell_line_id_norm"]).copy()
    meta = meta.drop_duplicates(subset=["cell_line_id_norm"])

    cell_cluster_meta = cell_clusters.merge(
        meta,
        left_on="cell_line_id",
        right_on="cell_line_id_norm",
        how="left",
    )
    cell_cluster_meta.to_csv(p.outdir / "cell_cluster_metadata_join_nmf_k8_c3.csv", index=False)

    meta_rows = []
    for cluster, cdf in cell_cluster_meta.groupby("cluster"):
        n_cells = int(cdf.shape[0])
        mgmt = cdf.get("MGMTstatusCulture", pd.Series(dtype=object)).fillna("Unknown").value_counts()
        idh = cdf.get("IDHMutation", pd.Series(dtype=object)).fillna("Unknown").value_counts()
        meta_rows.append(
            {
                "cluster": int(cluster),
                "n_cells": n_cells,
                "mgmt_top_label": mgmt.index[0] if len(mgmt) else "Unknown",
                "mgmt_top_fraction": float(mgmt.iloc[0] / n_cells) if len(mgmt) and n_cells else np.nan,
                "idh_top_label": idh.index[0] if len(idh) else "Unknown",
                "idh_top_fraction": float(idh.iloc[0] / n_cells) if len(idh) and n_cells else np.nan,
            }
        )
    meta_summary = pd.DataFrame(meta_rows).sort_values("cluster")
    meta_summary.to_csv(p.outdir / "cluster_cell_metadata_summary_nmf_k8_c3.csv", index=False)

    # TODO 3 + 4: marker sets, enrichment, robustness
    universe = set(drug_meta["drug_id"].dropna().astype(str).tolist())
    marker = marker[marker["drug_id"].isin(universe)].copy()

    moa_enrich = enrich_terms(marker, universe, drug_meta, "moa")
    target_enrich = enrich_terms(marker, universe, drug_meta, "target")
    moa_enrich.to_csv(p.outdir / "cluster_marker_enrichment_moa_nmf_k8_c3.csv", index=False)
    target_enrich.to_csv(p.outdir / "cluster_marker_enrichment_target_nmf_k8_c3.csv", index=False)

    # token overlap robustness between top10 and top20
    drug_to_moa = {
        r["drug_id"]: set(split_tokens(r["moa"]))
        for _, r in drug_meta.iterrows()
    }
    drug_to_target = {
        r["drug_id"]: set(split_tokens(r["target"]))
        for _, r in drug_meta.iterrows()
    }

    robust_rows = []
    for cluster, cdf in marker.groupby("cluster"):
        d10 = set(cdf.loc[cdf["rank"] <= 10, "drug_id"])
        d20 = set(cdf.loc[cdf["rank"] <= 20, "drug_id"])
        moa10 = set(t for d in d10 for t in drug_to_moa.get(d, set()))
        moa20 = set(t for d in d20 for t in drug_to_moa.get(d, set()))
        tgt10 = set(t for d in d10 for t in drug_to_target.get(d, set()))
        tgt20 = set(t for d in d20 for t in drug_to_target.get(d, set()))
        moa_top3_10 = top_terms(moa_enrich, int(cluster), 10, "moa", n=3)
        moa_top3_20 = top_terms(moa_enrich, int(cluster), 20, "moa", n=3)
        tgt_top3_10 = top_terms(target_enrich, int(cluster), 10, "target", n=3)
        tgt_top3_20 = top_terms(target_enrich, int(cluster), 20, "target", n=3)

        robust_rows.append(
            {
                "cluster": int(cluster),
                "n_top10": len(d10),
                "n_top20": len(d20),
                "jaccard_drugs_top10_vs_top20": robust_jaccard(d10, d20),
                "jaccard_moa_tokens_top10_vs_top20": robust_jaccard(moa10, moa20),
                "jaccard_target_tokens_top10_vs_top20": robust_jaccard(tgt10, tgt20),
                "overlap_top3_moa_terms": robust_jaccard(moa_top3_10, moa_top3_20),
                "overlap_top3_target_terms": robust_jaccard(tgt_top3_10, tgt_top3_20),
                "top3_moa_terms_top10": "|".join(moa_top3_10),
                "top3_moa_terms_top20": "|".join(moa_top3_20),
                "top3_target_terms_top10": "|".join(tgt_top3_10),
                "top3_target_terms_top20": "|".join(tgt_top3_20),
            }
        )
    robustness = pd.DataFrame(robust_rows).sort_values("cluster")
    robustness.to_csv(p.outdir / "cluster_robustness_top10_vs_top20_nmf_k8_c3.csv", index=False)

    # TODO 5: narrative
    mean_sens = sens.set_index("cluster")["mean_sensitivity_overall"].to_dict()
    size_map = sens.set_index("cluster")["n_cells"].to_dict()
    singleton_map = cluster_size.set_index("cluster")["singleton_cluster"].to_dict()

    def pick_mechanism(cluster_id: int) -> tuple[str, str]:
        top_moa = top_terms(moa_enrich, cluster_id, 20, "moa", n=4)
        top_tgt = top_terms(target_enrich, cluster_id, 20, "target", n=4)
        joined = " ".join(top_moa + top_tgt).lower()
        if any(k in joined for k in ["egfr", "raf", "pdgfr", "src", "kit", "tyrosine kinase", "mtor"]):
            return "selective kinase/signaling-axis", ", ".join(top_moa[:3] or top_tgt[:3])
        if len(top_moa) >= 3:
            return "broad multi-class cytotoxic/proliferative", ", ".join(top_moa[:3])
        return "narrow/uncertain", ", ".join((top_moa[:2] + top_tgt[:2])[:3])

    lines = []
    lines.append("# Cluster interpretation: NMF k=8, c=3\n")
    lines.append("## Caveat\n")
    lines.append("- Cluster 2 has one cell line (n=1) and is treated as case-report only, not a stable program-level cluster.\n")

    for cluster in sorted(marker["cluster"].unique()):
        cluster = int(cluster)
        cdf = marker[marker["cluster"] == cluster].sort_values("rank")
        top10_drugs = ", ".join(cdf["drug_id"].head(10).tolist())
        mode = "case_report_only" if bool(singleton_map.get(cluster, False)) else "full_program"
        mech, support_terms = pick_mechanism(cluster)
        sens_txt = f"{mean_sens.get(cluster, np.nan):.4f}"

        if mode == "case_report_only":
            one_sentence = (
                f"Cluster {cluster} is a singleton case (n=1) with apparent {mech} vulnerability signature "
                f"({support_terms}), but this should be interpreted as hypothesis-generating only."
            )
        else:
            one_sentence = (
                f"Cluster {cluster} is characterized by a {mech} response program supported by enriched terms "
                f"({support_terms}) and a mean overall sensitivity score of {sens_txt}."
            )

        lines.append(f"\n## Cluster {cluster}\n")
        lines.append(f"- n_cells: {int(size_map.get(cluster, 0))}\n")
        lines.append(f"- interpretation_mode: {mode}\n")
        lines.append(f"- top10_marker_drugs: {top10_drugs}\n")
        lines.append(f"- one_sentence: {one_sentence}\n")

        m20 = moa_enrich[(moa_enrich["cluster"] == cluster) & (moa_enrich["top_n"] == 20)].sort_values("q_value").head(8)
        t20 = target_enrich[(target_enrich["cluster"] == cluster) & (target_enrich["top_n"] == 20)].sort_values("q_value").head(8)
        if not m20.empty:
            lines.append("- top_moa_terms_top20:\n")
            for _, r in m20.iterrows():
                lines.append(f"  - {r['term']} (a={int(r['a'])}, OR={r['odds_ratio']:.2f}, q={r['q_value']:.3g})\n")
        if not t20.empty:
            lines.append("- top_target_terms_top20:\n")
            for _, r in t20.iterrows():
                lines.append(f"  - {r['term']} (a={int(r['a'])}, OR={r['odds_ratio']:.2f}, q={r['q_value']:.3g})\n")

    (p.outdir / "cluster_interpretation_nmf_k8_c3.md").write_text("".join(lines), encoding="utf-8")

    print(f"Wrote outputs to: {p.outdir}")


if __name__ == "__main__":
    main()

