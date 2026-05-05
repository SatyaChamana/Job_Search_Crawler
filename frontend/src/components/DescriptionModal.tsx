import { useEffect, useState } from "react";
import type { Job } from "../types";
import { getJobDescription, setJobDescription, fetchJobDescription } from "../api";
import { Modal } from "./Modal";
import { Spinner } from "./Spinner";

interface Props {
  job: Job | null;
  onClose: () => void;
  onToast: (text: string, type: "success" | "error" | "info") => void;
}

export function DescriptionModal({ job, onClose, onToast }: Props) {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (!job) return;
    setLoading(true);
    getJobDescription(job.id)
      .then((desc) => setDescription(desc))
      .finally(() => setLoading(false));
  }, [job]);

  async function handleFetch() {
    if (!job) return;
    setFetching(true);
    try {
      const desc = await fetchJobDescription(job.id);
      setDescription(desc);
      onToast("Job description fetched", "success");
    } catch (e) {
      onToast(e instanceof Error ? e.message : "Failed to fetch", "error");
    } finally {
      setFetching(false);
    }
  }

  async function handleSave() {
    if (!job) return;
    setSaving(true);
    try {
      await setJobDescription(job.id, description);
      onToast("Description saved", "success");
      onClose();
    } catch (e) {
      onToast(e instanceof Error ? e.message : "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={!!job} onClose={onClose} title={job ? `${job.title} - ${job.company}` : ""} wide>
      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner size="md" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Fetch from the job URL or paste manually.
            </p>
            <button
              onClick={handleFetch}
              disabled={fetching}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-1.5"
            >
              {fetching && <Spinner />}
              {fetching ? "Fetching..." : "Fetch from URL"}
            </button>
          </div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={16}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono bg-white dark:bg-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            placeholder="Paste the full job description here..."
          />
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !description.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? "Saving..." : "Save Description"}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
