from pathlib import Path
import json

SECTION_PATHS = {
    'watch_history': ['Your Activity', 'Watch History', 'VideoList'],
    'login_history': ['Your Activity', 'Login History', 'LoginHistoryList'],
}

WATCH_HISTORY_FIELDS = ('Date',)
LOGIN_HISTORY_FIELDS = ('Date', 'NetworkType')


def load_file_as_json(path: Path) -> dict:
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return data

    except FileNotFoundError as exc:
        raise FileNotFoundError('File cannot be found') from exc


    #We will santitise and remove any unused columns before casting into a dataframe
    #to ensure that we don't use any sensitive / private data when doing the anayltics.
    #It will also ensure that we don't do any redundant data handling later on.


def get_watch_history(data: dict | None) -> list[dict]:
    if data is None:
        raise ValueError('TikTok data cannot be empty')

    curr = data

    for key in SECTION_PATHS['watch_history']:
        curr = curr[key]

    watch_history = []

    for record in curr:
        sanitised_record = {}

        for field in WATCH_HISTORY_FIELDS:
            sanitised_record[field] = record.get(field)

        watch_history.append(sanitised_record)

    return watch_history


def get_login_history(data: dict | None) -> list[dict]:

    if data is None:
        raise ValueError('TikTok data cannot be empty')

    curr = data

    for key in SECTION_PATHS['login_history']:
        curr = curr[key]

    login_history = []

    for record in curr:
        sanitised_record = {}

        for field in LOGIN_HISTORY_FIELDS:
            sanitised_record[field] = record.get(field)

        login_history.append(sanitised_record)

    return login_history





