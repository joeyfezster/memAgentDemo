const LABEL_COLORS: Record<string, string> = {
  agent_persona: "#7c3aed",
  human: "#2563eb",
  user_persona_profile: "#16a34a",
  persona_service_experience: "#ea580c",
};

const LABEL_ORDER = [
  "agent_persona",
  "human",
  "user_persona_profile",
  "persona_service_experience",
];

export const AGENT_NODE_COLOR = "#0ea5e9";

export function getMemoryLabelColor(label?: string | null): string {
  if (!label) {
    return "#475569";
  }
  return LABEL_COLORS[label] ?? "#475569";
}

export function sortByLabelPriority<T extends { label: string | null }>(
  blocks: T[],
): T[] {
  return [...blocks].sort((a, b) => {
    const aIndex = LABEL_ORDER.indexOf(a.label ?? "");
    const bIndex = LABEL_ORDER.indexOf(b.label ?? "");
    if (aIndex === -1 && bIndex === -1) return 0;
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });
}
