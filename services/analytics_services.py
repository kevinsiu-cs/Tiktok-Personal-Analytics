from services import file_services


WATCH_HISTORY_FIELDS = ('Date',)
LOGIN_HISTORY_FIELDS = ('Date', 'NetworkType')


# We sanitize and remove unused fields before creating DataFrames so private
# data is not passed into the analytics pipeline.
def get_watch_history(data: dict | None) -> list[dict]:
    if data is None:
        raise ValueError('TikTok data cannot be empty')

    curr = data

    for key in file_services.SECTION_PATHS['watch_history']:
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

    for key in file_services.SECTION_PATHS['login_history']:
        curr = curr[key]

    login_history = []

    for record in curr:
        sanitised_record = {}

        for field in LOGIN_HISTORY_FIELDS:
            sanitised_record[field] = record.get(field)

        login_history.append(sanitised_record)

    return login_history
