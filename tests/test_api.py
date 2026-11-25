from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import types
import unittest


class _BasicAuth:
    def __init__(self, login: str, password: str) -> None:
        self.login = login
        self.password = password


class _ClientError(Exception):
    pass


# The production integration gets aiohttp from Home Assistant. These tiny
# stubs keep the API tests runnable on a normal Python installation.
sys.modules.setdefault(
    "aiohttp",
    types.SimpleNamespace(
        BasicAuth=_BasicAuth,
        ClientError=_ClientError,
        ClientResponseError=_ClientError,
        ClientSession=object,
    ),
)

xmatters_package = types.ModuleType("custom_components.xmatters")
xmatters_package.__path__ = [str(Path(__file__).parents[1] / "custom_components" / "xmatters")]
sys.modules.setdefault("custom_components.xmatters", xmatters_package)

from custom_components.xmatters.api import XMattersApi, normalise_instance  # noqa: E402


class _Response:
    def __init__(self, payload):
        self.status = 200
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self._payload


class _Session:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.calls = []

    def get(self, url, *, params, auth):
        self.calls.append((url, params, auth))
        return _Response(next(self.payloads))


class ApiTests(unittest.TestCase):
    def test_normalise_instance_accepts_hostname(self):
        self.assertEqual(normalise_instance("team.xmatters.com"), "https://team.xmatters.com")

    def test_normalise_instance_rejects_other_hosts(self):
        with self.assertRaises(ValueError):
            normalise_instance("https://example.com")

    def test_on_call_filters_to_user_and_makes_current_and_future_requests(self):
        user_shift = {
            "shift": {"id": "shift-1"},
            "start": "2026-11-23T09:00:00Z",
            "end": "2026-11-24T09:00:00Z",
            "members": {"data": [{"member": {"id": "user-1", "targetName": "gkendal"}}]},
        }
        other_shift = {
            "shift": {"id": "shift-2"},
            "start": "2026-11-24T09:00:00Z",
            "end": "2026-11-25T09:00:00Z",
            "members": {"data": [{"member": {"id": "user-2", "targetName": "other"}}]},
        }
        session = _Session([{"data": [user_shift, other_shift]}, {"data": [user_shift]}])
        api = XMattersApi(session, "team.xmatters.com", "api-key", "secret")

        result = asyncio.run(api.get_on_call("group-1", {"id": "user-1", "targetName": "gkendal"}, 7))

        self.assertEqual([item["shift"]["id"] for item in result], ["shift-1"])
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(session.calls[0][1]["groups"], "group-1")
        self.assertNotIn("from", session.calls[0][1])
        self.assertIn("from", session.calls[1][1])

    def test_last_notification_uses_xmatters_user_id(self):
        session = _Session(
            [
                {
                    "data": [
                        {"id": "event-1", "name": "Not delivered to user", "created": "2026-11-24T02:00:00Z"},
                        {"id": "event-2", "name": "Test notification", "created": "2026-11-24T01:00:00Z"},
                    ]
                },
                {"data": [{"person": {"id": "other-user"}}]},
                {"data": [{"person": {"id": "user-1"}}]},
            ]
        )
        api = XMattersApi(session, "team.xmatters.com", "api-key", "secret")

        result = asyncio.run(api.get_last_notification("user-1", "group-1", 7))

        self.assertEqual(result["id"], "event-2")
        self.assertEqual(session.calls[0][1]["resolvedUsers"], "user-1")
        self.assertEqual(session.calls[0][1]["targetedRecipients"], "group-1")
        self.assertIn("/events/event-1/user-deliveries", session.calls[1][0])
        self.assertIn("/events/event-2/user-deliveries", session.calls[2][0])


if __name__ == "__main__":
    unittest.main()
