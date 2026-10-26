# Pneumonia Detection from Chest X-ray (Flask website)

B.Tech Deep Learning Lab ESE project. MobileNetV2 transfer-learning model (original `pneumonia_cnn.keras`).
**Educational prototype. Not a medical diagnosis. Consult a qualified doctor.**

## Folder structure
```
pneumonia_website/
├── app.py                  <- Flask backend (loads model once, /predict route)
├── pneumonia_cnn.keras     <- ORIGINAL model (same folder as app.py)
├── model_config.json       <- ORIGINAL config: threshold 0.257, img_size 224 (same folder as app.py)
├── requirements.txt
├── xray_check.py           <- simple check that rejects obvious non-X-ray images
├── check_inputs.py         <- run on a folder of images to see which pass/reject
├── test_local.py           <- checks model loading / one real prediction on your PC
├── DEPLOY.md               <- deployment notes (read before Vercel)
├── README.md
├── templates/
│   └── index.html          <- the web page
└── static/
    ├── style.css           <- styling
    └── script.js           <- preview, upload, result display
```

## Run on Windows (step by step)
1. Install **Python 3.10, 3.11 or 3.12 (64-bit)** from python.org. Tick "Add Python to PATH".
2. Open Command Prompt and go to the project folder:
   `cd C:\path\to\pneumonia_website`
3. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies (TensorFlow is large, this can take a few minutes):
   `pip install -r requirements.txt`
5. Check the model loads (optional but recommended):
   `python test_local.py`
   and with a real image: `python test_local.py C:\path\to\xray.jpg`
6. Start the website: `python app.py`
7. Open **http://127.0.0.1:5000** in your browser. Stop with Ctrl + C.

## Troubleshooting
- Red "Model not available" banner: it shows the real error. `TensorFlow is not installed` -> redo step 4 inside the activated venv.
- Model load error mentioning Keras version / deserialization: the model was saved with Keras 3.13.2. Run `pip install --upgrade keras tensorflow` and try again.
- `pneumonia_cnn.keras not found`: the file must sit next to `app.py`.

## Model contract (from the original files)
Input (1, 224, 224, 3) RGB float32 0-255 (no /255, rescaling is inside the model) -> one sigmoid score for PNEUMONIA.
NORMAL = 0, PNEUMONIA = 1. Score >= 0.257 -> PNEUMONIA, else NORMAL. The score is a model output, not a calibrated probability.

## How it works (viva summary)
1. Browser: user picks a JPG/PNG; JavaScript checks type/size and shows a preview.
2. Predict click: JavaScript sends the file with `fetch` (POST, form field `file`) to `/predict`.
3. Flask `/predict`: checks file present, extension, real JPEG/PNG signature, then `xray_check.py`, then model available. The image stays in memory, never saved.
   `xray_check.py` is a heuristic (no ML): chest X-rays are grayscale, so it rejects images with more than 5% coloured pixels, more than 40% white-page pixels, or more than 60% black pixels. It does NOT change the model or its preprocessing. It is a basic filter, not a guarantee: a grayscale non-X-ray photo can still pass.
   Thresholds are constants at the top of `xray_check.py`. Run `python check_inputs.py <folder>` on your real X-rays to confirm none are rejected.
4. Preprocessing: `tf.io.decode_image` (RGB) -> `tf.image.resize` to 224x224 -> add batch dimension. No normalisation.
5. Prediction: `model.predict` returns one sigmoid score for PNEUMONIA.
6. Threshold: `score >= 0.257` -> PNEUMONIA, else NORMAL (value read from `model_config.json`).
7. Flask returns JSON; JavaScript shows the prediction, score, threshold and a score bar.
