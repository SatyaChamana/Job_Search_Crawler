import type { Job } from "../types";
import { Modal } from "./Modal";

interface Props {
  job: Job | null;
  docType: "resume" | "cover_letter" | null;
  blobUrl: string | null;
  onClose: () => void;
}

export function PreviewModal({ job, docType, blobUrl, onClose }: Props) {
  const title = docType === "resume" ? "Resume Preview" : "Cover Letter Preview";

  return (
    <Modal open={!!job && !!docType && !!blobUrl} onClose={onClose} title={job ? `${title} - ${job.company}` : ""} wide>
      {blobUrl ? (
        <div className="space-y-4">
          <iframe
            src={blobUrl}
            className="w-full h-[70vh] border border-gray-200 dark:border-gray-700 rounded-lg"
            title={title}
          />
          <div className="flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900">
              Close
            </button>
            <a
              href={blobUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Open in New Tab
            </a>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500 py-8 text-center">No document to preview. Generate one first.</p>
      )}
    </Modal>
  );
}
