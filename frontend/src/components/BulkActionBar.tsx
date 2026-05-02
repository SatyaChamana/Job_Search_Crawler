import { useState } from "react";
import { bulkGenerate } from "../api";

interface Props {
  selectedIds: Set<number>;
  onClear: () => void;
}

export function BulkActionBar({ selectedIds, onClear }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  if (selectedIds.size === 0) return null;

  async function handleBulkGenerate() {
    setLoading(true);
    setResult(null);
    try {
      const res = await bulkGenerate(Array.from(selectedIds));
      setResult(`Done: ${res.succeeded} succeeded, ${res.failed} failed out of ${res.total}`);
    } catch (e) {
      setResult(e instanceof Error ? e.message : "Bulk generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center gap-4 shadow-lg">
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        {selectedIds.size} job{selectedIds.size !== 1 ? "s" : ""} selected
      </span>
      <button
        onClick={handleBulkGenerate}
        disabled={loading}
        className={`px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors ${
          loading ? "bg-indigo-400 cursor-wait" : "bg-indigo-600 hover:bg-indigo-700"
        }`}
      >
        {loading ? "Generating..." : "Generate All Selected"}
      </button>
      <button
        onClick={onClear}
        className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
      >
        Clear
      </button>
      {result && (
        <span className="text-sm text-gray-600 dark:text-gray-400">{result}</span>
      )}
    </div>
  );
}
