import type {
  AgentArchivalResponse,
  AgentsOverviewResponse,
} from "../../api/client";

export const SAMPLE_OVERVIEW: AgentsOverviewResponse = {
  generated_at: new Date().toISOString(),
  agent_count: 2,
  block_count: 6,
  agents: [
    {
      id: "agent-sarah",
      name: "Sarah (PI)",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: {
        model: "openai/gpt-4o-mini",
      },
      user: {
        id: "user-sarah",
        email: "sarah@fastcasual.example",
        display_name: "Sarah Martinez",
      },
      memory_blocks: [
        {
          id: "block-persona-sarah",
          label: "agent_persona",
          description: "Personality + tone",
          value:
            "You are Sarah's PI agent, obsessed with site selection insights. You prefer concise, data-backed updates.",
          limit: 4000,
          read_only: false,
          block_type: "core",
          metadata: {},
        },
        {
          id: "block-human-sarah",
          label: "human",
          description: "Facts about Sarah",
          value:
            "Sarah leads real estate for a fast casual brand. Loves experiments that mix social data + mobility.",
          limit: 4000,
          read_only: false,
          block_type: "core",
          metadata: {},
        },
        {
          id: "block-shared-experience",
          label: "persona_service_experience",
          description: "Shared CX learnings",
          value:
            "Shared wins from pilot activations across all agents. Last update: launched late-night pop-up format.",
          limit: 6000,
          read_only: false,
          block_type: "shared",
          metadata: {},
        },
      ],
    },
    {
      id: "agent-daniel",
      name: "Daniel (PI)",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: {
        model: "openai/gpt-4o-mini",
      },
      user: {
        id: "user-daniel",
        email: "daniel.insights@goldtobacco.com",
        display_name: "Daniel Lee",
      },
      memory_blocks: [
        {
          id: "block-persona-daniel",
          label: "agent_persona",
          description: "Tone + expertise",
          value:
            "You are Daniel's insights co-pilot. Prioritize omni-channel activation experiments and brand lift.",
          limit: 4000,
          read_only: false,
          block_type: "core",
          metadata: {},
        },
        {
          id: "block-human-daniel",
          label: "human",
          description: "Facts about Daniel",
          value:
            "Daniel runs consumer insights at a tobacco brand. Obsessed with pairing mobility segments + retail media.",
          limit: 4000,
          read_only: false,
          block_type: "core",
          metadata: {},
        },
        {
          id: "block-shared-experience",
          label: "persona_service_experience",
          description: "Shared CX learnings",
          value:
            "Shared wins from pilot activations across all agents. Last update: launched late-night pop-up format.",
          limit: 6000,
          read_only: false,
          block_type: "shared",
          metadata: {},
        },
      ],
    },
  ],
};

export const SAMPLE_ARCHIVAL: Record<string, AgentArchivalResponse> = {
  "agent-sarah": {
    agent_id: "agent-sarah",
    requested_limit: 7,
    returned_count: 3,
    entries: [
      {
        id: "archival-s-1",
        content: "Logged demand spikes from weekend college foot traffic. Added to activation backlog.",
        tags: ["activation", "foot_traffic"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
      {
        id: "archival-s-2",
        content: "Summarized loyalty feedback: diners crave healthier late-night bites.",
        tags: ["loyalty"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
      {
        id: "archival-s-3",
        content: "Shared transcript snippet from Memphis trek. Key insight: college students love gamified tastings.",
        tags: ["fieldwork"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
    ],
  },
  "agent-daniel": {
    agent_id: "agent-daniel",
    requested_limit: 7,
    returned_count: 3,
    entries: [
      {
        id: "archival-d-1",
        content: "Captured learning: shoppers respond best to co-branded sampling when mobility index > 0.78.",
        tags: ["mobility", "sampling"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
      {
        id: "archival-d-2",
        content: "Archived summary from agency sync: trial kit uplift +23% when pushing TikTok hints night before.",
        tags: ["campaign", "tiktok"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
      {
        id: "archival-d-3",
        content: "Documented learnings from retail media swap: Kroger DOOH segments convert 2x once radio warms market.",
        tags: ["retail_media"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {},
      },
    ],
  },
};
