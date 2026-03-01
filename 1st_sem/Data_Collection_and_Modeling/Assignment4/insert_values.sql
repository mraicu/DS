-- 1) startup_data_growth.csv staging
DROP TABLE IF EXISTS stg_startup_growth;
CREATE TABLE stg_startup_growth (
  startup_name           TEXT,
  industry               TEXT,
  funding_rounds         INTEGER,
  funding_amount_musd    NUMERIC,
  valuation_musd         NUMERIC,
  revenue_musd           NUMERIC,
  employees              INTEGER,
  market_share_pct       NUMERIC,
  profitable             INTEGER,
  year_founded           INTEGER,
  region                 TEXT,
  exit_status            TEXT
);

-- 2) trends_interest_by_region.csv staging
DROP TABLE IF EXISTS stg_trends_by_region;
CREATE TABLE stg_trends_by_region (
  region          TEXT,
  geocode         TEXT,
  domain_interest NUMERIC,
  domain          TEXT
);

-- 3) trends_interest_over_time.csv staging 
DROP TABLE IF EXISTS stg_trends_over_time_wide;
CREATE TABLE stg_trends_over_time_wide (
  trend_date DATE,
  "Gaming" NUMERIC,
  "Cybersecurity" NUMERIC,
  "E-Commerce" NUMERIC,
  "AI" NUMERIC,
  "AI/ML" NUMERIC,
  "EdTech" NUMERIC,
  "HealthTech" NUMERIC,
  "Healthcare" NUMERIC,
  "FinTech" NUMERIC,
  "Finance" NUMERIC,
  "IoT" NUMERIC,
  "Logistics" NUMERIC,
  "Tech" NUMERIC,
  "Education" NUMERIC
);

-- import files using the GUI
select * from public.stg_startup_growth
select * from public.stg_trends_by_region
select * from public.stg_trends_over_time_wide

-- domains (from both startups + trends)
INSERT INTO domains(domain_name, domain_type)
SELECT DISTINCT industry, 'startup_industry'
FROM stg_startup_growth
WHERE industry IS NOT NULL AND industry <> ''
ON CONFLICT (domain_name) DO UPDATE
SET domain_type = CASE
  WHEN domains.domain_type IS NULL THEN EXCLUDED.domain_type
  WHEN domains.domain_type <> EXCLUDED.domain_type THEN 'both'
  ELSE domains.domain_type
END;

INSERT INTO domains(domain_name, domain_type)
SELECT DISTINCT domain, 'trends_topic'
FROM stg_trends_by_region
WHERE domain IS NOT NULL AND domain <> ''
ON CONFLICT (domain_name) DO UPDATE
SET domain_type = CASE
  WHEN domains.domain_type IS NULL THEN EXCLUDED.domain_type
  WHEN domains.domain_type <> EXCLUDED.domain_type THEN 'both'
  ELSE domains.domain_type
END;


-- regions (from both sources)
-- from startups (often continent-level, no geocode)
INSERT INTO regions(region_name, geo_code, region_level)
SELECT DISTINCT region, NULL, 'other'
FROM stg_startup_growth
WHERE region IS NOT NULL AND region <> ''
ON CONFLICT (region_name, geo_code) DO NOTHING;

-- from trends by region (country-level with geo codes)
INSERT INTO regions(region_name, geo_code, region_level)
SELECT DISTINCT region, NULLIF(geocode,''), 'country'
FROM stg_trends_by_region
WHERE region IS NOT NULL AND region <> ''
ON CONFLICT (region_name, geo_code) DO NOTHING;

-- exit_status
INSERT INTO exit_statuses(status_name)
SELECT DISTINCT exit_status
FROM stg_startup_growth
WHERE exit_status IS NOT NULL AND exit_status <> ''
ON CONFLICT (status_name) DO NOTHING;



-- Insert startups + metrics
INSERT INTO startups(
  startup_name, domain_id, region_id, year_founded, exit_status_id, profitable
)
SELECT
  s.startup_name,
  d.domain_id,
  r.region_id,
  s.year_founded::SMALLINT,
  e.exit_status_id,
  (s.profitable = 1) AS profitable
FROM stg_startup_growth s
JOIN domains d ON d.domain_name = s.industry
JOIN regions r ON r.region_name = s.region AND r.geo_code IS NULL
LEFT JOIN exit_statuses e ON e.status_name = s.exit_status
ON CONFLICT (startup_name) DO UPDATE
SET
  domain_id = EXCLUDED.domain_id,
  region_id = EXCLUDED.region_id,
  year_founded = EXCLUDED.year_founded,
  exit_status_id = EXCLUDED.exit_status_id,
  profitable = EXCLUDED.profitable;


-- startup_metrics
INSERT INTO startup_metrics(
  startup_id, funding_rounds, funding_amount_musd, valuation_musd,
  revenue_musd, employees, market_share_pct
)
SELECT
  st.startup_id,
  s.funding_rounds,
  s.funding_amount_musd,
  s.valuation_musd,
  s.revenue_musd,
  s.employees,
  s.market_share_pct
FROM stg_startup_growth s
JOIN startups st ON st.startup_name = s.startup_name
ON CONFLICT (startup_id) DO UPDATE
SET
  funding_rounds = EXCLUDED.funding_rounds,
  funding_amount_musd = EXCLUDED.funding_amount_musd,
  valuation_musd = EXCLUDED.valuation_musd,
  revenue_musd = EXCLUDED.revenue_musd,
  employees = EXCLUDED.employees,
  market_share_pct = EXCLUDED.market_share_pct;


-- trends_interest_by_region
INSERT INTO trends_interest_by_region(region_id, domain_id, domain_interest)
SELECT
  r.region_id,
  d.domain_id,
  t.domain_interest
FROM stg_trends_by_region t
JOIN regions r
  ON r.region_name = t.region AND r.geo_code = NULLIF(t.geocode,'')
JOIN domains d
  ON d.domain_name = t.domain
ON CONFLICT (region_id, domain_id) DO UPDATE
SET domain_interest = EXCLUDED.domain_interest;

-- trends_interest_over_time
INSERT INTO trends_interest_over_time(trend_date, domain_id, interest_value)
SELECT
  w.trend_date,
  d.domain_id,
  x.interest_value
FROM stg_trends_over_time_wide w
CROSS JOIN LATERAL (
  VALUES
    ('Gaming', w."Gaming"),
    ('Cybersecurity', w."Cybersecurity"),
    ('E-Commerce', w."E-Commerce"),
    ('AI', w."AI"),
    ('AI/ML', w."AI/ML"),
    ('EdTech', w."EdTech"),
    ('HealthTech', w."HealthTech"),
    ('Healthcare', w."Healthcare"),
    ('FinTech', w."FinTech"),
    ('Finance', w."Finance"),
    ('IoT', w."IoT"),
    ('Logistics', w."Logistics"),
    ('Tech', w."Tech"),
    ('Education', w."Education")
) AS x(domain_name, interest_value)
JOIN domains d ON d.domain_name = x.domain_name
WHERE x.interest_value IS NOT NULL
ON CONFLICT (trend_date, domain_id) DO UPDATE
SET interest_value = EXCLUDED.interest_value;
