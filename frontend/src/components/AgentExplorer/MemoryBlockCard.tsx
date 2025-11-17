import { useState } from "react";

import type { MemoryBlock } from "../../api/client";
import { getMemoryLabelColor } from "./colorUtils";

type MemoryBlockCardProps = {
  block: MemoryBlock;
  sharedCount: number;
};

export default function MemoryBlockCard({
  block,
  sharedCount,
}: MemoryBlockCardProps) {
  const [expanded, setExpanded] = useState(false);
  const value = block.value ?? "(no value set)";
  const previewLimit = 280;
  const shouldTruncate = value.length > previewLimit;
  const displayValue =
    expanded || !shouldTruncate
      ? value
      : `${value.slice(0, previewLimit)}…`;

  return (
    <article
      className="agent-memory"
      style={{ borderColor: getMemoryLabelColor(block.label) }}
    >
      <header className="agent-memory__header">
        <div>
          <p className="agent-memory__label">{block.label ?? "(unlabeled)"}</p>
          <p className="agent-memory__id">{block.id}</p>
        </div>
        <span
          className="agent-memory__pill"
          style={{ backgroundColor: getMemoryLabelColor(block.label) }}
        >
          {sharedCount > 1 ? `${sharedCount} agents` : "Private"}
        </span>
      </header>
      {block.description && (
        <p className="agent-memory__description">{block.description}</p>
      )}
      <p className="agent-memory__value">{displayValue}</p>
      {shouldTruncate && (
        <button
          type="button"
          className="agent-memory__expand"
          onClick={() => setExpanded((prev) => !prev)}
        >
          {expanded ? "Show less" : "Show full value"}
        </button>
      )}
      <footer className="agent-memory__meta">
        {block.limit && <span>Limit: {block.limit.toLocaleString()} chars</span>}
        {typeof block.read_only === "boolean" && (
          <span>{block.read_only ? "Read only" : "Editable"}</span>
        )}
      </footer>
    </article>
  );
}
