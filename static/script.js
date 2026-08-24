const uploadArea = document.querySelector('.upload-area');
const fileInput = document.querySelector('#tiktok-export');
const selectedFile = document.querySelector('#selected-file');
const selectedFileName = document.querySelector('#selected-file-name');
const fileError = document.querySelector('#file-error');

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
