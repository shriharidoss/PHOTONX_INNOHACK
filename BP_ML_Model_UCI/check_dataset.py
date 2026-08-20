import os
import re
import numpy as np
import pandas as pd

DATA_DIR = "data"
TXT_DIR = os.path.join(DATA_DIR, "0_subject")
XLSX_PATH = os.path.join(DATA_DIR, "PPG-BP dataset.xlsx")


def find_column(columns, candidates):
    normalized = {
        str(c).strip().lower().replace(" ", "").replace("_", ""): c
        for c in columns
    }

    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]

    for col in columns:
        value = str(col).strip().lower().replace(" ", "").replace("_", "")
        for candidate in candidates:
            key = candidate.lower().replace(" ", "").replace("_", "")
            if key in value:
                return col

    return None


print("====================================")
print("       PPG-BP DATASET CHECK")
print("====================================")

if not os.path.exists(XLSX_PATH):
    raise FileNotFoundError(
        f"Excel file not found:\n{XLSX_PATH}"
    )

if not os.path.isdir(TXT_DIR):
    raise FileNotFoundError(
        f"PPG folder not found:\n{TXT_DIR}"
    )

# Read Excel file
df = pd.read_excel(XLSX_PATH, header=1)

print("\nExcel columns:")
for column in df.columns:
    print(" ", column)

# Find required columns
id_col = find_column(
    df.columns,
    ["ID", "SubjectID", "Subject"]
)

sbp_col = find_column(
    df.columns,
    ["SBP", "SystolicPressure", "Systolic"]
)

dbp_col = find_column(
    df.columns,
    ["DBP", "DiastolicPressure", "Diastolic"]
)

print("\nDetected columns:")
print("Subject ID :", id_col)
print("SBP        :", sbp_col)
print("DBP        :", dbp_col)

if id_col is None or sbp_col is None or dbp_col is None:
    raise RuntimeError(
        "\nCould not identify the ID, SBP or DBP columns."
        "\nCheck the Excel column names printed above."
    )

# Create subject -> BP mapping
subject_map = {}

for _, row in df.iterrows():
    try:
        subject_id = int(float(row[id_col]))
        sbp = float(row[sbp_col])
        dbp = float(row[dbp_col])

        if np.isfinite(sbp) and np.isfinite(dbp):
            subject_map[subject_id] = (sbp, dbp)

    except Exception:
        continue

# Find PPG files
files = sorted(
    [
        f for f in os.listdir(TXT_DIR)
        if f.lower().endswith(".txt")
    ]
)

print("\nNumber of TXT files found:", len(files))
print("Number of subjects with BP labels:", len(subject_map))

# Check files
valid_files = 0
invalid_names = 0
wrong_length = 0
matched_files = 0

print("\nFirst 10 files:")

for filename in files[:10]:

    match = re.match(
        r"^(\d+)_([123])\.txt$",
        filename
    )

    if not match:
        print(filename, "-> filename format not recognized")
        invalid_names += 1
        continue

    subject_id = int(match.group(1))
    segment = int(match.group(2))

    filepath = os.path.join(
        TXT_DIR,
        filename
    )

    try:
        signal = np.loadtxt(
            filepath,
            dtype=np.float64
        ).ravel()

        samples = len(signal)

        if samples == 2100:
            valid_files += 1
        else:
            wrong_length += 1

        if subject_id in subject_map:
            sbp, dbp = subject_map[subject_id]
            matched_files += 1

            print(
                f"{filename} | "
                f"Subject: {subject_id} | "
                f"Segment: {segment} | "
                f"Samples: {samples} | "
                f"SBP: {sbp} | "
                f"DBP: {dbp}"
            )

        else:
            print(
                f"{filename} | "
                f"Subject: {subject_id} | "
                f"BP label NOT FOUND"
            )

    except Exception as e:
        print(
            f"{filename} -> ERROR: {e}"
        )

print("\n====================================")
print("             SUMMARY")
print("====================================")

print(
    "TXT files found       :",
    len(files)
)

print(
    "Correct length files  :",
    valid_files,
    "(expected approximately 657)"
)

print(
    "Wrong length files    :",
    wrong_length
)

print(
    "Matched with BP       :",
    matched_files
)

print(
    "Invalid filenames     :",
    invalid_names
)

print(
    "Subjects with BP      :",
    len(subject_map)
)

print("====================================")

if len(files) == 657 and matched_files > 0:
    print("DATASET STRUCTURE LOOKS GOOD!")
    print("\nNext command:")
    print("python preprocess.py")
else:
    print("Please check the dataset structure before preprocessing.")
