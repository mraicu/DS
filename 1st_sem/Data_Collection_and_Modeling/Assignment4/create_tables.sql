CREATE DATABASE dcm_db;
GRANT ALL PRIVILEGES ON DATABASE dcm_db TO dcm_user;

SELECT current_database();


-- public schema
SET search_path TO public;

-- clean re-run (drops in dependency-safe order)
-- DROP TABLE IF EXISTS trends_interest_over_time CASCADE;
-- DROP TABLE IF EXISTS trends_interest_by_region CASCADE;
-- DROP TABLE IF EXISTS startup_metrics CASCADE;
-- DROP TABLE IF EXISTS startups CASCADE;
-- DROP TABLE IF EXISTS exit_statuses CASCADE;
-- DROP TABLE IF EXISTS domains CASCADE;
-- DROP TABLE IF EXISTS regions CASCADE;

-- 1) regions
CREATE TABLE regions (
    region_id     BIGSERIAL PRIMARY KEY,
    region_name   VARCHAR(100) NOT NULL,
    geo_code      CHAR(2),
    region_level  VARCHAR(20),

    -- Helpful constraint to avoid duplicates (allows NULL geo_code)
    CONSTRAINT uq_regions_name_geocode UNIQUE (region_name, geo_code)
);

-- 2) domains
CREATE TABLE domains (
    domain_id    BIGSERIAL PRIMARY KEY,
    domain_name  VARCHAR(80) NOT NULL UNIQUE,
    domain_type  VARCHAR(30)
);

-- 3) exit_statuses
CREATE TABLE exit_statuses (
    exit_status_id SMALLSERIAL PRIMARY KEY,
    status_name    VARCHAR(40) NOT NULL UNIQUE
);

-- 4) startups
CREATE TABLE startups (
    startup_id     BIGSERIAL PRIMARY KEY,
    startup_name   VARCHAR(150) NOT NULL UNIQUE,
    domain_id      BIGINT NOT NULL,
    region_id      BIGINT NOT NULL,
    year_founded   SMALLINT NOT NULL,
    exit_status_id SMALLINT,
    profitable     BOOLEAN NOT NULL,

    CONSTRAINT fk_startups_domain
        FOREIGN KEY (domain_id)
        REFERENCES domains(domain_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_startups_region
        FOREIGN KEY (region_id)
        REFERENCES regions(region_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_startups_exit_status
        FOREIGN KEY (exit_status_id)
        REFERENCES exit_statuses(exit_status_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    -- sanity checks
    CONSTRAINT chk_year_founded_reasonable
        CHECK (year_founded BETWEEN 1900 AND 2100)
);

-- 5) startup_metrics
CREATE TABLE startup_metrics (
    startup_id           BIGINT PRIMARY KEY,
    funding_rounds       INTEGER,
    funding_amount_musd  NUMERIC(12,2),
    valuation_musd       NUMERIC(12,2),
    revenue_musd         NUMERIC(12,2),
    employees            INTEGER,
    market_share_pct     NUMERIC(5,2),

    CONSTRAINT fk_metrics_startup
        FOREIGN KEY (startup_id)
        REFERENCES startups(startup_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    -- sanity checks
    CONSTRAINT chk_market_share_pct
        CHECK (market_share_pct IS NULL OR (market_share_pct >= 0 AND market_share_pct <= 100)),
    CONSTRAINT chk_nonnegative_metrics
        CHECK (
            (funding_rounds IS NULL OR funding_rounds >= 0) AND
            (funding_amount_musd IS NULL OR funding_amount_musd >= 0) AND
            (valuation_musd IS NULL OR valuation_musd >= 0) AND
            (revenue_musd IS NULL OR revenue_musd >= 0) AND
            (employees IS NULL OR employees >= 0)
        )
);

-- 6) trends_interest_by_region
CREATE TABLE trends_interest_by_region (
    trend_region_id  BIGSERIAL PRIMARY KEY,
    region_id        BIGINT NOT NULL,
    domain_id        BIGINT NOT NULL,
    domain_interest  NUMERIC(6,2) NOT NULL,

    CONSTRAINT fk_trends_region
        FOREIGN KEY (region_id)
        REFERENCES regions(region_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_trends_domain
        FOREIGN KEY (domain_id)
        REFERENCES domains(domain_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_trends_region_domain UNIQUE (region_id, domain_id),

    -- sanity check
    CONSTRAINT chk_domain_interest
        CHECK (domain_interest >= 0)
);

-- 7) trends_interest_over_time
CREATE TABLE trends_interest_over_time (
    trend_time_id   BIGSERIAL PRIMARY KEY,
    trend_date      DATE NOT NULL,
    domain_id       BIGINT NOT NULL,
    interest_value  NUMERIC(6,2) NOT NULL,

    CONSTRAINT fk_trends_time_domain
        FOREIGN KEY (domain_id)
        REFERENCES domains(domain_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_trend_date_domain UNIQUE (trend_date, domain_id),

    -- sanity check
    CONSTRAINT chk_interest_value
        CHECK (interest_value >= 0)
);
