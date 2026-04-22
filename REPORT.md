# Report - Extenuating Circumstances Claims (2020/21)

- **Student Name**: Marzanul Islam
- **Student ID**: 20646593
- **Student Email**: leymi7@nottingham.ac.uk
- **Student GitHub Username**: MarjanNottingham

## Contents

- [Background](#background)
- [Question 1 - Do EC claims cluster around assessment deadlines?](#question-1---do-ec-claims-cluster-around-assessment-deadlines)
- [Question 2 - Which modules attract the most EC claims?](#question-2---which-modules-attract-the-most-ec-claims)
- [Question 3 - How does Panel response time vary across the year?](#question-3---how-does-panel-response-time-vary-across-the-year)
- [Question 4 - Does claim outcome differ by type of assessment?](#question-4---does-claim-outcome-differ-by-type-of-assessment)
- [Conclusion](#conclusion)

## Background

The dataset holds 1,236 (form, module) entries covering 586 EC
submissions from 295 anonymised students against 163 modules in
2020/21. Around **82%** of considered claims were approved. Each
question below is answered with a single SQL query in
[`src/analysis.py`](src/analysis.py); exploratory work shaping the
choice of questions lives in [`src/eda.ipynb`](src/eda.ipynb).

## Question 1 - Do EC claims cluster around assessment deadlines?

A SQL `julianday()` subtraction returns the days between `posted_date`
and `date_of_assessment_affected`.

![Q1 histogram](img/q1_claims_vs_deadline_hist.png)

The distribution peaks sharply **at the deadline**: roughly half of
all claims are filed within seven days either side. Claims also tail
more heavily into the days *after* the deadline than into the weeks
before it, consistent with self-certified late submissions.

![Q1 box plot](img/q1_claims_vs_deadline_box.png)

Approved and rejected claims show similar timing, so *when* a claim
is filed is not in itself a strong predictor of approval.

## Question 2 - Which modules attract the most EC claims?

A `GROUP BY module_code` count joined to `outcomes` gives both the
volume and the outcome mix per module.

![Q2 top modules](img/q2_top_modules.png)

Computer Science modules dominate. The top five each attract 45+
claims; the largest, **COMP2013**, attracts 53. Most have a similar
approval profile, but a handful (e.g. **COMP3018**, **COMP3006**) show
a noticeably larger rejection bar that would be worth raising with
module conveners.

## Question 3 - How does Panel response time vary across the year?

*Additional question beyond the brief's examples.*
`julianday(date_approved) - julianday(posted_date)` per claim,
bucketed by month-of-submission.

![Q3 response time](img/q3_response_time_monthly.png)

The median stays under ten days for most months but **widens
dramatically in December and February**, when a small number of
claims take 60+ days. These coincide with the Christmas break and the
start of semester two: the Panel is normally quick, but capacity is
sensitive to University holidays.

## Question 4 - Does claim outcome differ by type of assessment?

A grouped count of `(type_of_assessment, outcome_category)` plotted as
two charts - claim volume first, then approval rate.

![Q4 volume](img/q4_volume_by_assessment_type.png)

**Coursework** generates the most claims (n=906); examinations are
distant second (n=271).

![Q4 approval rate](img/q4_approval_rate_by_assessment_type.png)

Coursework also has the **lowest approval rate (88%)**. Examination
claims are approved 95% of the time and the smaller categories
almost always. The gap is consistent with coursework claims
including more "extension requested" cases the Panel may treat as
foreseeable.

## Conclusion

Three patterns stand out: (i) students mostly claim **right around
the deadline**, (ii) a few large Computer Science modules generate a
disproportionate share of claims, and (iii) coursework deadlines are
both the biggest source of EC volume and the source with the lowest
approval rate. Any future intervention - communications, deadline
staggering, automated extensions for low-risk cases - would have the
largest leverage if focused on **coursework** in the
**highest-volume modules** during the weeks before their deadlines.
