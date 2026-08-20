import os
import re
import glob
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt, resample_poly
from scipy.stats import skew
from sklearn.model_selection import train_test_split
from tqdm import tqdm

DATA_DIR = "data"
TXT_DIR = os.path.join(DATA_DIR, "0_subject")
XLSX_PATH = os.path.join(DATA_DIR, "PPG-BP dataset.xlsx")
OUT_DIR = os.path.join(DATA_DIR, "processed")

FS_IN = 1000
FS_MODEL = 100
EXPECTED_SAMPLES = 2100

# The PPG-BP paper used signal-quality screening.
USE_SKEWNESS_FILTER = True

RANDOM_STATE = 42


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


def load_labels():
    # Row 2 of the Excel file contains the actual column headers.
    df = pd.read_excel(XLSX_PATH, header=1)

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

    if id_col is None or sbp_col is None or dbp_col is None:
        raise RuntimeError(
            "Could not identify ID/SBP/DBP columns. "
            "Run check_dataset.py and inspect the Excel headers."
        )

    labels = {}

    for _, row in df.iterrows():
        try:
            subject_id = int(float(row[id_col]))
            sbp = float(row[sbp_col])
            dbp = float(row[dbp_col])

            if np.isfinite(sbp) and np.isfinite(dbp):
                labels[subject_id] = (sbp, dbp)

        except Exception:
            continue

    return labels


def bandpass_filter(x, fs):
    # Main pulsatile PPG frequency range.
    sos = butter(
        3,
        [0.5, 8.0],
        btype="bandpass",
        fs=fs,
        output="sos"
    )

    return sosfiltfilt(sos, x)


def normalize_signal(x):
    x = x.astype(np.float32)

    x = x - np.mean(x)

    std = np.std(x)

    if std < 1e-6:
        return None

    x = x / std

    return np.clip(x, -5, 5).astype(np.float32)


def process_signal(filepath):
    # Read one PPG recording.
    x = np.loadtxt(
        filepath,
        dtype=np.float64
    ).ravel()

    # Every PPG-BP recording should contain 2100 samples.
    if len(x) != EXPECTED_SAMPLES:
        return None, "wrong_length"

    if not np.all(np.isfinite(x)):
        return None, "nonfinite"

    if np.std(x) < 1e-6:
        return None, "flat"

    # Signal quality check.
    if USE_SKEWNESS_FILTER:
        signal_skewness = skew(
            x,
            bias=False
        )

        if not np.isfinite(signal_skewness):
            return None, "invalid_skewness"

        if signal_skewness <= 0:
            return None, "skewness"

    # Filter at the original 1000 Hz.
    x = bandpass_filter(
        x,
        FS_IN
    )

    # Convert 1000 Hz to 100 Hz so it matches your MAX30102 setup.
    x = resample_poly(
        x,
        FS_MODEL,
        FS_IN
    )

    # 2100 samples / 1000 Hz = 2.1 seconds.
    # At 100 Hz, this becomes 210 samples.
    if len(x) != 210:
        x = x[:210]

        if len(x) < 210:
            return None, "resample_length"

    x = normalize_signal(x)

    if x is None:
        return None, "normalization"

    return x, None


def main():

    print("====================================")
    print("       PPG-BP PREPROCESSING")
    print("====================================")

    os.makedirs(
        OUT_DIR,
        exist_ok=True
    )

    # Load BP labels from Excel.
    labels = load_labels()

    print(
        "Subjects with BP labels:",
        len(labels)
    )

    # Find all PPG TXT files.
    paths = sorted(
        glob.glob(
            os.path.join(
                TXT_DIR,
                "*_*.txt"
            )
        )
    )

    print(
        "PPG files found:",
        len(paths)
    )

    if not paths:
        raise FileNotFoundError(
            "No TXT files found in data/0_subject/"
        )

    records = []

    skipped = {}

    for filepath in tqdm(
        paths,
        desc="Processing PPG"
    ):

        filename = os.path.basename(filepath)

        match = re.match(
            r"^(\d+)_([123])\.txt$",
            filename
        )

        if not match:
            skipped["filename"] = skipped.get(
                "filename",
                0
            ) + 1
            continue

        subject_id = int(
            match.group(1)
        )

        segment = int(
            match.group(2)
        )

        # Find BP label for this subject.
        if subject_id not in labels:
            skipped["missing_bp"] = skipped.get(
                "missing_bp",
                0
            ) + 1
            continue

        x, reason = process_signal(
            filepath
        )

        if x is None:
            skipped[reason] = skipped.get(
                reason,
                0
            ) + 1
            continue

        sbp, dbp = labels[subject_id]

        # Basic BP sanity check.
        if not (
            70 <= sbp <= 220
            and
            35 <= dbp <= 140
            and
            sbp > dbp
        ):
            skipped["invalid_bp"] = skipped.get(
                "invalid_bp",
                0
            ) + 1
            continue

        records.append(
            {
                "subject": subject_id,
                "segment": segment,
                "ppg": x,
                "sbp": sbp,
                "dbp": dbp
            }
        )

    print()
    print(
        "Valid PPG records:",
        len(records)
    )

    print(
        "Skipped records:",
        sum(skipped.values())
    )

    if skipped:
        print(
            "Skip reasons:",
            skipped
        )

    if len(records) < 50:
        raise RuntimeError(
            "Too few valid records were produced."
        )

    # Get unique subjects.
    subjects = np.array(
        sorted(
            {
                r["subject"]
                for r in records
            }
        )
    )

    print(
        "Unique subjects:",
        len(subjects)
    )

    # IMPORTANT:
    # Split by subject, not by individual PPG segment.
    # This prevents the same person's signals appearing
    # in both training and testing.
    train_subjects, temp_subjects = train_test_split(
        subjects,
        test_size=0.30,
        random_state=RANDOM_STATE
    )

    val_subjects, test_subjects = train_test_split(
        temp_subjects,
        test_size=0.50,
        random_state=RANDOM_STATE
    )

    train_set = set(
        train_subjects
    )

    val_set = set(
        val_subjects
    )

    test_set = set(
        test_subjects
    )

    splits = {
        "train": [],
        "val": [],
        "test": []
    }

    for record in records:

        subject = record["subject"]

        if subject in train_set:
            splits["train"].append(
                record
            )

        elif subject in val_set:
            splits["val"].append(
                record
            )

        elif subject in test_set:
            splits["test"].append(
                record
            )

    # Save each split.
    for split_name, rows in splits.items():

        X = np.asarray(
            [
                r["ppg"]
                for r in rows
            ],
            dtype=np.float32
        )

        y = np.asarray(
            [
                [
                    r["sbp"],
                    r["dbp"]
                ]
                for r in rows
            ],
            dtype=np.float32
        )

        subject_ids = np.asarray(
            [
                r["subject"]
                for r in rows
            ],
            dtype=np.int32
        )

        output_file = os.path.join(
            OUT_DIR,
            split_name + ".npz"
        )

        np.savez_compressed(
            output_file,
            X=X,
            y=y,
            subject=subject_ids
        )

        print()
        print(
            split_name.upper()
        )
        print(
            "Records :",
            len(rows)
        )
        print(
            "Subjects:",
            len(
                set(
                    subject_ids.tolist()
                )
            )
        )
        print(
            "X shape :",
            X.shape
        )
        print(
            "Y shape :",
            y.shape
        )

    print()
    print("====================================")
    print("       PREPROCESSING COMPLETE")
    print("====================================")
    print()
    print("Created:")
    print("data/processed/train.npz")
    print("data/processed/val.npz")
    print("data/processed/test.npz")
    print()
    print("Next command:")
    print("python train.py")


if __name__ == "__main__":
    main()