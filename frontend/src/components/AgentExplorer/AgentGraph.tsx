import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";

import type { AgentOverview, MemoryBlock } from "../../api/client";
import { AGENT_NODE_COLOR, getMemoryLabelColor } from "./colorUtils";

type BlockSummary = {
  block: MemoryBlock;
  agentIds: string[];
};

type AgentGraphProps = {
  agents: AgentOverview[];
  blocks: BlockSummary[];
};

type NodePosition = {
  cx: number;
  cy: number;
};

type RectMap = Record<string, NodePosition>;

const POSITION_EPSILON = 0.5;

const positionsEqual = (a: RectMap, b: RectMap) => {
  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;
  return aKeys.every((key) => {
    const first = a[key];
    const second = b[key];
    if (!first || !second) return false;
    return (
      Math.abs(first.cx - second.cx) < POSITION_EPSILON &&
      Math.abs(first.cy - second.cy) < POSITION_EPSILON
    );
  });
};

export default function AgentGraph({ agents, blocks }: AgentGraphProps) {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const agentRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const blockRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [agentPositions, setAgentPositions] = useState<RectMap>({});
  const [blockPositions, setBlockPositions] = useState<RectMap>({});
  const [graphSize, setGraphSize] = useState({ width: 0, height: 0 });

  const updatePositions = useCallback(() => {
    if (!graphRef.current) return;
    const containerRect = graphRef.current.getBoundingClientRect();

    const nextAgents: RectMap = {};
    Object.entries(agentRefs.current).forEach(([id, element]) => {
      if (!element) return;
      const rect = element.getBoundingClientRect();
      nextAgents[id] = {
        cx: rect.left - containerRect.left + rect.width / 2,
        cy: rect.top - containerRect.top + rect.height / 2,
      };
    });

    const nextBlocks: RectMap = {};
    Object.entries(blockRefs.current).forEach(([id, element]) => {
      if (!element) return;
      const rect = element.getBoundingClientRect();
      nextBlocks[id] = {
        cx: rect.left - containerRect.left + rect.width / 2,
        cy: rect.top - containerRect.top + rect.height / 2,
      };
    });

    setAgentPositions((current) =>
      positionsEqual(current, nextAgents) ? current : nextAgents,
    );
    setBlockPositions((current) =>
      positionsEqual(current, nextBlocks) ? current : nextBlocks,
    );
    setGraphSize((current) => {
      if (
        Math.abs(current.width - containerRect.width) < POSITION_EPSILON &&
        Math.abs(current.height - containerRect.height) < POSITION_EPSILON
      ) {
        return current;
      }
      return { width: containerRect.width, height: containerRect.height };
    });
  }, []);

  useLayoutEffect(() => {
    const handleResize = () => updatePositions();
    window.addEventListener("resize", handleResize);
    const observer =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(handleResize)
        : null;
    if (observer && graphRef.current) {
      observer.observe(graphRef.current);
    }
    return () => {
      window.removeEventListener("resize", handleResize);
      observer?.disconnect();
    };
  }, [updatePositions]);

  const edges = useMemo(() => {
    const connections: Array<{
      id: string;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
      color: string;
    }> = [];
    agents.forEach((agent) => {
      agent.memory_blocks.forEach((block) => {
        const agentPos = agentPositions[agent.id];
        const blockPos = blockPositions[block.id];
        if (!agentPos || !blockPos) return;
        connections.push({
          id: `${agent.id}-${block.id}`,
          x1: agentPos.cx,
          y1: agentPos.cy,
          x2: blockPos.cx,
          y2: blockPos.cy,
          color: getMemoryLabelColor(block.label),
        });
      });
    });
    return connections;
  }, [agents, agentPositions, blockPositions]);

  const registerAgentRef = useCallback((id: string) => {
    return (node: HTMLDivElement | null) => {
      agentRefs.current[id] = node;
    };
  }, []);

  const registerBlockRef = useCallback((id: string) => {
    return (node: HTMLDivElement | null) => {
      blockRefs.current[id] = node;
    };
  }, []);

  useLayoutEffect(() => {
    const raf = requestAnimationFrame(() => updatePositions());
    return () => cancelAnimationFrame(raf);
  }, [agents, blocks, updatePositions]);

  return (
    <div className="agent-graph" ref={graphRef}>
      <div className="agent-graph__column">
        <p className="agent-graph__title">Agents</p>
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="agent-graph__node agent-graph__node--agent"
            style={{ borderColor: AGENT_NODE_COLOR }}
            ref={registerAgentRef(agent.id)}
          >
            <strong>
              {agent.name ||
                (agent.metadata?.handle as string | undefined) ||
                agent.id}
            </strong>
            <span>{agent.user?.display_name ?? "Unassigned"}</span>
          </div>
        ))}
      </div>
      <div className="agent-graph__column agent-graph__column--blocks">
        <p className="agent-graph__title">Memory blocks</p>
        {blocks.map((summary) => (
          <div
            key={summary.block.id}
            className="agent-graph__node"
            style={{ borderColor: getMemoryLabelColor(summary.block.label) }}
            ref={registerBlockRef(summary.block.id)}
          >
            <strong>{summary.block.label ?? "(unlabeled)"}</strong>
            <span>{summary.block.id}</span>
            <span className="agent-graph__badge">
              {summary.agentIds.length} agent
              {summary.agentIds.length === 1 ? "" : "s"}
            </span>
          </div>
        ))}
      </div>
      <svg
        className="agent-graph__edges"
        width={graphSize.width}
        height={graphSize.height}
      >
        {edges.map((edge) => (
          <line
            key={edge.id}
            x1={edge.x1}
            y1={edge.y1}
            x2={edge.x2}
            y2={edge.y2}
            stroke={edge.color}
            strokeWidth={2}
            strokeOpacity={0.5}
          />
        ))}
      </svg>
    </div>
  );
}
