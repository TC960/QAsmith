"""Shared utility functions."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    timestamp = datetime.utcnow().isoformat()
    hash_input = f"{prefix}{timestamp}".encode()
    hash_digest = hashlib.md5(hash_input).hexdigest()[:8]
    return f"{prefix}{hash_digest}" if prefix else hash_digest


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def save_json(data: Any, file_path: Path) -> None:
    """Save data as JSON to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON data from file."""
    with open(file_path, "r") as f:
        return json.load(f)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip()


def format_duration(ms: int) -> str:
    """Format duration in milliseconds to human-readable string."""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.2f}s"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.2f}s"