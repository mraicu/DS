## Exercise 7: Fix the Project Structure

Reorganized folder tree

```
project/
├── data/
│   ├── raw/
│   │   └── dataset_raw.csv              # renamed from: data.csv
│   └── processed/
│       └── dataset_processed_v2.xlsx    # renamed from: final_v2.xlsx
├── src/
│   └── run_pipeline.py                  # renamed from: script.py
├── reports/
│   └── project_notes.txt                # renamed from: notes.txt
└── README.md

```

I separated files by purpose: immutable inputs go in data/raw, cleaned/ready outputs go in data/processed, code lives in src, and human-readable outputs/notes go in reports to keep analysis artifacts distinct from code and data. Filenames use consistent snake*case, avoid vague labels like “final”, and include lifecycle stage + versioning (e.g., *\_raw, \_\_processed_v2) to improve traceability and reproducibility.

---

## Exercise 8: Detect a Changed File

```python
import hashlib

def sha256_checksum(file_path, chunk_size=8192):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


checksum_before = sha256_checksum("data.csv")
# modify one value in data.csv
checksum_after = sha256_checksum("data.csv")

print(checksum_before)
print(checksum_after)
```

data.csv:

before:

```
a,b,c,d
1,2,3,4
2,3,4,5
3,4,5,6
```

after:

```
a,b,c,d
1,2,3,4
2,3,4,5
3,4,5,7
```

-   checksum before: fda2b565323b24c356ac802ce9d7ba06f90f62a5ed25730c4b1989c3b25d46b9
-   checksum after: 2e3e83067739fe2b6c02ff78d1d81098dbf9ae6f6d064bb668fee786260749c0

Did the checksum change?
Yes. Even modifying a single value in the file produces a completely different SHA-256 checksum.

Why is this useful in collaborative research?
Checksums guarantee data integrity: collaborators can verify that a dataset has not been altered, corrupted, or replaced during sharing, downloading, or storage. This is essential for reproducibility, version control, and trust in shared scientific results.
