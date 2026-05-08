from __future__ import annotations

import json
from typing import Any

import httpx


class FeishuClient:
    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        base_url: str = "https://open.feishu.cn",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    async def tenant_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
        payload = _checked_payload(response)
        token = payload.get("tenant_access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Feishu token response did not include tenant_access_token.")
        return token

    async def list_table_field_names(self, *, token: str, app_token: str, table_id: str) -> set[str]:
        field_names: set[str] = set()
        page_token = ""
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
                response = await client.get(
                    f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            payload = _checked_payload(response)
            data = payload.get("data", {})
            for item in data.get("items", []):
                if isinstance(item, dict):
                    name = item.get("field_name") or item.get("name")
                    if isinstance(name, str) and name:
                        field_names.add(name)
            if not data.get("has_more"):
                return field_names
            page_token = data.get("page_token") or ""

    async def search_records(
        self,
        *,
        token: str,
        app_token: str,
        table_id: str,
        conditions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
                response = await client.post(
                    f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"filter": {"conjunction": "and", "conditions": conditions}, "automatic_fields": False},
                )
            payload = _checked_payload(response)
            data = payload.get("data", {})
            items = data.get("items", [])
            if isinstance(items, list):
                records.extend(item for item in items if isinstance(item, dict))
            if not data.get("has_more"):
                return records
            page_token = data.get("page_token") or ""

    async def list_records(self, *, token: str, app_token: str, table_id: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
                response = await client.get(
                    f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            payload = _checked_payload(response)
            data = payload.get("data", {})
            items = data.get("items", [])
            if isinstance(items, list):
                records.extend(item for item in items if isinstance(item, dict))
            if not data.get("has_more"):
                return records
            page_token = data.get("page_token") or ""

    async def create_record(self, *, token: str, app_token: str, table_id: str, fields: dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers={"Authorization": f"Bearer {token}"},
                json={"fields": fields},
            )
        payload = _checked_payload(response)
        record_id = payload.get("data", {}).get("record", {}).get("record_id")
        if not isinstance(record_id, str) or not record_id:
            raise RuntimeError("Feishu create record response did not include record_id.")
        return record_id

    async def batch_create_records(
        self,
        *,
        token: str,
        app_token: str,
        table_id: str,
        records: list[dict[str, Any]],
    ) -> None:
        if not records:
            return
        async with httpx.AsyncClient(timeout=60, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                headers={"Authorization": f"Bearer {token}"},
                json={"records": [{"fields": fields} for fields in records]},
            )
        _checked_payload(response)

    async def update_record(
        self,
        *,
        token: str,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> None:
        async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
            response = await client.put(
                f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"fields": fields},
            )
        _checked_payload(response)

    async def batch_update_records(
        self,
        *,
        token: str,
        app_token: str,
        table_id: str,
        records: list[dict[str, Any]],
    ) -> None:
        if not records:
            return
        async with httpx.AsyncClient(timeout=60, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
                headers={"Authorization": f"Bearer {token}"},
                json={"records": records},
            )
        _checked_payload(response)

    async def send_interactive_card(
        self,
        *,
        token: str,
        receive_id_type: str,
        receive_id: str,
        card: dict[str, Any],
    ) -> None:
        async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
            response = await client.post(
                f"{self.base_url}/open-apis/im/v1/messages",
                params={"receive_id_type": receive_id_type},
                headers={"Authorization": f"Bearer {token}"},
                json={"receive_id": receive_id, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
            )
        _checked_payload(response)


def _checked_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text
        hint = ""
        if response.status_code == 403 and '"code":91403' in detail:
            hint = (
                " Hint: Feishu accepted the API token but rejected this operation on the target Bitable. "
                "Check that the app has record create/update scopes published and that the app/bot has edit "
                "permission on this specific Bitable."
            )
        raise RuntimeError(f"Feishu HTTP {response.status_code}: {detail}{hint}") from exc
    payload = response.json()
    if payload.get("code", 0) != 0:
        raise RuntimeError(f"Feishu API error {payload.get('code')}: {payload.get('msg')}")
    return payload
