import { useCallback, useEffect, useState } from "react";
import type { Job } from "./types";
import type { ToastMessage } from "./components/Toast";
import { useJobs } from "./hooks/useJobs";
import { getLLMProvider, setLLMProvider } from "./api";
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
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [showMasterResume, setShowMasterResume] = useState(false);
  const [llmProvider, setLlmProvider] = useState<string>("ollama");

  useEffect(() => {
    getLLMProvider().then((data) => setLlmProvider(data.provider));
  }, []);

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

  const showPreview = useCallback((job: Job, docType: "resume" | "cover_letter", blobUrl: string) => {
    setPreviewJob(job);
    setPreviewDocType(docType);
    setPreviewBlobUrl(blobUrl);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Job Search Dashboard</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={async () => {
              const next = llmProvider === "ollama" ? "nvidia" : "ollama";
              try {
                await setLLMProvider(next);
                setLlmProvider(next);
                addToast(`Switched to ${next === "ollama" ? "Ollama (local)" : "NVIDIA Cloud"}`, "info");
              } catch {
                addToast("Failed to switch LLM provider", "error");
              }
            }}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
              llmProvider === "ollama"
                ? "border-green-500 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/40"
                : "border-purple-500 text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40"
            }`}
          >
            {llmProvider === "ollama" ? "Ollama" : "NVIDIA"}
          </button>
          <button
            onClick={() => setShowMasterResume(true)}
            className="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            Master Resume
          </button>
        </div>
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
      <PreviewModal job={previewJob} docType={previewDocType} blobUrl={previewBlobUrl} onClose={() => { setPreviewJob(null); setPreviewDocType(null); setPreviewBlobUrl(null); }} />
      <MasterResumeModal open={showMasterResume} onClose={() => setShowMasterResume(false)} onToast={addToast} />

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
