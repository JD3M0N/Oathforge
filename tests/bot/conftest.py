"""Handler tests run without the per-user rate limit."""

import pytest

from oathforge.bot.handlers import callbacks, creation, text


@pytest.fixture(autouse=True)
def no_rate_limit(monkeypatch):
    monkeypatch.setattr(callbacks.router, "rate_ok", lambda ctx, uid: True)
    monkeypatch.setattr(text, "rate_ok", lambda ctx, uid: True)
    monkeypatch.setattr(creation, "rate_ok", lambda ctx, uid: True)
