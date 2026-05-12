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

export type SummaryResponse = {
    records: number;
    average_score: number;
    top_country: string;
    top_score: number;
    user: { id: number; username: string; email: string };
};

export type DatasetShapeResponse = {
    rows: number;
    columns: number;
};

export type GenericRowsResponse = {
    rows: Record<string, unknown>[];
};

export type PredictionRequest = {
    social_support: number;
    healthy_life_expectancy: number;
    log_gdp_per_capita: number;
    freedom: number;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers ?? {}),
        },
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

export function getSummary(token: string): Promise<SummaryResponse> {
    return request<SummaryResponse>("/dashboard/summary", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
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
