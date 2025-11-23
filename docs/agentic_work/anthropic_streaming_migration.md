# Anthropic Streaming Migration

## Goals
- Enable streaming chat responses from the Anthropics API through the backend to the frontend UI.
- Update the chat experience to render tokens incrementally.
- Add Playwright coverage that validates streaming behavior end-to-end.

## Plan
1. Review backend chat pipeline (FastAPI routes, AgentService, message persistence) and identify where to hook streaming responses.
2. Implement streaming support in the backend using Server-Sent Events with Anthropic streaming, ensuring messages are persisted after completion and user messages are created up front.
3. Update frontend chat client to consume the streaming endpoint, rendering assistant tokens incrementally and reconciling final message IDs.
4. Expand Playwright tests to cover streaming UI behavior, verifying that assistant responses update while streaming and finalize correctly.
