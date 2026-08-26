import base64
from io import BytesIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def create_hourly_chart(hourly_counts: pd.Series):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(hourly_counts.index, hourly_counts.values)

    hour_labels = [
        '12 AM',
        *[f'{hour} AM' for hour in range(1, 12)],
        '12 PM',
        *[f'{hour} PM' for hour in range(1, 12)],
    ]
    ax.set_xticks(range(24), hour_labels, rotation=45, ha='right')
    ax.set_title('Viewing activity by hour')
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Videos Watched')

    fig.tight_layout()
    return fig


def create_weekday_chart(weekday_counts: pd.Series):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_title('Viewing activity by weekday')

    if weekday_counts.sum() > 0:
        ax.pie(
            weekday_counts.values,
            labels=weekday_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            counterclock=False,
        )
        ax.axis('equal')
    else:
        ax.text(
            0.5,
            0.5,
            'No weekday activity to display',
            ha='center',
            va='center',
            transform=ax.transAxes,
        )
        ax.axis('off')

    fig.tight_layout()
    return fig


def create_monthly_chart(monthly_counts: pd.Series):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(monthly_counts.index, monthly_counts.values, marker='o')

    ax.set_xticks(monthly_counts.index)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_title('Monthly viewing trend')
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
                color='black',
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
                transform=ax.get_xaxis_transform(),
            )

    fig.subplots_adjust(bottom=0.32)
    return fig


def figure_to_buffer(fig) -> BytesIO:
    buffer = BytesIO()

    fig.savefig(buffer, format='png')
    buffer.seek(0)

    plt.close(fig)

    return buffer


def buffer_to_base64(buffer: BytesIO) -> str:

    encoded_image = base64.b64encode(buffer.getvalue())
    image_representation = encoded_image.decode('utf-8')

    buffer.close()
    return image_representation
