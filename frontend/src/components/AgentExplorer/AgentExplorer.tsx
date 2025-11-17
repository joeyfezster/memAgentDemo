import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getAgentArchival,
  getAgentsOverview,
  type AgentArchivalResponse,
  type AgentOverview,
  type AgentsOverviewResponse,
  type MemoryBlock,
} from "../../api/client";
import AgentGraph from "./AgentGraph";
import ArchivalTable from "./ArchivalTable";
import MemoryBlockCard from "./MemoryBlockCard";
import { getMemoryLabelColor, sortByLabelPriority } from "./colorUtils";
import { SAMPLE_ARCHIVAL, SAMPLE_OVERVIEW } from "./sampleData";
import "./AgentExplorer.css";

type AgentExplorerProps = {
  token: string;
};

type ArchivalState = {
  entries: AgentArchivalResponse["entries"];
  loading: boolean;
  error: string | null;
  limit: number;
};

const USE_SAMPLE_DATA =
  (import.meta.env.VITE_AGENT_EXPLORER_SAMPLE ?? "").toLowerCase() === "true";

function groupBlocks(agents: AgentOverview[]) {
  const map = new Map<
    string,
    {
      block: MemoryBlock;
      agentIds: Set<string>;
    }
  >();
  agents.forEach((agent) => {
    agent.memory_blocks.forEach((block) => {
      if (!map.has(block.id)) {
        map.set(block.id, { block, agentIds: new Set() });
      }
      map.get(block.id)!.agentIds.add(agent.id);
    });
  });
  return Array.from(map.values()).map((entry) => ({
    block: entry.block,
    agentIds: Array.from(entry.agentIds.values()),
  }));
}

export default function AgentExplorer({ token }: AgentExplorerProps) {
  const [overview, setOverview] = useState<AgentsOverviewResponse | null>(
    USE_SAMPLE_DATA ? SAMPLE_OVERVIEW : null,
  );
  const [loading, setLoading] = useState(!USE_SAMPLE_DATA);
  const [error, setError] = useState<string | null>(null);
  const [archival, setArchival] = useState<Record<string, ArchivalState>>(() => {
    if (!USE_SAMPLE_DATA) return {};
    return Object.fromEntries(
      Object.entries(SAMPLE_ARCHIVAL).map(([agentId, response]) => [
        agentId,
        {
          entries: response.entries,
          loading: false,
          error: null,
          limit: response.requested_limit,
        },
      ]),
    );
  });

  useEffect(() => {
    if (USE_SAMPLE_DATA) return;
    let cancelled = false;
    const fetchOverview = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getAgentsOverview(token);
        if (!cancelled) {
          setOverview(response);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : "Unable to load Letta agents";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    fetchOverview();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const loadArchival = useCallback(
    async (agentId: string, limit: number) => {
      if (USE_SAMPLE_DATA) return;
      setArchival((prev) => ({
        ...prev,
        [agentId]: {
          entries: prev[agentId]?.entries ?? [],
          loading: true,
          error: null,
          limit,
        },
      }));
      try {
        const response = await getAgentArchival(token, agentId, limit);
        setArchival((prev) => ({
          ...prev,
          [agentId]: {
            entries: response.entries,
            loading: false,
            error: null,
            limit,
          },
        }));
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Unable to load archival entries";
        setArchival((prev) => ({
          ...prev,
          [agentId]: {
            entries: prev[agentId]?.entries ?? [],
            loading: false,
            error: message,
            limit,
          },
        }));
      }
    },
    [token],
  );

  useEffect(() => {
    if (!overview || USE_SAMPLE_DATA) return;
    overview.agents.forEach((agent) => {
      loadArchival(agent.id, 7);
    });
  }, [overview, loadArchival]);

  const blockSummaries = useMemo(() => {
    if (!overview) return [];
    return groupBlocks(overview.agents);
  }, [overview]);

  if (!overview) {
    return (
      <section className="agent-explorer">
        {loading ? (
          <p>Loading agents…</p>
        ) : (
          <p className="agent-explorer__error">{error ?? "No data"}</p>
        )}
      </section>
    );
  }

  return (
      <section className="agent-explorer">
        <header className="agent-explorer__intro">
          <div>
            <h2>Agent + memory atlas</h2>
            <p>
              Visualize every agent, their assigned users, attached memory blocks, and
              the latest archival activity.
            </p>
            {USE_SAMPLE_DATA && (
              <p className="agent-explorer__sample-mode">
                Showing built-in sample data — remove VITE_AGENT_EXPLORER_SAMPLE to use
                live Letta data.
              </p>
            )}
          </div>
          <div className="agent-explorer__stats">
            <div>
              <span>{overview.agent_count}</span>
            <small>Agents</small>
          </div>
          <div>
            <span>{overview.block_count}</span>
            <small>Attached blocks</small>
          </div>
          <div>
            <span>{new Date(overview.generated_at).toLocaleTimeString()}</span>
            <small>Generated</small>
          </div>
        </div>
      </header>

      {error && !loading && (
        <p className="agent-explorer__error">{error}</p>
      )}

      <section className="agent-explorer__graph">
        <div className="agent-explorer__legend">
          <span>
            <span
              className="agent-explorer__legend-swatch"
              style={{ backgroundColor: getMemoryLabelColor("agent_persona") }}
            />
            Agent persona
          </span>
          <span>
            <span
              className="agent-explorer__legend-swatch"
              style={{ backgroundColor: getMemoryLabelColor("human") }}
            />
            Human
          </span>
          <span>
            <span
              className="agent-explorer__legend-swatch"
              style={{ backgroundColor: getMemoryLabelColor("user_persona_profile") }}
            />
            User profile
          </span>
          <span>
            <span
              className="agent-explorer__legend-swatch"
              style={{
                backgroundColor: getMemoryLabelColor("persona_service_experience"),
              }}
            />
            Shared experience
          </span>
        </div>
        <AgentGraph agents={overview.agents} blocks={blockSummaries} />
      </section>

      <div className="agent-explorer__grid">
        {overview.agents.map((agent) => {
          const agentArchival = archival[agent.id] ?? {
            entries: [],
            loading: !USE_SAMPLE_DATA,
            error: null,
            limit: 7,
          };
          return (
            <article key={agent.id} className="agent-card">
              <header className="agent-card__header">
                <div>
                  <h3>{agent.name ?? agent.id}</h3>
                  <p>{agent.user?.display_name ?? "Unassigned user"}</p>
                </div>
                <div className="agent-card__badge">{agent.id}</div>
              </header>
              <div className="agent-card__memories">
                {sortByLabelPriority(agent.memory_blocks).map((block) => {
                  const sharedCount =
                    blockSummaries.find((summary) => summary.block.id === block.id)?.agentIds
                      .length ?? 1;
                  return (
                    <MemoryBlockCard
                      key={block.id}
                      block={block}
                      sharedCount={sharedCount}
                    />
                  );
                })}
              </div>
              <ArchivalTable
                entries={agentArchival.entries}
                loading={agentArchival.loading}
                error={agentArchival.error}
                onReload={() => loadArchival(agent.id, agentArchival.limit)}
                onShowMore={() =>
                  loadArchival(
                    agent.id,
                    Math.min(agentArchival.limit + 10, 200),
                  )
                }
              />
            </article>
          );
        })}
      </div>
    </section>
  );
}
