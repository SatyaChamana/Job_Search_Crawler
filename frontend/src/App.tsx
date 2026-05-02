import { useCallback, useState } from "react";
import type { Job } from "./types";
import type { ToastMessage } from "./components/Toast";
import { useJobs } from "./hooks/useJobs";
import { StatsBar } from "./components/StatsBar";
import { SearchBar } from "./components/SearchBar";
import { JobTable } from "./components/JobTable";
import { Pagination } from "./components/Pagination";
import { BulkActionBar } from "./components/BulkActionBar";
import { ToastContainer } from "./components/Toast";
import { DescriptionModal } from "./components/DescriptionModal";
import { PreviewModal } from "./components/PreviewModal";
import { MasterResumeModal } from "./components/MasterResumeModal";

let toastId = 0;

export default function App() {
  const { jobs, total, page, pages, loading, error, params, setPage, setSearch, setCompany, setSort } = useJobs();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Modal state
  const [descriptionJob, setDescriptionJob] = useState<Job | null>(null);
  const [previewJob, setPreviewJob] = useState<Job | null>(null);
  const [previewDocType, setPreviewDocType] = useState<"resume" | "cover_letter" | null>(null);
  const [showMasterResume, setShowMasterResume] = useState(false);

  const addToast = useCallback((text: string, type: "success" | "error" | "info") => {
    const id = ++toastId;
    setToasts((prev) => [...prev.slice(-4), { id, text, type }]);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toggleSelect = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      const allSelected = jobs.every((j) => prev.has(j.id));
      if (allSelected) return new Set();
      return new Set(jobs.map((j) => j.id));
    });
  }, [jobs]);

  const clearSelection = useCallback(() => setSelectedIds(new Set()), []);

  const showPreview = useCallback((job: Job, docType: "resume" | "cover_letter") => {
    setPreviewJob(job);
    setPreviewDocType(docType);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Job Search Dashboard</h1>
        <button
          onClick={() => setShowMasterResume(true)}
          className="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          Master Resume
        </button>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 flex-1 w-full">
        <StatsBar />
        <SearchBar onSearch={setSearch} onCompanyFilter={setCompany} />

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {total.toLocaleString()} jobs found
          </span>
        </div>

        <JobTable
          jobs={jobs}
          sortBy={params.sort_by}
          sortDir={params.sort_dir}
          onSort={setSort}
          loading={loading}
          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
          onToggleAll={toggleAll}
          onToast={addToast}
          onShowPreview={showPreview}
          onShowDescription={setDescriptionJob}
        />

        <Pagination page={page} pages={pages} onPageChange={setPage} />
      </main>

      <BulkActionBar selectedIds={selectedIds} onClear={clearSelection} />

      {/* Modals */}
      <DescriptionModal job={descriptionJob} onClose={() => setDescriptionJob(null)} onToast={addToast} />
      <PreviewModal job={previewJob} docType={previewDocType} onClose={() => { setPreviewJob(null); setPreviewDocType(null); }} />
      <MasterResumeModal open={showMasterResume} onClose={() => setShowMasterResume(false)} onToast={addToast} />

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
