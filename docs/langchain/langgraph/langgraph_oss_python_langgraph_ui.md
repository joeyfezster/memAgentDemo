# Agent Chat UI

LangChain provides a powerful prebuilt user interface that work seamlessly with agents created using [`create_agent`](/oss/python/langchain/agents). This UI is designed to provide rich, interactive experiences for your agents with minimal setup, whether you're running locally or in a deployed context (such as [LangSmith](/langsmith/)).

## Agent Chat UI

[Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) is a Next.js application that provides a conversational interface for interacting with any LangChain agent. It supports real-time chat, tool visualization, and advanced features like time-travel debugging and state forking.

Agent Chat UI is open source and can be adapted to your application needs.

<Frame>
  <iframe className="w-full aspect-video rounded-xl" src="https://www.youtube.com/embed/lInrwVnZ83o?si=Uw66mPtCERJm0EjU" title="Agent Chat UI" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen />
</Frame>

### Features

<Accordion title="Tool visualization">
  Studio automatically renders tool calls and results in an intuitive interface.

  <Frame>
        <img src="https://mintcdn.com/langchain-5e9cc07a/zA84oCipUuW8ow2z/oss/images/studio_tools.gif?s=64e762e917f092960472b61a862a81cb" alt="Tool visualization in Studio" data-og-width="1280" width="1280" data-og-height="833" height="833" data-path="oss/images/studio_tools.gif" data-optimize="true" data-opv="3" />
  </Frame>
</Accordion>

<Accordion title="Time-travel debugging">
  Navigate through conversation history and fork from any point

  <Frame>
        <img src="https://mintcdn.com/langchain-5e9cc07a/TCDks4pdsHdxWmuJ/oss/images/studio_fork.gif?s=0bb5a397d4b2ed3ff8ec62b9d0f92e3e" alt="Time-travel debugging in Studio" data-og-width="1280" width="1280" data-og-height="833" height="833" data-path="oss/images/studio_fork.gif" data-optimize="true" data-opv="3" />
  </Frame>
</Accordion>

<Accordion title="State inspection">
  View and modify agent state at any point during execution

  <Frame>
        <img src="https://mintcdn.com/langchain-5e9cc07a/zA84oCipUuW8ow2z/oss/images/studio_state.gif?s=908d69765b0655cb532620c6e0fa96c8" alt="State inspection in Studio" data-og-width="1280" width="1280" data-og-height="833" height="833" data-path="oss/images/studio_state.gif" data-optimize="true" data-opv="3" />
  </Frame>
</Accordion>

<Accordion title="Human-in-the-loop">
  Built-in support for reviewing and responding to agent requests

  <Frame>
        <img src="https://mintcdn.com/langchain-5e9cc07a/TCDks4pdsHdxWmuJ/oss/images/studio_hitl.gif?s=ce7ce6378caf4db29ea6062b9aff0220" alt="Human-in-the-Loop in Studio" data-og-width="1280" width="1280" data-og-height="833" height="833" data-path="oss/images/studio_hitl.gif" data-optimize="true" data-opv="3" />
  </Frame>
</Accordion>

<Tip>
  You can use generative UI in the Agent Chat UI. For more information, see [Implement generative user interfaces with LangGraph](/langsmith/generative-ui-react).
</Tip>

### Quick start

The fastest way to get started is using the hosted version:

1. **Visit [Agent Chat UI](https://agentchat.vercel.app)**
2. **Connect your agent** by entering your deployment URL or local server address
3. **Start chatting** - the UI will automatically detect and render tool calls and interrupts

### Local development

For customization or local development, you can run Agent Chat UI locally:

<CodeGroup>
  ```bash Use npx theme={null}
  # Create a new Agent Chat UI project
  npx create-agent-chat-app --project-name my-chat-ui
  cd my-chat-ui

# Install dependencies and start

pnpm install
pnpm dev

````

```bash Clone repository theme={null}
# Clone the repository
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui

# Install dependencies and start
pnpm install
pnpm dev
````

</CodeGroup>

### Connect to your agent

Agent Chat UI can connect to both [local](/oss/python/langgraph/studio#setup-local-agent-server) and [deployed agents](/oss/python/langgraph/deploy).

After starting Agent Chat UI, you'll need to configure it to connect to your agent:

1. **Graph ID**: Enter your graph name (find this under `graphs` in your `langgraph.json` file)
2. **Deployment URL**: Your Agent server's endpoint (e.g., `http://localhost:2024` for local development, or your deployed agent's URL)
3. **LangSmith API key (optional)**: Add your LangSmith API key (not required if you're using a local Agent server)

Once configured, Agent Chat UI will automatically fetch and display any interrupted threads from your agent.

<Tip>
  Agent Chat UI has out-of-the-box support for rendering tool calls and tool result messages. To customize what messages are shown, see [Hiding Messages in the Chat](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#hiding-messages-in-the-chat).
</Tip>

---

<Callout icon="pen-to-square" iconType="regular">
  [Edit the source of this page on GitHub.](https://github.com/langchain-ai/docs/edit/main/src/oss/langgraph/ui.mdx)
</Callout>

<Tip icon="terminal" iconType="regular">
  [Connect these docs programmatically](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
</Tip>
