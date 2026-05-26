export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type AuthPayload = {
    username?: string;
    email: string;
    password: string;
};

export type AuthResponse = {
    access_token: string;
    token_type: string;
    username: string;
    email: string;
};

export type DatasetShapeResponse = {
    rows: number;
    columns: number;
};

export type ColumnProfile = {
    name: string;
    dtype: string;
    missing_count: number;
    unique_count: number;
    is_categorical: boolean;
    sample_values: string[];
};

export type DatasetConfigResponse = {
    dataset_name: string;
    is_default_dataset: boolean;
    prediction_ranges: Record<string, { min: number | null; max: number | null }>;
};

export type UploadDatasetResponse = DatasetConfigResponse;

export type DropMissingRowsResponse = DatasetConfigResponse & {
    removed_rows: number;
};

export type GenericRowsResponse = {
    rows: Record<string, unknown>[];
};

export type MLAlgorithmType = "regression" | "classification" | "clustering";
export type CategoricalEncoding = "one_hot" | "ordinal";

export type TrainedModelState = {
    algorithm_type: MLAlgorithmType;
    feature_columns: string[];
    target_column: string | null;
    categorical_encoding: CategoricalEncoding;
    categorical_features: string[];
    encoded_feature_names: string[];
    feature_profiles: ColumnProfile[];
    training_rows: number;
    dataset_name: string;
    target_classes: string[] | null;
    cluster_count?: number;
};

export type MLStateResponse = {
    columns: ColumnProfile[];
    trained_model: TrainedModelState | null;
};

export type MLTrainRequest = {
    algorithm_type: MLAlgorithmType;
    feature_columns: string[];
    target_column?: string | null;
    categorical_encoding: CategoricalEncoding;
};

export type MLPredictRequest = {
    values: Record<string, string | number>;
};

export type PredictionRequest = {
    social_support: number;
    healthy_life_expectancy: number;
    log_gdp_per_capita: number;
    freedom: number;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers ?? {});
    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail ?? "Request failed");
    }

    return response.json() as Promise<T>;
}

export function signUp(payload: AuthPayload): Promise<AuthResponse> {
    return request<AuthResponse>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function login(payload: AuthPayload): Promise<AuthResponse> {
    return request<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function getDatasetShape(token: string): Promise<DatasetShapeResponse> {
    return request<DatasetShapeResponse>("/dashboard/dataset/shape", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getDatasetDtypes(token: string): Promise<GenericRowsResponse> {
    return request<GenericRowsResponse>("/dashboard/dataset/dtypes", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getDatasetConfig(token: string): Promise<DatasetConfigResponse> {
    return request<DatasetConfigResponse>("/dashboard/dataset/config", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getMLState(token: string): Promise<MLStateResponse> {
    return request<MLStateResponse>("/dashboard/ml/state", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getDatasetHead(
    token: string,
    n: number,
): Promise<GenericRowsResponse> {
    return request<GenericRowsResponse>(`/dashboard/dataset/head?n=${n}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getDatasetTail(
    token: string,
    n: number,
): Promise<GenericRowsResponse> {
    return request<GenericRowsResponse>(`/dashboard/dataset/tail?n=${n}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function getDatasetDescribe(
    token: string,
): Promise<GenericRowsResponse> {
    return request<GenericRowsResponse>("/dashboard/dataset/describe", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function predictScore(
    token: string,
    payload: PredictionRequest,
): Promise<{ predicted_score: number }> {
    return request<{ predicted_score: number }>("/dashboard/predict", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
}

export function uploadDataset(token: string, file: File): Promise<UploadDatasetResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return request<UploadDatasetResponse>("/dashboard/dataset/upload", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        body: formData,
    });
}

export function dropMissingRows(token: string): Promise<DropMissingRowsResponse> {
    return request<DropMissingRowsResponse>("/dashboard/dataset/dropna", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

export function trainModel(token: string, payload: MLTrainRequest): Promise<{ message: string; trained_model: TrainedModelState }> {
    return request<{ message: string; trained_model: TrainedModelState }>("/dashboard/ml/train", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
}

export function predictWithModel(
    token: string,
    payload: MLPredictRequest,
): Promise<{ prediction: string | number; algorithm_type: MLAlgorithmType; target_column: string | null }> {
    return request<{ prediction: string | number; algorithm_type: MLAlgorithmType; target_column: string | null }>("/dashboard/ml/predict", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });
}
