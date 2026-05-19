"""
Distribution figures (proof of concept) for the True-Behavior Profile.

Produces three figures supporting the FRAME paper's category-error / construct-
dissociation argument:

  Fig 1 — Paired dot plot (EP top panel / CFI bottom panel) with the var-ratio
          annotation. The headline visual: EP is essentially constant across 6
          (target × condition) cells; CFI varies 22.6× more.

  Fig 2 — Per-cell distribution (raincloud-style) of per-article CFI scores.
          Shows that scalar reporting hides substantial within-cell variance.

  Fig 3 — True-Behavior Profile heatmap. The matrix-form summary that captures
          the central methodological proposal.

Visual style matches existing figures/ palette (BG_COLOR, SONNET_COLOR, GPT_COLOR).
600 DPI exports.

Citations for plot choices in METHODS.md:
  - Allen et al. 2019, Wellcome Open Research (raincloud plots)
  - Tufte 1983, 1990 (small multiples / visual rhetoric)
  - arXiv:2303.17709 (defensive raincloud-plot design)
  - Reuel et al. 2025, NeurIPS D&B (recommendation: capture inherent variability
    without single-point aggregation)
"""

from __future__ import annotations
import json, pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ── Palette (shared with other figures/) ──
BG_COLOR     = "#FAF8F5"
TEXT_DARK    = "#2D2D2D"
TEXT_MID     = "#999999"
GRID_COLOR   = "#E8E4DE"
SONNET_COLOR = "#C55A11"
SONNET_LIGHT = "#F0D5BC"
GPT_COLOR    = "#3B6FA0"
GPT_LIGHT    = "#B8D4EC"
EP_ACCENT    = "#5C8D89"
CFI_ACCENT   = "#A33D3D"

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGS = ROOT / "figures"

CONDITIONS = ["baseline", "ablation", "full"]
TARGETS = ["sonnet", "gpt"]


# ============================================================================
# Data loaders
# ============================================================================

def load_tbp() -> dict:
    """Load the True-Behavior Profile JSON produced by true_behavior_profile.py."""
    p = DATA / "true_behavior_profile.json"
    if not p.exists():
        raise SystemExit(f"Missing {p}; run analysis/true_behavior_profile.py first.")
    return json.loads(p.read_text())


def load_decomp() -> pd.DataFrame:
    """Load the per-(article × target × judge × condition × bias_type) decomposition."""
    p = DATA / "long_decomp.parquet"
    if not p.exists():
        raise SystemExit(f"Missing {p}; run analysis/absorption_generation.py first.")
    return pd.read_parquet(p)


def per_article_cfi(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (article, target, judge, condition), compute per-article CFI:
      CFI_article = absorbed / (absorbed + resisted)  (when source_present > 0)
    """
    df = df[df["threshold"] == 5].copy()
    grouped = df.groupby(["article_id", "target", "judge", "condition"], observed=False)
    rows = []
    for (aid, tgt, jdg, cond), sub in grouped:
        absorbed = int(sub["absorbed"].sum())
        resisted = int(sub["resisted"].sum())
        sp_total = absorbed + resisted
        if sp_total > 0:
            cfi_a = absorbed / sp_total
        else:
            cfi_a = np.nan
        rows.append({"article_id": aid, "target": tgt, "judge": jdg,
                     "condition": cond, "cfi": cfi_a, "n_source": sp_total})
    return pd.DataFrame(rows)


def cell_summary(tbp: dict) -> pd.DataFrame:
    """Build a flat (target, condition) × {EP, CFI_opus, CFI_gpt5} summary."""
    rows = []
    for cell_key, cell in tbp["profile"].items():
        tgt, cond = cell_key.split("__")
        rows.append({
            "target": tgt,
            "condition": cond,
            "EP": cell["EP"].get("EP"),
            "EP_lo": cell["EP"].get("EP_ci_low"),
            "EP_hi": cell["EP"].get("EP_ci_high"),
            "CFI_opus": cell["CFI_per_judge"]["opus"].get("CFI_absorption_rate"),
            "CFI_gpt5": cell["CFI_per_judge"]["gpt5"].get("CFI_absorption_rate"),
        })
    return pd.DataFrame(rows)


# ============================================================================
# Figure 1 — Paired dot plot (EP / CFI dissociation)
# ============================================================================

def figure_1_paired_dotplot(tbp: dict, out_path: pathlib.Path):
    """
    Two stacked panels sharing the x-axis:
      Top:    EP per (target, condition) cell, with bootstrap CI bars
      Bottom: CFI per (target, condition, judge) cell

    Annotations: var ratio CCDR(CFI, EP) = N×, Pearson r and p.
    """
    summary = cell_summary(tbp)
    dissoc = tbp["dissociation"]

    fig, axes = plt.subplots(2, 1, figsize=(11, 7),
                             sharex=True,
                             gridspec_kw={"height_ratios": [1, 1.2]})
    fig.patch.set_facecolor(BG_COLOR)

    # Cell ordering: sonnet/baseline, sonnet/ablation, sonnet/full,
    #                gpt/baseline, gpt/ablation, gpt/full
    cell_order = []
    cell_labels = []
    for tgt in TARGETS:
        for cond in CONDITIONS:
            cell_order.append((tgt, cond))
            tgt_label = "Sonnet" if tgt == "sonnet" else "GPT-4.1"
            cell_labels.append(f"{tgt_label}\n{cond}")
    xs = np.arange(len(cell_order))

    # --- Top panel: EP ---
    ax = axes[0]
    ax.set_facecolor(BG_COLOR)
    for i, (tgt, cond) in enumerate(cell_order):
        row = summary[(summary.target == tgt) & (summary.condition == cond)].iloc[0]
        color = SONNET_COLOR if tgt == "sonnet" else GPT_COLOR
        ax.errorbar(i, row["EP"],
                    yerr=[[row["EP"] - row["EP_lo"]], [row["EP_hi"] - row["EP"]]],
                    fmt="o", color=color, markersize=11, ecolor=color, alpha=0.9,
                    capsize=4, linewidth=1.5)
        ax.annotate(f"{row['EP']:.3f}", xy=(i, row["EP"]),
                    xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=9, color=TEXT_DARK)
    ax.set_ylabel("EP\nEngagement Parity", fontsize=11, color=TEXT_DARK,
                  fontweight="600")
    ax.set_ylim(0.85, 1.05)
    ax.axhline(1.0, color=TEXT_MID, linestyle="--", linewidth=0.5, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(TEXT_MID)
    ax.spines["bottom"].set_color(TEXT_MID)
    ax.tick_params(axis="y", colors=TEXT_DARK, labelsize=9)
    ax.tick_params(axis="x", colors=TEXT_DARK, labelsize=10)

    # var(EP) annotation in top panel
    var_ep = dissoc.get("variance_EP", float("nan"))
    ax.text(0.99, 0.07, f"var(EP) = {var_ep:.5f}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color=TEXT_MID, style="italic")

    # --- Bottom panel: CFI per judge ---
    ax = axes[1]
    ax.set_facecolor(BG_COLOR)
    for i, (tgt, cond) in enumerate(cell_order):
        row = summary[(summary.target == tgt) & (summary.condition == cond)].iloc[0]
        # Two judges side-by-side at this cell
        for j, (judge, jcolor, marker) in enumerate(
            [("opus", "#7B3F00", "o"), ("gpt5", "#1E4067", "^")]
        ):
            cfi_val = row[f"CFI_{judge}"]
            x_offset = -0.13 + j * 0.26
            ax.scatter(i + x_offset, cfi_val * 100,
                       color=jcolor, s=80, marker=marker, zorder=3,
                       edgecolors="white", linewidths=1.0)
            if i == 0:  # legend label only on first
                pass
        # Connect the two judges
        ax.plot([i - 0.13, i + 0.13],
                [row["CFI_opus"] * 100, row["CFI_gpt5"] * 100],
                color=TEXT_MID, alpha=0.4, linewidth=0.8, zorder=1)

    ax.set_ylabel("CFI\nContent Framing Inheritance\n(% absorbed)",
                  fontsize=11, color=TEXT_DARK, fontweight="600")
    ax.set_ylim(0, 35)
    ax.set_xticks(xs)
    ax.set_xticklabels(cell_labels, fontsize=9, color=TEXT_DARK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(TEXT_MID)
    ax.spines["bottom"].set_color(TEXT_MID)
    ax.tick_params(axis="y", colors=TEXT_DARK, labelsize=9)

    # var(CFI) annotation
    var_cfi = dissoc.get("variance_CFI", float("nan"))
    ax.text(0.99, 0.93, f"var(CFI) = {var_cfi:.5f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=9, color=TEXT_MID, style="italic")

    # Cross-construct dispersion ratio annotation (the headline)
    ratio = dissoc.get("variance_ratio_CFI_to_EP", float("nan"))
    pearson_r = dissoc.get("pearson_r_EP_CFI", float("nan"))
    pearson_p = dissoc.get("pearson_p_EP_CFI", float("nan"))
    callout_text = (f"CCDR(CFI, EP) = {ratio:.1f}×\n"
                    f"r(EP, CFI) = {pearson_r:+.2f}, p = {pearson_p:.2f}")
    ax.text(0.02, 0.93, callout_text,
            transform=ax.transAxes, ha="left", va="top",
            fontsize=10, color=TEXT_DARK, fontweight="700",
            bbox=dict(boxstyle="round,pad=0.5",
                      facecolor=BG_COLOR, edgecolor=TEXT_MID, linewidth=0.8))

    # Legend for judges
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#7B3F00",
               markersize=9, label="Opus 4.6 judge"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#1E4067",
               markersize=9, label="GPT-5 judge"),
    ]
    ax.legend(handles=legend_elements, loc="lower center",
              bbox_to_anchor=(0.5, -0.32), ncol=2,
              fontsize=9, frameon=True, facecolor=BG_COLOR, edgecolor=TEXT_MID)

    # Title
    fig.suptitle("EP and CFI dissociate: scalar collapse hides distinct constructs",
                 fontsize=14, fontweight="700", color=TEXT_DARK, y=0.98)
    fig.text(0.5, 0.93,
             "Engagement parity is essentially constant across all 6 cells; "
             "content framing inheritance varies dramatically. "
             "Same data, two methodologies, different conclusions.",
             ha="center", fontsize=9.5, color=TEXT_DARK, style="italic")

    plt.tight_layout(rect=[0, 0.02, 1, 0.92])
    fig.savefig(out_path, dpi=600, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved {out_path}")


# ============================================================================
# Figure 2 — Per-cell distribution of per-article CFI (raincloud-style)
# ============================================================================

def figure_2_distribution_per_cell(df_pa: pd.DataFrame, out_path: pathlib.Path):
    """
    For each (target, condition, judge) cell, show:
      - Half-violin (KDE of per-article CFI)
      - Box plot
      - Jittered raw points

    Panels: 2 rows (judges) × 6 columns (target × condition)
    """
    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    fig.patch.set_facecolor(BG_COLOR)

    cell_order = []
    cell_labels = []
    for tgt in TARGETS:
        for cond in CONDITIONS:
            cell_order.append((tgt, cond))
            tgt_label = "Sonnet" if tgt == "sonnet" else "GPT-4.1"
            cell_labels.append(f"{tgt_label}\n{cond}")
    xs = np.arange(len(cell_order))

    rng = np.random.default_rng(0)
    for ax_idx, judge in enumerate(["opus", "gpt5"]):
        ax = axes[ax_idx]
        ax.set_facecolor(BG_COLOR)
        for i, (tgt, cond) in enumerate(cell_order):
            sub = df_pa[(df_pa["target"] == tgt) &
                        (df_pa["condition"] == cond) &
                        (df_pa["judge"] == judge) &
                        (df_pa["cfi"].notna())]
            cfi_vals = sub["cfi"].values * 100
            if len(cfi_vals) == 0:
                continue
            color = SONNET_COLOR if tgt == "sonnet" else GPT_COLOR
            light = SONNET_LIGHT if tgt == "sonnet" else GPT_LIGHT

            # Half-violin
            try:
                parts = ax.violinplot([cfi_vals], positions=[i],
                                       widths=0.6, showmeans=False,
                                       showmedians=False, showextrema=False)
                for body in parts["bodies"]:
                    # Make it a half-violin (right side only)
                    m = np.mean(body.get_paths()[0].vertices[:, 0])
                    body.get_paths()[0].vertices[:, 0] = np.clip(
                        body.get_paths()[0].vertices[:, 0], m, np.inf)
                    body.set_facecolor(light)
                    body.set_edgecolor(color)
                    body.set_alpha(0.7)
            except Exception:
                pass

            # Boxplot (slim)
            bp = ax.boxplot([cfi_vals], positions=[i - 0.18], widths=0.12,
                             showfliers=False, patch_artist=True,
                             boxprops=dict(facecolor=color, edgecolor=color, alpha=0.7),
                             medianprops=dict(color="white", linewidth=1.5),
                             whiskerprops=dict(color=color),
                             capprops=dict(color=color))

            # Jittered points
            jitter = rng.uniform(-0.05, 0.05, len(cfi_vals))
            ax.scatter(np.full(len(cfi_vals), i - 0.32) + jitter,
                       cfi_vals, color=color, alpha=0.4, s=10, zorder=2,
                       edgecolors="none")

        ax.set_ylabel(f"CFI per article (%)\n[{judge.upper()} judge]",
                       fontsize=11, color=TEXT_DARK, fontweight="600")
        ax.set_ylim(-5, 105)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(TEXT_MID)
        ax.spines["bottom"].set_color(TEXT_MID)
        ax.tick_params(axis="y", colors=TEXT_DARK, labelsize=9)
        if ax_idx == 1:
            ax.set_xticks(xs)
            ax.set_xticklabels(cell_labels, fontsize=9, color=TEXT_DARK)
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.5, alpha=0.5)
        ax.set_axisbelow(True)

    fig.suptitle("Per-article CFI distributions hide behind cell means",
                 fontsize=14, fontweight="700", color=TEXT_DARK, y=0.98)
    fig.text(0.5, 0.94,
             "Each cell's mean (e.g., Sonnet × baseline = 27.8% CFI under Opus) "
             "summarizes a substantial within-cell distribution. "
             "Distribution-based reporting reveals where models behave consistently vs noisily.",
             ha="center", fontsize=9.5, color=TEXT_DARK, style="italic")

    plt.tight_layout(rect=[0, 0.02, 1, 0.92])
    fig.savefig(out_path, dpi=600, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved {out_path}")


# ============================================================================
# Figure 3 — True-Behavior Profile heatmap
# ============================================================================

def figure_3_tbp_heatmap(tbp: dict, out_path: pathlib.Path):
    """
    The TBP matrix-form summary: rows = constructs, columns = (target × condition).
    Each cell shows the metric value with color encoding magnitude.
    """
    summary = cell_summary(tbp)
    cell_labels = []
    for tgt in TARGETS:
        for cond in CONDITIONS:
            tgt_label = "Sonnet" if tgt == "sonnet" else "GPT-4.1"
            cell_labels.append(f"{tgt_label}\n{cond}")

    # Pull LCA from the TBP json
    rows = []
    for cell_key, cell in tbp["profile"].items():
        tgt, cond = cell_key.split("__")
        rows.append({
            "target": tgt,
            "condition": cond,
            "EP": cell["EP"].get("EP", float("nan")),
            "CFI_opus": cell["CFI_per_judge"]["opus"].get("CFI_absorption_rate", float("nan")),
            "CFI_gpt5": cell["CFI_per_judge"]["gpt5"].get("CFI_absorption_rate", float("nan")),
            "LCA_AllSides": cell["LCA"]["vs_AllSides"]["3class_accuracy"],
            "LCA_Opus": cell["LCA"]["vs_Opus"]["3class_accuracy"],
            "LCA_GPT5": cell["LCA"]["vs_GPT5"]["3class_accuracy"],
        })
    df = pd.DataFrame(rows)
    df["cell"] = df["target"] + "__" + df["condition"]
    df = df.set_index("cell")
    cell_order_keys = [f"{t}__{c}" for t in TARGETS for c in CONDITIONS]
    df = df.loc[cell_order_keys]

    metrics = ["EP", "CFI_opus", "CFI_gpt5", "LCA_AllSides", "LCA_Opus", "LCA_GPT5"]
    metric_labels = ["EP", "CFI (Opus)", "CFI (GPT-5)",
                     "LCA (AllSides)", "LCA (Opus)", "LCA (GPT-5)"]

    matrix = df[metrics].to_numpy().T  # rows = metrics, cols = cells

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Use a normalized colormap per row (each metric on its own scale)
    norm_matrix = np.zeros_like(matrix)
    for i in range(matrix.shape[0]):
        row = matrix[i]
        if np.nanmax(row) - np.nanmin(row) > 0:
            norm_matrix[i] = (row - np.nanmin(row)) / (np.nanmax(row) - np.nanmin(row))
        else:
            norm_matrix[i] = 0.5

    im = ax.imshow(norm_matrix, cmap="RdYlBu_r", aspect="auto", alpha=0.6)

    ax.set_xticks(range(len(cell_order_keys)))
    ax.set_xticklabels(cell_labels, fontsize=9.5, color=TEXT_DARK)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metric_labels, fontsize=10, color=TEXT_DARK, fontweight="600")

    # Annotate cell values
    for i, m_key in enumerate(metrics):
        for j, cell_key in enumerate(cell_order_keys):
            val = matrix[i, j]
            if np.isnan(val):
                txt = "—"
            elif m_key == "EP":
                txt = f"{val:.3f}"
            else:
                txt = f"{val*100:.1f}%"
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=10.5, color=TEXT_DARK, fontweight="600")

    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)

    fig.suptitle("True-Behavior Profile (TBP) — replaces single-number model rankings",
                 fontsize=14, fontweight="700", color=TEXT_DARK, y=0.98)
    fig.text(0.5, 0.91,
             "Each row is a behavioral construct; each column a (target × condition) cell. "
             "No single number summarizes 'political bias' — the profile is the report.",
             ha="center", fontsize=9.5, color=TEXT_DARK, style="italic")

    plt.tight_layout(rect=[0, 0.02, 1, 0.88])
    fig.savefig(out_path, dpi=600, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved {out_path}")


# ============================================================================
# Main
# ============================================================================

def main():
    print("=== distribution_figures.py ===\n")
    tbp = load_tbp()
    df_decomp = load_decomp()
    df_pa = per_article_cfi(df_decomp)
    print(f"Loaded TBP profile ({len(tbp['profile'])} cells) and "
          f"per-article CFI ({len(df_pa)} rows)")

    print("\n--- Figure 1: paired dot plot (EP / CFI dissociation) ---")
    figure_1_paired_dotplot(tbp, FIGS / "tbp_dissociation.png")

    print("\n--- Figure 2: per-cell CFI distribution (raincloud) ---")
    figure_2_distribution_per_cell(df_pa, FIGS / "tbp_distributions.png")

    print("\n--- Figure 3: True-Behavior Profile heatmap ---")
    figure_3_tbp_heatmap(tbp, FIGS / "tbp_matrix.png")

    print("\nDone. Three figures written to figures/")


if __name__ == "__main__":
    main()
