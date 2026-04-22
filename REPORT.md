# Report - Extenuating Circumstances Claims (2020/21)

- **Student Name**: Marzanul Islam
- **Student ID**: 20646593
- **Student Email**: leymi7@nottingham.ac.uk
- **Student GitHub Username**: MarjanNottingham

## Background

The dataset has 1,236 (form, module) entries covering 586 EC submissions
from 295 students across 163 modules in 2020/21. Roughly 82% of the
claims that were considered ended up approved. Each of the four
questions below is answered by a single SQL query in `src/analysis.py`.
Exploratory work that helped me pick these questions is in
`src/eda.ipynb`.

## Question 1 - do EC claims cluster around assessment deadlines?

Using `julianday()` in SQL to work out the days between `posted_date`
and `date_of_assessment_affected`.

![Q1 histogram](img/q1_claims_vs_deadline_hist.png)

The distribution has a sharp peak right around the deadline itself -
about half of all claims are filed within a week either side of the
assessment date. There's a longer tail on the "after" side than on
the "before" side, which fits with self-certified late submissions.

![Q1 box plot](img/q1_claims_vs_deadline_box.png)

Splitting by outcome, approved and rejected claims have similar
timings - so when a claim is filed doesn't seem to be a strong
predictor of whether it gets approved.

## Question 2 - which modules attract the most EC claims?

A `GROUP BY module_code` count joined to `outcomes` gives both the
volume and the outcome mix per module. The top 15 are shown.

![Q2 top modules](img/q2_top_modules.png)

Computer Science modules dominate - every module in the top 15 is
COMP-something. The top five each have 45+ claims, with COMP2013 at
53. Most modules have a similar approval profile but a couple
(COMP3018, COMP3006) have noticeably more rejections than the rest,
which might be worth flagging to the module convener.

## Question 3 - how does Panel response time vary across the year?

*Additional question beyond the brief's examples.* For each claim I
compute `julianday(date_approved) - julianday(posted_date)` and group
by month of submission.

![Q3 response time](img/q3_response_time_monthly.png)

The monthly median stays under 10 days for most of the year, but the
distribution gets much wider in December and February, where some
claims took 60+ days. These months line up with the Christmas break
and the start of semester 2, which suggests Panel capacity is
affected by University holidays.

## Question 4 - does claim outcome differ by type of assessment?

A grouped count of `(type_of_assessment, outcome_category)` shown as
two charts: first the volume, then the approval rate.

![Q4 volume](img/q4_volume_by_assessment_type.png)

Coursework is by far the biggest category (n=906), with examinations
a distant second (n=271).

![Q4 approval rate](img/q4_approval_rate_by_assessment_type.png)

Interestingly, coursework also has the lowest approval rate at 88%.
Examination claims are approved 95% of the time and the smaller
categories are approved nearly always. This fits the idea that
coursework claims include more "please can I have an extension"
cases that the Panel sometimes decides are foreseeable.

## Conclusion

Three things stand out:

1. Students mostly claim right around the deadline.
2. A small number of big Computer Science modules account for a large
   share of claims.
3. Coursework deadlines are both the biggest source of EC claims and
   the source with the lowest approval rate.

So if the University wanted to reduce EC workload, the biggest lever
would probably be around coursework in the busiest modules in the
week or two before the deadline - for example clearer communication,
spacing deadlines out, or automatic short extensions for low-risk
cases.
