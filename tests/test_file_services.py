import unittest
from io import BytesIO
import json
from unittest.mock import patch
import zipfile

from werkzeug.datastructures import FileStorage

from services.analytics_services import get_login_history, get_watch_history
from services.file_services import (
    validate_tiktok_archive,
    validate_tiktok_required_fields,
    validate_tiktok_structure,
    validate_zip_archive,
)


class TikTokStructureValidationTests(unittest.TestCase):

    def setUp(self):
        self.valid_data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'Link': 'https://example.com/video',
                        }
                    ],
                },
                'Login History': {
                    'LoginHistoryList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'NetworkType': 'Wi-Fi',
                        }
                    ],
                },
            }
        }

    def test_valid_structure_is_accepted(self):
        is_valid, error = validate_tiktok_structure(self.valid_data)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_empty_history_lists_are_accepted(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [],
                },
                'Login History': {
                    'LoginHistoryList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_missing_your_activity_is_rejected(self):
        data = {}

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: Your Activity.',
        )

    def test_missing_watch_history_is_rejected(self):
        data = {
            'Your Activity': {
                'Login History': {
                    'LoginHistoryList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: Watch History.',
        )

    def test_missing_video_list_is_rejected(self):
        data = {
            'Your Activity': {
                'Watch History': {},
                'Login History': {
                    'LoginHistoryList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: VideoList.',
        )

    def test_missing_login_history_is_rejected(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: Login History.',
        )

    def test_missing_login_history_list_is_rejected(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [],
                },
                'Login History': {},
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: LoginHistoryList.',
        )

    def test_both_history_sections_missing_are_rejected(self):
        data = {'Your Activity': {}}

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_history_dictionary_instead_of_list_is_rejected(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': {},
                },
                'Login History': {
                    'LoginHistoryList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(error, 'Invalid data format for watch_history.')

    def test_non_dictionary_parent_is_rejected(self):
        data = {'Your Activity': []}

        is_valid, error = validate_tiktok_structure(data)

        self.assertFalse(is_valid)
        self.assertEqual(error, 'Invalid structure for watch_history.')


class TikTokRequiredFieldsValidationTests(unittest.TestCase):

    def setUp(self):
        self.valid_data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'Link': 'https://example.com/video',
                        }
                    ],
                },
                'Login History': {
                    'LoginHistoryList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'NetworkType': 'Wi-Fi',
                        }
                    ],
                },
            }
        }

    def test_records_with_all_required_fields_are_accepted(self):
        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_empty_history_lists_are_accepted(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [],
                },
                'Login History': {
                    'LoginHistoryList': [],
                },
            }
        }

        is_valid, error = validate_tiktok_required_fields(data)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_watch_record_missing_date_is_rejected(self):
        self.valid_data['Your Activity']['Watch History']['VideoList'][0] = {
            'Link': 'https://example.com/video',
        }

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in watch_history: Date.',
        )

    def test_watch_record_missing_link_is_rejected(self):
        self.valid_data['Your Activity']['Watch History']['VideoList'][0] = {
            'Date': '2026-01-01 10:00:00',
        }

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in watch_history: Link.',
        )

    def test_watch_record_missing_multiple_fields_is_rejected(self):
        self.valid_data['Your Activity']['Watch History']['VideoList'][0] = {}

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in watch_history: Date, Link.',
        )

    def test_login_record_missing_date_is_rejected(self):
        login_records = self.valid_data['Your Activity']['Login History'][
            'LoginHistoryList'
        ]
        login_records[0] = {'NetworkType': 'Wi-Fi'}

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in login_history: Date.',
        )

    def test_login_record_missing_network_type_is_rejected(self):
        login_records = self.valid_data['Your Activity']['Login History'][
            'LoginHistoryList'
        ]
        login_records[0] = {'Date': '2026-01-01 10:00:00'}

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in login_history: NetworkType.',
        )

    def test_watch_record_that_is_not_dictionary_is_rejected(self):
        self.valid_data['Your Activity']['Watch History']['VideoList'][0] = (
            'not a record'
        )

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Invalid record format in watch_history.',
        )

    def test_login_record_that_is_not_dictionary_is_rejected(self):
        login_records = self.valid_data['Your Activity']['Login History'][
            'LoginHistoryList'
        ]
        login_records[0] = ['not', 'a', 'record']

        is_valid, error = validate_tiktok_required_fields(self.valid_data)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Invalid record format in login_history.',
        )


class ZipArchiveValidationTests(unittest.TestCase):

    @staticmethod
    def create_upload(files: dict[str, bytes]) -> FileStorage:
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for filename, contents in files.items():
                archive.writestr(filename, contents)
        stream.seek(0)
        return FileStorage(stream=stream, filename='export.zip')

    @staticmethod
    def valid_tiktok_data() -> dict:
        return {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [
                        {'Date': '2026-01-01 10:00:00', 'Link': 'video'}
                    ],
                },
                'Login History': {
                    'LoginHistoryList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'NetworkType': 'Wi-Fi',
                        }
                    ],
                },
            }
        }

    def test_valid_zip_archive_is_accepted_and_rewound(self):
        uploaded_file = self.create_upload({'example.txt': b'content'})

        is_valid, error = validate_zip_archive(uploaded_file)

        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertEqual(uploaded_file.stream.tell(), 0)

    def test_non_zip_file_is_rejected_and_rewound(self):
        uploaded_file = FileStorage(
            stream=BytesIO(b'not a zip file'),
            filename='fake.zip',
        )

        is_valid, error = validate_zip_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(error, 'The uploaded file is not a valid ZIP archive.')
        self.assertEqual(uploaded_file.stream.tell(), 0)

    def test_zip_over_uncompressed_size_limit_is_rejected(self):
        uploaded_file = self.create_upload({'large.txt': b'12345'})

        with patch('services.file_services.MAX_UNCOMPRESSED_SIZE', 4):
            is_valid, error = validate_zip_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'The ZIP archive contains too much uncompressed data.',
        )

    def test_valid_tiktok_archive_returns_parsed_data(self):
        expected_data = self.valid_tiktok_data()
        uploaded_file = self.create_upload({
            'user_data_tiktok.json': json.dumps(expected_data).encode(),
        })

        is_valid, error, data = validate_tiktok_archive(uploaded_file)

        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertEqual(data, expected_data)

    def test_archive_missing_tiktok_file_is_rejected(self):
        uploaded_file = self.create_upload({'other.json': b'{}'})

        is_valid, error, data = validate_tiktok_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'TikTok data file is missing from the archive.',
        )
        self.assertIsNone(data)

    def test_archive_with_invalid_json_is_rejected(self):
        uploaded_file = self.create_upload({
            'user_data_tiktok.json': b'{invalid json',
        })

        is_valid, error, data = validate_tiktok_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(error, 'The TikTok JSON file is invalid.')
        self.assertIsNone(data)

    def test_archive_with_invalid_structure_is_rejected(self):
        uploaded_file = self.create_upload({
            'user_data_tiktok.json': b'{}',
        })

        is_valid, error, data = validate_tiktok_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required TikTok section: Your Activity.',
        )
        self.assertIsNone(data)

    def test_archive_with_missing_record_field_is_rejected(self):
        invalid_data = self.valid_tiktok_data()
        invalid_data['Your Activity']['Watch History']['VideoList'][0].pop(
            'Link'
        )
        uploaded_file = self.create_upload({
            'user_data_tiktok.json': json.dumps(invalid_data).encode(),
        })

        is_valid, error, data = validate_tiktok_archive(uploaded_file)

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            'Missing required field(s) in watch_history: Link.',
        )
        self.assertIsNone(data)


class LoginHistoryExtractionTests(unittest.TestCase):

    def test_only_date_is_extracted_from_watch_history(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'Link': 'https://example.com/video',
                        }
                    ]
                }
            }
        }

        records = get_watch_history(data)

        self.assertEqual(
            records,
            [{'Date': '2026-01-01 10:00:00'}],
        )

    def test_only_allowlisted_login_fields_are_extracted(self):
        data = {
            'Your Activity': {
                'Login History': {
                    'LoginHistoryList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'NetworkType': 'Wi-Fi',
                            'IP': '192.0.2.1',
                            'DeviceModel': 'Example phone',
                            'DeviceSystem': 'Example OS',
                            'Carrier': 'Example carrier',
                        }
                    ]
                }
            }
        }

        records = get_login_history(data)

        self.assertEqual(
            records,
            [
                {
                    'Date': '2026-01-01 10:00:00',
                    'NetworkType': 'Wi-Fi',
                }
            ],
        )


if __name__ == '__main__':
    unittest.main()
