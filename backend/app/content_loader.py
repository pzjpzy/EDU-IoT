import os

import yaml

_CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")


def load_yaml(filename: str):
    with open(os.path.join(_CONTENT_DIR, filename), encoding="utf-8") as f:
        return yaml.safe_load(f)
