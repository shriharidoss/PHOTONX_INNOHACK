# Cuffless Blood-Pressure Estimation from MAX30102 PPG

This project trains a **PPG-only 1D CNN** to estimate:
- SBP (systolic blood pressure)
- DBP (diastolic blood pressure)

Dataset: UCI Cuff-Less Blood Pressure Estimation Dataset.

The UCI dataset contains synchronized PPG, ABP and ECG at 125 Hz. This project uses **PPG only** as the model input because the target hardware is ESP32 + MAX30102. ABP is used only to generate the training labels (SBP/DBP), never as an input.

Important: the model is a research/prototype model, not a medical device.

## Project flow

UCI PPG + ABP
-> quality filtering
-> resample PPG 125 Hz -> 100 Hz
-> 8-second windows (800 samples)
-> PPG band-pass filtering
-> per-window normalization
-> 1D CNN
-> SBP + DBP

## 1. Download the dataset

Download the four UCI files:
Part_1.mat
Part_2.mat
Part_3.mat
Part_4.mat

Put them inside:
data/raw/

The complete UCI download is about 3.1 GB, so the dataset is intentionally NOT included in this package.

Official dataset:
https://archive.ics.uci.edu/dataset/340/cuff

## 2. Install

Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## 3. Preprocess

Run:

python preprocess.py

For a first test, edit MAX_RECORDS in preprocess.py to a small number such as 100.
For the full run, set MAX_RECORDS = None.

The script:
- reads MATLAB v7.3 files with h5py
- extracts channel 1 PPG and channel 2 ABP
- rejects invalid/abnormal ABP
- band-pass filters PPG
- creates 8-second windows
- creates SBP/DBP labels from ABP using robust beat peaks/troughs
- resamples PPG to 100 Hz to match the MAX30102 configuration
- saves train/validation/test NPZ files

## 4. Train

python train.py

The best model is saved to:
models/bp_cnn_best.pt

The target scaling is saved to:
models/target_scaler.joblib

## 5. Evaluate

python evaluate.py

Metrics:
- MAE
- RMSE
- R2
- mean error

A scatter plot is saved to:
models/evaluation.png

## 6. Real-time inference

The file infer_ppg.py accepts a CSV containing one PPG column with samples collected at 100 Hz from the MAX30102.

Example:
python infer_ppg.py my_ppg.csv

It uses the same preprocessing and predicts:
SBP and DBP.

## MAX30102 integration

Your Arduino code should collect approximately:
100 samples/second
for about 8 seconds
= about 800 IR samples.

Use the **IR PPG channel** as the model input.

The ESP32 does not need to run the PyTorch model initially. The recommended project architecture is:

MAX30102 -> ESP32 -> serial/Wi-Fi -> Python inference -> SBP/DBP

After the model is validated, it can be converted/quantized for an embedded deployment if required.

## Safety

This is not a medical device. Do not use the predicted BP for diagnosis, medication decisions, or emergency decisions. Validate the prototype against a clinically appropriate cuff before making health claims.
