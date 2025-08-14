import yaml
from functools import lru_cache
from yaml.error import YAMLError

from .exceptions import TemplateNotFoundError, TemplateParsingError


@lru_cache(maxsize=None)
def load_template(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise TemplateNotFoundError(f"Template file not found at: {path}")
    except YAMLError as e:
        raise TemplateParsingError(f"Error parsing YAML file at {path}: {e}")
