from pathlib import Path
import json

SECTION_PATHS = {
    'watch_history': ['Your Activity', 'Watch History', 'VideoList'],
}

def load_file_as_json(path: Path) -> dict:
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return data

    except FileNotFoundError as exc:
        raise FileNotFoundError('File cannot be found') from exc


def get_watch_history(data: dict | None) -> list[dict]:
    if data is None:
        raise ValueError('TikTok data cannot be empty')

    curr = data

    for key in SECTION_PATHS['watch_history']:
        curr = curr[key]

    return curr









