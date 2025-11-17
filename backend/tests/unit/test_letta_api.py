from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.main import app


class FakeModel:
    def __init__(self, **data: Any) -> None:
        self._data = data

    def model_dump(self) -> dict[str, Any]:
        return dict(self._data)

    def __getattr__(self, item: str) -> Any:
        if item in self._data:
            return self._data[item]
        raise AttributeError(item)


class FakeAgentBlocks:
    def __init__(self, block_map: dict[str, list[FakeModel]]) -> None:
        self._block_map = block_map

    def list(self, agent_id: str) -> list[FakeModel]:
        return self._block_map.get(agent_id, [])


class FakeAgentPassages:
    def __init__(self, passage_map: dict[str, list[FakeModel]]) -> None:
        self._passage_map = passage_map

    def list(self, agent_id: str, limit: int, ascending: bool = False) -> list[FakeModel]:
        del ascending
        passages = self._passage_map.get(agent_id, [])
        return passages[:limit]


class FakeAgentsNamespace:
    def __init__(
        self,
        agents: list[FakeModel],
        block_map: dict[str, list[FakeModel]],
        passage_map: dict[str, list[FakeModel]],
    ) -> None:
        self._agents = agents
        self.blocks = FakeAgentBlocks(block_map)
        self.passages = FakeAgentPassages(passage_map)

    def list(self) -> list[FakeModel]:
        return self._agents


class FakeLettaClient:
    def __init__(self, agents: list[FakeModel], blocks, passages) -> None:
        self.agents = FakeAgentsNamespace(agents, blocks, passages)


def build_fake_letta_client() -> FakeLettaClient:
    agents = [
        FakeModel(id="agent-alpha", name="Alpha", created_at=datetime(2024, 1, 1, tzinfo=UTC)),
        FakeModel(id="agent-beta", name="Beta", created_at=datetime(2024, 2, 1, tzinfo=UTC)),
    ]
    blocks = {
        "agent-alpha": [
            FakeModel(
                id="block-shared",
                label="human",
                value="Knows about product roadmap",
                description="User insights",
                limit=4000,
            ),
            FakeModel(
                id="block-persona",
                label="agent_persona",
                value="A helpful analyst",
                description="Agent instructions",
                limit=2000,
            ),
        ],
        "agent-beta": [
            FakeModel(
                id="block-shared",
                label="human",
                value="Knows about product roadmap",
                description="User insights",
                limit=4000,
            )
        ],
    }
    passages = {
        "agent-alpha": [
            FakeModel(
                id="passage-1",
                content="Met with customer about feature X",
                tags=["meeting"],
                created_at=datetime(2024, 3, 1, tzinfo=UTC),
            ),
            FakeModel(
                id="passage-2",
                content="Documented onboarding workflow",
                tags=["process"],
                created_at=datetime(2024, 3, 2, tzinfo=UTC),
            ),
        ]
    }
    return FakeLettaClient(agents, blocks, passages)


@pytest.fixture
def patched_letta_client(monkeypatch):
    fake_client = build_fake_letta_client()

    def _factory(*_: Any, **__: Any) -> FakeLettaClient:
        return fake_client

    monkeypatch.setattr("app.api.letta.create_letta_client", _factory)
    return fake_client


@pytest.mark.asyncio
async def test_agents_overview_endpoint(patched_letta_client):
    del patched_letta_client
    async with AsyncClient(app=app, base_url="http://test") as client:
        login = await client.post(
            "/auth/login",
            json={
                "email": "daniel.insights@goldtobacco.com",
                "password": "test-password",
            },
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = await client.get(
            "/letta/agents/overview",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["agent_count"] == 2
        assert payload["block_count"] == 3
        assert len(payload["agents"]) == 2
        first_agent = payload["agents"][0]
        assert first_agent["memory_blocks"]
        assert any(
            block["label"] == "agent_persona"
            for block in first_agent["memory_blocks"]
        )


@pytest.mark.asyncio
async def test_archival_endpoint_uses_limit(patched_letta_client):
    del patched_letta_client
    async with AsyncClient(app=app, base_url="http://test") as client:
        login = await client.post(
            "/auth/login",
            json={
                "email": "daniel.insights@goldtobacco.com",
                "password": "test-password",
            },
        )
        token = login.json()["access_token"]

        response = await client.get(
            "/letta/agents/agent-alpha/archival?limit=1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["requested_limit"] == 1
        assert payload["returned_count"] == 1
        assert payload["entries"][0]["content"].startswith("Met with customer")
