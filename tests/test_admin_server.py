from unittest.mock import patch

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
