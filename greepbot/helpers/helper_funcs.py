"""A module containing various helper functions used by the bot."""
import json
import pathlib
from numpy import random
from typing import Any, List


def read_file(file_name: str) -> List[str]:
    """Returns the lines of the given file as a list of strings."""
    with open(file_name) as f:
        lines = f.readlines()

    return lines


def read_json(file_name: str) -> Any:
    """Parses the given file as JSON and returns the result as the appropriate type."""
    with open(file_name, 'r') as f:
        result = json.load(f)

    return result


def write_json(obj: Any, file_name: str) -> None:
    """Writes the given object as JSON to a file with the given name."""
    path = pathlib.Path(file_name).parent
    if not path.is_dir():
        path.mkdir(parents=True)

    with open(file_name, 'w') as f:
        json.dump(obj, f)


def random_selector(arr: List[Any]) -> int:
    """Selects a random entry in the given array."""
    random_num = random.randint(0, len(arr))
    return random_num
