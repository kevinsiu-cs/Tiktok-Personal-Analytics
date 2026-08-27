import unittest

import pandas as pd

from analytics import watch_history


class WatchHistoryAnalyticsTests(unittest.TestCase):

    def setUp(self):
        records = [
            '2026-01-01 23:50:00',
            '2026-01-02 00:20:00',
            '2026-01-02 01:00:01',
            '2026-01-04 12:00:00',
        ]
        dataframe = watch_history.create_watch_history_dataframe(records)
        self.watch_history_df = watch_history.add_watch_history_features(
            dataframe
        )

    def test_session_threshold_is_inclusive(self):
        sessions = watch_history.infer_watch_sessions(
            self.watch_history_df
        )

        self.assertEqual(len(sessions), 3)
        self.assertEqual(sessions.loc[0, 'VideosWatched'], 2)
        self.assertEqual(
            sessions.loc[0, 'EstimatedDuration'],
            pd.Timedelta(minutes=30),
        )

    def test_session_summary_does_not_invent_final_video_duration(self):
        sessions = watch_history.infer_watch_sessions(
            self.watch_history_df
        )
        statistics = watch_history.get_watch_session_statistics(sessions)

        self.assertEqual(
            statistics['estimated_total_observed_scrolling_time'],
            pd.Timedelta(minutes=30),
        )
        self.assertEqual(statistics['maximum_videos_in_one_session'], 2)

    def test_summary_contains_daily_and_session_metrics(self):
        summary = watch_history.create_watch_history_summary(
            self.watch_history_df
        )

        self.assertEqual(summary['total_videos_watched'], 4)
        self.assertEqual(summary['active_days'], 3)
        self.assertEqual(summary['maximum_videos_in_one_day'], 2)
        self.assertEqual(summary['number_of_estimated_sessions'], 3)
        self.assertEqual(summary['average_sessions_per_active_day'], 1.0)
        self.assertEqual(summary['late_night_activity_percentage'], 50.0)

    def test_dataframe_drops_invalid_dates(self):
        records = [
            '2026-01-01 10:00:00',
            'not a date',
        ]

        dataframe = watch_history.create_watch_history_dataframe(records)

        self.assertEqual(list(dataframe.columns), ['Date'])
        self.assertEqual(len(dataframe), 1)
        self.assertEqual(dataframe.iloc[0]['Date'], pd.Timestamp('2026-01-01 10:00:00'))

    def test_features_are_added_without_modifying_original_dataframe(self):
        dataframe = watch_history.create_watch_history_dataframe([
            '2026-01-03 14:00:00',
        ])

        featured = watch_history.add_watch_history_features(dataframe)

        self.assertEqual(list(dataframe.columns), ['Date'])
        self.assertEqual(featured.iloc[0]['Day'], 'Saturday')
        self.assertEqual(featured.iloc[0]['Hour'], 14)
        self.assertEqual(str(featured.iloc[0]['DateOnly']), '2026-01-03')

    def test_basic_range_metrics(self):
        self.assertEqual(watch_history.get_total_videos_watched(self.watch_history_df), 4)
        self.assertEqual(
            watch_history.get_first_watch_datetime(self.watch_history_df),
            pd.Timestamp('2026-01-01 23:50:00'),
        )
        self.assertEqual(
            watch_history.get_last_watch_datetime(self.watch_history_df),
            pd.Timestamp('2026-01-04 12:00:00'),
        )

    def test_empty_dataframe_has_empty_range_metrics(self):
        empty = watch_history.add_watch_history_features(
            watch_history.create_watch_history_dataframe([])
        )

        self.assertIsNone(watch_history.get_first_watch_datetime(empty))
        self.assertIsNone(watch_history.get_last_watch_datetime(empty))
        self.assertEqual(watch_history.get_watch_active_days(empty), 0)

    def test_count_functions_group_events_correctly(self):
        hourly = watch_history.get_watch_hourly_counts(self.watch_history_df)
        daily = watch_history.get_watch_daily_counts(self.watch_history_df)
        weekdays = watch_history.get_watch_weekday_counts(self.watch_history_df)
        weekly = watch_history.get_watch_weekly_counts(self.watch_history_df)
        monthly = watch_history.get_watch_monthly_counts(self.watch_history_df)

        self.assertEqual(hourly.loc[0], 1)
        self.assertEqual(daily.loc['2026-01-02'], 2)
        self.assertEqual(weekdays.loc['Friday'], 2)
        self.assertEqual(weekly.sum(), 4)
        self.assertEqual(monthly.loc['2026-01-01'], 4)

    def test_daily_activity_statistics_use_only_active_days(self):
        statistics = watch_history.get_watch_daily_activity_statistics(
            self.watch_history_df
        )

        self.assertAlmostEqual(statistics['average_videos_per_active_day'], 4 / 3)
        self.assertEqual(statistics['median_videos_per_active_day'], 1.0)
        self.assertEqual(statistics['maximum_videos_in_one_day'], 2)

    def test_empty_daily_activity_statistics_are_zero(self):
        empty = watch_history.create_watch_history_dataframe([])

        statistics = watch_history.get_watch_daily_activity_statistics(empty)

        self.assertEqual(statistics['average_videos_per_active_day'], 0.0)
        self.assertEqual(statistics['maximum_videos_in_one_day'], 0)

    def test_late_night_period_supports_crossing_midnight(self):
        percentage = watch_history.get_watch_late_night_activity_percentage(
            self.watch_history_df,
            start_hour=23,
            end_hour=1,
        )

        self.assertEqual(percentage, 50.0)

    def test_late_night_period_rejects_invalid_boundaries(self):
        for start_hour, end_hour in [(-1, 5), (0, 24), (5, 5)]:
            with self.subTest(start_hour=start_hour, end_hour=end_hour):
                with self.assertRaises(ValueError):
                    watch_history.get_watch_late_night_activity_percentage(
                        self.watch_history_df,
                        start_hour,
                        end_hour,
                    )

    def test_daily_usage_trend_detects_increase(self):
        records = [
            '2026-01-01 10:00:00',
            '2026-01-02 10:00:00',
            '2026-01-02 11:00:00',
            '2026-01-03 10:00:00',
            '2026-01-03 11:00:00',
            '2026-01-03 12:00:00',
        ]
        dataframe = watch_history.create_watch_history_dataframe(records)

        trend = watch_history.get_watch_daily_usage_trend(dataframe)

        self.assertEqual(trend['direction'], 'increasing')
        self.assertEqual(trend['daily_slope'], 1.0)

    def test_daily_usage_trend_rejects_negative_threshold(self):
        with self.assertRaisesRegex(ValueError, 'cannot be negative'):
            watch_history.get_watch_daily_usage_trend(
                self.watch_history_df,
                stable_threshold=-0.1,
            )

    def test_session_inference_sorts_events(self):
        unordered = self.watch_history_df.sort_values('Date', ascending=False)

        sessions = watch_history.infer_watch_sessions(unordered)

        self.assertEqual(sessions.iloc[0]['StartTime'], pd.Timestamp('2026-01-01 23:50:00'))

    def test_session_inference_rejects_non_positive_threshold(self):
        for threshold in [pd.Timedelta(0), pd.Timedelta(minutes=-1)]:
            with self.subTest(threshold=threshold):
                with self.assertRaisesRegex(ValueError, 'greater than zero'):
                    watch_history.infer_watch_sessions(
                        self.watch_history_df,
                        threshold,
                    )

    def test_empty_session_statistics_are_zero(self):
        empty_sessions = watch_history.infer_watch_sessions(
            watch_history.create_watch_history_dataframe([])
        )

        statistics = watch_history.get_watch_session_statistics(
            empty_sessions
        )

        self.assertEqual(statistics['number_of_estimated_sessions'], 0)
        self.assertEqual(
            statistics['longest_estimated_session_duration'],
            pd.Timedelta(0),
        )

    def test_average_sessions_per_active_day(self):
        sessions = watch_history.infer_watch_sessions(self.watch_history_df)

        self.assertEqual(
            watch_history.get_average_watch_sessions_per_active_day(sessions, 3),
            1.0,
        )
        self.assertEqual(
            watch_history.get_average_watch_sessions_per_active_day(sessions, 0),
            0.0,
        )
        with self.assertRaisesRegex(ValueError, 'cannot be negative'):
            watch_history.get_average_watch_sessions_per_active_day(sessions, -1)


if __name__ == '__main__':
    unittest.main()
