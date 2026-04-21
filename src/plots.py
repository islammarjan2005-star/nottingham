"""
plots.py
--------
One plotting function per analytical question. Each function takes the
DataFrame returned by analysis.py and saves a PNG into the img/
folder. The PNGs are then linked from REPORT.md.
"""

# matplotlib does the actual drawing.
import matplotlib.pyplot as plt
# seaborn gives nicer defaults and a few high-level chart types.
import seaborn as sns

# Use the IMG_DIR constant from config so we know where to save files.
from config import IMG_DIR

# Set a consistent visual style for every plot.
sns.set_theme(style="whitegrid")

# A small dictionary so the same outcome category is the same colour
# in every plot (green = approved, red = rejected, grey = other).
OUTCOME_COLOURS = {
    "Approved": "#3a7d44",
    "Rejected": "#c0392b",
    "Other":    "#888888",
}


def save_figure(fig, filename):
    """Save fig as a PNG inside IMG_DIR and close it to free memory."""
    # Make sure the img/ directory exists.
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    # Build the full path for the file.
    out_path = IMG_DIR / filename
    # 150 dpi gives a sharp picture without a huge file.
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    # Close so we don't leak memory if many plots are made.
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------
# Q1 - timing of claims relative to the deadline.
# ---------------------------------------------------------------------

def plot_q1_histogram(df):
    """Histogram of how many days after the deadline a claim is filed."""
    # Copy the DataFrame so we don't change the caller's version.
    data = df.copy()
    # Clip to a sensible window so a few extreme outliers don't squash
    # the rest of the distribution.
    data["days_after_deadline"] = data["days_after_deadline"].clip(-90, 90)

    # Make a new figure.
    fig, ax = plt.subplots(figsize=(9, 5))
    # Draw the histogram.
    ax.hist(data["days_after_deadline"], bins=40,
            color="#2c7fb8", edgecolor="white")
    # Draw a dashed vertical line at zero (the deadline).
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    # Add a title and axis labels.
    ax.set_title("Q1: Timing of EC claims relative to assessment deadline")
    ax.set_xlabel("Days between submission and assessment date "
                  "(negative = before deadline)")
    ax.set_ylabel("Number of claims")
    return save_figure(fig, "q1_claims_vs_deadline_hist.png")


def plot_q1_boxplot(df):
    """Box plot of the same metric, split by outcome category."""
    # Copy and clip as before.
    data = df.copy()
    data["days_after_deadline"] = data["days_after_deadline"].clip(-90, 90)
    # Keep only Approved / Rejected so the comparison is clear.
    data = data[data["outcome_category"].isin(["Approved", "Rejected"])]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    # seaborn boxplot is a one-liner.
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
    ax.set_title("Q1: Submission timing by outcome (approved vs rejected)")
    ax.set_xlabel("Days between submission and assessment date")
    ax.set_ylabel("Outcome category")
    return save_figure(fig, "q1_claims_vs_deadline_box.png")


# ---------------------------------------------------------------------
# Q2 - top modules by claim count, stacked by outcome.
# ---------------------------------------------------------------------

def plot_q2_top_modules(df):
    """Horizontal stacked bar chart of the top modules by claim count."""
    # We need one row per module, with one column per outcome category.
    # The pivot_table call below does that. We default missing values
    # to zero (a module with no rejected claims gets a 0 in that column).
    wide = df.pivot_table(
        index="module_code",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    # Add a 'total' column and sort smallest-to-largest, so when we
    # plot horizontally the biggest bar appears at the top.
    wide["total"] = wide.sum(axis=1)
    wide = wide.sort_values("total", ascending=True)
    wide = wide.drop(columns="total")

    # Decide which order the outcome columns appear in (Approved first).
    column_order = []
    for cat in ["Approved", "Rejected", "Other"]:
        if cat in wide.columns:
            column_order.append(cat)
    wide = wide[column_order]

    # Build the colour list in the same order as the columns.
    colours = []
    for cat in column_order:
        colours.append(OUTCOME_COLOURS[cat])

    # Draw the stacked bar chart.
    fig, ax = plt.subplots(figsize=(9, 6))
    wide.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=colours,
        edgecolor="white",
    )
    ax.set_title("Q2: Top 15 modules by EC claim count")
    ax.set_xlabel("Number of EC claims")
    ax.set_ylabel("Module code")
    ax.legend(title="Outcome", loc="lower right")
    return save_figure(fig, "q2_top_modules.png")


# ---------------------------------------------------------------------
# Q3 - monthly response time.
# ---------------------------------------------------------------------

def plot_q3_response_time(df):
    """Box plot of response time per month, with a median line."""
    # Drop rows with extreme response times so the y-axis stays sensible.
    data = df[(df["response_days"] >= 0) & (df["response_days"] <= 90)]

    fig, ax = plt.subplots(figsize=(11, 5))
    # Box plot per month.
    sns.boxplot(
        data=data,
        x="posted_month",
        y="response_days",
        color="#74a9cf",
        ax=ax,
    )
    # Compute the median per month and draw it as a line on top.
    medians = data.groupby("posted_month")["response_days"].median()
    ax.plot(
        range(len(medians)),
        medians.values,
        color="#08306b",
        marker="o",
        linewidth=2,
        label="Monthly median",
    )
    ax.set_title("Q3: Panel response time by month of submission")
    ax.set_xlabel("Month claim was posted (YYYY-MM)")
    ax.set_ylabel("Days from submission to Panel approval")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper right")
    return save_figure(fig, "q3_response_time_monthly.png")


# ---------------------------------------------------------------------
# Q4 - outcome by type of assessment.
# We make TWO plots here so the report has two angles on the same data:
#   * a stacked bar showing volume of claims per assessment type
#   * a simple bar showing the approval percentage per assessment type
# ---------------------------------------------------------------------

def plot_q4_volume(df):
    """Stacked bar of claim volume per assessment type."""
    # Pivot to one row per assessment type, one column per outcome.
    wide = df.pivot_table(
        index="type_of_assessment",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    # Sort so the biggest assessment type is on the left.
    wide["total"] = wide.sum(axis=1)
    wide = wide.sort_values("total", ascending=False)
    wide = wide.drop(columns="total")

    # Same colour ordering as Q2.
    column_order = []
    for cat in ["Approved", "Rejected", "Other"]:
        if cat in wide.columns:
            column_order.append(cat)
    wide = wide[column_order]
    colours = [OUTCOME_COLOURS[c] for c in column_order]

    fig, ax = plt.subplots(figsize=(9, 5))
    wide.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=colours,
        edgecolor="white",
    )
    ax.set_title("Q4a: EC claim volume by type of assessment")
    ax.set_xlabel("")
    ax.set_ylabel("Number of claims")
    ax.legend(title="Outcome", loc="upper right")
    ax.tick_params(axis="x", rotation=30)
    return save_figure(fig, "q4_volume_by_assessment_type.png")


def plot_q4_approval_rate(df):
    """Simple bar of approval percentage per assessment type."""
    # Build a wide table and compute approval %.
    wide = df.pivot_table(
        index="type_of_assessment",
        columns="outcome_category",
        values="claim_count",
        fill_value=0,
    )
    # Approval rate = approved / (approved + rejected). We ignore "Other"
    # (claims that were never considered) so the rate is comparable.
    approved = wide.get("Approved", 0)
    rejected = wide.get("Rejected", 0)
    considered = approved + rejected
    # Replace zero denominators with 1 so we don't divide by zero.
    safe_denom = considered.replace(0, 1)
    approval_pct = (approved / safe_denom) * 100

    # Build a small DataFrame for plotting.
    plot_df = approval_pct.reset_index()
    plot_df.columns = ["type_of_assessment", "approval_pct"]
    plot_df["n_considered"] = considered.values
    # Sort so the biggest assessment type is on the left.
    plot_df = plot_df.sort_values("n_considered", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=plot_df,
        x="type_of_assessment",
        y="approval_pct",
        hue="type_of_assessment",
        palette="Blues_d",
        legend=False,
        ax=ax,
    )
    # Write the percentage and the sample size on top of each bar.
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


# ---------------------------------------------------------------------
# Convenience: produce every plot in one call.
# ---------------------------------------------------------------------

def plot_all(results):
    """Take the dict from ECAnalyser.run_all() and save every plot."""
    paths = []
    paths.append(plot_q1_histogram(results["q1"]))
    paths.append(plot_q1_boxplot(results["q1"]))
    paths.append(plot_q2_top_modules(results["q2"]))
    paths.append(plot_q3_response_time(results["q3"]))
    paths.append(plot_q4_volume(results["q4"]))
    paths.append(plot_q4_approval_rate(results["q4"]))
    return paths
