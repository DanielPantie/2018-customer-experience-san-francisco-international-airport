# Learning to analyse the SFO survey

## 1. What is one row?

One respondent, not one flight or one complaint. The 2018 file has 2,809 rows
and 97 columns. It contains ratings, recommendation, service use, trip
characteristics, demographics and coded comments. Survey weights aim to
represent SFO passengers according to the supplied dictionary.

## 2. Read codes question by question

| Question group | Valid answers for this project | Exclusions |
| --- | --- | --- |
| Q7 service and overall rating | 1-5; top two = 4 or 5 | 0 blank, 6 not applicable/never used, BLANK/missing |
| Q14 navigation and security | 1-5; top two = 4 or 5 | 0 blank, 6 unknown/not applicable, missing |
| NETPRO recommendation | 0-10 | 11 blank, missing |
| Q15PROBLEM | 1 Yes and 2 No | 0 blank/multiple, 3 Don't know, missing |
| Q4 usage/purchase | 1 Yes and 2 No | 0 blank/multiple, 3 Don't know, missing |
| Q5FIRSTTIME | 2 first time and 1 returning | 0 and missing |

The same number means different things in different questions. In particular,
**0 is a valid detractor recommendation score**, whereas it is blank in Q7.
**6 is not the best rating**, and **11 must not become an NPS promoter**.

## 3. Define the numerator and denominator together

For overall top-two share, count the weights of ratings 4/5 and divide by the
weights of valid ratings 1-5. Keep actual n separately.

Suppose two people answer: weight 1 with score 3, and weight 3 with score 5.
The unweighted top-two share is 50%; the weighted share is 75%. Both have
actual n = 2. Weighting does not create extra respondents.

This project preserves source fields and adds `valid_*` flags and nullable
outcomes. Missing or out-of-scope outcomes remain NA, distinct from False.

## 4. Calculate NPS correctly

- Promoters score 9-10.
- Passives score 7-8.
- Detractors score 0-6.

NPS = promoter percentage minus detractor percentage, measured in **points**.
It ranges from -100 to +100. For the weighted SFO file, 50.7% are promoters
and 15.6% detractors, yielding +35.1 points.

NPS measures stated willingness to recommend. It is not a direct measure of
observed loyalty, future travel, spending or retention.

## 5. Use one person per problem theme

The dictionary supplies problem codes in Q15-1 to Q15-3. Codes 31-36 map to
security/immigration, for example. A person selecting codes 31 and 32 belongs
once in that theme, not twice. The theme denominator includes all 369 people
who explicitly reported a problem, including 15 without a recognized code.

The project uses these existing categories. It does not guess themes using a
language model or publish raw comments in its analysis outputs.

## 6. Inspect service usage before judging a rating

Q4WIFI asks about Wi-Fi use that day. Q7WIFI asks for a rating. Someone who
did not use it that day may still have used it earlier. Excluding every such
rating would change the population being described.

Report both definitions when useful: 73.1% rating 4/5 among all valid raters,
and 82.4% among same-day users with valid ratings. The difference is a change
of response base, not evidence that use improved a person's assessment.

Restaurants and retail have purchase indicators rather than complete visit
or exposure measures. Purchasing, visiting and having an opinion can differ.

## 7. Separate association from improvement effects

Problem reporters have much lower NPS than people reporting no problems.
However, this survey does not randomly assign problems or measure an
intervention. Travel disruption, service use and general sentiment may affect
both answers. The gap is an observed association.

The boarding-area sensitivity check holds one part of passenger mix fixed.
Some cells are small, and many other differences remain unadjusted.

Spearman correlations similarly describe co-ratings. They do not establish
causal service importance or predict what an investment would achieve.

## 8. Make a business recommendation testable

Evidence: security/immigration is the most frequently coded theme among
problem reporters.

Next investigation: inspect the specific security codes and relate them to
queue, support and incident records with the responsible organizations.

Measure next: waiting time, incident type, resolution experience and later
recommendation. Do not assume the survey identifies an airport-only cause or
the revenue benefit of fixing it.

## Suggested practice

1. Reproduce the valid overall-rating base of 2,625.
2. Reproduce the NPS base of 2,650 and compare weighted with unweighted NPS.
3. Explain why the two problem-status NPS groups total 2,540, not 2,650.
4. Reproduce the Wi-Fi same-day-user base of 1,353.
5. Pick a boarding area and explain its response base before comparing it.

Use the executed notebook as a walkthrough, then rerun the cells yourself.
