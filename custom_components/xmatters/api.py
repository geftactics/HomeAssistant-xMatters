from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlparse

from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession


class XMattersApiError(Exception):
    """Raised when xMatters returns an error."""


class XMattersAuthError(XMattersApiError):
    """Raised when xMatters rejects credentials."""


def normalise_instance(instance: str) -> str:
    value = instance.strip().rstrip("/")
    if not value.startswith(("https://", "http://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname.endswith(".xmatters.com"):
        raise ValueError("Use an HTTPS xMatters company URL such as yourcompany.xmatters.com")
    return value


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class XMattersApi:
    """Small async client for the xMatters REST API."""

    def __init__(self, session: ClientSession, instance: str, api_key: str, secret: str) -> None:
        self._session = session
        self.instance = normalise_instance(instance)
        username = api_key if api_key.startswith("x-api-key-") else f"x-api-key-{api_key}"
        self._auth = BasicAuth(username, secret)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.instance}/api/xm/1{path}"
        try:
            async with self._session.get(url, params=params, auth=self._auth) as response:
                if response.status in (401, 403):
                    raise XMattersAuthError(f"xMatters rejected the API credentials or permissions for {path}")
                if response.status >= 400:
                    detail = await response.text()
                    raise XMattersApiError(f"xMatters returned HTTP {response.status} for {path}: {detail[:500]}")
                return await response.json()
        except (ClientResponseError, ClientError) as err:
            raise XMattersApiError(f"Could not connect to xMatters: {err}") from err

    async def get_user(self, username: str) -> dict[str, Any]:
        # webLogin and targetName are both commonly used as the user's username.
        for field in ("webLogin", "targetName"):
            result = await self._get("/people", {field: username, "limit": 2})
            people = result.get("data", [])
            if people:
                if len(people) > 1:
                    raise XMattersApiError(f"More than one xMatters user matched {username!r}")
                return people[0]
        raise XMattersApiError(f"No xMatters user found for {username!r}")

    async def get_group_memberships(self, user_id: str) -> list[dict[str, Any]]:
        result = await self._get(f"/people/{quote(user_id, safe='')}/group-memberships", {"limit": 1000})
        return result.get("data", [])

    async def get_on_call(self, group_id: str, user: dict[str, Any], days: int) -> list[dict[str, Any]]:
        base = {"groups": group_id, "membersPerShift": 100, "embed": "members.owner"}
        now = datetime.now(timezone.utc)
        occurrences: list[dict[str, Any]] = []
        # xMatters rejects a range that crosses from historical data into future data.
        for time_params in (
            {},
            {"from": _utc(now), "to": _utc(now + timedelta(days=days))},
        ):
            result = await self._get("/on-call", {**base, **time_params})
            occurrences.extend(result.get("data", []))
        unique = {
            (item.get("shift", {}).get("id"), item.get("start")): item
            for item in occurrences
            if any(self._member_matches(member, user) for member in item.get("members", {}).get("data", []))
        }
        return sorted(unique.values(), key=lambda item: item.get("start", ""))

    @staticmethod
    def _member_matches(member: dict[str, Any], user: dict[str, Any]) -> bool:
        recipient = member.get("member", member)
        owner = recipient.get("owner", {})
        identifiers = {str(recipient.get(key, "")).casefold() for key in ("id", "targetName", "webLogin")}
        identifiers.update(str(owner.get(key, "")).casefold() for key in ("id", "targetName", "webLogin"))
        wanted = {str(user.get(key, "")).casefold() for key in ("id", "targetName", "webLogin")}
        return bool((identifiers - {""}) & (wanted - {""}))

    async def get_last_notification(self, user_id: str, group_id: str, lookback_days: int) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        result = await self._get(
            "/events",
            {
                "resolvedUsers": user_id,
                "targetedRecipients": group_id,
                "from": _utc(now - timedelta(days=lookback_days)),
                "to": _utc(now),
                "at": _utc(now),
                "sortBy": "START_TIME",
                "sortOrder": "DESCENDING",
                "limit": 10,
            },
        )
        events = result.get("data", []) if isinstance(result, dict) else result
        for event in events:
            if not event.get("name"):
                continue
            event_id = event.get("id") or event.get("eventId")
            if not event_id:
                continue
            deliveries = await self._get(
                f"/events/{quote(str(event_id), safe='')}/user-deliveries",
                {"at": _utc(now), "embed": "person.properties"},
            )
            if self._user_has_delivery(deliveries, user_id):
                return event
        return None

    @staticmethod
    def _user_has_delivery(deliveries: Any, user_id: str) -> bool:
        records = deliveries.get("data", []) if isinstance(deliveries, dict) else deliveries
        return any(
            isinstance(record, dict)
            and str(record.get("person", {}).get("id", "")) == user_id
            for record in records or []
        )

    async def validate(self, username: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        user = await self.get_user(username)
        memberships = await self.get_group_memberships(user["id"])
        return user, memberships
