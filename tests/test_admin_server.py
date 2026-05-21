from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from nanobot.admin.server import create_app
from nanobot.bus.events import OutboundMessage
from nanobot.admin.server import _make_provider
from nanobot.config.schema import Config


def test_admin_make_provider_uses_factory() -> None:
    config = Config.model_validate(
        {
            "agents": {
                "defaults": {
                    "provider": "github-copilot",
                    "model": "github-copilot/gpt-4.1",
                }
            }
        }
    )

    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI"):
        provider = _make_provider(config)

    assert provider.__class__.__name__ == "GitHubCopilotProvider"


def _create_standalone_app_with_agent(agent: AsyncMock, config: Config | None = None):
    with (
        patch("nanobot.admin.server._make_provider", return_value=object()),
        patch("nanobot.agent.loop.AgentLoop.from_config", return_value=agent),
    ):
        return create_app(bus=None, config=config or Config())


def test_admin_standalone_chat_passes_attachment_media(monkeypatch, tmp_path: Path) -> None:
    agent = AsyncMock()
    agent.process_direct.return_value = OutboundMessage(
        channel="admin",
        chat_id="default",
        content="ok",
    )
    app = _create_standalone_app_with_agent(agent)
    app.state.config.agents.defaults.workspace = str(tmp_path)
    expected_path = tmp_path / "uploads" / "demo.png"

    monkeypatch.setattr(
        "nanobot.admin.files.get_file_path",
        lambda _workspace, file_id: expected_path if file_id == "file-1" else None,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={
                "message": "see file",
                "session_id": "admin:default",
                "attachments": [{"file_id": "file-1"}],
            },
        )

    assert response.status_code == 200
    agent.process_direct.assert_awaited_once()
    assert agent.process_direct.await_args.kwargs["media"] == [str(expected_path)]


def test_admin_standalone_stream_passes_attachment_media(monkeypatch, tmp_path: Path) -> None:
    agent = AsyncMock()
    agent.process_direct.return_value = OutboundMessage(
        channel="admin",
        chat_id="default",
        content="ok",
    )
    app = _create_standalone_app_with_agent(agent)
    app.state.config.agents.defaults.workspace = str(tmp_path)
    expected_path = tmp_path / "uploads" / "demo.pdf"

    monkeypatch.setattr(
        "nanobot.admin.files.get_file_path",
        lambda _workspace, file_id: expected_path if file_id == "file-1" else None,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/stream",
            json={
                "message": "see file",
                "session_id": "admin:default",
                "attachments": [{"file_id": "file-1"}],
            },
        )

    assert response.status_code == 200
    assert "ok" in response.text
    agent.process_direct.assert_awaited_once()
    assert agent.process_direct.await_args.kwargs["media"] == [str(expected_path)]


@pytest.mark.parametrize("payload", [{"type": "message", "content": "see file", "attachments": [{"file_id": "file-1"}]}])
def test_admin_standalone_websocket_passes_attachment_media(
    monkeypatch,
    tmp_path: Path,
    payload: dict,
) -> None:
    agent = AsyncMock()
    agent.process_direct.return_value = OutboundMessage(
        channel="admin",
        chat_id="default",
        content="ok",
    )
    app = _create_standalone_app_with_agent(agent)
    app.state.config.agents.defaults.workspace = str(tmp_path)
    expected_path = tmp_path / "uploads" / "demo.txt"

    monkeypatch.setattr(
        "nanobot.admin.files.get_file_path",
        lambda _workspace, file_id: expected_path if file_id == "file-1" else None,
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/default") as websocket:
            websocket.send_json(payload)
            assert websocket.receive_json()["content"] == "ok"

    agent.process_direct.assert_awaited_once()
    assert agent.process_direct.await_args.kwargs["media"] == [str(expected_path)]
