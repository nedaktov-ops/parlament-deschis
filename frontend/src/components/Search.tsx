import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";

export default function Search({ onSelect }: { onSelect: (id: string) => void }) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

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
  const people = results.data ?? [];

  const selectPerson = (id: string) => {
    onSelect(id);
    setOpen(false);
    setQ("");
    setActiveIndex(-1);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
      return;
    }
    if (event.key === "ArrowDown" && people.length > 0) {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => {
        const next = index < people.length - 1 ? index + 1 : 0;
        optionRefs.current[next]?.scrollIntoView({ block: "nearest" });
        return next;
      });
    } else if (event.key === "ArrowUp" && people.length > 0) {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => {
        const next = index > 0 ? index - 1 : people.length - 1;
        optionRefs.current[next]?.scrollIntoView({ block: "nearest" });
        return next;
      });
    } else if (event.key === "Enter" && showList && activeIndex >= 0) {
      event.preventDefault();
      const person = people[activeIndex];
      if (person) selectPerson(person.id);
    }
  };

  return (
    <div className="relative w-full sm:w-72" ref={ref}>
      <input
        id="person-search"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder={t("search")}
        role="combobox"
        aria-label={t("search")}
        aria-autocomplete="list"
        aria-expanded={showList}
        aria-controls="person-search-results"
        aria-activedescendant={activeIndex >= 0 ? `person-option-${activeIndex}` : undefined}
        className="w-full bg-slate-800 border border-slate-600 rounded-md px-3 py-2.5 text-sm placeholder:text-slate-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
      />
      {showList && (
        <div
          id="person-search-results"
          role="listbox"
          aria-label={t("searchResults")}
          className="absolute z-50 mt-1 w-full card max-h-72 overflow-y-auto shadow-xl"
        >
          {results.isLoading && (
            <div role="status" className="px-3 py-2 text-sm text-slate-300">{t("loading")}</div>
          )}
          {results.isError && (
            <div role="alert" className="px-3 py-2 text-sm text-rose-300">{t("searchError")}</div>
          )}
          {!results.isLoading && !results.isError && people.length === 0 && (
            <div className="px-3 py-2 text-sm text-slate-300">{t("noResults")}</div>
          )}
          {people.map((p, index) => (
            <button
              key={p.id}
              ref={(element) => { optionRefs.current[index] = element; }}
              id={`person-option-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              tabIndex={-1}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => selectPerson(p.id)}
              className={`w-full text-left px-3 py-2.5 transition-colors ${
                index === activeIndex ? "bg-slate-700" : "hover:bg-slate-800"
              }`}
            >
              <div className="text-sm">{p.name}</div>
              <div className="text-xs text-slate-300">{p.chambers.join(" · ")}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}