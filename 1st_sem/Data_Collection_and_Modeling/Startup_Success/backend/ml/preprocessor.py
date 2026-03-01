import pandas as pd
from sklearn.preprocessing import RobustScaler


class GrowthPreprocessor:
    """
    Handles:
      - One-hot encoding of Industry, Region, Exit Status
      - Robust scaling of numeric features
      - Dropping ID/target columns from X
      - Remembering columns so we can apply same transformation at inference
    """
    def __init__(self):
        self.scaler = None
        self.numeric_cols = None     # numeric columns to scale
        self.feature_cols = None     # final X columns for the model

    def _ohe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply one-hot encoding to the known categorical columns."""
        return pd.get_dummies(
            df,
            columns=["Industry", "Region", "Exit Status"],
            drop_first=True
        )

    def fit_transform(self, df: pd.DataFrame):
        """
        Fit the preprocessing on the *training* dataframe (original/raw format)
        and return:
          - X (features DataFrame, already scaled)
          - y (target Series)
        """
        # Separate target
        if "Profitable" not in df.columns:
            raise ValueError("Expected 'Profitable' column in training data.")
        y = df["Profitable"].astype(float)

        # One-hot encode
        df_ohe = self._ohe(df)

        # Identify numeric columns to scale
        numeric_cols = [
            col for col in df_ohe.columns
            if df_ohe[col].dtype != "uint8"  # one-hot cols are uint8
            and col not in ["Profitable", "Startup Name"]  # exclude target & ID
        ]
        self.numeric_cols = numeric_cols

        # Fit scaler on training numerics
        self.scaler = RobustScaler()
        df_ohe_scaled = df_ohe.copy()
        df_ohe_scaled[self.numeric_cols] = self.scaler.fit_transform(
            df_ohe_scaled[self.numeric_cols]
        )

        # Drop target & ID from features
        X = df_ohe_scaled.drop(columns=["Profitable", "Startup Name"])

        # Save final feature column order for inference
        self.feature_cols = X.columns.tolist()

        return X, y

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the *already-fitted* preprocessing to new data
        (original/raw format). Returns X (features DataFrame).
        """
        if self.scaler is None or self.numeric_cols is None or self.feature_cols is None:
            raise RuntimeError("Preprocessor not fitted. Call fit_transform on training data first.")

        # One-hot encode new data
        df_ohe = self._ohe(df)

        # If Profitable happens to be present, drop it 
        if "Profitable" in df_ohe.columns:
            df_ohe = df_ohe.drop(columns=["Profitable"])

        # Ensure all numeric_cols exist before scaling (missing ones -> fill with 0)
        for col in self.numeric_cols:
            if col not in df_ohe.columns:
                df_ohe[col] = 0.0

        # Scale numeric columns using the training scaler
        df_ohe_scaled = df_ohe.copy()
        df_ohe_scaled[self.numeric_cols] = self.scaler.transform(
            df_ohe_scaled[self.numeric_cols]
        )

        # Ensure we have exactly the same columns as in training, in same order
        # Missing columns -> 0, extra columns -> dropped
        X = df_ohe_scaled.reindex(columns=self.feature_cols, fill_value=0.0)

        return X
