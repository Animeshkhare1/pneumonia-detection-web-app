"""
Pneumonia Detection from Chest X-ray - Flask backend
Educational prototype. Not a medical diagnosis.

Uses the ORIGINAL model (pneumonia_cnn.keras) and the ORIGINAL settings
in model_config.json. Nothing is re-trained or re-tuned here.
"""
import json
import os

from flask import Flask, request, jsonify, render_template

from xray_check import check_xray_like

# ---------------------------------------------------------------- settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'pneumonia_cnn.keras')
CONFIG_PATH = os.path.join(BASE_DIR, 'model_config.json')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_UPLOAD_MB = 10
NOTE = 'Model prediction from an educational prototype. Not a medical diagnosis.'

# ------------------------------------------------- load config + model ONCE
# If anything fails, we store a clear message in MODEL_ERROR. We never
# substitute another model and never fake a prediction.
tf = None
model = None
config = None
IMG_SIZE = THRESHOLD = CLASS_NAMES = None
MODEL_ERROR = None

try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    IMG_SIZE = config['img_size']            # 224
    THRESHOLD = config['threshold']          # 0.257
    CLASS_NAMES = config['class_names']      # ['NORMAL', 'PNEUMONIA']
except FileNotFoundError:
    MODEL_ERROR = 'model_config.json not found next to app.py.'
except (KeyError, json.JSONDecodeError) as e:
    MODEL_ERROR = f'model_config.json is invalid: {e!r}'

if MODEL_ERROR is None:
    try:
        import tensorflow as tf
    except ImportError:
        MODEL_ERROR = ('TensorFlow is not installed. '
                       'Run: pip install -r requirements.txt')

if MODEL_ERROR is None:
    if not os.path.exists(MODEL_PATH):
        MODEL_ERROR = 'pneumonia_cnn.keras not found next to app.py.'
    else:
        try:
            model = tf.keras.models.load_model(MODEL_PATH)   # no custom objects
            print('Model loaded:', MODEL_PATH)
        except Exception as e:  # show the REAL error, do not hide it
            MODEL_ERROR = f'Model failed to load: {type(e).__name__}: {e}'

if MODEL_ERROR:
    print('MODEL ERROR:', MODEL_ERROR)


# ------------------------------------------------------------- helper functions
def allowed_file(filename):
    """True if the file name ends with .jpg, .jpeg or .png."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def has_image_signature(data):
    """Check the first bytes of the file: real JPEG or PNG files start with these."""
    return data.startswith(b'\xff\xd8\xff') or data.startswith(b'\x89PNG\r\n\x1a\n')


def preprocess_image(file_bytes):
    """SAME steps as training: RGB, resize to 224x224, float32 0-255, add batch dim.
    No division by 255 - the model rescales internally."""
    image = tf.io.decode_image(file_bytes, channels=3, expand_animations=False)
    image = tf.image.resize(image, (IMG_SIZE, IMG_SIZE))
    return tf.expand_dims(image, axis=0)             # shape (1, 224, 224, 3)


def decide_label(score):
    """Threshold rule from model_config.json: score >= threshold -> PNEUMONIA."""
    return CLASS_NAMES[1] if score >= THRESHOLD else CLASS_NAMES[0]


def predict_bytes(file_bytes):
    """Image bytes -> (label, score). Score is the model output for PNEUMONIA."""
    score = float(model.predict(preprocess_image(file_bytes), verbose=0)[0][0])
    return decide_label(score), score


# ------------------------------------------------------------------- Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024


@app.route('/')
def index():
    return render_template('index.html', model_error=MODEL_ERROR,
                           threshold=THRESHOLD, max_mb=MAX_UPLOAD_MB)


@app.route('/predict', methods=['POST'])
def predict():
    # 1. Was a file sent?
    if 'file' not in request.files:
        return jsonify({'error': 'no file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected. Please choose a chest X-ray image.'}), 400

    # 2. Is it a JPG/PNG? (extension, then real file content)
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a JPG, JPEG or PNG image.'}), 400
    file_bytes = file.read()          # kept in memory only - never saved to disk
    if not file_bytes:
        return jsonify({'error': 'The uploaded file is empty.'}), 400
    if not has_image_signature(file_bytes):
        return jsonify({'error': 'The file content is not a valid JPG or PNG image.'}), 400

    # 3. Does it look like a chest X-ray? (simple check, rejects colour photos/screenshots)
    looks_ok, message, _ = check_xray_like(file_bytes)
    if not looks_ok:
        if not message.startswith('The image could not be read'):
            return jsonify({'code': 'not_xray', 'error': 'No X-ray image detected.',
                            'reason': message}), 422
        return jsonify({'error': message}), 400

    # 4. Is the model available?
    if MODEL_ERROR:
        return jsonify({'error': 'Model is not available. ' + MODEL_ERROR}), 503

    # 5. Decode + preprocess + predict
    try:
        batch = preprocess_image(file_bytes)
    except Exception:
        return jsonify({'error': 'The image could not be read. It may be corrupted.'}), 400
    try:
        score = float(model.predict(batch, verbose=0)[0][0])
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {type(e).__name__}'}), 500

    return jsonify({
        'model_prediction': decide_label(score),
        'pneumonia_score': round(score, 4),
        'threshold': THRESHOLD,
        'note': NOTE
    })


@app.errorhandler(413)
def file_too_large(_):
    return jsonify({'error': f'File too large. Maximum size is {MAX_UPLOAD_MB} MB.'}), 413


if __name__ == '__main__':
    # debug=False so the model is loaded only once (debug mode starts the app twice).
    app.run(debug=False)
