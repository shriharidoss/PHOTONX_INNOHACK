import os
import numpy as np
import joblib
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from model import BP1DCNN

DATA_DIR = "data/processed"
MODEL_DIR = "models"


def main():
    d = np.load(os.path.join(DATA_DIR, "test.npz"))
    X = d["X"].astype(np.float32)
    y = d["y"].astype(np.float32)

    scaler = joblib.load(os.path.join(MODEL_DIR, "target_scaler.joblib"))

    ckpt = torch.load(
        os.path.join(MODEL_DIR, "bp_cnn_best.pt"),
        map_location="cpu"
    )
    model = BP1DCNN()
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    with torch.no_grad():
        pred_s = model(torch.from_numpy(X).unsqueeze(1)).numpy()

    pred = scaler.inverse_transform(pred_s)

    print("\n=== TEST RESULTS ===")
    for j, name in enumerate(["SBP", "DBP"]):
        mae = mean_absolute_error(y[:, j], pred[:, j])
        rmse = np.sqrt(mean_squared_error(y[:, j], pred[:, j]))
        r2 = r2_score(y[:, j], pred[:, j])
        me = np.mean(pred[:, j] - y[:, j])

        print(f"{name}:")
        print(f"  MAE  : {mae:.2f} mmHg")
        print(f"  RMSE : {rmse:.2f} mmHg")
        print(f"  R2   : {r2:.3f}")
        print(f"  Mean error: {me:.2f} mmHg")

    fig = plt.figure(figsize=(7, 6))
    plt.scatter(y[:, 0], pred[:, 0], s=8, alpha=0.4, label="SBP")
    plt.scatter(y[:, 1], pred[:, 1], s=8, alpha=0.4, label="DBP")
    lo = min(y.min(), pred.min())
    hi = max(y.max(), pred.max())
    plt.plot([lo, hi], [lo, hi])
    plt.xlabel("Reference BP (mmHg)")
    plt.ylabel("Predicted BP (mmHg)")
    plt.title("BP Prediction on Test Set")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, "evaluation.png"), dpi=200)
    print("\nSaved:", os.path.join(MODEL_DIR, "evaluation.png"))


if __name__ == "__main__":
    main()
