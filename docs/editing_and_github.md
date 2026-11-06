# Edit the project and publish it on GitHub

## Suggested repository

- Name: `sfo-2018-customer-experience`
- Description: `A reproducible Python customer experience case study using SFO's 2018 passenger survey.`
- Topics: `python`, `customer-experience`, `survey-analysis`, `nps`, `data-analysis`, `sfo`

## What to upload

Extract the project ZIP. Upload the **contents of `sfo_case_study`**, so
README.md is at the repository's top level. Keep all project folders and files
together. Raw CSV/XLSX inputs are excluded from the ZIP and are retrieved by
the download script. Do not upload the ZIP itself as your only project file.

Create an empty GitHub repository, use its upload-existing-files option, and
drag the extracted contents into it. Commit the upload. Alternatively, use:

```bash
git init
git add .
git commit -m "Add SFO 2018 customer experience case study"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace YOUR_REPOSITORY_URL with the repository URL GitHub provides.
No GitHub repository is created or pushed by this package.

## Which text file should I edit?

| What you want to change | Edit this source | Rebuild needed? |
| --- | --- | --- |
| Main project introduction | README.md | No |
| Survey learning guide | docs/survey_guide.md | No |
| Case-study wording | reports/case_study_template.md | Yes |
| Carousel headings and notes | presentation/carousel_content.json | Yes |
| LinkedIn caption | presentation/linkedin_caption.md | No |
| Metric definitions or calculations | src/sfo_cx/analysis.py | Yes, and rerun tests |
| Chart layout or notebook explanations | scripts/build_outputs.py | Yes |

You can edit Markdown, JSON and Python text in GitHub's file editor.
Preserve JSON syntax and numeric placeholders such as `{{NPS_GAP_0}}`.
These placeholders fill from computed results rather than manual numbers.

Run `python scripts/run_analysis.py` locally after changing a source template,
then upload the regenerated report/PDF/notebook. GitHub text editing does not
run Python automatically. Direct edits to generated output files can be
overwritten on the next rebuild.

Edit the notebook in Jupyter or VS Code. This package's build also regenerates
the guided notebook from the generator, so keep permanent instructional
changes in the generator if you continue using it.

After publishing, put the real repository link in the LinkedIn caption and
your portfolio. No placeholder repository URL appears in the carousel.
