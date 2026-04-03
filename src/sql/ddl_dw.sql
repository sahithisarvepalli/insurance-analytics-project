-- Insurance Analytics Data Warehouse schema for DuckDB
-- Dimensions and fact table. Summary tables are created dynamically by dw_load.py.

CREATE TABLE IF NOT EXISTS dim_member (
    member_id   BIGINT PRIMARY KEY,
    dob         DATE,
    gender      VARCHAR(10),
    region      VARCHAR(50),
    age_band    VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS dim_provider (
    provider_id  BIGINT PRIMARY KEY,
    specialty    VARCHAR(80),
    in_network   BOOLEAN,
    region       VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     DATE PRIMARY KEY,
    year         INTEGER,
    month_num    INTEGER,
    month_name   VARCHAR(12),
    quarter      INTEGER,
    day_of_week  VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS fact_claims (
    claim_id          BIGINT PRIMARY KEY,
    member_id         BIGINT,
    provider_id       BIGINT,
    date_key          DATE,
    billed_amount     DOUBLE,
    allowed_amount    DOUBLE,
    paid_amount       DOUBLE,
    diagnosis_code    VARCHAR(8),
    procedure_code    VARCHAR(8),
    place_of_service  VARCHAR(20)
);
