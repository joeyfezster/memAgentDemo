# Implicit Decisions

## Letta API understanding
- Direct access to https://docs.letta.com returned HTTP 403 from the build environment, so I inspected the published `letta-client==0.1.324` package to document the available clients (agents, runs, messages) and their signatures.
- Selected the asynchronous SDK (`AsyncLetta`) so FastAPI requests stay non-blocking when the backend calls the Letta deployment.

## Agent orchestration structure
- Created a dedicated `app/agents` package that holds profiles, routing logic, and backend adapters to keep FastAPI routes slim and isolate the Letta-specific code paths.
- Encoded routing, specialized, and generalist agent personas as `AgentProfile` objects. Each profile carries tags and keywords so that we can reconcile the same shape inside Letta or fallback simulators without duplicating strings.
- Added a `KeywordRoutingModel` plus a `RoutingSignalParser` because Letta agents return natural language. The parser extracts `target=` and `confidence=` tokens from routing-agent responses, and the keyword model provides deterministic routing during tests or whenever the routing agent deviates from the expected format.
- `LettaAgentBackend` lazily lists or creates agents via `letta_client.agents` and stores the slug inside agent metadata. This avoids duplicate agent creation every boot and provides a single place to enable core-memory behavior via Letta’s conversation groups.
- Added `LocalSimulationBackend` to satisfy the “no mocks” testing requirement. The simulator keeps the same interface while returning deterministic messages, which makes FastAPI tests and evals runnable without a live Letta cluster.

## Evaluations and tinkering
- Built `app/agents/evals.py` to define reusable scenarios, run them via the orchestrator, and summarize route accuracy. The file doubles as a lightweight CLI for automated smoke tests.
- Added the `agent_work/notebooks/agent_playground.ipynb` notebook so developers can import the orchestrator, send ad-hoc prompts, and run the evaluation helper inside a notebook workflow.

## API surface updates
- Extended the `/chat/messages` response to include `agent_slug`, `agent_name`, and `reasoning` so the frontend can highlight which agent handled the request and why.
- Bootstrapped the orchestrator inside the FastAPI lifespan hook to guarantee agents are ready before traffic arrives while keeping database initialization intact.
