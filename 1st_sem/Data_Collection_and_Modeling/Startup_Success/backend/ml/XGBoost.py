from xgboost import XGBClassifier
import numpy as np

class XGBoostModel:
    def __init__(self, scale_pos_weight=None, **kwargs):

        params = {
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "random_state": 42,
            "n_jobs": -1,
        }

        if scale_pos_weight is not None:
            params["scale_pos_weight"] = scale_pos_weight

        params.update(kwargs)
        self.model = XGBClassifier(**params)

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]

    def save(self, path):
        import joblib
        joblib.dump(self.model, path)
