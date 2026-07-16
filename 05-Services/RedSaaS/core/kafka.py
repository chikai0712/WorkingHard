"""Kafka REST Proxy 事件寫入。失敗時靜默略過，不影響掃描主流程。"""
import json
import requests
from core.config import KAFKA_URL


def kafka_produce(topic: str, event: dict) -> None:
    try:
        requests.post(
            f"{KAFKA_URL}/topics/{topic}",
            json={"records": [{"value": json.dumps(event)}]},
            headers={"Content-Type": "application/vnd.kafka.json.v2+json"},
            timeout=2,
        )
    except Exception:
        pass
