import os

from flask import Flask, render_template
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired

from dotenv import load_dotenv

from wtforms import SubmitField

from analytics import watch_history
from services import analytics_services, file_services
from visualisations import matplotlib_charts


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MiB

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

                daily_statistics = (
                    watch_history.get_watch_daily_activity_statistics(
                        watch_history_df
                    )
                )

                statistics = {
                    'total_videos': watch_history.get_total_videos_watched(
                        watch_history_df
                    ),
                    'active_days': watch_history.get_watch_active_days(
                        watch_history_df
                    ),
                    'average_per_active_day': daily_statistics[
                        'average_videos_per_active_day'
                    ],
                }

                hourly_counts = watch_history.get_watch_hourly_counts(
                    watch_history_df
                )
                monthly_counts = watch_history.get_watch_monthly_counts(
                    watch_history_df
                )
                weekday_counts = watch_history.get_watch_weekday_counts(
                    watch_history_df
                )

                figures = {
                    'hourly': matplotlib_charts.create_hourly_chart(
                        hourly_counts
                    ),
                    'monthly': matplotlib_charts.create_monthly_chart(
                        monthly_counts
                    ),
                    'weekday': matplotlib_charts.create_weekday_chart(
                        weekday_counts
                    ),
                }

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
