import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";

export default function Search({ onSelect }: { onSelect: (id: string) => void }) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(q.trim()), 250);
    return () => window.clearTimeout(id);
  }, [q]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const results = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => api.persons(debounced),
    enabled: debounced.length >= 2,
  });

  const showList = open && debounced.length >= 2;

  return (
    <div className="relative w-full sm:w-72" ref={ref}>
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={t("search")}
        className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
      />
      {showList && (
        <div className="absolute z-50 mt-1 w-full card max-h-72 overflow-y-auto shadow-xl">
          {results.isLoading && (
            <div className="px-3 py-2 text-sm text-slate-500">{t("loading")}</div>
          )}
          {results.data?.length === 0 && (
            <div className="px-3 py-2 text-sm text-slate-500">{t("noResults")}</div>
          )}
          {results.data?.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                onSelect(p.id);
                setOpen(false);
                setQ("");
              }}
              className="w-full text-left px-3 py-2 hover:bg-slate-800 transition-colors"
            >
              <div className="text-sm">{p.name}</div>
              <div className="text-[10px] text-slate-500">{p.chambers.join(" · ")}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}