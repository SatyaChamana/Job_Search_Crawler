import { useEffect, useState } from "react";
import type { Job } from "../types";
import { getGenerationStatus } from "../api";
import { Modal } from "./Modal";
import { Spinner } from "./Spinner";

interface Props {
  job: Job | null;
  docType: "resume" | "cover_letter" | null;
  onClose: () => void;
}

export function PreviewModal({ job, docType, onClose }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!job || !docType) return;
    setLoading(true);
    setUrl(null);
    getGenerationStatus(job.id)
      .then((status) => {
        const doc = docType === "resume" ? status.resume : status.cover_letter;
        if (doc?.url) setUrl(doc.url);
      })
      .finally(() => setLoading(false));
  }, [job, docType]);

  const title = docType === "resume" ? "Resume Preview" : "Cover Letter Preview";

  return (
    <Modal open={!!job && !!docType} onClose={onClose} title={job ? `${title} - ${job.company}` : ""} wide>
      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="md" />
        </div>
      ) : url ? (
        <div className="space-y-4">
          <iframe
            src={url}
            className="w-full h-[70vh] border border-gray-200 dark:border-gray-700 rounded-lg"
            title={title}
          />
          <div className="flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900">
              Close
            </button>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Open in New Tab
            </a>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500 py-8 text-center">No generated document found. Generate one first.</p>
      )}
    </Modal>
  );
}
