# Report - Extenuating Circumstances Claims (2020/21)

- **Student Name**: Marzanul Islam
- **Student ID**: 20646593
- **Student Email**: leymi7@nottingham.ac.uk
- **Student GitHub Username**: MarjanNottingham

## Background

The dataset has 1,236 (form, module) entries - 586 EC submissions
from 295 students across 163 modules in 2020/21. About 82% of the
claims that were considered got approved. Each question below is
answered by one SQL query in `src/analysis.py`, and my exploratory
work is in `src/eda.ipynb`.

## Question 1 - do EC claims cluster around assessment deadlines?

I used `julianday()` to get the number of days between `posted_date`
and `date_of_assessment_affected`.

![Q1 histogram](img/q1_claims_vs_deadline_hist.png)

The graph peaks right at the deadline - about half of all claims are
submitted within a week either side of it. There are more claims
after the deadline than before, which I think is because students
can self-certify if they're late.

![Q1 box plot](img/q1_claims_vs_deadline_box.png)

If I split by outcome, approved and rejected claims have pretty
similar timings, so when you submit the claim doesn't really change
whether it gets approved.

## Question 2 - which modules get the most EC claims?

A `GROUP BY module_code` count joined to `outcomes` gives both the
volume and the outcome mix for each module. The top 15 are shown.

![Q2 top modules](img/q2_top_modules.png)

The top 15 modules are all Computer Science modules. The top five
each have 45+ claims, with COMP2013 on 53. COMP3018 and COMP3006
have more rejections than the other modules.

## Question 3 - how does Panel response time vary across the year?

For each claim I calculated
`julianday(date_approved) - julianday(posted_date)`, grouped by the
month the claim was posted.

![Q3 response time](img/q3_response_time_monthly.png)

The median is under 10 days for most months, but December and
February are much slower - some claims took 60+ days. Those months
line up with the Christmas break and the start of semester 2, so I
think the Panel just slows down over the holidays.

## Question 4 - does the outcome change with the type of assessment?

*This is my additional question, beyond the four example ones in the
brief.* A count of `(type_of_assessment, outcome_category)` shown as
a volume chart and an approval-rate chart.

![Q4 volume](img/q4_volume_by_assessment_type.png)

Coursework is by far the biggest, and examinations are second but
much smaller.

![Q4 approval rate](img/q4_approval_rate_by_assessment_type.png)

Coursework also has the lowest approval rate. The numbers:

| Assessment type    | n considered | approved | approval % |
|--------------------|-------------:|---------:|-----------:|
| Coursework         | 784          | 693      | 88%        |
| Examination        | 241          | 228      | 95%        |
| In class assessment | 24           | 24       | 100%       |
| Presentation       | 11           | 10       | 91%        |

This is probably because coursework claims are often about
extensions, and the Panel sometimes decides the student could have
planned ahead.

## Conclusion

Three things stand out:

1. Students mostly submit claims right around the deadline.
2. A small number of big Computer Science modules account for a
   large share of the claims.
3. Coursework deadlines are both the biggest source of EC claims
   and the source with the lowest approval rate.

If the University wanted to reduce the EC workload, the main thing
would be coursework in the busiest modules in the week before a
deadline - clearer communication, spacing the deadlines, or short
automatic extensions for claims that are clearly fine. Dissertation
and Placement each only had one considered claim, so I wouldn't
read much into those percentages.
