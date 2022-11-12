import tomllib
from pathlib import Path


def load_config(conf_file: Path | str) -> dict:
    with open(str(conf_file), "rb") as f:
        data = tomllib.load(f)
    return data
