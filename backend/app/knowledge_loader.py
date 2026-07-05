"""Loads static commerce knowledge packs from the knowledge_packs directory."""

import json
import os
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKS_DIR = _REPO_ROOT / "knowledge_packs"
DEFAULT_UNIVERSITY_PACKS_DIR = _REPO_ROOT / "university_packs"
DEFAULT_LOCATION_PACKS_DIR = _REPO_ROOT / "location_packs"


def _packs_dir() -> Path:
    return Path(os.environ.get("KNOWLEDGE_PACKS_DIR", DEFAULT_PACKS_DIR))


def _load_json_dir(path: Path) -> dict[str, dict]:
    packs: dict[str, dict] = {}
    if not path.is_dir():
        return packs
    for file in sorted(path.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
        if "id" in data:
            packs[data["id"]] = data
    return packs


@lru_cache(maxsize=1)
def load_all() -> tuple[dict, dict]:
    """Return (disciplines, common) where disciplines maps pack id -> pack dict."""
    disciplines: dict[str, dict] = {}
    common: dict = {}
    for path in sorted(_packs_dir().glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("pack_type") == "common":
            common = data
        elif "id" in data:
            disciplines[data["id"]] = data
    if not disciplines:
        raise RuntimeError(f"No knowledge packs found in {_packs_dir()}")
    return disciplines, common


def get_disciplines() -> dict[str, dict]:
    return load_all()[0]


def get_common() -> dict:
    return load_all()[1]


def get_pack(discipline_id: str) -> dict | None:
    return get_disciplines().get(discipline_id)


@lru_cache(maxsize=1)
def get_universities() -> dict[str, dict]:
    return _load_json_dir(
        Path(os.environ.get("UNIVERSITY_PACKS_DIR", DEFAULT_UNIVERSITY_PACKS_DIR))
    )


@lru_cache(maxsize=1)
def get_locations() -> dict[str, dict]:
    return _load_json_dir(
        Path(os.environ.get("LOCATION_PACKS_DIR", DEFAULT_LOCATION_PACKS_DIR))
    )
