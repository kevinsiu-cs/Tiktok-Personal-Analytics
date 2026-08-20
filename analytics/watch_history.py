import pandas as pd


DEFAULT_SESSION_INACTIVITY_THRESHOLD = pd.Timedelta(minutes=30)
DEFAULT_LATE_NIGHT_START_HOUR = 0
DEFAULT_LATE_NIGHT_END_HOUR = 5


def create_watch_history_dataframe(watch_history: list[dict]) -> pd.DataFrame:

    watch_history_df = pd.DataFrame(watch_history, columns=['Date'])

    if 'Date' not in watch_history_df.columns:
        raise ValueError('Watch History is missing Date Column')

    watch_history_df['Date'] = pd.to_datetime(
        watch_history_df['Date'],
        errors='coerce',
    )
    watch_history_df = watch_history_df.dropna(subset=['Date'])

    return watch_history_df

def add_watch_history_features(watch_history_df: pd.DataFrame) -> pd.DataFrame:
    featured_df = watch_history_df.copy()

    # Create features based off of what metrics we want to compute
    featured_df['Day'] = featured_df['Date'].dt.day_name()
    featured_df['DateOnly'] = featured_df['Date'].dt.date # Needed due to normal date returning the time
    featured_df['Hour'] = featured_df['Date'].dt.hour

    return featured_df


def get_total_videos_watched(watch_history_df: pd.DataFrame) -> int:
    return len(watch_history_df)

'''
The next two functions are useful for determining how many days the dataset spans
'''
def get_first_watch_datetime(
    watch_history_df: pd.DataFrame,
) -> pd.Timestamp | None:
    if watch_history_df.empty:
        return None

    return watch_history_df['Date'].min()


def get_last_watch_datetime(
    watch_history_df: pd.DataFrame,
) -> pd.Timestamp | None:
    if watch_history_df.empty:
        return None

    return watch_history_df['Date'].max()


def get_calendar_days_covered(watch_history_df: pd.DataFrame) -> int:
    if watch_history_df.empty:
        return 0

    first_date = watch_history_df['Date'].min().normalize()
    last_date = watch_history_df['Date'].max().normalize()
    return (last_date - first_date).days + 1


def get_hourly_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Hour'].value_counts()

def get_daily_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df.resample('D', on='Date').size()

def get_weekday_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df['Day'].value_counts()


def get_weekly_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    # rule: W-Mon, Weekly buckets starting from Monday
    # label: Label is using the left value of the 'bucket'
    # closed: We are including the left value and ignoring the right.
    return watch_history_df.resample(
        'W-MON', on='Date', label='left', closed='left'
    ).size()


def get_monthly_counts(watch_history_df: pd.DataFrame) -> pd.Series:
    return watch_history_df.resample('MS', on='Date').size()


def get_active_days(watch_history_df: pd.DataFrame) -> int:
    return int((get_daily_counts(watch_history_df) > 0).sum())


def get_daily_activity_statistics(
    watch_history_df: pd.DataFrame,
) -> dict[str, float | int]:
    active_daily_counts = get_daily_counts(watch_history_df)
    active_daily_counts = active_daily_counts[active_daily_counts > 0]

    if active_daily_counts.empty:
        return {
            'average_videos_per_active_day': 0.0,
            'median_videos_per_active_day': 0.0,
            'maximum_videos_in_one_day': 0,
        }

    return {
        'average_videos_per_active_day': float(active_daily_counts.mean()),
        'median_videos_per_active_day': float(active_daily_counts.median()),
        'maximum_videos_in_one_day': int(active_daily_counts.max()),
    }


def get_weekday_weekend_activity(
    watch_history_df: pd.DataFrame,
) -> dict[str, int | float]:

    #dt.weekday returns an integer from 0 to 6 to represent the weekdays, In order for
    #our sum function to be correct, we will need to create a boolean series representing
    #which day is a weekday, rather than the specific days.

    weekday_events = int((watch_history_df['Date'].dt.weekday < 5).sum())
    weekend_events = len(watch_history_df) - weekday_events
    total_events = len(watch_history_df)

    return {
        'weekday_count': weekday_events,
        'weekend_count': weekend_events,
        'weekday_percentage': (
            weekday_events / total_events * 100 if total_events else 0.0
        ),
        'weekend_percentage': (
            weekend_events / total_events * 100 if total_events else 0.0
        ),
    }


def get_late_night_activity_percentage(
    watch_history_df: pd.DataFrame,
    start_hour: int = DEFAULT_LATE_NIGHT_START_HOUR,
    end_hour: int = DEFAULT_LATE_NIGHT_END_HOUR,
) -> float:
    """Return watch activity in a configurable half-open hourly period."""
    if not 0 <= start_hour <= 23 or not 0 <= end_hour <= 23:
        raise ValueError('Late-night hours must be between 0 and 23')

    if start_hour == end_hour:
        raise ValueError('Late-night start and end hours must differ')

    if watch_history_df.empty:
        return 0.0

    hours = watch_history_df['Date'].dt.hour

    # Handle time ranges that cross midnight, such as 22:00 to 05:00.
    if start_hour < end_hour:
        late_night_events = hours.between(start_hour, end_hour - 1)
    else:
        late_night_events = (hours >= start_hour) | (hours < end_hour)

    return float(late_night_events.mean() * 100)


def get_daily_usage_trend(
    watch_history_df: pd.DataFrame,
    stable_threshold: float = 0.01,
) -> dict[str, float | str]:
    """Estimate the linear change in daily video counts over the date range."""
    if stable_threshold < 0:
        raise ValueError('Stable threshold cannot be negative')

    daily_counts = get_daily_counts(watch_history_df).astype(float)


    """
    daily_slope => estimated rate of change
    direction => increasing, decreasing or stable
    """
    if len(daily_counts) < 2:
        return {'daily_slope': 0.0,
                'direction': 'stable'}


    #Centering subtracts the average from each value so everything is measured relative to the usual value.
    #This makes it easier to see whether usage tends to increase or decrease over time.

    day_numbers = pd.Series(range(len(daily_counts)), dtype='float64')
    centred_days = day_numbers - day_numbers.mean()
    centred_counts = daily_counts.reset_index(drop=True) - daily_counts.mean()


    daily_slope = float(
        (centred_days * centred_counts).sum()
        / centred_days.pow(2).sum()
    )

    if daily_slope > stable_threshold:
        direction = 'increasing'
    elif daily_slope < -stable_threshold:
        direction = 'decreasing'
    else:
        direction = 'stable'

    return {'daily_slope': daily_slope,
            'direction': direction}


def infer_estimated_sessions(
    watch_history_df: pd.DataFrame,
    inactivity_threshold: pd.Timedelta = DEFAULT_SESSION_INACTIVITY_THRESHOLD,
) -> pd.DataFrame:
    """Infer sessions from timestamps separated by no more than the threshold."""
    if inactivity_threshold <= pd.Timedelta(0):
        raise ValueError('Inactivity threshold must be greater than zero')

    session_columns = [
        'SessionId',
        'StartTime',
        'EndTime',
        'EstimatedDuration',
        'VideosWatched',
    ]

    if watch_history_df.empty:
        return pd.DataFrame(columns=session_columns)

    ordered_events = watch_history_df[['Date']].sort_values('Date').copy()
    event_gaps = ordered_events['Date'].diff()

    # Flag to see if threshold is broken to start a new session.
    starts_new_session = event_gaps.isna() | (
        event_gaps > inactivity_threshold
    )

    # Assign each event to a SessionId
    ordered_events['SessionId'] = starts_new_session.cumsum()

    sessions = ordered_events.groupby('SessionId')['Date'].agg(
        StartTime='min',
        EndTime='max',
        VideosWatched='size',
    ).reset_index()
    sessions['EstimatedDuration'] = (
        sessions['EndTime'] - sessions['StartTime']
    )

    return sessions[session_columns]


def get_estimated_session_statistics(
    estimated_sessions_df: pd.DataFrame,
) -> dict[str, int | float | pd.Timedelta]:
    """Summarise sessions inferred from observed Watch History timestamps."""
    number_of_sessions = len(estimated_sessions_df)

    if estimated_sessions_df.empty:
        return {
            'number_of_estimated_sessions': 0,
            'estimated_total_observed_scrolling_time': pd.Timedelta(0),
            'average_estimated_session_duration': pd.Timedelta(0),
            'median_estimated_session_duration': pd.Timedelta(0),
            'longest_estimated_session_duration': pd.Timedelta(0),
            'average_videos_per_session': 0.0,
            'median_videos_per_session': 0.0,
            'maximum_videos_in_one_session': 0,
        }

    durations = estimated_sessions_df['EstimatedDuration']
    videos_per_session = estimated_sessions_df['VideosWatched']

    return {
        'number_of_estimated_sessions': number_of_sessions,
        'estimated_total_observed_scrolling_time': durations.sum(),
        'average_estimated_session_duration': durations.mean(),
        'median_estimated_session_duration': durations.median(),
        'longest_estimated_session_duration': durations.max(),
        'average_videos_per_session': float(videos_per_session.mean()),
        'median_videos_per_session': float(videos_per_session.median()),
        'maximum_videos_in_one_session': int(videos_per_session.max()),
    }


def get_average_sessions_per_active_day(
    estimated_sessions_df: pd.DataFrame,
    active_days: int,
) -> float:
    if active_days < 0:
        raise ValueError('Active days cannot be negative')

    if estimated_sessions_df.empty or active_days == 0:
        return 0.0

    return len(estimated_sessions_df) / active_days


def _get_most_active_value(counts: pd.Series):
    if counts.empty or counts.sum() == 0:
        return None

    return counts.idxmax()


def create_watch_history_summary(
    watch_history_df: pd.DataFrame,
    inactivity_threshold: pd.Timedelta = DEFAULT_SESSION_INACTIVITY_THRESHOLD,
    late_night_start_hour: int = DEFAULT_LATE_NIGHT_START_HOUR,
    late_night_end_hour: int = DEFAULT_LATE_NIGHT_END_HOUR,
) -> dict[str, object]:
    hourly_counts = get_hourly_counts(watch_history_df)
    daily_counts = get_daily_counts(watch_history_df)
    weekday_counts = get_weekday_counts(watch_history_df)
    weekly_counts = get_weekly_counts(watch_history_df)
    monthly_counts = get_monthly_counts(watch_history_df)
    estimated_sessions = infer_estimated_sessions(
        watch_history_df,
        inactivity_threshold,
    )

    summary = {
        'hourly_counts': hourly_counts,
        'daily_counts': daily_counts,
        'weekday_counts': weekday_counts,
        'weekly_counts': weekly_counts,
        'monthly_counts': monthly_counts,

        'most_active_hour': _get_most_active_value(hourly_counts),
        'most_active_weekday': _get_most_active_value(weekday_counts),
        'most_active_day': _get_most_active_value(daily_counts),
        'most_active_week': _get_most_active_value(weekly_counts),
        'most_active_month': _get_most_active_value(monthly_counts),
        'total_videos_watched': get_total_videos_watched(watch_history_df),
        'first_watch_datetime': get_first_watch_datetime(watch_history_df),
        'last_watch_datetime': get_last_watch_datetime(watch_history_df),
        'calendar_days_covered': get_calendar_days_covered(watch_history_df),
        'active_days': get_active_days(watch_history_df),
        'weekday_weekend_activity': get_weekday_weekend_activity(
            watch_history_df
        ),
        'late_night_activity_percentage': get_late_night_activity_percentage(
            watch_history_df,
            late_night_start_hour,
            late_night_end_hour,
        ),
        'daily_usage_trend': get_daily_usage_trend(watch_history_df),
        'estimated_sessions': estimated_sessions,
    }
    summary.update(get_daily_activity_statistics(watch_history_df))
    summary.update(get_estimated_session_statistics(estimated_sessions))
    summary['average_sessions_per_active_day'] = (
        get_average_sessions_per_active_day(
            estimated_sessions,
            summary['active_days'],
        )
    )

    return summary
