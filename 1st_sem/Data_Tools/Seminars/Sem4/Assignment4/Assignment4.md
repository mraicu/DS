## Exercise 1

Original -> cheese_analyses_v1.0.0_2025-03-10.csv

Version A – Correct two numeric values (patch -> v1.0.1)

-   File name: cheese_analyses_v1.0.1_2025-03-10.csv
-   Description: Version number changed from 1.0.0 to 1.0.1 because we applied a small, backward-compatible bugfix correcting two incorrect quantity values.

Version B – Add a new derived column (minor -> v1.1.0)

-   File name: cheese_analyses_v1.1.0_2025-03-10.csv
-   Now start from Version A and add a new derived numeric column:
-   New column: quantity_per_month = quantity / months (rounded to 3 decimals).
-   Description: Version number changed from 1.0.1 to 1.1.0 because we added a new derived column (quantity_per_month), which is a backward-compatible feature addition.

Version C – Remove rows with missing data (major -> v2.0.0)

-   File name: cheese_analyses_v2.0.0_2025-03-10.csv
-   Description: Version number changed from 1.1.0 to 2.0.0 because removing rows with missing data is a potentially destructive, backward-incompatible change to the dataset (even though in this case no rows were actually dropped).

## Exercise 2

1.

```
data/
    raw/
    interim/
    cleaned/
    analysis_ready/
    data_version.txt
```

2.

```
data/
    raw/cheese_analyses_v1.0.0_2025-03-10.csv
    interim/cheese_analyses_v1.0.1_2025-03-10.csv
    cleaned/cheese_analyses_v1.1.0_2025-03-10.csv
    analysis_ready/cheese_analyses_v2.0.0_2025-03-10.csv
    data_version.txt
```

3.

README.md

```md
# RAW DATA

## What belongs here

Unmodified datasets exactly as received from source systems, field collection, or collaborators.

## Who should modify files here

No one. Raw data is append-only and must never be overwritten or edited.

## When data is allowed to move to the next stage

Only after validation, initial inspection, and once a reproducible script is created for parsing / cleaning.

## What never goes into this folder

No intermediate datasets, no corrected datasets, no manually edited files, and no derived columns.
```

```md
# INTERIM DATA

## What belongs here

Temporary datasets produced during cleaning, exploration, or preprocessing steps
(e.g., partially cleaned data, flagged records, datasets with placeholder fixes).

## Who should modify files here

Data engineers or analysts performing cleaning and validation.

## When data is allowed to move to the next stage

When all required cleaning operations are complete and documented,
and the dataset is ready to become an official cleaned version.

## What never goes into this folder

Final cleaned datasets, analysis-ready data, or raw unmodified files.
```

```md
# CLEANED DATA

## What belongs here

Fully cleaned datasets with corrected values, consistent formats, removed invalid records,
and documented transformations. These datasets reflect the best-known truth of the data.

## Who should modify files here

Only authorized data engineers or project maintainers.
All changes must be version-controlled and documented.

## When data is allowed to move to the next stage

Once the cleaned dataset is validated, stable, and no further structural changes are expected.

## What never goes into this folder

Raw data, experimental transformations, or files not intended for broad consumption.
```

```md
# ANALYSIS-READY DATA

## What belongs here

Datasets that are fully cleaned AND feature engineered, with derived columns, encoded fields,
aggregations, or modeling-ready formats.

## Who should modify files here

Data analysts or modelers following reproducible scripts.

## When data is allowed to move to the next stage

This is the final stage—data here is ready for statistical analysis, dashboards, ML models.

## What never goes into this folder

Raw or partially cleaned data, manual edits, or undocumented transformations.
```

4. data_version.txt

```
DATA VERSION: v2.0.0
DATE: 2025-03-10

SUMMARY OF CHANGES:
- Raw dataset (cheese_analyses.csv) ingested into data/raw/.
- Version 1.0.1: Applied two numeric corrections (patch update).
- Version 1.1.0: Added derived column 'quantity_per_month' (minor update).
- Version 2.0.0: Performed row-removal step for missing data (major lifecycle step).
- Cleaned and analysis-ready versions prepared and placed into respective folders.

NOTES:
- Raw data remains untouched and stored in data/raw/.
- All transformations performed through reproducible scripts.
- Dataset maturity now advanced from raw → interim → cleaned → analysis_ready.
```

## Exercise 3

1. Python

```Python
import hashlib
from pathlib import Path

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

files = [
    "data/raw/cheese_analyses.csv",
    "data/interim/cheese_analyses_v1.0.1_2025-03-10.csv",
    "data/cleaned/cheese_analyses_v1.1.0_2025-03-10.csv",
    "data/analysis_ready/cheese_analyses_v2.0.0_2025-03-10.csv",
]

for f in files:
    print(f, "->", sha256_file(f))

```

2.

-   cheese_analyses.csv -> b1ab501103919722e49051805c57028eb6e3bfecc1cda7736324799044186318
-   cheese_analyses_v1.0.1_2025-03-10.csv -> cc70e985d68406b0b2437c97bd698b3dfa46d13c9157482dd5ade66b43936fcc
-   cheese_analyses_v1.1.0_2025-03-10.csv -> 5dd74945ff3e007d5afea91658c7ec3943a88b687db7a7a60ef8e37e88770fda
-   cheese_analyses_v2.0.0_2025-03-10.csv -> 5dd74945ff3e007d5afea91658c7ec3943a88b687db7a7a60ef8e37e88770fda

3 & 4.

```md
## 2025-03-10 – Version 1.0.0 (Initial Raw Ingest)

Changes:

-   Ingested the original `cheese_analyses.csv` dataset exactly as received from the source, with no transformations or corrections applied.

Reason:

-   Establish a frozen baseline snapshot of the raw data for auditability and reproducibility.

Integrity:

-   SHA256: b1ab501103919722e49051805c57028eb6e3bfecc1cda7736324799044186318

Possible impact on analysis:

-   Contains potential transcription or data-entry errors; should not be used directly for final analysis but can be used to verify all later transformations.

---

## 2025-03-10 – Version 1.0.1

Changes:

-   Corrected 2 numeric quantity values that were originally recorded as 0 (for `2025-04-30, roachford, 6 months` and `2025-09-21, brie, 10 months`) to realistic non-zero values.

Reason:

-   Fixing transcription / data-entry errors identified during manual QA checks.

Integrity:

-   SHA256: cc70e985d68406b0b2437c97bd698b3dfa46d13c9157482dd5ade66b43936fcc

Possible impact on analysis:

-   Descriptive statistics and any analyses involving those specific records (e.g., average quantity per cheese type, time series totals) will change slightly; results are now more accurate but no structural changes were introduced.

---

## 2025-03-10 – Version 1.1.0

Changes:

-   Based on v1.0.1, added a new derived column `quantity_per_month = quantity / months` for each record.
-   No further corrections to existing numeric fields.

Reason:

-   Provide an analysis-friendly feature representing normalized quantity per maturation month, reducing repeated transformations by analysts.

Integrity:

-   SHA256: 5dd74945ff3e007d5afea91658c7ec3943a88b687db7a7a60ef8e37e88770fda

Possible impact on analysis:

-   Enables simpler and more consistent modeling and visualization (e.g., comparisons across cheeses with different maturation periods); existing analyses using only the original columns remain compatible but can now use the new feature.

---

## 2025-03-10 – Version 2.0.0

Changes:

-   Applied a “remove rows with missing data” step to the v1.1.0 dataset; in this particular dataset, no rows actually contained missing values, so the resulting file is byte-identical to v1.1.0.

Reason:

-   Promote the dataset to an "analysis-ready" lifecycle stage with an explicit integrity check for missing values, even if no rows were dropped this time.

Integrity:

-   SHA256: 5dd74945ff3e007d5afea91658c7ec3943a88b687db7a7a60ef8e37e88770fda

Possible impact on analysis:

-   No change in numeric results compared to v1.1.0 (hash confirms identical content), but downstream users can rely on the guarantee that this version has passed a missing-data filter and is considered stable and final for analysis.
```
