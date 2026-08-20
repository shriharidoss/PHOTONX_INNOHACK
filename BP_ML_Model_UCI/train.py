import os
import json
import numpy as np
import joblib
import torch
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from model import BP1DCNN

DATA_DIR = "data/processed"
MODEL_DIR = "models"
BATCH_SIZE = 256
EPOCHS = 30
LR = 1e-3
SEED = 42


def load_npz(name):
    d = np.load(os.path.join(DATA_DIR, name + ".npz"))
    return d["X"].astype(np.float32), d["y"].astype(np.float32)


def make_loader(X, y, batch, shuffle):
    X = torch.from_numpy(X).unsqueeze(1)
    y = torch.from_numpy(y)
    return DataLoader(TensorDataset(X, y), batch_size=batch, shuffle=shuffle, num_workers=0)


def evaluate(model, loader, device):
    model.eval()
    ys, ps = [], []
    with torch.no_grad():
        for xb, yb in loader:
            pred = model(xb.to(device)).cpu().numpy()
            ys.append(yb.numpy())
            ps.append(pred)
    y = np.vstack(ys)
    p = np.vstack(ps)

    metrics = {}
    for j, name in enumerate(["SBP", "DBP"]):
        metrics[name + "_MAE"] = float(mean_absolute_error(y[:, j], p[:, j]))
        metrics[name + "_RMSE"] = float(np.sqrt(mean_squared_error(y[:, j], p[:, j])))
        metrics[name + "_R2"] = float(r2_score(y[:, j], p[:, j]))
        metrics[name + "_ME"] = float(np.mean(p[:, j] - y[:, j]))
    return metrics


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    X_train, y_train = load_npz("train")
    X_val, y_val = load_npz("val")

    # Scale targets using training set only.
    scaler = StandardScaler()
    y_train_s = scaler.fit_transform(y_train).astype(np.float32)
    y_val_s = scaler.transform(y_val).astype(np.float32)
    joblib.dump(scaler, os.path.join(MODEL_DIR, "target_scaler.joblib"))

    train_loader = make_loader(X_train, y_train_s, BATCH_SIZE, True)
    val_loader = make_loader(X_val, y_val_s, BATCH_SIZE, False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    model = BP1DCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
    loss_fn = torch.nn.SmoothL1Loss()

    best_val = float("inf")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        running = 0.0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)

            optimizer.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            running += loss.item() * xb.size(0)

        train_loss = running / len(train_loader.dataset)

        val_metrics_scaled = evaluate(model, val_loader, device)
        # These metrics are in scaled target units only; use the separate evaluate.py
        # for the final original-mmHg metrics.
        val_loss_proxy = val_metrics_scaled["SBP_RMSE"] + val_metrics_scaled["DBP_RMSE"]

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"train_loss={train_loss:.5f} | "
            f"val_proxy={val_loss_proxy:.5f}"
        )

        if val_loss_proxy < best_val:
            best_val = val_loss_proxy
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "input_samples": 800,
                    "sample_rate": 100,
                    "targets": ["SBP", "DBP"]
                },
                os.path.join(MODEL_DIR, "bp_cnn_best.pt")
            )

    print("\nTraining finished.")
    print("Saved:", os.path.join(MODEL_DIR, "bp_cnn_best.pt"))
    print("Saved:", os.path.join(MODEL_DIR, "target_scaler.joblib"))


if __name__ == "__main__":
    main()
