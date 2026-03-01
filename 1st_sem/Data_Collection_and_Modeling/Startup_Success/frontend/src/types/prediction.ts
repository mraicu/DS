export interface StartupInput {
    startup_name: string;
    industry: string;
    funding_rounds: number;
    funding_amount_musd: number;
    valuation_musd: number;
    revenue_musd: number;
    employees: number;
    market_share_pct: number;
    year_founded: number;
    region: string;
    exit_status: string;
}

export type PredictionResponse = {
    predicted_probability: number;
    predicted_class: string;
    positive_factor: string;
    negative_factor: string;
};
