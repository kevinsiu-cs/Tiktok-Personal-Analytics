import json
import zipfile
from werkzeug.datastructures import FileStorage

from typing import Any


SECTION_PATHS = {
    'watch_history': ['Your Activity', 'Watch History', 'VideoList'],
    'login_history': ['Your Activity', 'Login History', 'LoginHistoryList'],
}

REQUIRED_FIELDS = {
    'watch_history': {'Date', 'Link'},
    'login_history': {'Date', 'NetworkType'},
}

TIKTOK_JSON_FILENAME = 'user_data_tiktok.json'

MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500 MiB

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


def validate_tiktok_archive(
    uploaded_file: FileStorage,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Validate the TikTok export and return its parsed JSON data."""

    file_stream = uploaded_file.stream
    file_stream.seek(0)

    try:
        with zipfile.ZipFile(file_stream) as archive:

            # Ensure the ZIP contains the TikTok JSON file we expect.
            if TIKTOK_JSON_FILENAME not in archive.namelist():
                return False, 'TikTok data file is missing from the archive.', None


            with archive.open(TIKTOK_JSON_FILENAME) as json_file:
                data = json.load(json_file)

            structure_valid, error = validate_tiktok_structure(data)

            if not structure_valid:
                return False, error, None

            fields_valid, error = validate_tiktok_required_fields(data)

            if not fields_valid:
                return False, error, None

    except zipfile.BadZipFile:
        return False, 'The uploaded ZIP archive is corrupted.', None

    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, 'The TikTok JSON file is invalid.', None

    except RuntimeError:
        return False, 'The TikTok data file could not be read.', None

    return True, None, data

