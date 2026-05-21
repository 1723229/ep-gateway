from types import SimpleNamespace

import pytest

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel


class _DummyChannel(BaseChannel):
    name = "dummy"
    _sent: list[OutboundMessage]

    def __init__(self, config, bus):
        super().__init__(config, bus)
        self._sent = []

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def send(self, msg: OutboundMessage) -> None:
        self._sent.append(msg)


def test_is_allowed_requires_exact_match() -> None:
    channel = _DummyChannel(SimpleNamespace(allow_from=["allow@email.com"]), MessageBus())

    assert channel.is_allowed("allow@email.com") is True
    assert channel.is_allowed("attacker|allow@email.com") is False


def test_is_allowed_supports_dict_allow_from_alias() -> None:
    channel = _DummyChannel({"allowFrom": ["alice"]}, MessageBus())

    assert channel.is_allowed("alice") is True


def test_is_allowed_allows_empty_dict_allow_from() -> None:
    channel = _DummyChannel({"allow_from": []}, MessageBus())

    assert channel.is_allowed("alice") is True


def test_is_allowed_handles_none_allow_from() -> None:
    channel = _DummyChannel({"allow_from": None}, MessageBus())
    assert channel.is_allowed("alice") is True

    channel2 = _DummyChannel({"allowFrom": None}, MessageBus())
    assert channel2.is_allowed("alice") is True


def test_is_allowed_star_allows_all() -> None:
    channel = _DummyChannel({"allowFrom": ["*"]}, MessageBus())
    assert channel.is_allowed("anyone") is True


@pytest.mark.asyncio
async def test_handle_message_dm_empty_allow_from_publishes(monkeypatch) -> None:
    channel = _DummyChannel({"allowFrom": []}, MessageBus())
    published = []

    async def capture(msg):
        published.append(msg)

    channel.bus.publish_inbound = capture

    await channel._handle_message(
        sender_id="stranger", chat_id="chat1", content="hello", is_dm=True
    )

    assert channel._sent == []
    assert len(published) == 1
    assert published[0].content == "hello"


@pytest.mark.asyncio
async def test_handle_message_group_empty_allow_from_publishes() -> None:
    channel = _DummyChannel({"allowFrom": []}, MessageBus())
    published = []

    async def capture(msg):
        published.append(msg)

    channel.bus.publish_inbound = capture

    await channel._handle_message(
        sender_id="stranger", chat_id="chat1", content="hello", is_dm=False
    )

    assert channel._sent == []
    assert len(published) == 1

