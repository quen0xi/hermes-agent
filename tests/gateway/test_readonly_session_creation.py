"""Regression tests for read-only slash commands creating ghost sessions."""

from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionSource, SessionStore


def _make_store(tmp_path):
    config = GatewayConfig()
    with patch("hermes_state.SessionDB", side_effect=RuntimeError("disabled for test")):
        store = SessionStore(sessions_dir=tmp_path, config=config)
    store._db = None
    store._loaded = True
    return store, config


def _make_runner(store, config):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = config
    runner.session_store = store
    runner.adapters = {}
    return runner


def _make_source():
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="user-1",
        user_name="alice",
    )


@pytest.mark.asyncio
async def test_retry_no_previous_message_does_not_create_session(tmp_path):
    store, config = _make_store(tmp_path)
    runner = _make_runner(store, config)

    result = await runner._handle_retry_command(
        MessageEvent(text="/retry", message_type=MessageType.TEXT, source=_make_source())
    )

    assert result == "No previous message to retry."
    assert store._entries == {}
    assert not (tmp_path / "sessions.json").exists()


@pytest.mark.asyncio
async def test_undo_no_history_does_not_create_session(tmp_path):
    store, config = _make_store(tmp_path)
    runner = _make_runner(store, config)

    result = await runner._handle_undo_command(
        MessageEvent(text="/undo", message_type=MessageType.TEXT, source=_make_source())
    )

    assert result == "Nothing to undo."
    assert store._entries == {}
    assert not (tmp_path / "sessions.json").exists()


@pytest.mark.asyncio
async def test_compress_no_history_does_not_create_session(tmp_path):
    store, config = _make_store(tmp_path)
    runner = _make_runner(store, config)

    result = await runner._handle_compress_command(
        MessageEvent(text="/compress", message_type=MessageType.TEXT, source=_make_source())
    )

    assert result == "Not enough conversation to compress (need at least 4 messages)."
    assert store._entries == {}
    assert not (tmp_path / "sessions.json").exists()


@pytest.mark.asyncio
async def test_goal_status_no_session_does_not_create_session(tmp_path):
    store, config = _make_store(tmp_path)
    runner = _make_runner(store, config)

    result = await runner._handle_goal_command(
        MessageEvent(text="/goal status", message_type=MessageType.TEXT, source=_make_source())
    )

    assert result == "No active goal. Set one with /goal <text>."
    assert store._entries == {}
    assert not (tmp_path / "sessions.json").exists()
