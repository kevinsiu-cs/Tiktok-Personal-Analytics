import os

from flask import Flask, render_template
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired

from dotenv import load_dotenv

from wtforms import SubmitField

from analytics import login_history, watch_history
from services import analytics_services, file_services
from visualisations import matplotlib_charts


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MiB


def format_duration(duration) -> str:
    """Format an observed session duration for concise dashboard display."""
    total_minutes = int(duration.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)

    if hours:
        return f'{hours} h {minutes} min'

    return f'{minutes} min'


def format_hour(hour: int | None) -> str:
    """Format a 24-hour integer as a familiar dashboard label."""
    if hour is None:
        return '—'

    suffix = 'AM' if hour < 12 else 'PM'
    display_hour = hour % 12 or 12
    return f'{display_hour} {suffix}'


class UploadFileForm(FlaskForm):

    uploaded_file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(["zip"],)
        ]
    )

    submit = SubmitField('Upload')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadFileForm()
    statistics = None
    charts = None

    if form.validate_on_submit():
        uploaded_file = form.uploaded_file.data
        is_valid, error_message = file_services.validate_zip_archive(
            uploaded_file
        )

        if not is_valid:
            form.uploaded_file.errors.append(error_message)
        else:
            is_valid, error_message, data = (
                file_services.validate_tiktok_archive(uploaded_file)
            )

            if not is_valid:
                form.uploaded_file.errors.append(error_message)
            else:
                watch_history_records = analytics_services.get_watch_history(
                    data
                )
                watch_history_df = watch_history.create_watch_history_dataframe(
                    watch_history_records
                )
                watch_history_df = watch_history.add_watch_history_features(
                    watch_history_df
                )

                statistics = watch_history.create_watch_history_summary(
                    watch_history_df
                )
                statistics['average_session_duration_display'] = (
                    format_duration(
                        statistics['average_estimated_session_duration']
                    )
                )
                statistics['longest_session_duration_display'] = (
                    format_duration(
                        statistics['longest_estimated_session_duration']
                    )
                )
                statistics['most_active_hour_display'] = format_hour(
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

                login_history_records = analytics_services.get_login_history(
                    data
                )
                login_history_df = login_history.create_login_history_dataframe(
                    login_history_records
                )
                login_statistics = login_history.create_login_history_summary(
                    login_history_df
                )
                login_statistics['most_active_hour_display'] = format_hour(
                    login_statistics['most_active_login_hour']
                )

                if not login_history_df.empty:
                    figures['login_daily'] = (
                        matplotlib_charts.create_daily_login_chart(
                            login_statistics['daily_counts']
                        )
                    )

                charts = {}
                for chart_name, figure in figures.items():
                    buffer = matplotlib_charts.figure_to_buffer(figure)
                    charts[chart_name] = (
                        matplotlib_charts.buffer_to_base64(buffer)
                    )

    return render_template(
        'index.html',
        form=form,
        statistics=statistics,
        charts=charts,
        login_statistics=(
            login_statistics if statistics is not None else None
        ),
    )


@app.errorhandler(413)
def upload_too_large(error):
    # Render the normal form instead of Flask's generic oversized-request page.
    form = UploadFileForm(formdata=None)
    return render_template(
        'index.html',
        form=form,
        request_error='The uploaded file must be 50 MB or smaller.',
    ), 413

if __name__ == '__main__':
    app.run(debug=True)
