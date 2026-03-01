import os
import numpy as np
import pandas as pd
import torch
import joblib
from torch.utils.data import DataLoader, TensorDataset
from torch import optim, nn

from LogisticRegression import LogisticRegressionModel


from preprocessor import GrowthPreprocessor 


def main():
    # Paths
    here = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(here, "..", "app", "data", "startup_data_growth.csv"))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    model_path = os.path.join(repo_root, "model.pt")
    preproc_path = os.path.join(repo_root, "preprocessor.pkl")

    # Load raw dataset (original columns: Startup Name, Industry, Region, Exit Status, etc.)
    df = pd.read_csv(data_path)

    # --- Preprocessing ---
    preproc = GrowthPreprocessor()
    X_df, y_series = preproc.fit_transform(df)

    # Quick sanity check
    print("Training feature columns:", len(preproc.feature_cols))
    print("First few columns:", preproc.feature_cols[:5])

    # Convert to tensors
    X = torch.tensor(X_df.to_numpy(dtype=np.float32))
    y = torch.tensor(y_series.to_numpy(dtype=np.float32).reshape(-1, 1))

    # Train/val split
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

    # Save model
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

    # Save preprocessor
    joblib.dump({
    "numeric_cols": preproc.numeric_cols,
    "feature_cols": preproc.feature_cols,
    "scaler": preproc.scaler
    }, preproc_path)

    print(f"Preprocessor saved to {preproc_path}")

if __name__ == "__main__":
    main()
