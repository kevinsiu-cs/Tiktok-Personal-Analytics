from typing import Any

from werkzeug.datastructures import FileStorage

from analytics import login_history, watch_history
from services import file_services
from visualisations import matplotlib_charts


def _format_duration(duration) -> str:
    """Format an observed session duration for concise dashboard display."""
    total_minutes = int(duration.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)

    if hours:
        return f'{hours} h {minutes} min'

    return f'{minutes} min'


def _format_hour(hour: int | None) -> str:
    """Format a 24-hour integer as a familiar dashboard label."""
    if hour is None:
        return '—'

    suffix = 'AM' if hour < 12 else 'PM'
    display_hour = hour % 12 or 12
    return f'{display_hour} {suffix}'


def _create_watch_dashboard(
    watch_history_dates: list[Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create watch statistics and the figures that depend on them."""
    watch_history_df = watch_history.create_watch_history_dataframe(
        watch_history_dates
    )
    watch_history_df = watch_history.add_watch_history_features(
        watch_history_df
    )

    statistics = watch_history.create_watch_history_summary(
        watch_history_df
    )
    statistics['average_session_duration_display'] = _format_duration(
        statistics['average_estimated_session_duration']
    )
    statistics['longest_session_duration_display'] = _format_duration(
        statistics['longest_estimated_session_duration']
    )
    statistics['most_active_hour_display'] = _format_hour(
        statistics['most_active_hour']
    )

    figures = {
        'hourly': matplotlib_charts.create_hourly_chart(
            statistics['hourly_counts']
        ),
        'daily': matplotlib_charts.create_daily_chart(
            statistics['daily_counts']
        ),
        'weekly': matplotlib_charts.create_weekly_chart(
            statistics['weekly_counts']
        ),
        'monthly': matplotlib_charts.create_monthly_chart(
            statistics['monthly_counts']
        ),
        'weekday': matplotlib_charts.create_weekday_chart(
            statistics['weekday_counts']
        ),
    }

    return statistics, figures


def _create_login_dashboard(
    login_history_dates: list[Any],
) -> tuple[dict[str, Any], Any | None]:
    """Create login statistics and its optional daily figure."""
    login_history_df = login_history.create_login_history_dataframe(
        login_history_dates
    )
    login_statistics = login_history.create_login_history_summary(
        login_history_df
    )
    login_statistics['most_active_hour_display'] = _format_hour(
        login_statistics['most_active_login_hour']
    )

    login_figure = None
    if not login_history_df.empty:
        login_figure = matplotlib_charts.create_daily_login_chart(
            login_statistics['daily_counts']
        )

    return login_statistics, login_figure


def _encode_figures(figures: dict[str, Any]) -> dict[str, str]:
    """Convert dashboard figures into base64 strings for the template."""
    charts = {}

    for chart_name, figure in figures.items():
        buffer = matplotlib_charts.figure_to_buffer(figure)
        charts[chart_name] = matplotlib_charts.buffer_to_base64(buffer)

    return charts


def process_tiktok_upload(
    uploaded_file: FileStorage,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Validate a TikTok export and coordinate dashboard creation."""
    is_valid, error_message, histories = (
        file_services.validate_tiktok_archive(uploaded_file)
    )

    if not is_valid or histories is None:
        return False, error_message, None

    statistics, figures = _create_watch_dashboard(
        histories['watch_history']
    )
    login_statistics, login_figure = _create_login_dashboard(
        histories['login_history']
    )

    if login_figure is not None:
        figures['login_daily'] = login_figure

    return True, None, {
        'statistics': statistics,
        'login_statistics': login_statistics,
        'charts': _encode_figures(figures),
    }
