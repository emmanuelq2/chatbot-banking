from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass
class IntentConfig:
    """Structured representation of an intent definition."""

    name: str
    handler: str
    keywords: Sequence[str]
    entities: Dict[str, Sequence[str]]


def load_intents(config_path: Path) -> List[IntentConfig]:
    """Load all intents from a JSON configuration file."""

    with config_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    intents: List[IntentConfig] = []
    for item in raw.get("intents", []):
        intents.append(
            IntentConfig(
                name=item["name"],
                handler=item["handler"],
                keywords=tuple(keyword.lower() for keyword in item.get("keywords", [])),
                entities={key: tuple(value) for key, value in item.get("entities", {}).items()},
            )
        )
    return intents
