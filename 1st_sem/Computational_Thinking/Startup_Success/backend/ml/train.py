import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset
from torch import optim, nn

from LogisticRegression import LogisticRegressionModel


def main():
    # Paths
    here = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(here, "..", "app", "data", "startup_failure_prediction.csv"))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    save_path = os.path.join(repo_root, "model.pt")

    # Load dataset
    df = pd.read_csv(data_path)

    target_col = "Startup_Status"
    drop_cols = [c for c in ["Startup_Name"] if c in df.columns]

    X_df = df.drop(columns=[target_col] + drop_cols)
    y_series = df[target_col].astype(float)

    # One-hot encode categorical columns
    X_df = pd.get_dummies(X_df, drop_first=True)

    # DEBUG: show non-numeric columns
    non_numeric = X_df.select_dtypes(include=["object"]).columns
    if len(non_numeric) > 0:
        print("Non-numeric columns detected:", list(non_numeric))

    # Convert everything to numeric
    X_df = X_df.apply(pd.to_numeric, errors="coerce")

    # Fill any NaNs that might result
    X_df = X_df.fillna(0)

    # Final safety check
    print("All columns numeric:", all(np.issubdtype(dt, np.number) for dt in X_df.dtypes))

    # Convert to tensors
    X = torch.tensor(X_df.to_numpy(dtype=np.float32))
    y = torch.tensor(y_series.to_numpy(dtype=np.float32).reshape(-1, 1))

    # Train/validation split
    n = X.shape[0]
    idx = np.random.RandomState(42).permutation(n)
    split = int(0.8 * n)

    train_idx_t = torch.from_numpy(idx[:split]).long()
    val_idx_t = torch.from_numpy(idx[split:]).long()

    X_train = X.index_select(0, train_idx_t)
    y_train = y.index_select(0, train_idx_t)

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

    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")


if __name__ == "__main__":
    main()
