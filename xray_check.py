"""
Simple input check: does the uploaded image look like a chest X-ray?

This is a HEURISTIC (plain image statistics, no machine learning). It does not
change the model, the threshold or the model's preprocessing. It only rejects
images that are clearly not X-rays, such as colour photos and screenshots.

Chest X-rays are essentially grayscale and are not mostly white page.
"""
import io

import numpy as np
from PIL import Image

CHECK_SIZE = 256            # image is shrunk to 256x256 only for this check
COLOR_CHROMA = 20           # a pixel counts as "coloured" if max(R,G,B) - min(R,G,B) > 20
MAX_COLOR_FRACTION = 0.05   # reject if more than 5% of pixels are coloured
WHITE_LEVEL = 245           # a pixel counts as "white page" if its brightness >= 245
MAX_WHITE_FRACTION = 0.40   # reject if more than 40% of pixels are white page
BLACK_LEVEL = 15            # a pixel counts as "black" if its brightness <= 15
MAX_BLACK_FRACTION = 0.60   # reject if more than 60% of pixels are black (e.g. dark screenshot)


def measure(file_bytes):
    """Return the two numbers used by the check."""
    img = Image.open(io.BytesIO(file_bytes)).convert('RGB').resize((CHECK_SIZE, CHECK_SIZE))
    pixels = np.asarray(img, dtype=np.int16)
    chroma = pixels.max(axis=2) - pixels.min(axis=2)    # 0 for pure gray pixels
    brightness = pixels.mean(axis=2)
    return {
        'color_fraction': float((chroma > COLOR_CHROMA).mean()),
        'white_fraction': float((brightness >= WHITE_LEVEL).mean()),
        'black_fraction': float((brightness <= BLACK_LEVEL).mean()),
    }


def check_xray_like(file_bytes):
    """Return (ok, message, numbers). ok=False means 'does not look like a chest X-ray'."""
    try:
        m = measure(file_bytes)
    except Exception:
        return False, 'The image could not be read. It may be corrupted.', {}
    if m['color_fraction'] > MAX_COLOR_FRACTION:
        return False, 'The image is in colour (like a photo, selfie or screenshot). Chest X-rays are grayscale.', m
    if m['white_fraction'] > MAX_WHITE_FRACTION:
        return False, 'The image has a large white background (like a document or screenshot).', m
    if m['black_fraction'] > MAX_BLACK_FRACTION:
        return False, 'The image is mostly black (like a dark screenshot).', m
    return True, '', m
