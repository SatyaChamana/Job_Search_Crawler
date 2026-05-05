import type { BulkGenerateResponse, JobListResponse, JobQueryParams, Stats } from "./types";

const BASE = "/api";

export async function fetchJobs(params: JobQueryParams): Promise<JobListResponse> {
  const qs = new URLSearchParams({
    page: String(params.page),
    per_page: String(params.per_page),
    sort_by: params.sort_by,
    sort_dir: params.sort_dir,
  });
  if (params.company) qs.set("company", params.company);
  if (params.search) qs.set("search", params.search);

  const res = await fetch(`${BASE}/jobs?${qs}`);
  if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.status}`);
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export async function generateDocument(
  jobId: number,
  docType: "resume" | "cover_letter"
): Promise<{ blob: Blob; filename: string }> {
  const endpoint = docType === "resume" ? "resume" : "cover-letter";
  const res = await fetch(`${BASE}/generate/${endpoint}/${jobId}`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Generation failed: ${res.status}`);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="(.+?)"/);
  const ext = docType === "resume" ? "docx" : "pdf";
  const filename = match ? match[1] : `${docType}_${jobId}.${ext}`;
  return { blob, filename };
}

export async function getJobDescription(jobId: number): Promise<string> {
  const res = await fetch(`${BASE}/jobs/${jobId}/description`);
  if (!res.ok) return "";
  const data = await res.json();
  return data.description || "";
}

export async function fetchJobDescription(jobId: number): Promise<string> {
  const res = await fetch(`${BASE}/jobs/${jobId}/fetch-description`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to fetch description: ${res.status}`);
  }
  const data = await res.json();
  return data.description || "";
}

export async function setJobDescription(jobId: number, description: string): Promise<void> {
  const res = await fetch(`${BASE}/jobs/${jobId}/description`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to save description: ${res.status}`);
  }
}

export async function getLLMProvider(): Promise<{ provider: string; nvidia_model: string; ollama_model: string }> {
  const res = await fetch(`${BASE}/llm-provider`);
  if (!res.ok) return { provider: "ollama", nvidia_model: "", ollama_model: "" };
  return res.json();
}

export async function setLLMProvider(provider: string): Promise<{ provider: string }> {
  const res = await fetch(`${BASE}/llm-provider`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  if (!res.ok) throw new Error("Failed to switch provider");
  return res.json();
}

export async function getMasterResume(): Promise<{ content: string; content_hash: string } | null> {
  const res = await fetch(`${BASE}/master-resume`);
  if (!res.ok) return null;
  return res.json();
}

export async function updateMasterResume(content: string): Promise<{ message: string }> {
  const res = await fetch(`${BASE}/master-resume`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to update master resume: ${res.status}`);
  }
  return res.json();
}

export async function bulkGenerate(
  jobIds: number[],
  docTypes: string[] = ["resume", "cover_letter"]
): Promise<BulkGenerateResponse> {
  const res = await fetch(`${BASE}/bulk-generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_ids: jobIds, doc_types: docTypes }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Bulk generation failed: ${res.status}`);
  }
  return res.json();
}
