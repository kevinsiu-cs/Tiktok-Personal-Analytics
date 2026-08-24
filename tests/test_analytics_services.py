import unittest

from services.analytics_services import get_login_history, get_watch_history


class WatchHistoryExtractionTests(unittest.TestCase):

    def test_only_allowlisted_watch_fields_are_extracted(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [
                        {
                            'Date': '2026-01-01 10:00:00',
                            'Link': 'https://example.com/private-video',
                            'ExtraPrivateField': 'private',
                        }
                    ]
                }
            }
        }

        records = get_watch_history(data)

        self.assertEqual(records, [{'Date': '2026-01-01 10:00:00'}])

    def test_empty_watch_history_returns_empty_list(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [],
                }
            }
        }

        self.assertEqual(get_watch_history(data), [])

    def test_missing_watch_date_is_returned_as_none(self):
        data = {
            'Your Activity': {
                'Watch History': {
                    'VideoList': [{'Link': 'private'}],
                }
            }
        }

        self.assertEqual(get_watch_history(data), [{'Date': None}])

    def test_none_watch_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'TikTok data cannot be empty'):
            get_watch_history(None)


class LoginHistoryExtractionTests(unittest.TestCase):

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
                        }
                    ]
                }
            }
        }

        records = get_login_history(data)

        self.assertEqual(records, [{
            'Date': '2026-01-01 10:00:00',
            'NetworkType': 'Wi-Fi',
        }])

    def test_empty_login_history_returns_empty_list(self):
        data = {
            'Your Activity': {
                'Login History': {
                    'LoginHistoryList': [],
                }
            }
        }

        self.assertEqual(get_login_history(data), [])

    def test_missing_login_fields_are_returned_as_none(self):
        data = {
            'Your Activity': {
                'Login History': {
                    'LoginHistoryList': [{}],
                }
            }
        }

        self.assertEqual(get_login_history(data), [{
            'Date': None,
            'NetworkType': None,
        }])

    def test_none_login_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'TikTok data cannot be empty'):
            get_login_history(None)


if __name__ == '__main__':
    unittest.main()
