import { useState } from "react";
import type { Job } from "../types";
import { generateDocument } from "../api";
import { Spinner } from "./Spinner";

interface Props {
  job: Job;
  selected: boolean;
  onToggleSelect: () => void;
  onToast: (text: string, type: "success" | "error" | "info") => void;
  onShowPreview: (job: Job, docType: "resume" | "cover_letter") => void;
  onShowDescription: (job: Job) => void;
}

type DocState = "idle" | "loading" | "done" | "error";

export function JobRow({ job, selected, onToggleSelect, onToast, onShowPreview, onShowDescription }: Props) {
  const [resumeState, setResumeState] = useState<DocState>("idle");
  const [coverState, setCoverState] = useState<DocState>("idle");
  const [resumeUrl, setResumeUrl] = useState<string | null>(null);
  const [coverUrl, setCoverUrl] = useState<string | null>(null);

  const addedDate = job.added_on
    ? new Date(job.added_on).toLocaleDateString()
    : "";

  async function handleGenerate(docType: "resume" | "cover_letter") {
    const setState = docType === "resume" ? setResumeState : setCoverState;
    const setUrl = docType === "resume" ? setResumeUrl : setCoverUrl;
    setState("loading");
    try {
      const result = await generateDocument(job.id, docType);
      setState("done");
      setUrl(result.download_url);
      window.open(result.download_url, "_blank");
      const label = docType === "resume" ? "Resume" : "Cover letter";
      onToast(`${label} ready for ${job.company}${result.cached ? " (cached)" : ""}`, "success");
    } catch (e) {
      setState("error");
      const msg = e instanceof Error ? e.message : "Generation failed";
      onToast(`Failed: ${msg}`, "error");
    }
  }

  function handleRegenerate(docType: "resume" | "cover_letter") {
    const setUrl = docType === "resume" ? setResumeUrl : setCoverUrl;
    const setState = docType === "resume" ? setResumeState : setCoverState;
    setUrl(null);
    setState("idle");
    handleGenerate(docType);
  }

  return (
    <tr className={`border-b border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800/50 ${selected ? "bg-blue-50 dark:bg-blue-900/20" : ""}`}>
      <td className="px-3 py-2.5 w-8">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          className="rounded border-gray-300 dark:border-gray-600"
        />
      </td>
      <td className="px-3 py-2.5 text-sm max-w-[300px]">
        <div className="truncate" title={job.title}>{job.title}</div>
        <button
          onClick={() => onShowDescription(job)}
          className="text-[10px] text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mt-0.5"
        >
          {job.description ? "View description" : "Add description"}
        </button>
      </td>
      <td className="px-3 py-2.5 text-sm">{job.company}</td>
      <td className="px-3 py-2.5 text-sm max-w-[200px] truncate" title={job.location}>
        {job.location}
      </td>
      <td className="px-3 py-2.5 text-sm whitespace-nowrap">{job.date_posted}</td>
      <td className="px-3 py-2.5 text-sm whitespace-nowrap">{addedDate}</td>
      <td className="px-3 py-2.5 text-sm">
        <div className="flex gap-1.5 items-center flex-wrap">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-2.5 py-1 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Apply
          </a>

          {/* Resume button */}
          {resumeState === "done" && resumeUrl ? (
            <span className="flex gap-0.5">
              <a
                href={resumeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-2 py-1 text-xs font-medium rounded-l bg-green-600 text-white hover:bg-green-700 transition-colors"
              >
                Resume
              </a>
              <button
                onClick={() => onShowPreview(job, "resume")}
                title="Preview"
                className="px-1.5 py-1 text-xs bg-green-700 text-white hover:bg-green-800 transition-colors"
              >
                P
              </button>
              <button
                onClick={() => handleRegenerate("resume")}
                title="Regenerate"
                className="px-1.5 py-1 text-xs rounded-r bg-green-700 text-white hover:bg-green-800 transition-colors"
              >
                R
              </button>
            </span>
          ) : (
            <button
              onClick={() => handleGenerate("resume")}
              disabled={resumeState === "loading"}
              title="Generate tailored resume"
              className={`px-2.5 py-1 text-xs font-medium rounded text-white transition-colors inline-flex items-center gap-1 ${
                resumeState === "loading"
                  ? "bg-green-400 cursor-wait"
                  : resumeState === "error"
                    ? "bg-red-500 hover:bg-green-600"
                    : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {resumeState === "loading" && <Spinner />}
              {resumeState === "loading" ? "Generating..." : "Resume"}
            </button>
          )}

          {/* Cover Letter button */}
          {coverState === "done" && coverUrl ? (
            <span className="flex gap-0.5">
              <a
                href={coverUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-2 py-1 text-xs font-medium rounded-l bg-purple-600 text-white hover:bg-purple-700 transition-colors"
              >
                Cover Letter
              </a>
              <button
                onClick={() => onShowPreview(job, "cover_letter")}
                title="Preview"
                className="px-1.5 py-1 text-xs bg-purple-700 text-white hover:bg-purple-800 transition-colors"
              >
                P
              </button>
              <button
                onClick={() => handleRegenerate("cover_letter")}
                title="Regenerate"
                className="px-1.5 py-1 text-xs rounded-r bg-purple-700 text-white hover:bg-purple-800 transition-colors"
              >
                R
              </button>
            </span>
          ) : (
            <button
              onClick={() => handleGenerate("cover_letter")}
              disabled={coverState === "loading"}
              title="Generate tailored cover letter"
              className={`px-2.5 py-1 text-xs font-medium rounded text-white transition-colors inline-flex items-center gap-1 ${
                coverState === "loading"
                  ? "bg-purple-400 cursor-wait"
                  : coverState === "error"
                    ? "bg-red-500 hover:bg-purple-600"
                    : "bg-purple-600 hover:bg-purple-700"
              }`}
            >
              {coverState === "loading" && <Spinner />}
              {coverState === "loading" ? "Generating..." : "Cover Letter"}
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
