"""
plots.py - plotting functions for the four assessment questions.

Each function takes the DataFrame returned by analysis.py and saves
a PNG into the img/ folder.
"""

import matplotlib.pyplot as plt
import seaborn as sns

from config import IMG_DIR

sns.set_theme(style="whitegrid")

# Colours so the same outcome category looks the same in every chart.
OUTCOME_COLOURS = {
    "Approved": "#3a7d44",
    "Rejected": "#c0392b",
    "Other": "#888888",
}

# Column order used by the Q2 and Q4 stacked bar charts.
CATEGORY_ORDER = ["Approved", "Rejected", "Other"]


def save_figure(fig, filename):
    """Save fig into img/filename and close it."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = IMG_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_q1_histogram(df):
    """Q1 - histogram of days between submission and deadline."""
    data = df.copy()
    # Cap extreme values so they don't stretch the x-axis.
    data["days_after_deadline"] = data["days_after_deadline"].clip(-90, 90)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(data["days_after_deadline"], bins=40,
            color="#2c7fb8", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Q1: Timing of EC claims relative to assessment deadline")
    ax.set_xlabel("Days between submission and assessment date "
                  "(negative = before deadline)")
    ax.set_ylabel("Number of claims")
    return save_figure(fig, "q1_claims_vs_deadline_hist.png")


def plot_q1_boxplot(df):
    """Q1 - same metric but split by outcome (approved vs rejected)."""
    data = df.copy()
    data["days_after_deadline"] = data["days_after_deadline"].clip(-90, 90)
    data = data[data["outcome_category"].isin(["Approved", "Rejected"])]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.boxplot(
        data=data,
        x="days_after_deadline",
        y="outcome_category",
        hue="outcome_category",
        palette=OUTCOME_COLOURS,
        legend=False,
        ax=ax,
    )
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Q1: Submission timing by outcome")
    ax.set_xlabel("Days between submission and assessment date")
    ax.set_ylabel("Outcome category")
    return save_figure(fig, "q1_claims_vs_deadline_box.png")


def plot_q2_top_modules(df):
    """Q2 - horizontal stacked bar of the top 15 modules by claim count."""
    # Pivot so each module is a row and each outcome is a column.
    wide = df.pivot_table(
        index="module_code",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    # Sort smallest to largest - makes the biggest bar appear at the top
    # when we plot horizontally.
    wide["total"] = wide.sum(axis=1)
    wide = wide.sort_values("total", ascending=True).drop(columns="total")

    # Keep only the categories that actually appear, in the colour order.
    column_order = [c for c in CATEGORY_ORDER if c in wide.columns]
    wide = wide[column_order]
    colours = [OUTCOME_COLOURS[c] for c in column_order]

    fig, ax = plt.subplots(figsize=(9, 6))
    wide.plot(kind="barh", stacked=True, ax=ax,
              color=colours, edgecolor="white")
    ax.set_title("Q2: Top 15 modules by EC claim count")
    ax.set_xlabel("Number of EC claims")
    ax.set_ylabel("Module code")
    ax.legend(title="Outcome", loc="lower right")
    return save_figure(fig, "q2_top_modules.png")


def plot_q3_response_time(df):
    """Q3 - box plot of monthly response times with a median line."""
    # Drop rows with very long response times so the y-axis stays tidy.
    data = df[(df["response_days"] >= 0) & (df["response_days"] <= 90)]

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(
        data=data, x="posted_month", y="response_days",
        color="#74a9cf", ax=ax,
    )
    # Overlay the monthly median.
    medians = data.groupby("posted_month")["response_days"].median()
    ax.plot(range(len(medians)), medians.values,
            color="#08306b", marker="o", linewidth=2,
            label="Monthly median")
    ax.set_title("Q3: Panel response time by month of submission")
    ax.set_xlabel("Month claim was posted (YYYY-MM)")
    ax.set_ylabel("Days from submission to Panel approval")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper right")
    return save_figure(fig, "q3_response_time_monthly.png")


def plot_q4_volume(df):
    """Q4a - stacked bar of claim volume per assessment type."""
    wide = df.pivot_table(
        index="type_of_assessment",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    wide["total"] = wide.sum(axis=1)
    wide = wide.sort_values("total", ascending=False).drop(columns="total")

    column_order = [c for c in CATEGORY_ORDER if c in wide.columns]
    wide = wide[column_order]
    colours = [OUTCOME_COLOURS[c] for c in column_order]

    fig, ax = plt.subplots(figsize=(9, 5))
    wide.plot(kind="bar", stacked=True, ax=ax,
              color=colours, edgecolor="white")
    ax.set_title("Q4a: EC claim volume by type of assessment")
    ax.set_xlabel("")
    ax.set_ylabel("Number of claims")
    ax.legend(title="Outcome", loc="upper right")
    ax.tick_params(axis="x", rotation=30)
    return save_figure(fig, "q4_volume_by_assessment_type.png")


def plot_q4_approval_rate(df):
    """Q4b - approval % for each type of assessment."""
    wide = df.pivot_table(
        index="type_of_assessment",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    # Approval rate ignores "Other" (not considered at all).
    approved = wide.get("Approved", 0)
    rejected = wide.get("Rejected", 0)
    considered = approved + rejected
    safe_denom = considered.replace(0, 1)
    approval_pct = (approved / safe_denom) * 100

    plot_df = approval_pct.reset_index()
    plot_df.columns = ["type_of_assessment", "approval_pct"]
    plot_df["n_considered"] = considered.values
    plot_df = plot_df.sort_values("n_considered", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=plot_df, x="type_of_assessment", y="approval_pct",
        hue="type_of_assessment", palette="Blues_d",
        legend=False, ax=ax,
    )
    # Label each bar with the % and the sample size.
    for i in range(len(plot_df)):
        pct = plot_df["approval_pct"].iloc[i]
        n = int(plot_df["n_considered"].iloc[i])
        ax.text(i, pct + 1, f"{pct:.0f}%\n(n={n})",
                ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, 115)
    ax.set_title("Q4b: Approval rate by type of assessment")
    ax.set_xlabel("")
    ax.set_ylabel("Approved as % of considered")
    ax.tick_params(axis="x", rotation=30)
    return save_figure(fig, "q4_approval_rate_by_assessment_type.png")


def plot_all(results):
    """Save every plot in one call."""
    paths = []
    paths.append(plot_q1_histogram(results["q1"]))
    paths.append(plot_q1_boxplot(results["q1"]))
    paths.append(plot_q2_top_modules(results["q2"]))
    paths.append(plot_q3_response_time(results["q3"]))
    paths.append(plot_q4_volume(results["q4"]))
    paths.append(plot_q4_approval_rate(results["q4"]))
    return paths
