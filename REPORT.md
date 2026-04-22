# Report - Extenuating Circumstances Claims (2020/21)

- **Student Name**: Marzanul Islam
- **Student ID**: 20646593
- **Student Email**: leymi7@nottingham.ac.uk
- **Student GitHub Username**: MarjanNottingham

## Background

The dataset has 1,236 (form, module) entries covering 586 EC
submissions from 295 students across 163 modules in 2020/21. Around
82% of considered claims were approved. Each question below is
answered by one SQL query in `src/analysis.py`, with exploratory
work in `src/eda.ipynb`.

## Question 1 - do EC claims cluster around assessment deadlines?

Using `julianday()` to get the days between `posted_date` and
`date_of_assessment_affected`.

![Q1 histogram](img/q1_claims_vs_deadline_hist.png)

The distribution peaks sharply right around the deadline - about
half of all claims are filed within a week either side. The tail on
the "after" side is heavier than the "before" side, which fits with
self-certified late submissions.

![Q1 box plot](img/q1_claims_vs_deadline_box.png)

Splitting by outcome, approved and rejected claims have similar
timings, so when a claim is filed is not a strong predictor of
approval.

## Question 2 - which modules attract the most EC claims?

A `GROUP BY module_code` count joined to `outcomes` gives the volume
and outcome mix per module. The top 15 are shown.

![Q2 top modules](img/q2_top_modules.png)

Every module in the top 15 is a Computer Science one. The top five
each have 45+ claims, with COMP2013 on 53. COMP3018 and COMP3006
stand out with more rejections than the rest.

## Question 3 - how does Panel response time vary across the year?

For each claim: `julianday(date_approved) - julianday(posted_date)`,
grouped by month of submission.

![Q3 response time](img/q3_response_time_monthly.png)

The monthly median stays under 10 days for most of the year but
widens a lot in December and February where some claims took 60+
days. These line up with the Christmas break and the start of
semester 2, so Panel capacity seems sensitive to holidays.

## Question 4 - does claim outcome differ by type of assessment?

*This is my additional question, beyond the four examples in the
brief.* A count of `(type_of_assessment, outcome_category)` as a
volume chart and an approval-rate chart.

![Q4 volume](img/q4_volume_by_assessment_type.png)

Coursework is by far the biggest category, examinations a distant
second.

![Q4 approval rate](img/q4_approval_rate_by_assessment_type.png)

Coursework also has the lowest approval rate. Summary numbers:

| Assessment type    | n considered | approved | approval % |
|--------------------|-------------:|---------:|-----------:|
| Coursework         | 784          | 693      | 88%        |
| Examination        | 241          | 228      | 95%        |
| In class assessment | 24           | 24       | 100%       |
| Presentation       | 11           | 10       | 91%        |

This fits the idea that coursework claims include more extension
requests that the Panel sometimes decides are foreseeable.

## Conclusion

Three things stand out:

1. Students mostly claim right around the deadline.
2. A small number of big Computer Science modules account for a
   large share of claims.
3. Coursework deadlines are both the biggest source of EC volume and
   the source with the lowest approval rate.

To reduce EC workload the biggest lever is probably coursework in
the busiest modules in the week before a deadline - clearer
communication, spacing deadlines, or short automatic extensions for
low-risk cases. Dissertation and Placement only had one considered
claim each, so those approval rates are anecdotal.
