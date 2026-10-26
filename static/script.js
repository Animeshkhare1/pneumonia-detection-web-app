// Frontend logic: choose file -> preview -> send to /predict -> show result.
const MAX_MB = 10;
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const previewBox = document.getElementById('preview-box');
const preview = document.getElementById('preview');
const fileNameEl = document.getElementById('file-name');
const errorBox = document.getElementById('error');
const predictBtn = document.getElementById('predict-btn');
const resetBtn = document.getElementById('reset-btn');
const resultCard = document.getElementById('result-card');

let selectedFile = null;

// The result box shows one state at a time: idle | loading | result | noxray
function setState(state) { resultCard.dataset.state = state; }
function showError(msg) { errorBox.textContent = msg; errorBox.classList.remove('hidden'); }
function clearError() { errorBox.classList.add('hidden'); errorBox.textContent = ''; }

function handleFile(file) {
  clearError();
  setState('idle');
  if (!file) return;
  if (!/\.(jpe?g|png)$/i.test(file.name)) { showError('Invalid file type. Please upload a JPG, JPEG or PNG image.'); return; }
  if (file.size > MAX_MB * 1024 * 1024) { showError('File too large. Maximum size is ' + MAX_MB + ' MB.'); return; }
  selectedFile = file;
  if (preview.src) URL.revokeObjectURL(preview.src);
  preview.src = URL.createObjectURL(file);
  fileNameEl.textContent = file.name;
  previewBox.classList.remove('hidden');
  predictBtn.disabled = false;
  resetBtn.classList.remove('hidden');
}

fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));
['dragenter', 'dragover'].forEach(ev => dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('dragover'); }));
['dragleave', 'drop'].forEach(ev => dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('dragover'); }));
dropzone.addEventListener('drop', e => handleFile(e.dataTransfer.files[0]));

predictBtn.addEventListener('click', async () => {
  if (!selectedFile) { showError('Please choose an image first.'); return; }
  clearError();
  predictBtn.disabled = true;
  setState('loading');

  const formData = new FormData();
  formData.append('file', selectedFile);          // field name must be "file"

  try {
    const response = await fetch('/predict', { method: 'POST', body: formData });
    let data;
    try { data = await response.json(); } catch { throw new Error('Unexpected response from the server.'); }

    if (data.code === 'not_xray') {                // not a chest X-ray -> no prediction
      document.getElementById('noxray-reason').textContent = data.reason;
      setState('noxray');
    } else if (!response.ok) {
      throw new Error(data.error || 'Something went wrong.');
    } else {
      showResult(data);
    }
  } catch (err) {
    setState('idle');
    showError(err.message || 'Could not reach the server.');
  } finally {
    predictBtn.disabled = false;
  }
});

function showResult(data) {
  const isPneumonia = data.model_prediction === 'PNEUMONIA';
  const badge = document.getElementById('result-badge');
  badge.textContent = data.model_prediction;
  badge.className = 'badge ' + data.model_prediction.toLowerCase();
  document.getElementById('score-value').textContent = data.pneumonia_score.toFixed(4);
  document.getElementById('threshold-value').textContent = data.threshold;
  document.getElementById('rule-text').textContent =
    data.pneumonia_score.toFixed(4) + (isPneumonia ? ' \u2265 ' : ' < ') + data.threshold +
    '  \u2192  ' + data.model_prediction;
  document.getElementById('bar-fill').style.width = (Math.min(Math.max(data.pneumonia_score, 0), 1) * 100) + '%';
  document.getElementById('bar-threshold').style.left = 'calc(' + (data.threshold * 100) + '% - 1px)';
  setState('result');
}

resetBtn.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  if (preview.src) URL.revokeObjectURL(preview.src);
  preview.removeAttribute('src');
  previewBox.classList.add('hidden');
  resetBtn.classList.add('hidden');
  predictBtn.disabled = true;
  clearError();
  setState('idle');
});
