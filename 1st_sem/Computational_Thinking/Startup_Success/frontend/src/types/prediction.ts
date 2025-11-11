export type StartupInput = {
  Industry: string;
  Startup_Age: number;
  Funding_Amount: number;
  Number_of_Founders: number;
  Founder_Experience: number;
  Employees_Count: number;
  Revenue: number;
  Burn_Rate: number;
  Market_Size: string;
  Business_Model: string;
  Product_Uniqueness_Score: number;
  Customer_Retention_Rate: number;
  Marketing_Expense: number;
};

export type PredictionResponse = {
  predicted_probability: number;
  predicted_class: string;
  positive_factor: string;
  negative_factor: string;
};
