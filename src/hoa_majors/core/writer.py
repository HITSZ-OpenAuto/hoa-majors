from pathlib import Path
import toml
from typing import Dict, Any

def ensure_dir(path: Path):
    """Create directory recursively."""
    path.mkdir(parents=True, exist_ok=True)

def write_toml(path: Path, data: Dict[str, Any]):
    """Write TOML dict to file, ensuring info comes before courses."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        if "info" in data:
            f.write("[info]\n")
            for key, value in data["info"].items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                else:
                    f.write(f"{key} = {value}\n")
            f.write("\n")

        if "courses" in data:
            toml.dump({"courses": data["courses"]}, f)
