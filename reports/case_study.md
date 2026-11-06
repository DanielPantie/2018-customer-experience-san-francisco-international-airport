# Customer experience at San Francisco International Airport

## Business question

Which parts of the passenger experience deserve follow-up, and how do reported problems relate to willingness to recommend SFO?

This independent case study uses the **2018 SFO Customer Survey** and its supplied DataSF dictionary: **2,809 respondents and 97 fields**. It combines overall ratings, recommendation, service ratings, problem categories and usage information. Results are historical and must not be presented as current SFO performance.

## Executive findings

| Measure | Weighted estimate | Actual valid n |
| --- | --- | --- |
| Airport overall: rating 4 or 5 | 80.5% | 2625 |
| Net Promoter Score | +35.1 points | 2650 |
| Reported a problem | 12.9% | 2616 |

1. **A positive overall rating coexists with weaker recommendation among problem reporters.** 80.5% of valid respondents rated the airport 4 or 5. Overall NPS is +35.1 points, calculated separately from recommendation scores.
2. **Reported problems coincide with a large recommendation gap.** NPS is +41.5 among passengers reporting no problem, compared with -1.9 among those reporting a problem. The difference is 43.4 points. These are contemporaneous self-reports, not a causal estimate.
3. **Retail and restaurants have the lowest top-two service-rating shares.** Retail reaches 54.7% and restaurants 56.8%, compared with about 79% for walkways/elevators and flight information screens. Base sizes and service users differ. A lower score alone does not establish the highest return on investment.
4. **Security/immigration is the most frequently coded problem theme.** It appears for 35.8% of the 369 problem reporters, followed by directions/information at 19.8%. These themes draw on existing survey codes, rather than an invented AI classification of comments. Passengers can have multiple themes.
5. **Usage changes the Wi-Fi picture.** The positive-rating share is 73.1% among all valid Wi-Fi raters, and 82.4% among people who reported using Wi-Fi that day and rated it validly. Nonusers today may be rating previous use. The difference is not a causal effect of using the service.

## Metric definitions

**Overall and service top-two rating share:** sum of weights for ratings 4 or 5, divided by the sum of weights for valid ratings 1-5. The Q7 anchors are 1 = unacceptable and 5 = outstanding. Intermediate response labels are not supplied, so the case study reports explicit scores rather than inventing a label for 4. This is a project-defined positive-rating indicator, not a claimed official SFO CSAT formula.

**NPS:** weighted percentage of promoters (recommendation scores 9-10) minus weighted percentage of detractors (0-6). Passives score 7-8. The valid scale is 0-10; code 11 is blank. NPS is measured in points and ranges from -100 to +100. It measures stated recommendation, not observed loyalty, retention or repeat purchase.

**Problem prevalence:** weighted Yes responses to Q15PROBLEM divided by weighted Yes + No responses. Yes = 1, No = 2, don't know = 3, blank/multiple = 0. Do not treat code 2 as twice the severity of code 1.

**Problem themes:** classify Q15-1, Q15-2 and Q15-3 using the dictionary's categories. Count each respondent once per theme. The denominator is all 369 people answering Yes to problems, including 15 without a recognized theme code. Theme percentages need not sum to 100%.

**Navigation/security:** share rating Q14FIND or Q14PASSTHRU as 4 or 5 among valid 1-5 answers, with anchors 1 = difficult and 5 = easy.

**Usage sensitivity:** restrict to an explicit Yes in Q4WIFI, Q4FOOD or Q4STORE, then require a valid rating for the corresponding service. These variables ask about use/purchases on the survey day, whereas a valid Q7 service rating may draw on broader experience.

## Data preparation

- Keep source CSV and dictionary unchanged. Verify accepted source checksums before reading.
- Strip outer whitespace from column names. The user-supplied CSV has `Q14FIND ` and `NETPRO  `, which otherwise cause selection errors.
- Normalize respondent IDs for uniqueness checks. Preserve their meaning as identifiers.
- Coerce mixed numeric survey fields carefully. Q7ALL contains the literal text `BLANK` in 184 rows.
- For 1-5 ratings, exclude code 0, code 6, literal blanks and missing values. Code 6 means not applicable/never used for Q7, rather than the best rating.
- Retain **0** as a valid recommendation score. Exclude **11** from NPS.
- Distinguish unanswered/inapplicable outcomes using nullable booleans; do not silently turn them into negative answers.
- Use `WEIGHT` for headline estimates and actual response counts for n. Kish effective n is a weight-concentration diagnostic only.

The audit found **zero duplicate respondent IDs**, **zero missing/nonpositive weights** and **zero recognized problem themes attached to people who did not answer Yes to problems**. It also found **20 Wi-Fi users with a not-applicable rating** and **582 nonusers that day with a valid Wi-Fi rating**. These records are retained and handled by explicit eligibility rules rather than deleted wholesale.

The two accepted CSV byte hashes represent the user-supplied export and a verified public DataSF export. Export formatting differs. Source regression checks establish the same headline counts and estimates; they do not assume identical bytes. The dictionary bytes match exactly.

## Findings in more detail

### Overall experience and recommendation

| Measure | Weighted estimate | Actual valid n |
| --- | --- | --- |
| Promoters: recommendation 9-10 | 50.7% | 2650 |
| Passives: recommendation 7-8 | 33.7% | 2650 |
| Detractors: recommendation 0-6 | 15.6% | 2650 |
| Net Promoter Score | +35.1 points | 2650 |

The overall positive-rating base is 2,625 and the NPS base is 2,650. They cannot be substituted for each other. A 4/5 overall rating does not automatically make someone a promoter.

### Problem reporters and recommendation

| Problem answer | Measure | Weighted estimate | Actual valid n |
| --- | --- | --- | --- |
| Reported a problem | nps | -1.9 points | 359 |
| Reported a problem | overall_top2 | 68.3% | 345 |
| Reported no problem | nps | +41.5 points | 2181 |
| Reported no problem | overall_top2 | 82.6% | 2136 |

The NPS groups include 359 problem reporters and 2,181 people reporting no problem. A further 110 valid NPS respondents have a non-substantive problem answer and do not enter this comparison. That is why the group bases do not sum to the full 2,650 NPS base.

Holding boarding-area mix fixed reduces the descriptive gap from 43.4 to 41.0 points. This sensitivity calculation adjusts one composition factor only. Some problem-group area cells contain as few as 8 respondents, so the standardized result is exploratory. It cannot establish causality or control for airline, trip disruption, travel purpose or other unmeasured differences.

### Service ratings and exposure

| Measure | Weighted estimate | Actual valid n |
| --- | --- | --- |
| Walkways and elevators: rating 4 or 5 | 79.0% | 2537 |
| Flight information screens: rating 4 or 5 | 78.6% | 2611 |
| Indoor signs and directions: rating 4 or 5 | 78.3% | 2648 |
| AirTrain: rating 4 or 5 | 75.8% | 1309 |
| Free Wi-Fi: rating 4 or 5 | 73.1% | 2074 |
| Roadway signs: rating 4 or 5 | 71.8% | 1772 |
| Artwork and exhibitions: rating 4 or 5 | 71.3% | 2160 |
| Information: departures: rating 4 or 5 | 68.2% | 1529 |
| Information: arrivals: rating 4 or 5 | 66.9% | 1518 |
| Rental car center: rating 4 or 5 | 65.5% | 910 |
| Parking facilities: rating 4 or 5 | 64.9% | 1065 |
| Long-term parking shuttle: rating 4 or 5 | 63.3% | 649 |
| Restaurants: rating 4 or 5 | 56.8% | 2342 |
| Retail shops: rating 4 or 5 | 54.7% | 2277 |

The primary table includes all valid raters of each service. The separate usage table checks three services with same-day purchase/use questions. Wi-Fi is the clearest response-base example: 73.1% among 2,074 valid raters compared with 82.4% among 1,353 valid same-day users.

### Correlations are exploratory co-ratings

`rating_associations.csv` reports unweighted pairwise Spearman correlations between each service's valid 1-5 score and the valid overall airport rating. The unweighted choice is explicit and differs from weighted headline estimates. Each pair uses its own response base and excludes invalid scores.

These correlations identify co-rating patterns. They are not estimated causal importance, incremental drivers, or a basis for an ROI ranking. Common questionnaire context, passenger sentiment, service exposure, missing ratings and relationships among services can all contribute. The project does not claim that improving the most correlated service will raise overall satisfaction by a known amount.

## Actions to investigate

| Evidence | Proposed follow-up | Ownership and measure needed |
| --- | --- | --- |
| Security/immigration appears for 35.8% of problem reporters | Inspect which coded security experiences account for complaints, then connect them with queue and service records | Joint work with relevant airport/security partners; queue time, incident type, complaint resolution |
| Restaurants and retail have lower rating shares | Investigate value, availability, assortment and service using targeted follow-up questions and concession data | Commercial/concession teams; reasons for low ratings, availability, service recovery and value perceptions |
| Recommendation differs by problem status | Follow up problem resolution and recovery rather than assuming the survey gap is an improvement effect | Customer experience team with partner organizations; resolution experience and later recommendation |
| Wi-Fi results depend on who rates it | Define an actual-user measure and check access, connection and task completion | Digital/service teams; connection success, completion and user-rated experience |

These are research and test priorities. The file does not identify the organization responsible for each issue or contain the costs, causal uplift and revenues required for a financial business case.

## Reliability and limitations

- **Historical scope:** only 2018 is analysed. No current performance claim or time trend is inferred.
- **Coverage and nonresponse:** the dictionary describes weights as representing SFO passengers, but the two supplied files do not establish complete sampling, cluster or nonresponse information. Do not generalize to every airport user or claim a simple random sample.
- **Weighting sensitivity:** `metrics_unweighted.csv` permits direct comparison. Overall NPS is +31.0 unweighted versus +35.1 weighted. Problem prevalence is 14.1% unweighted versus 12.9% weighted.
- **Uncertainty:** no formal confidence intervals or p-values are supplied. Full design-based precision is not established by these two files. Kish n does not replace the missing design information.
- **Question bases:** service bases differ and may reflect selective usage or response. Associations and rankings can change with exposure.
- **Shared control:** airlines, security authorities and concessionaires contribute to the experience. The data cannot attribute every problem to airport management.
- **Comments:** the project uses the supplied codes. It does not republish raw comment text, build an unverifiable sentiment score or count multiple codes as multiple people.

## Learning path

1. Read `docs/survey_guide.md` and the metric dictionary.
2. Open the executed notebook and reproduce the valid bases before interpreting percentages.
3. Check NPS with a hand calculation: scores 0 and 10 are valid, while 11 is blank.
4. Compare weighted and unweighted findings, then inspect the Wi-Fi usage sensitivity.
5. Review the action table and explain which additional evidence would test each hypothesis.

## Sources

- [2018 SFO Customer Survey, DataSF](https://data.sf.gov/Transportation/2018-SFO-Customer-Survey/3w8r-nuxp)
- [Official CSV download](https://data.sf.gov/api/views/3w8r-nuxp/rows.csv?accessType=DOWNLOAD)
- [2018 dictionary download](https://data.sf.gov/download/wkh6-n369/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
- [Dictionary catalogue](https://catalog.data.gov/dataset/2018-sfo-customer-survey-data-dictionary)

Source: San Francisco International Airport / DataSF. All estimates are independent calculations. The DataSF survey listing identifies an Open Data Commons Public Domain Dedication and License. Original sources remain credited; no endorsement is implied.
