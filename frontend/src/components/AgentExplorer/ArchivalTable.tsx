import { useMemo, useState } from "react";

import type { ArchivalEntry } from "../../api/client";

type ArchivalTableProps = {
  entries: ArchivalEntry[];
  loading: boolean;
  error: string | null;
  onReload: () => void;
  onShowMore: () => void;
};

function formatTimestamp(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function ArchivalTable({
  entries,
  loading,
  error,
  onReload,
  onShowMore,
}: ArchivalTableProps) {
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const sortedEntries = useMemo(() => {
    return [...entries].sort((a, b) => {
      const first = new Date(b.created_at ?? 0).getTime();
      const second = new Date(a.created_at ?? 0).getTime();
      return first - second;
    });
  }, [entries]);

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="archival">
      <header className="archival__header">
        <h4>Archival memory</h4>
        <div className="archival__actions">
          <button type="button" onClick={onReload}>
            Refresh
          </button>
          <button type="button" onClick={onShowMore}>
            Show more entries
          </button>
        </div>
      </header>
      {error && <p className="archival__error">{error}</p>}
      {loading && <p className="archival__loading">Loading archival entries…</p>}
      {!loading && sortedEntries.length === 0 && (
        <p className="archival__empty">No archival entries yet.</p>
      )}
      {!loading && sortedEntries.length > 0 && (
        <div className="archival__table" role="table">
          <div className="archival__row archival__row--header" role="row">
            <span role="columnheader">Timestamp</span>
            <span role="columnheader">Tags</span>
            <span role="columnheader">Content</span>
            <span role="columnheader">Actions</span>
          </div>
          {sortedEntries.map((entry) => {
            const expanded = expandedRows[entry.id] ?? false;
            return (
              <div className="archival__row" role="row" key={entry.id}>
                <span role="cell">{formatTimestamp(entry.created_at)}</span>
                <span role="cell">
                  {entry.tags.length === 0
                    ? "—"
                    : entry.tags.map((tag) => `#${tag}`).join(" ")}
                </span>
                <span role="cell" className="archival__content">
                  {expanded
                    ? entry.content
                    : `${entry.content.slice(0, 200)}${
                        entry.content.length > 200 ? "…" : ""
                      }`}
                </span>
                <span role="cell">
                  <button type="button" onClick={() => toggleRow(entry.id)}>
                    {expanded ? "Collapse" : "Expand"}
                  </button>
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
