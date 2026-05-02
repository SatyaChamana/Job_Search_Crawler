import { useEffect, useState } from "react";
import { fetchStats } from "../api";
import type { Stats } from "../types";

export function StatsBar() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return null;

  const items = [
    { label: "Total Jobs", value: stats.total_jobs.toLocaleString() },
    { label: "Companies", value: stats.companies_count },
    { label: "Added Today", value: stats.jobs_added_today },
  ];

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {items.map((item) => (
        <div key={item.label} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{item.value}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
