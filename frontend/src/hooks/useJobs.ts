import { useCallback, useEffect, useState } from "react";
import { fetchJobs } from "../api";
import type { Job, JobQueryParams } from "../types";

interface UseJobsResult {
  jobs: Job[];
  total: number;
  page: number;
  pages: number;
  loading: boolean;
  error: string | null;
  params: JobQueryParams;
  setPage: (p: number) => void;
  setSearch: (s: string) => void;
  setCompany: (c: string) => void;
  setSort: (col: string) => void;
}

export function useJobs(): UseJobsResult {
  const [params, setParams] = useState<JobQueryParams>({
    page: 1,
    per_page: 50,
    sort_by: "added_on",
    sort_dir: "desc",
  });
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchJobs(params)
      .then((data) => {
        if (cancelled) return;
        setJobs(data.jobs);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [params]);

  const setPage = useCallback((p: number) => {
    setParams((prev) => ({ ...prev, page: p }));
  }, []);

  const setSearch = useCallback((s: string) => {
    setParams((prev) => ({ ...prev, search: s || undefined, page: 1 }));
  }, []);

  const setCompany = useCallback((c: string) => {
    setParams((prev) => ({ ...prev, company: c || undefined, page: 1 }));
  }, []);

  const setSort = useCallback((col: string) => {
    setParams((prev) => {
      const sameCol = prev.sort_by === col;
      return {
        ...prev,
        sort_by: col,
        sort_dir: sameCol && prev.sort_dir === "desc" ? "asc" : "desc",
        page: 1,
      };
    });
  }, []);

  return { jobs, total, page: params.page, pages, loading, error, params, setPage, setSearch, setCompany, setSort };
}
