"""Run on YOUR machine (where TensorFlow is installed):
    python test_local.py                      -> checks the model loads
    python test_local.py path\\to\\xray.jpg    -> also runs a real prediction
"""
import sys
import app

if app.MODEL_ERROR:
    print('FAIL - model not available:', app.MODEL_ERROR)
    sys.exit(1)
print('OK - model loaded. Input shape:', app.model.input_shape, ' Output shape:', app.model.output_shape)
print('Threshold from config:', app.THRESHOLD, ' Classes:', app.CLASS_NAMES)

if len(sys.argv) > 1:
    with open(sys.argv[1], 'rb') as f:
        label, score = app.predict_bytes(f.read())
    print(f'Prediction: {label}   score: {score:.4f}')
