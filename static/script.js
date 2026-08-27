const uploadArea = document.querySelector('.upload-area');
const uploadForm = document.querySelector('.upload-form');
const fileInput = document.querySelector('#tiktok-export');
const submitButton = document.querySelector('#upload-submit');
const loadingState = document.querySelector('#upload-loading');
const selectedFile = document.querySelector('#selected-file');
const selectedFileName = document.querySelector('#selected-file-name');
const fileError = document.querySelector('#file-error');
let isSubmitting = false;

const dashboardResults = document.querySelector('[data-refresh-url]');
if (dashboardResults) {
    window.history.replaceState(null, '', dashboardResults.dataset.refreshUrl);
}

function isZipFile(file) {
    return file.name.toLowerCase().endsWith('.zip');
}

function showSelectedFile(file) {
    selectedFileName.textContent = file.name;
    selectedFile.hidden = false;
    fileError.textContent = '';
    fileError.hidden = true;
}

function showFileError(message) {
    fileInput.value = '';
    selectedFileName.textContent = 'None';
    selectedFile.hidden = false;
    fileError.textContent = message;
    fileError.hidden = false;
}

if (fileInput && uploadArea && uploadForm && submitButton && loadingState) {
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];

        if (!file) {
            selectedFileName.textContent = 'None';
            selectedFile.hidden = false;
            return;
        }

        if (!isZipFile(file)) {
            showFileError('Please select a ZIP file.');
            return;
        }

        showSelectedFile(file);
    });

    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();

        const files = event.dataTransfer.files;

        if (files.length !== 1) {
            showFileError('Please drop one ZIP file at a time.');
            return;
        }

        const file = files[0];

        if (!isZipFile(file)) {
            showFileError('Please select a ZIP file.');
            return;
        }

        fileInput.files = files;
        showSelectedFile(file);
    });

    uploadForm.addEventListener('submit', (event) => {
        if (isSubmitting) {
            event.preventDefault();
            return;
        }

        const file = fileInput.files[0];

        if (!file) {
            event.preventDefault();
            showFileError('Please select a ZIP file.');
            return;
        }

        if (!isZipFile(file)) {
            event.preventDefault();
            showFileError('Please select a ZIP file.');
            return;
        }

        isSubmitting = true;
        submitButton.disabled = true;
        uploadArea.classList.add('is-processing');
        uploadArea.setAttribute('aria-disabled', 'true');
        loadingState.hidden = false;
    });
}
