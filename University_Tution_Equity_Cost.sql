CREATE TABLE institutions (
  institution_id   BIGSERIAL PRIMARY KEY,
  institution_name TEXT        NOT NULL,
  state            VARCHAR(2), -- ex: "TX", "CA"
  degree_length    SMALLINT, -- ex: 2, 4
  region           TEXT,
  CONSTRAINT uq_institution UNIQUE (institution_name, state)
);

CREATE TABLE tuition_cost (
  cost_id        BIGSERIAL PRIMARY KEY,
  institution_id BIGINT     NOT NULL REFERENCES institutions(institution_id) ON UPDATE CASCADE ON DELETE CASCADE,
  year           SMALLINT   NOT NULL CHECK (year BETWEEN 1900 AND 2100),
  tuition_data   NUMERIC(12,2) NOT NULL, -- total annual tuition
  CONSTRAINT uq_tuition_per_year UNIQUE (institution_id, year)
);

CREATE INDEX idx_tuition_institution ON tuition_cost (institution_id);
CREATE INDEX idx_tuition_year        ON tuition_cost (year);

CREATE TABLE diversity_metrics (
  diversity_id    BIGSERIAL PRIMARY KEY,
  institution_id  BIGINT     NOT NULL REFERENCES institutions(institution_id) ON UPDATE CASCADE ON DELETE CASCADE,
  year            SMALLINT   NOT NULL CHECK (year BETWEEN 1900 AND 2100),
  demographics    JSON      NOT NULL, -- ex: {"female_pct":..., "hispanic_pct":..., "pell_pct":...}
  CONSTRAINT uq_diversity_per_year UNIQUE (institution_id, year)
);

CREATE INDEX idx_diversity_institution ON diversity_metrics (institution_id);
CREATE INDEX idx_diversity_year        ON diversity_metrics (year);

CREATE TABLE salary_outcome (
  salary_id      BIGSERIAL PRIMARY KEY,
  institution_id BIGINT   NOT NULL REFERENCES institutions(institution_id) ON UPDATE CASCADE ON DELETE CASCADE,
  salary_data    NUMERIC(12,2) NOT NULL -- ex: median early-career salary
);

CREATE INDEX idx_salary_institution ON salary_outcome (institution_id);

CREATE TABLE income_by_bracket (
  income_bracket_id BIGSERIAL PRIMARY KEY,
  institution_id    BIGINT   NOT NULL REFERENCES institutions(institution_id) ON UPDATE CASCADE ON DELETE CASCADE,
  income_bracket    TEXT     NOT NULL, -- ex: "<30k", "30k-60k", ">60k"
  avg_net_cost      NUMERIC(12,2) NOT NULL,
  CONSTRAINT uq_income_bracket UNIQUE (institution_id, income_bracket)
);

CREATE INDEX idx_income_institution ON income_by_bracket (institution_id);