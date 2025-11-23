# Plan

This is a collaborative plan, where the quotes (>) sections are my feedback to the AI agent's proposed plan.

## Plan: Basic Chat with Anthropic API (Phase 1)

Replace hardcoded chat responses with real LLM-powered conversations using Anthropic's API. No tools, no context truncation, no WebSocket streaming—just working chat that knows the user's name and maintains conversation history.

## Steps

1. Add Anthropic SDK and configuration — Add anthropic>=0.74.1 to requirements.txt, add anthropic_api_key: str and anthropic_model: str = "claude-3-5-haiku-20241022" to Settings class, verify ANTHROPIC_API_KEY exists in .env file (ask user if missing)

   > search online for the lastest haiku model name

1. Create minimal agent service — Create backend/app/services/agent_service.py with AgentService class containing single method generate_response(conversation_id, user_message_content, user, session): retrieves conversation messages via message_crud.get_conversation_messages(), converts DB messages to Anthropic format (list of dicts with role and content), constructs system prompt using user.display_name (e.g., "You are a helpful assistant. The user's name is {display_name}."), calls Anthropic Messages API synchronously with messages list, returns assistant response text as string

   > Actually, we need to make sure our own message db model has all the necessary fields to be converted to the Anthropic message format. Please check that as part of this step, make the changes to the db model if needed.
   > We need a place to keep together all the system behavioral items, e.g. the system prompt. Let's make sure we put it in a Seiton way.

1. Replace hardcoded response in chat endpoint — Update send_message_to_conversation() in chat.py: instantiate AgentService with settings, replace assistant_reply = f"hi {current_user.display_name}" with assistant_reply = await agent_service.generate_response(conversation_id, payload.content, current_user, session), keep all existing message persistence and title generation logic unchanged

   > yep

1. Add basic integration tests — Create backend/tests/test_agent_basic.py with two test cases: Test 1 - User name recognition: Sarah logs in, says "hi, my name is Joe", verify assistant response uses "Sarah" not "Joe"; Test 2 - Multi-user isolation: Sarah and Daniel create separate conversations, both send messages concurrently, verify each gets responses with correct name and messages persist to correct conversation_id. Both tests require ANTHROPIC_API_KEY in test environment, use real API calls per project guidelines
   > there should be a single key in .env. this is a demo, so no prod key management needed now.

## Further Considerations

Async vs sync Anthropic client — Anthropic Python SDK supports both sync and async. Start with async AsyncAnthropic() client since FastAPI endpoint is async? Or use sync client with await asyncio.to_thread() wrapper to avoid mixing async/sync patterns?

> async is better here.

Error handling for API failures — When Anthropic API returns errors (rate limit, network timeout, invalid key), should we return generic error message to user or raise HTTPException with specific details? Consider user experience vs debugging needs.

> debugging needs are more important for now.

System prompt storage — Current plan hardcodes system prompt in service. Should it be in Settings for easy modification without code changes? Or keep simple for now and refactor when adding persona-specific prompts later?

> not just modification without code change, but also for Seiton organization. Let's keep all system behavior related items together in a clear way.
