import os
import sys
import importlib.util

import joblib
import numpy as np
import torch

from scipy.signal import butter, sosfiltfilt


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)


# ============================================================
# LOAD BP MODEL CLASS FROM model.py
# ============================================================

MODEL_PY = os.path.join(
    BASE_DIR,
    "model.py"
)

if not os.path.exists(MODEL_PY):
    raise FileNotFoundError(
        f"BP model definition not found:\n{MODEL_PY}"
    )


spec = importlib.util.spec_from_file_location(
    "bp_model_module",
    MODEL_PY
)

bp_model_module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    bp_model_module
)

BP1DCNN = bp_model_module.BP1DCNN


# ============================================================
# SETTINGS
# ============================================================

FS = 100
WINDOW = 210


# ============================================================
# CHECK TRAINED MODEL FILES
# ============================================================

SCALER_PATH = os.path.join(
    MODEL_DIR,
    "target_scaler.joblib"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "bp_cnn_best.pt"
)


if not os.path.exists(SCALER_PATH):
    raise FileNotFoundError(
        f"Target scaler not found:\n{SCALER_PATH}"
    )


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Trained BP model not found:\n{MODEL_PATH}"
    )


# ============================================================
# PREPROCESS PPG
# ============================================================

def preprocess(ppg):

    ppg = np.asarray(
        ppg,
        dtype=np.float64
    )

    # BP model requires at least 210 samples
    if len(ppg) < WINDOW:

        raise ValueError(
            f"Need at least {WINDOW} PPG samples. "
            f"Received {len(ppg)} samples."
        )

    # Use latest 210 samples
    ppg = ppg[-WINDOW:]

    # Replace invalid values
    median_value = np.nanmedian(ppg)

    ppg = np.nan_to_num(
        ppg,
        nan=median_value
    )

    # --------------------------------------------------------
    # Bandpass filter
    # --------------------------------------------------------

    sos = butter(
        3,
        [0.5, 8.0],
        btype="bandpass",
        fs=FS,
        output="sos"
    )

    ppg = sosfiltfilt(
        sos,
        ppg
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    std = np.std(ppg)

    if std < 1e-6:

        raise ValueError(
            "PPG signal is too flat."
        )

    ppg = (
        ppg - np.mean(ppg)
    ) / std

    # Prevent extreme values
    ppg = np.clip(
        ppg,
        -5,
        5
    )

    return ppg.astype(
        np.float32
    )


# ============================================================
# BLOOD PRESSURE PREDICTION
# ============================================================

def predict_bp(ppg):

    """
    Predict blood pressure from PPG.

    Parameters
    ----------
    ppg : array-like
        IR/PPG signal.

    Returns
    -------
    systolic_bp : float
        Estimated systolic blood pressure.

    diastolic_bp : float
        Estimated diastolic blood pressure.
    """

    # ========================================================
    # PREPROCESS
    # ========================================================

    x = preprocess(
        ppg
    )


    # ========================================================
    # LOAD TARGET SCALER
    # ========================================================

    scaler = joblib.load(
        SCALER_PATH
    )


    # ========================================================
    # LOAD TRAINED CNN
    # ========================================================

    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu"
    )


    model = BP1DCNN()


    model.load_state_dict(
        checkpoint["model_state_dict"]
    )


    model.eval()


    # ========================================================
    # PREPARE INPUT
    # ========================================================

    input_tensor = torch.from_numpy(
        x
    ).view(
        1,
        1,
        WINDOW
    )


    # ========================================================
    # RUN MODEL
    # ========================================================

    with torch.no_grad():

        prediction = model(
            input_tensor
        ).numpy()


    # ========================================================
    # CONVERT MODEL OUTPUT TO mmHg
    # ========================================================

    prediction = scaler.inverse_transform(
        prediction
    )[0]


    systolic_bp = float(
        prediction[0]
    )

    diastolic_bp = float(
        prediction[1]
    )


    return (
        systolic_bp,
        diastolic_bp
    )


# ============================================================
# DIRECT COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("================================")
    print(" BP ML MODEL TEST")
    print("================================")
    print()


    # --------------------------------------------------------
    # Check command-line argument
    # --------------------------------------------------------

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python infer_bp.py <csv_file>"
        )

        sys.exit(1)


    csv_file = sys.argv[1]


    # --------------------------------------------------------
    # Check CSV
    # --------------------------------------------------------

    if not os.path.exists(csv_file):

        raise FileNotFoundError(
            f"PPG CSV not found:\n{csv_file}"
        )


    print(
        "PPG file:",
        csv_file
    )


    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    raw = np.genfromtxt(
        csv_file,
        delimiter=",",
        names=True
    )


    names = list(
        raw.dtype.names or []
    )


    if not names:

        raise ValueError(
            "CSV has no readable columns."
        )


    print(
        "CSV columns:",
        names
    )


    # --------------------------------------------------------
    # Find PPG / IR column
    # --------------------------------------------------------

    selected_column = None


    for candidate in [
        "ir",
        "IR",
        "ppg",
        "PPG",
        "value"
    ]:

        if candidate in names:

            selected_column = candidate

            break


    # --------------------------------------------------------
    # If no named PPG column exists,
    # use first column
    # --------------------------------------------------------

    if selected_column is None:

        print(
            "IR/PPG column not found by name."
        )

        print(
            "Using first column:",
            names[0]
        )

        selected_column = names[0]


    print(
        "Using PPG column:",
        selected_column
    )


    # --------------------------------------------------------
    # Extract PPG
    # --------------------------------------------------------

    ppg = np.asarray(
        raw[selected_column],
        dtype=np.float32
    )


    print(
        "PPG samples:",
        len(ppg)
    )


    # --------------------------------------------------------
    # Calculate BP
    # --------------------------------------------------------

    sbp, dbp = predict_bp(
        ppg
    )


    # --------------------------------------------------------
    # Display result
    # --------------------------------------------------------

    print()
    print("================================")
    print(" BLOOD PRESSURE RESULT")
    print("================================")

    print(
        f"Estimated SBP: {sbp:.1f} mmHg"
    )

    print(
        f"Estimated DBP: {dbp:.1f} mmHg"
    )

    print()