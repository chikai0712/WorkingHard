"""Cloud DNS 管理輔助工具。

此模組包裝 `dns.googleapis.com` API 常見操作，包含：
1. 建立與查詢 Managed Zone
2. 計算記錄差異並送出 changes
3. 輪詢變更狀態並回傳結果

依賴套件：
- google-api-python-client
- google-auth
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence

from google.auth.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient import discovery, errors

SCOPES = ["https://www.googleapis.com/auth/ndev.clouddns.readwrite"]
DEFAULT_POLL_INTERVAL = 5
DEFAULT_POLL_TIMEOUT = 120


@dataclass
class RecordSet:
    name: str
    type: str
    ttl: int
    rrdatas: Sequence[str]

    def to_api(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "ttl": self.ttl,
            "rrdatas": list(self.rrdatas),
        }


@dataclass
class ChangePlan:
    additions: List[RecordSet] = field(default_factory=list)
    deletions: List[RecordSet] = field(default_factory=list)

    def is_noop(self) -> bool:
        return not self.additions and not self.deletions

    def to_api(self) -> Dict[str, Any]:
        return {
            "additions": [record.to_api() for record in self.additions],
            "deletions": [record.to_api() for record in self.deletions],
        }


class DnsManager:
    def __init__(self, project_id: str, credentials: Credentials):
        self.project_id = project_id
        self._client = discovery.build(
            "dns", "v1", credentials=credentials, cache_discovery=False
        )

    @classmethod
    def from_service_account_file(cls, project_id: str, key_path: str) -> "DnsManager":
        creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=SCOPES
        )
        return cls(project_id, creds)

    def ensure_managed_zone(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """確保 Managed Zone 存在，若不存在則建立。"""
        name = body["name"]
        try:
            return (
                self._client.managedZones()
                .get(project=self.project_id, managedZone=name)
                .execute()
            )
        except errors.HttpError as exc:  # type: ignore[has-type]
            if exc.resp.status == 404:
                return (
                    self._client.managedZones()
                    .insert(project=self.project_id, body=body)
                    .execute()
                )
            raise

    def list_rrsets(self, zone_name: str) -> List[Dict[str, Any]]:
        """列出指定 zone 的全部 RRsets（迭代分頁）。"""
        request = self._client.resourceRecordSets().list(
            project=self.project_id, managedZone=zone_name
        )
        items: List[Dict[str, Any]] = []
        while request is not None:
            response = request.execute()
            items.extend(response.get("rrsets", []))
            request = self._client.resourceRecordSets().list_next(
                previous_request=request, previous_response=response
            )
        return items

    def plan_changes(
        self,
        desired: Iterable[RecordSet],
        existing: Iterable[Dict[str, Any]],
    ) -> ChangePlan:
        """比較目前/目標記錄，回傳需要新增與刪除的 RRsets。"""
        existing_map = {
            (item["name"], item["type"]): item for item in existing
        }
        additions: List[RecordSet] = []
        deletions: List[RecordSet] = []

        desired_map = {(record.name, record.type): record for record in desired}

        for key, record in desired_map.items():
            current = existing_map.get(key)
            if not current or current.get("rrdatas") != list(record.rrdatas):
                additions.append(record)
                if current:
                    deletions.append(
                        RecordSet(
                            name=current["name"],
                            type=current["type"],
                            ttl=current["ttl"],
                            rrdatas=current["rrdatas"],
                        )
                    )

        for key, item in existing_map.items():
            if key not in desired_map:
                deletions.append(
                    RecordSet(
                        name=item["name"],
                        type=item["type"],
                        ttl=item["ttl"],
                        rrdatas=item["rrdatas"],
                    )
                )

        return ChangePlan(additions=additions, deletions=deletions)

    def apply_changes(
        self,
        zone_name: str,
        plan: ChangePlan,
        poll_timeout: int = DEFAULT_POLL_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> Dict[str, Any]:
        """送出變更並等待完成。"""
        if plan.is_noop():
            return {"status": "done", "id": None, "additions": [], "deletions": []}

        request = self._client.changes().create(
            project=self.project_id,
            managedZone=zone_name,
            body=plan.to_api(),
        )
        change = request.execute()
        deadline = time.time() + poll_timeout

        while change.get("status") != "done":
            if time.time() > deadline:
                raise TimeoutError(
                    f"Change {change['id']} did not finish within {poll_timeout}s"
                )
            time.sleep(poll_interval)
            change = (
                self._client.changes()
                .get(
                    project=self.project_id,
                    managedZone=zone_name,
                    changeId=change["id"],
                )
                .execute()
            )
        return change

