from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, Sequence

from app.agents.base import AgentReply, AgentRequestContext
from app.agents.orchestrator import get_agent_orchestrator


@dataclass(frozen=True)
class AgentEvalCase:
    name: str
    prompt: str
    expected_slug: str


@dataclass
class AgentEvalResult:
    case: AgentEvalCase
    reply: AgentReply


def default_eval_cases(specialized_slug: str, generalist_slug: str) -> tuple[AgentEvalCase, ...]:
    return (
        AgentEvalCase(
            name="quantitative-signal",
            prompt="Break down the revenue variance versus plan with specific metrics and next steps.",
            expected_slug=specialized_slug,
        ),
        AgentEvalCase(
            name="generalist-signal",
            prompt="Draft a note that reassures the product marketing team about the next milestone.",
            expected_slug=generalist_slug,
        ),
    )


async def run_eval(cases: Sequence[AgentEvalCase] | None = None) -> list[AgentEvalResult]:
    orchestrator = get_agent_orchestrator()
    await orchestrator.bootstrap()
    _, specialized_profile, generalist_profile = orchestrator.profiles()
    inputs = cases or default_eval_cases(
        specialized_slug=specialized_profile.slug,
        generalist_slug=generalist_profile.slug,
    )
    context = AgentRequestContext(
        user_id="eval-user",
        persona_handle="eval",
        display_name="Eval User",
    )
    results: list[AgentEvalResult] = []
    for case in inputs:
        reply = await orchestrator.route(context, case.prompt)
        results.append(AgentEvalResult(case=case, reply=reply))
    return results


def summarize_eval(results: Iterable[AgentEvalResult]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for result in results:
        outcome = "pass" if result.reply.agent_slug == result.case.expected_slug else "route"
        output.append(
            {
                "case": result.case.name,
                "expected": result.case.expected_slug,
                "observed": result.reply.agent_slug,
                "status": outcome,
                "reasoning": result.reply.reasoning,
            }
        )
    return output


if __name__ == "__main__":
    eval_results = asyncio.run(run_eval())
    for row in summarize_eval(eval_results):
        print(row)
