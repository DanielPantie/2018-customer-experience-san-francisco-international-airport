# Validation record

The project was extracted into a clean directory containing no raw CSV or
dictionary. Its analysis command downloaded both official DataSF sources,
verified their bytes, rebuilt all outputs and executed all notebook cells.
All **ten tests passed** on the public-export data and on the user-supplied CSV.

## Source verification

- Survey rows: 2,809. Columns: 97.
- Duplicate respondent IDs: zero.
- Missing/nonpositive weights: zero.
- User-export CSV SHA-256: `bb2e61e215983121b767a36e3f85d86424d890128e94a2010d800fbda843741c`.
- Public-export CSV SHA-256: `8d8e368dffb048679044159486bf89c5b838c7dbff731304ba02d4a8a2099c8b`.
- Dictionary SHA-256: `63b264f9215516c012991f13b08a4567d54166751997efd592e1a3962d65fbe2`.

The two CSV exports have different byte formatting. The source regression
checks establish matching headline counts and estimates. The dictionary
bytes are identical.

## Logic and artifact checks

- Correct handling of 0 and 11 for recommendation and 6/BLANK for ratings.
- Explicit unknown outcomes for the problem question.
- No double counting of a respondent with several codes in the same theme.
- Uncoded problem reporters remain in the theme denominator.
- Header whitespace and respondent-ID normalization.
- Weighted arithmetic, scaling invariance, empty groups and invalid-source failures.
- Recommendation categories sum to 100%; promoter share minus detractor share equals NPS.
- Wi-Fi usage base and problem-group NPS match source regression values.
- All ten notebook code cells executed with no errors or stderr output.
- The ten-page PDF was rendered and visually reviewed; an overlap found on page 3 was corrected.
- The release ZIP excludes raw CSV/XLSX files and Python cache files.

These checks establish implementation consistency, not causal validity or
full survey-design precision. They were performed with the pinned Python
dependencies in the preparation environment. PDF creation metadata can differ
between runs while the data values and chart content remain reproducible.
