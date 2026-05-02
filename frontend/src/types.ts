export interface Job {
  id: number;
  job_id: string;
  requisition_id: string;
  title: string;
  company: string;
  location: string;
  date_posted: string;
  url: string;
  added_on: string;
  description: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Stats {
  total_jobs: number;
  companies_count: number;
  jobs_added_today: number;
}

export interface JobQueryParams {
  page: number;
  per_page: number;
  company?: string;
  search?: string;
  sort_by: string;
  sort_dir: "asc" | "desc";
}

export interface BulkJobResult {
  job_id: number;
  doc_type: string;
  success: boolean;
  download_url: string | null;
  cached: boolean;
  error: string | null;
}

export interface BulkGenerateResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: BulkJobResult[];
}
