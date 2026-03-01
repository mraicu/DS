import argparse
import os
import numpy as np
import pandas as pd
import torch
import joblib
from torch.utils.data import DataLoader, TensorDataset
from torch import optim, nn

from LogisticRegression import LogisticRegressionModel
from XGBoost import XGBoostModel
from sklearn.metrics import classification_report

from preprocessor import GrowthPreprocessor 


def parse_args():
    parser = argparse.ArgumentParser(description="Train startup success models.")
    parser.add_argument(
        "--model",
        choices=["logistic", "xgboost"],
        default="logistic",
        help="Model type to train.",
    )
    return parser.parse_args()


def save_metrics(y_true, y_pred, metrics_path):
    report = classification_report(
        y_true,
        y_pred,
        target_names=["Not Profitable", "Profitable"],
        output_dict=True,
        zero_division=0,
    )
    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv(metrics_path)
    print("Per-class evaluation metrics:")
    print(report_df)
    print(f"Metrics saved to {metrics_path}")


def main():
    args = parse_args()
    # Paths
    here = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(here, "..", "app", "data", "startup_data_growth.csv"))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    preproc_path = os.path.join(repo_root, "preprocessor.pkl")

    # Load raw dataset (original columns: Startup Name, Industry, Region, Exit Status, etc.)
    df = pd.read_csv(data_path)

    # --- Preprocessing ---
    preproc = GrowthPreprocessor()
    X_df, y_series = preproc.fit_transform(df)

    # Quick sanity check
    print("Training feature columns:", len(preproc.feature_cols))
    print("First few columns:", preproc.feature_cols[:5])

    X_np = X_df.to_numpy(dtype=np.float32)
    y_np = y_series.to_numpy(dtype=np.float32)

    # Train/val split
    n = X_np.shape[0]
    idx = np.random.RandomState(42).permutation(n)
    split = int(0.8 * n)

    n = X_np.shape[0]
    idx = np.random.RandomState(42).permutation(n)
    split = int(0.8 * n)

    train_idx = idx[:split]
    val_idx = idx[split:]

    # Save preprocessor
    joblib.dump({
    "numeric_cols": preproc.numeric_cols,
    "feature_cols": preproc.feature_cols,
    "scaler": preproc.scaler
    }, preproc_path)

    print(f"Preprocessor saved to {preproc_path}")

    if args.model == "logistic":
        model_path = os.path.join(repo_root, "model_lr.pt")
        metrics_path = os.path.join(repo_root, "evaluation_metrics.csv")

        X_train = torch.tensor(X_np[train_idx], dtype=torch.float32)
        y_train = torch.tensor(y_np[train_idx].reshape(-1, 1), dtype=torch.float32)
        X_val = torch.tensor(X_np[val_idx], dtype=torch.float32)
        y_val = torch.tensor(y_np[val_idx].reshape(-1, 1), dtype=torch.float32)

        # DataLoader
        batch_size = 128
        train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)

        # Model setup
        input_dim = X_train.shape[1]
        model = LogisticRegressionModel(input_dim)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=1e-2)

        # Training loop
        model.train()
        epochs = 20
        for epoch in range(epochs):
            total_loss = 0.0
            for xb, yb in train_loader:
                optimizer.zero_grad(set_to_none=True)
                preds = model(xb)
                loss = criterion(preds, yb)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")

        # Save model
        torch.save(model.state_dict(), model_path)
        print(f"Model saved to {model_path}")

        # Evaluation
        model.eval()
        with torch.no_grad():
            val_probs = model(X_val)
            val_preds = (val_probs >= 0.5).float()

            y_true = y_val.cpu().numpy().ravel().astype(int)
            y_pred = val_preds.cpu().numpy().ravel().astype(int)

        save_metrics(y_true, y_pred, metrics_path)
    else:
        model_path = os.path.join(repo_root, "model_xgboost.pt")
        metrics_path = os.path.join(repo_root, "evaluation_metrics_xgboost.csv")

        X_train = X_np[train_idx]
        y_train = y_np[train_idx].astype(int)
        X_val = X_np[val_idx]
        y_val = y_np[val_idx].astype(int)

        # Compute class imbalance from TRAINING DATA ONLY
        num_pos = (y_train == 1).sum()
        num_neg = (y_train == 0).sum()
        scale_pos_weight = num_neg / num_pos

        print(f"scale_pos_weight = {scale_pos_weight:.2f}")

        model = XGBoostModel(scale_pos_weight=scale_pos_weight)
        model.fit(X_train, y_train)

        model.save(model_path)
        print(f"Model saved to {model_path}")

        val_probs = model.predict_proba(X_val)
        y_pred = (val_probs >= 0.5).astype(int)

        save_metrics(y_val, y_pred, metrics_path)



if __name__ == "__main__":
    main()
