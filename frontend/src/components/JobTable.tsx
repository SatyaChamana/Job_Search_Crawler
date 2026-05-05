import type { Job } from "../types";
import { JobRow } from "./JobRow";

interface Props {
  jobs: Job[];
  sortBy: string;
  sortDir: "asc" | "desc";
  onSort: (col: string) => void;
  loading: boolean;
  selectedIds: Set<number>;
  onToggleSelect: (id: number) => void;
  onToggleAll: () => void;
  onToast: (text: string, type: "success" | "error" | "info") => void;
  onShowPreview: (job: Job, docType: "resume" | "cover_letter", blobUrl: string) => void;
  onShowDescription: (job: Job) => void;
}

const COLUMNS: { key: string; label: string; sortable: boolean }[] = [
  { key: "title", label: "Title", sortable: true },
  { key: "company", label: "Company", sortable: true },
  { key: "location", label: "Location", sortable: false },
  { key: "date_posted", label: "Date Posted", sortable: true },
  { key: "added_on", label: "Added On", sortable: true },
  { key: "actions", label: "Actions", sortable: false },
];

function SortArrow({ col, sortBy, sortDir }: { col: string; sortBy: string; sortDir: string }) {
  if (col !== sortBy) return <span className="text-gray-300 ml-1">&#8597;</span>;
  return <span className="ml-1">{sortDir === "asc" ? "\u2191" : "\u2193"}</span>;
}

export function JobTable({ jobs, sortBy, sortDir, onSort, loading, selectedIds, onToggleSelect, onToggleAll, onToast, onShowPreview, onShowDescription }: Props) {
  const allSelected = jobs.length > 0 && jobs.every((j) => selectedIds.has(j.id));
  const colCount = COLUMNS.length + 1; // +1 for checkbox

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-left">
        <thead className="bg-gray-100 dark:bg-gray-800">
          <tr>
            <th className="px-3 py-2.5 w-8">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleAll}
                className="rounded border-gray-300 dark:border-gray-600"
              />
            </th>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={col.sortable ? () => onSort(col.key) : undefined}
                className={`px-3 py-2.5 text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 ${col.sortable ? "cursor-pointer select-none hover:text-gray-900 dark:hover:text-white" : ""}`}
              >
                {col.label}
                {col.sortable && <SortArrow col={col.key} sortBy={sortBy} sortDir={sortDir} />}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={colCount} className="px-3 py-12 text-center text-gray-500">
                Loading jobs...
              </td>
            </tr>
          ) : jobs.length === 0 ? (
            <tr>
              <td colSpan={colCount} className="px-3 py-12 text-center text-gray-500">
                No jobs found.
              </td>
            </tr>
          ) : (
            jobs.map((job) => (
              <JobRow
                key={job.id}
                job={job}
                selected={selectedIds.has(job.id)}
                onToggleSelect={() => onToggleSelect(job.id)}
                onToast={onToast}
                onShowPreview={onShowPreview}
                onShowDescription={onShowDescription}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
