
CREATE SCHEMA IF NOT EXISTS insurance;

CREATE TABLE IF NOT EXISTS insurance.member (
  member_id BIGSERIAL PRIMARY KEY,
  person_id BIGINT,
  dob DATE,
  gender VARCHAR(1),
  region VARCHAR(50),
  effective_date DATE,
  termination_date DATE
);

CREATE TABLE IF NOT EXISTS insurance.provider (
  provider_id BIGSERIAL PRIMARY KEY,
  specialty VARCHAR(80),
  in_network BOOLEAN,
  region VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS insurance.claim (
  claim_id BIGSERIAL PRIMARY KEY,
  member_id BIGINT REFERENCES insurance.member(member_id),
  provider_id BIGINT REFERENCES insurance.provider(provider_id),
  service_date DATE,
  diagnosis_code VARCHAR(8),
  procedure_code VARCHAR(8),
  billed_amount NUMERIC(12,2),
  allowed_amount NUMERIC(12,2),
  paid_amount NUMERIC(12,2),
  place_of_service VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_claim_member ON insurance.claim(member_id);
CREATE INDEX IF NOT EXISTS idx_claim_service_date ON insurance.claim(service_date);
