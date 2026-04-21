"""
plots.py
--------
One plotting function per analytical question. Each function takes the
DataFrame returned by the matching ``ECAnalyser`` method and writes a
PNG into the ``img/`` directory.

The plots are written to disk (rather than only being displayed) so
that ``REPORT.md`` can embed them with relative-path Markdown links.
"""

# Third-party imports.
import matplotlib.pyplot as plt
import seaborn as sns

# Project imports.
from config import IMG_DIR

# A consistent visual style for the whole report.
sns.set_theme(style="whitegrid", context="notebook")

# Stable colour mapping for the three outcome categories so the same
# colour means the same thing across every plot.
OUTCOME_COLOURS = {
    "Approved": "#3a7d44",   # green
    "Rejected": "#c0392b",   # red
    "Other":    "#888888",   # grey
    "Unknown":  "#bdbdbd",   # light grey
}


def _save(fig, filename):
    """Save ``fig`` as a PNG into IMG_DIR and close it to free memory."""
    # Make sure the output directory exists.
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    # Build the full path inside img/.
    out_path = IMG_DIR / filename
    # 150 dpi gives a sharp image without making the file enormous.
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------
# Q1 plots: distribution of "days after deadline".
# ---------------------------------------------------------------------
def plot_q1_histogram(df):
    """Histogram of how many days after the deadline a claim is filed."""
    # Restrict the x-axis to a sensible window so a few extreme outliers
    # do not flatten the bulk of the distribution.
    clipped = df.copy()
    clipped["days_after_deadline"] = clipped["days_after_deadline"].clip(-90, 90)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(
        data=clipped,
        x="days_after_deadline",
        bins=40,
        color="#2c7fb8",
        edgecolor="white",
        ax=ax,
    )
    # A vertical line at zero marks the deadline itself.
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Q1: Timing of EC claims relative to assessment deadline")
    ax.set_xlabel("Days between submission and assessment date "
                  "(negative = before deadline)")
    ax.set_ylabel("Number of claims")
    ax.text(
        0.99, 0.97,
        "Source: anonymised EC dataset 2020/21",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=8, color="#555",
    )
    return _save(fig, "q1_claims_vs_deadline_hist.png")


def plot_q1_boxplot(df):
    """Box plot of the same metric, split by outcome category."""
    clipped = df.copy()
    clipped["days_after_deadline"] = clipped["days_after_deadline"].clip(-90, 90)
    # Restrict to the two categories that drive the question.
    clipped = clipped[clipped["outcome_category"].isin(["Approved", "Rejected"])]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.boxplot(
        data=clipped,
        x="days_after_deadline",
        y="outcome_category",
        hue="outcome_category",
        palette=OUTCOME_COLOURS,
        legend=False,
        ax=ax,
    )
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Q1: Submission timing by outcome (approved vs rejected)")
    ax.set_xlabel("Days between submission and assessment date")
    ax.set_ylabel("Outcome category")
    return _save(fig, "q1_claims_vs_deadline_box.png")


# ---------------------------------------------------------------------
# Q2 plot: top modules by claim count, stacked by outcome.
# ---------------------------------------------------------------------
def plot_q2_top_modules(df):
    """Horizontal stacked bar chart of the top modules by claim count."""
    # Pivot from long format to wide so each outcome category becomes a
    # column, which is what matplotlib's stacked bar wants.
    wide = (
        df.pivot_table(
            index="module_code",
            columns="outcome_category",
            values="claim_count",
            fill_value=0,
        )
        .assign(total=lambda d: d.sum(axis=1))
        .sort_values("total", ascending=True)   # ascending so largest is at top
        .drop(columns="total")
    )

    # Order the outcome columns so the legend reads Approved -> Other.
    column_order = [c for c in ("Approved", "Rejected", "Other", "Unknown")
                    if c in wide.columns]
    wide = wide[column_order]

    fig, ax = plt.subplots(figsize=(9, 6))
    wide.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=[OUTCOME_COLOURS[c] for c in column_order],
        edgecolor="white",
    )
    ax.set_title("Q2: Top 15 modules by EC claim count")
    ax.set_xlabel("Number of EC claims")
    ax.set_ylabel("Module code")
    ax.legend(title="Outcome", loc="lower right")
    return _save(fig, "q2_top_modules.png")


# ---------------------------------------------------------------------
# Q3 plot: monthly response time.
# ---------------------------------------------------------------------
def plot_q3_response_time(df):
    """Box plot of Panel response time per month-of-submission."""
    # Cap the response time at 90 days so a few stragglers do not stretch
    # the y-axis into uselessness.
    clipped = df.copy()
    clipped = clipped[clipped["response_days"].between(0, 90)]

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(
        data=clipped,
        x="posted_month",
        y="response_days",
        color="#74a9cf",
        ax=ax,
    )
    # Overlay the median with a connecting line so the trend is obvious.
    medians = clipped.groupby("posted_month")["response_days"].median()
    ax.plot(
        range(len(medians)), medians.values,
        color="#08306b", marker="o", linewidth=2, label="Monthly median",
    )
    ax.set_title("Q3: Panel response time by month of submission")
    ax.set_xlabel("Month claim was posted (YYYY-MM)")
    ax.set_ylabel("Days from submission to Panel approval")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper right")
    return _save(fig, "q3_response_time_monthly.png")


# ---------------------------------------------------------------------
# Q4 plot: approval rate by level / finalist.
# ---------------------------------------------------------------------
def plot_q4_outcome_by_assessment_type(df):
    """Side-by-side view: claim volume + approval rate by assessment type.

    The left panel is a stacked bar of total claim volume so the reader
    sees how dominant Coursework is. The right panel is the approval
    percentage so the reader can compare like-for-like rates.
    """
    # Pivot so each assessment type has one row and outcome categories
    # become columns.
    wide = (
        df.pivot_table(
            index="type_of_assessment",
            columns="outcome_category",
            values="claim_count",
            fill_value=0,
        )
        .assign(total=lambda d: d.sum(axis=1))
        .sort_values("total", ascending=False)
    )
    # Order the outcome columns consistently across the panels.
    column_order = [c for c in ("Approved", "Rejected", "Other", "Unknown")
                    if c in wide.columns]
    colours = [OUTCOME_COLOURS[c] for c in column_order]

    # Compute approval rate (% of considered = approved + rejected).
    considered = wide[[c for c in ("Approved", "Rejected") if c in wide.columns]]
    approval_pct = (considered.get("Approved", 0)
                    / considered.sum(axis=1).replace(0, 1)) * 100

    # Two side-by-side panels.
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12, 5))

    # ---- Left: stacked bar of claim volume ---------------------------
    wide[column_order].plot(
        kind="bar", stacked=True, ax=ax_left,
        color=colours, edgecolor="white",
    )
    ax_left.set_title("Claim volume by assessment type")
    ax_left.set_xlabel("")
    ax_left.set_ylabel("Number of claims")
    ax_left.legend(title="Outcome", loc="upper right")
    ax_left.tick_params(axis="x", rotation=30)

    # ---- Right: approval rate bar ------------------------------------
    sns.barplot(
        x=approval_pct.index,
        y=approval_pct.values,
        hue=approval_pct.index,
        palette="Blues_d",
        legend=False,
        ax=ax_right,
    )
    for i, (label, pct) in enumerate(approval_pct.items()):
        n_considered = int(considered.loc[label].sum())
        ax_right.text(
            i, pct + 1, f"{pct:.0f}%\n(n={n_considered})",
            ha="center", va="bottom", fontsize=8,
        )
    ax_right.set_ylim(0, 115)
    ax_right.set_title("Approval rate by assessment type")
    ax_right.set_xlabel("")
    ax_right.set_ylabel("Approved as % of considered")
    ax_right.tick_params(axis="x", rotation=30)

    fig.suptitle("Q4: Outcome of EC claims by type of assessment",
                 fontsize=13, y=1.02)
    return _save(fig, "q4_outcome_by_assessment_type.png")


# ---------------------------------------------------------------------
# Convenience: produce every plot in one call.
# ---------------------------------------------------------------------
def plot_all(results):
    """Take the dict returned by ECAnalyser.run_all() and save all PNGs."""
    paths = [
        plot_q1_histogram(results["q1"]),
        plot_q1_boxplot(results["q1"]),
        plot_q2_top_modules(results["q2"]),
        plot_q3_response_time(results["q3"]),
        plot_q4_outcome_by_assessment_type(results["q4"]),
    ]
    return paths
