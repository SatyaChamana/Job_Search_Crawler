import { useEffect, useState } from "react";
import { getMasterResume, updateMasterResume } from "../api";
import { Modal } from "./Modal";
import { Spinner } from "./Spinner";

interface Props {
  open: boolean;
  onClose: () => void;
  onToast: (text: string, type: "success" | "error" | "info") => void;
}

export function MasterResumeModal({ open, onClose, onToast }: Props) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getMasterResume()
      .then((data) => { if (data) setContent(data.content); })
      .finally(() => setLoading(false));
  }, [open]);

  async function handleSave() {
    setSaving(true);
    try {
      const res = await updateMasterResume(content);
      onToast(res.message, "success");
      onClose();
    } catch (e) {
      onToast(e instanceof Error ? e.message : "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Master Resume" wide>
      {loading ? (
        <div className="flex justify-center py-8"><Spinner size="md" /></div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            This is the base resume used for all tailored generation. Changes will apply to future generations (existing cached documents are not affected).
          </p>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={20}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono bg-white dark:bg-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            placeholder="Paste your full master resume here..."
          />
          <div className="flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !content.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? "Saving..." : "Save Resume"}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
