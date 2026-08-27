import os

from flask import Flask, render_template
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired

from dotenv import load_dotenv

from wtforms import SubmitField

from services import dashboard_service, file_services


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
    dashboard = None

    if form.validate_on_submit():
        uploaded_file = form.uploaded_file.data
        is_valid, error_message = file_services.validate_zip_archive(
            uploaded_file
        )

        if not is_valid:
            form.uploaded_file.errors.append(error_message)
        else:
            is_valid, error_message, dashboard = (
                dashboard_service.process_tiktok_upload(uploaded_file)
            )

            if not is_valid:
                form.uploaded_file.errors.append(error_message)

    return render_template(
        'index.html',
        form=form,
        statistics=(dashboard['statistics'] if dashboard else None),
        charts=(dashboard['charts'] if dashboard else None),
        login_statistics=(
            dashboard['login_statistics'] if dashboard else None
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
