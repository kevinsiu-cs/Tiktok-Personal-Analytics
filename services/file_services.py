import zipfile
from werkzeug.datastructures import FileStorage

import ijson

from typing import Any


SECTION_PATHS = {
    'watch_history': ['Your Activity', 'Watch History', 'VideoList'],
    'login_history': ['Your Activity', 'Login History', 'LoginHistoryList'],
}

REQUIRED_FIELDS = {
    'watch_history': {'Date'},
    'login_history': {'Date'},
}

TIKTOK_JSON_FILENAME = 'user_data_tiktok.json'

MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500 MiB

JSON_VALUE_EVENTS = {
    'start_array',
    'start_map',
    'boolean',
    'null',
    'number',
    'string',
}

def validate_zip_archive(
    uploaded_file: FileStorage,
) -> tuple[bool, str | None]:
    """Validate that the uploaded file is a valid ZIP of a reasonable size. (500MiB)"""

    file_stream = uploaded_file.stream
    file_stream.seek(0)

    if not zipfile.is_zipfile(file_stream):
        file_stream.seek(0)
        return False, 'The uploaded file is not a valid ZIP archive.'

    file_stream.seek(0)

    try:
        with zipfile.ZipFile(file_stream) as archive:
            total_uncompressed_size = sum(
                entry.file_size for entry in archive.infolist()
            )

            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                return False, 'The ZIP archive contains too much uncompressed data.'

    except zipfile.BadZipFile:
        return False, 'The uploaded ZIP archive is corrupted.'

    file_stream.seek(0)

    return True, None


def validate_tiktok_structure(
    data: dict[str, Any],
) -> tuple[bool, str | None]:
    """Validate the TikTok JSON sections required by the analytics pipeline."""

    # Only validate the sections required by the analytics pipeline:
    # Watch History -> VideoList and Login History -> LoginHistoryList.

    for section_name, path in SECTION_PATHS.items():
        current_data: Any = data

        for key in path:
            if not isinstance(current_data, dict):
                return False, f'Invalid structure for {section_name}.'

            if key not in current_data:
                return False, f'Missing required TikTok section: {key}.'

            current_data = current_data[key]

        if not isinstance(current_data, list):
            return False, f'Invalid data format for {section_name}.'

    return True, None



def validate_tiktok_required_fields(
    data: dict[str, Any],
) -> tuple[bool, str | None]:
    """Validate that each required TikTok record contains the expected fields."""

    for section_name, path in SECTION_PATHS.items():
        current_data: Any = data

        for key in path:
            current_data = current_data[key]

        required_fields = REQUIRED_FIELDS[section_name]

        for entry in current_data:
            # Each history record should itself be a JSON object/dictionary.
            if not isinstance(entry, dict):
                return False, f'Invalid record format in {section_name}.'

            # Find any fields required by our analytics that are missing.
            missing_fields = required_fields - entry.keys()

            if missing_fields:
                missing = ', '.join(sorted(missing_fields))
                return False, (
                    f'Missing required field(s) in {section_name}: {missing}.'
                )

    return True, None


def stream_watch_history(
    json_file,
) -> tuple[list[Any], str | None]:
    """Stream and validate Watch History while retaining only Date values.

    The parser walks the complete JSON document as a sequence of events instead
    of building the full export as nested Python dictionaries and lists. Only
    Date values from records inside Watch History -> VideoList are retained.

    The complete stream is deliberately consumed before validation errors are
    returned. This ensures malformed JSON appearing after Watch History is still
    detected by ijson rather than being overlooked after the required records
    have been found.
    """
    # ijson represents an object's location as a dotted prefix. The ``item``
    # component identifies each element inside the VideoList array.
    your_activity_prefix = 'Your Activity'
    history_prefix = 'Your Activity.Watch History'
    records_prefix = 'Your Activity.Watch History.VideoList'
    record_prefix = f'{records_prefix}.item'
    date_prefix = f'{record_prefix}.Date'

    # These flags distinguish a missing section from a section that exists with
    # the wrong JSON type. Empty history arrays are valid, so record count alone
    # cannot be used to determine whether VideoList was present.
    your_activity_seen = False
    your_activity_is_object = False
    history_seen = False
    history_is_object = False
    records_seen = False
    records_are_array = False
    current_record = None
    record_error = None
    records = []

    # ijson.parse() yields one (prefix, event, value) tuple at a time. Unrelated
    # TikTok sections pass through this loop as events but are never assembled
    # into Python dictionaries, keeping their memory cost bounded.
    for prefix, event, value in ijson.parse(json_file):
        # A required parent section must exist and contain a JSON object. Only
        # value-start events are examined here; matching end_map events do not
        # describe the section's type and must not overwrite these flags.
        if prefix == your_activity_prefix and event in JSON_VALUE_EVENTS:
            your_activity_seen = True
            your_activity_is_object = event == 'start_map'

        if prefix == history_prefix and event in JSON_VALUE_EVENTS:
            history_seen = True
            history_is_object = event == 'start_map'

        if prefix == records_prefix and event in JSON_VALUE_EVENTS:
            records_seen = True
            records_are_array = event == 'start_array'

        # Keep validation state for only the current VideoList record. This
        # short-lived dictionary is discarded at end_map and is not retained
        # for every watched video.
        if prefix == record_prefix and event == 'start_map':
            current_record = {
                'date_present': False,
                'date_value': None,
            }

        elif prefix == record_prefix and event in JSON_VALUE_EVENTS:
            if record_error is None:
                record_error = 'Invalid record format in watch_history.'

        # Detect the Date map key separately from its value. This preserves the
        # distinction between a missing Date field and a present null value.
        # Present but invalid values are retained and later handled by Pandas'
        # existing errors='coerce' conversion.
        if (
            current_record is not None
            and prefix == record_prefix
            and event == 'map_key'
            and value == 'Date'
        ):
            current_record['date_present'] = True

        # Scalar Date values can be retained directly. A Date represented by an
        # object or array is recorded as None so the field remains "present"
        # for structural validation but is dropped during DataFrame cleaning.
        if (
            current_record is not None
            and prefix == date_prefix
            and event in JSON_VALUE_EVENTS
        ):
            current_record['date_value'] = (
                value if event not in {'start_array', 'start_map'} else None
            )

        # At the end of a record, validate Date and append only its value. The
        # first record-level error is remembered, but parsing continues to EOF
        # so later malformed JSON still takes precedence as invalid JSON.
        if prefix == record_prefix and event == 'end_map':
            if current_record is not None:
                if not current_record['date_present']:
                    if record_error is None:
                        record_error = (
                            'Missing required field(s) in watch_history: Date.'
                        )
                else:
                    records.append(current_record['date_value'])

            current_record = None

    # Structure validation follows the same parent-to-child order as the former
    # full-document validator, preserving its user-facing errors where possible.
    if not your_activity_seen:
        return [], 'Missing required TikTok section: Your Activity.'

    if not your_activity_is_object:
        return [], 'Invalid structure for watch_history.'

    if not history_seen:
        return [], 'Missing required TikTok section: Watch History.'

    if not history_is_object:
        return [], 'Invalid structure for watch_history.'

    if not records_seen:
        return [], 'Missing required TikTok section: VideoList.'

    if not records_are_array:
        return [], 'Invalid data format for watch_history.'

    if record_error is not None:
        return [], record_error

    return records, None


def stream_login_history(
    json_file,
) -> tuple[list[Any], str | None]:
    """Stream and validate Login History while retaining only Date values.

    This is the second streaming pass over the ZIP member. It consumes the full
    JSON event stream, validates Login History -> LoginHistoryList, and retains
    only each record's Date value. No unrelated TikTok sections are materialized
    as Python dictionaries.

    Parsing continues to end-of-file even after a structural or record error is
    observed, allowing ijson to reject malformed JSON anywhere in the export.
    """
    # Prefixes identify the required parent objects, the history array, each
    # array item, and the Date field within the current item.
    your_activity_prefix = 'Your Activity'
    history_prefix = 'Your Activity.Login History'
    records_prefix = 'Your Activity.Login History.LoginHistoryList'
    record_prefix = f'{records_prefix}.item'
    date_prefix = f'{record_prefix}.Date'

    # Presence and type are tracked independently so an empty array remains
    # distinguishable from a missing or incorrectly typed history section.
    your_activity_seen = False
    your_activity_is_object = False
    history_seen = False
    history_is_object = False
    records_seen = False
    records_are_array = False
    current_record = None
    record_error = None
    records = []

    # Each parser event is handled as it arrives. Values outside Login History
    # are ignored immediately rather than retained in a decoded document.
    for prefix, event, value in ijson.parse(json_file):
        # Record the JSON type of each required section from its value-start
        # event. End events sharing the same prefix are intentionally ignored.
        if prefix == your_activity_prefix and event in JSON_VALUE_EVENTS:
            your_activity_seen = True
            your_activity_is_object = event == 'start_map'

        if prefix == history_prefix and event in JSON_VALUE_EVENTS:
            history_seen = True
            history_is_object = event == 'start_map'

        if prefix == records_prefix and event in JSON_VALUE_EVENTS:
            records_seen = True
            records_are_array = event == 'start_array'

        # Maintain state for one LoginHistoryList item at a time. Scalar or array
        # items are invalid because every login record must be a JSON object.
        if prefix == record_prefix and event == 'start_map':
            current_record = {
                'date_present': False,
                'date_value': None,
            }

        elif prefix == record_prefix and event in JSON_VALUE_EVENTS:
            if record_error is None:
                record_error = 'Invalid record format in login_history.'

        # Seeing the map key proves Date exists even when its value is null.
        if (
            current_record is not None
            and prefix == record_prefix
            and event == 'map_key'
            and value == 'Date'
        ):
            current_record['date_present'] = True

        # Retain the scalar Date directly. Complex Date values become None and
        # continue through the existing Pandas coercion/cleaning behavior.
        if (
            current_record is not None
            and prefix == date_prefix
            and event in JSON_VALUE_EVENTS
        ):
            current_record['date_value'] = (
                value if event not in {'start_array', 'start_map'} else None
            )

        # Append only the Date value once the object closes. Defer returning a
        # record error until the parser has consumed and validated the full JSON.
        if prefix == record_prefix and event == 'end_map':
            if current_record is not None:
                if not current_record['date_present']:
                    if record_error is None:
                        record_error = (
                            'Missing required field(s) in login_history: Date.'
                        )
                else:
                    records.append(current_record['date_value'])

            current_record = None

    # Resolve missing and invalid parents before record errors, matching the
    # validation order used before streaming was introduced.
    if not your_activity_seen:
        return [], 'Missing required TikTok section: Your Activity.'

    if not your_activity_is_object:
        return [], 'Invalid structure for login_history.'

    if not history_seen:
        return [], 'Missing required TikTok section: Login History.'

    if not history_is_object:
        return [], 'Invalid structure for login_history.'

    if not records_seen:
        return [], 'Missing required TikTok section: LoginHistoryList.'

    if not records_are_array:
        return [], 'Invalid data format for login_history.'

    if record_error is not None:
        return [], record_error

    return records, None


def validate_tiktok_archive(
    uploaded_file: FileStorage,
) -> tuple[
    bool,
    str | None,
    dict[str, list[Any]] | None,
]:
    """Validate the TikTok export and return its required history records."""

    file_stream = uploaded_file.stream
    file_stream.seek(0)

    try:
        with zipfile.ZipFile(file_stream) as archive:

            # Ensure the ZIP contains the TikTok JSON file we expect.
            if TIKTOK_JSON_FILENAME not in archive.namelist():
                return False, 'TikTok data file is missing from the archive.', None

            with archive.open(TIKTOK_JSON_FILENAME) as json_file:
                watch_records, error = stream_watch_history(json_file)

            if error is not None:
                return False, error, None

            with archive.open(TIKTOK_JSON_FILENAME) as json_file:
                login_records, error = stream_login_history(json_file)

            if error is not None:
                return False, error, None

            extracted_histories = {
                'watch_history': watch_records,
                'login_history': login_records,
            }

    except zipfile.BadZipFile:
        return False, 'The uploaded ZIP archive is corrupted.', None

    except (ijson.JSONError, UnicodeDecodeError):
        return False, 'The TikTok JSON file is invalid.', None

    except RuntimeError:
        return False, 'The TikTok data file could not be read.', None

    return True, None, extracted_histories
