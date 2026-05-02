import { useEffect, useRef, useState } from "react";

interface Props {
  onSearch: (q: string) => void;
  onCompanyFilter: (c: string) => void;
}

export function SearchBar({ onSearch, onCompanyFilter }: Props) {
  const [query, setQuery] = useState("");
  const [company, setCompany] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => onSearch(query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [query, onSearch]);

  return (
    <div className="flex flex-wrap gap-3 mb-4">
      <input
        type="text"
        placeholder="Search jobs..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100"
      />
      <input
        type="text"
        placeholder="Filter by company..."
        value={company}
        onChange={(e) => {
          setCompany(e.target.value);
          onCompanyFilter(e.target.value);
        }}
        className="w-[200px] px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100"
      />
    </div>
  );
}
