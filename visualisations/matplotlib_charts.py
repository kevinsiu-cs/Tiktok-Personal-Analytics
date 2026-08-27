import base64
from io import BytesIO

import matplotlib.dates as mdates
from matplotlib.figure import Figure
import pandas as pd


BACKGROUND_COLOUR = '#121a2a'
CARD_COLOUR = '#192335'
TEXT_COLOUR = '#f7f8fb'
MUTED_COLOUR = '#9ba7b8'
ACCENT_COLOUR = '#fe2c55'
SECONDARY_ACCENT_COLOUR = '#25f4ee'


def _style_axes(ax):
    """Apply the dashboard's shared visual style to a chart."""
    ax.set_facecolor(CARD_COLOUR)
    ax.tick_params(colors=MUTED_COLOUR)
    ax.xaxis.label.set_color(MUTED_COLOUR)
    ax.yaxis.label.set_color(MUTED_COLOUR)
    ax.grid(axis='y', color='#2b374b', linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_visible(False)


def _create_figure(figsize=(9, 5)):
    fig = Figure(figsize=figsize)
    ax = fig.subplots()
    fig.patch.set_facecolor(CARD_COLOUR)
    _style_axes(ax)
    return fig, ax


def _format_date_axis(ax, maximum_ticks: int = 6):
    """Keep time-series labels concise and readable at dashboard sizes."""
    date_locator = mdates.AutoDateLocator(minticks=3, maxticks=maximum_ticks)
    ax.xaxis.set_major_locator(date_locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
    ax.tick_params(axis='x', labelrotation=0)


def _format_month_axis(ax, interval: int = 2):
    """Show uncluttered month and year labels on longer time series."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.tick_params(axis='x', labelrotation=0)


def create_hourly_chart(hourly_counts: pd.Series):
    fig, ax = _create_figure()
    ax.bar(hourly_counts.index, hourly_counts.values, color=ACCENT_COLOUR)

    hour_labels = [
        '12 AM',
        *[f'{hour} AM' for hour in range(1, 12)],
        '12 PM',
        *[f'{hour} PM' for hour in range(1, 12)],
    ]
    ax.set_xticks(range(24), hour_labels, rotation=45, ha='right')
    ax.set_ylabel('Videos Watched')

    fig.tight_layout()
    return fig


def create_weekday_chart(weekday_counts: pd.Series):
    fig, ax = _create_figure()

    if weekday_counts.sum() > 0:
        colours = [
            '#fe2c55',
            '#e54768',
            '#ca617c',
            '#a77991',
            '#7e94aa',
            '#54bac3',
            '#25f4ee',
        ]
        _, _, percentages = ax.pie(
            weekday_counts.values,
            labels=weekday_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            counterclock=False,
            colors=colours,
            textprops={'color': TEXT_COLOUR},
        )
        for percentage in percentages:
            percentage.set_fontsize(8)
        ax.axis('equal')
    else:
        ax.text(
            0.5,
            0.5,
            'No weekday activity to display',
            ha='center',
            va='center',
            color=MUTED_COLOUR,
            transform=ax.transAxes,
        )
        ax.axis('off')

    fig.tight_layout()
    return fig


def create_monthly_chart(monthly_counts: pd.Series):
    fig, ax = _create_figure()
    ax.plot(
        monthly_counts.index,
        monthly_counts.values,
        marker='o',
        color=ACCENT_COLOUR,
    )

    ax.set_xticks(monthly_counts.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_ylabel('Videos Watched')

    if not monthly_counts.empty:
        first_month = monthly_counts.index.min()
        last_month = monthly_counts.index.max()
        ax.set_xlim(
            first_month - pd.Timedelta(days=15),
            last_month + pd.Timedelta(days=15),
        )

        for year in monthly_counts.index.year.unique():
            year_months = monthly_counts.index[
                monthly_counts.index.year == year
            ]
            span_start = mdates.date2num(
                year_months.min() - pd.Timedelta(days=15)
            )
            span_end = mdates.date2num(
                year_months.max() + pd.Timedelta(days=15)
            )
            span_centre = (span_start + span_end) / 2

            ax.plot(
                [span_start, span_start, span_end, span_end],
                [-0.18, -0.22, -0.22, -0.18],
                color=MUTED_COLOUR,
                linewidth=0.8,
                transform=ax.get_xaxis_transform(),
                clip_on=False,
            )
            ax.text(
                span_centre,
                -0.27,
                str(year),
                ha='center',
                va='top',
                color=MUTED_COLOUR,
                transform=ax.get_xaxis_transform(),
            )

    fig.subplots_adjust(bottom=0.32)
    return fig


def create_daily_chart(daily_counts: pd.Series):
    fig, ax = _create_figure(figsize=(12, 5))
    rolling_average = daily_counts.rolling(
        window=7,
        min_periods=1,
    ).mean()

    ax.plot(
        daily_counts.index,
        daily_counts.values,
        color=ACCENT_COLOUR,
        linewidth=0.8,
        alpha=0.38,
        label='Daily activity',
    )
    ax.plot(
        rolling_average.index,
        rolling_average.values,
        color=SECONDARY_ACCENT_COLOUR,
        linewidth=2.4,
        label='7-day average',
    )
    ax.set_ylabel('Videos Watched')
    _format_month_axis(ax)
    legend = ax.legend(frameon=False, loc='upper right')
    for label in legend.get_texts():
        label.set_color(TEXT_COLOUR)
    fig.tight_layout()
    return fig


def create_weekly_chart(weekly_counts: pd.Series):
    fig, ax = _create_figure()
    ax.plot(
        weekly_counts.index,
        weekly_counts.values,
        color=SECONDARY_ACCENT_COLOUR,
        linewidth=2.2,
    )
    ax.set_ylabel('Videos Watched')
    _format_month_axis(ax)
    fig.tight_layout()
    return fig


def create_daily_login_chart(daily_counts: pd.Series):
    fig, ax = _create_figure(figsize=(12, 5))
    rolling_average = daily_counts.rolling(
        window=7,
        min_periods=1,
    ).mean()

    ax.plot(
        daily_counts.index,
        daily_counts.values,
        color=ACCENT_COLOUR,
        linewidth=0.8,
        alpha=0.38,
        label='Daily activity',
    )
    ax.plot(
        rolling_average.index,
        rolling_average.values,
        color=SECONDARY_ACCENT_COLOUR,
        linewidth=2.4,
        label='7-day average',
    )
    ax.set_ylabel('Login Events')
    _format_month_axis(ax)
    legend = ax.legend(frameon=False, loc='upper right')
    for label in legend.get_texts():
        label.set_color(TEXT_COLOUR)
    fig.tight_layout()
    return fig


def figure_to_buffer(fig) -> BytesIO:
    buffer = BytesIO()

    fig.savefig(
        buffer,
        format='png',
        facecolor=fig.get_facecolor(),
        bbox_inches='tight',
    )
    buffer.seek(0)

    return buffer


def buffer_to_base64(buffer: BytesIO) -> str:

    encoded_image = base64.b64encode(buffer.getvalue())
    image_representation = encoded_image.decode('utf-8')

    buffer.close()
    return image_representation
