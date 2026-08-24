import unittest

import pandas as pd

from analytics import login_history


class LoginHistoryAnalyticsTests(unittest.TestCase):

    def setUp(self):
        records = [
            {'Date': '2026-01-01 08:00:00', 'NetworkType': 'Wi-Fi'},
            {'Date': '2026-01-01 08:30:00', 'NetworkType': '5G'},
            {'Date': '2026-01-02 09:00:00', 'NetworkType': 'Unexpected'},
        ]
        self.login_history_df = (
            login_history.create_login_history_dataframe(records)
        )

    def test_dataframe_contains_only_allowlisted_columns(self):
        records = [
            {
                'Date': '2026-01-01 08:00:00',
                'NetworkType': 'Wi-Fi',
                'IP': '192.0.2.1',
            }
        ]

        dataframe = login_history.create_login_history_dataframe(records)

        self.assertEqual(list(dataframe.columns), ['Date', 'NetworkType'])

    def test_summary_calculates_login_metrics(self):
        summary = login_history.create_login_history_summary(
            self.login_history_df
        )

        self.assertEqual(summary['total_login_events'], 3)
        self.assertEqual(summary['most_active_login_hour'], 8)
        self.assertEqual(summary['average_logins_per_active_day'], 1.5)
        self.assertEqual(summary['network_type_counts']['Wi-Fi'], 1)
        self.assertEqual(summary['network_type_counts']['Cellular'], 1)
        self.assertEqual(summary['network_type_counts']['Other'], 1)

    def test_dataframe_drops_invalid_dates(self):
        records = [
            {'Date': '2026-01-01 08:00:00', 'NetworkType': 'Wi-Fi'},
            {'Date': 'invalid', 'NetworkType': '5G'},
        ]

        dataframe = login_history.create_login_history_dataframe(records)

        self.assertEqual(len(dataframe), 1)
        self.assertEqual(
            dataframe.iloc[0]['Date'],
            pd.Timestamp('2026-01-01 08:00:00'),
        )

    def test_empty_dataframe_has_expected_columns(self):
        dataframe = login_history.create_login_history_dataframe([])

        self.assertTrue(dataframe.empty)
        self.assertEqual(list(dataframe.columns), ['Date', 'NetworkType'])

    def test_count_functions_group_logins_correctly(self):
        daily = login_history.get_login_daily_counts(self.login_history_df)
        weekly = login_history.get_login_weekly_counts(self.login_history_df)
        monthly = login_history.get_login_monthly_counts(self.login_history_df)
        hourly = login_history.get_login_hourly_counts(self.login_history_df)
        weekdays = login_history.get_login_weekday_counts(
            self.login_history_df
        )

        self.assertEqual(daily.loc['2026-01-01'], 2)
        self.assertEqual(weekly.sum(), 3)
        self.assertEqual(monthly.loc['2026-01-01'], 3)
        self.assertEqual(hourly.loc[8], 2)
        self.assertEqual(weekdays.loc['Thursday'], 2)

    def test_average_logins_ignores_inactive_days(self):
        records = [
            {'Date': '2026-01-01 08:00:00', 'NetworkType': 'Wi-Fi'},
            {'Date': '2026-01-03 08:00:00', 'NetworkType': 'Wi-Fi'},
            {'Date': '2026-01-03 09:00:00', 'NetworkType': 'Wi-Fi'},
        ]
        dataframe = login_history.create_login_history_dataframe(records)

        average = login_history.get_average_logins_per_active_day(dataframe)

        self.assertEqual(average, 1.5)

    def test_average_logins_for_empty_history_is_zero(self):
        dataframe = login_history.create_login_history_dataframe([])

        self.assertEqual(
            login_history.get_average_logins_per_active_day(dataframe),
            0.0,
        )

    def test_network_labels_are_normalised(self):
        cases = {
            ' WiFi ': 'Wi-Fi',
            'WI-FI': 'Wi-Fi',
            '5g': 'Cellular',
            ' LTE ': 'Cellular',
            'unknown': 'Other',
            None: 'Other',
            5: 'Other',
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(
                    login_history.classify_network_type(value),
                    expected,
                )

    def test_network_counts_include_zero_value_categories(self):
        dataframe = login_history.create_login_history_dataframe([
            {'Date': '2026-01-01 08:00:00', 'NetworkType': 'Wi-Fi'},
        ])

        counts = login_history.get_network_type_counts(dataframe)

        self.assertEqual(list(counts.index), ['Wi-Fi', 'Cellular', 'Other'])
        self.assertEqual(counts.to_dict(), {
            'Wi-Fi': 1,
            'Cellular': 0,
            'Other': 0,
        })

    def test_network_percentages_total_one_hundred(self):
        percentages = login_history.get_network_type_percentages(
            self.login_history_df
        )

        self.assertAlmostEqual(percentages.sum(), 100.0)
        self.assertAlmostEqual(percentages.loc['Wi-Fi'], 100 / 3)

    def test_empty_network_percentages_are_zero(self):
        dataframe = login_history.create_login_history_dataframe([])

        percentages = login_history.get_network_type_percentages(dataframe)

        self.assertEqual(percentages.to_dict(), {
            'Wi-Fi': 0.0,
            'Cellular': 0.0,
            'Other': 0.0,
        })

    def test_empty_summary_has_no_most_active_values(self):
        dataframe = login_history.create_login_history_dataframe([])

        summary = login_history.create_login_history_summary(dataframe)

        self.assertEqual(summary['total_login_events'], 0)
        self.assertIsNone(summary['most_active_login_hour'])
        self.assertIsNone(summary['most_active_login_weekday'])


if __name__ == '__main__':
    unittest.main()
