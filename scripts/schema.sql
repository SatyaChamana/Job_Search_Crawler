-- Run this in Supabase SQL Editor to create the tables

CREATE TABLE IF NOT EXISTS jobs (
    id              BIGSERIAL PRIMARY KEY,
    job_id          TEXT NOT NULL,
    requisition_id  TEXT DEFAULT '',
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT DEFAULT '',
    date_posted     TEXT DEFAULT '',
    url             TEXT NOT NULL,
    added_on        TIMESTAMPTZ DEFAULT NOW(),
    description     TEXT,
    UNIQUE (title, job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_added_on ON jobs (added_on DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company);

CREATE TABLE IF NOT EXISTS generated_documents (
    id              BIGSERIAL PRIMARY KEY,
    job_id          BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
    doc_type        TEXT NOT NULL CHECK (doc_type IN ('resume', 'cover_letter')),
    storage_path    TEXT NOT NULL,
    llm_model       TEXT,
    prompt_hash     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gendocs_job ON generated_documents (job_id, doc_type);

CREATE TABLE IF NOT EXISTS master_resume (
    id              BIGSERIAL PRIMARY KEY,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
