"""Run on YOUR machine to see how the X-ray check treats your own images.
    python check_inputs.py C:\\path\\to\\folder_with_images
Prints PASS/REJECT and the measured numbers for every JPG/PNG in the folder
(subfolders included). Use it on real X-rays (all should PASS) and on a few
screenshots/photos (should REJECT)."""
import os
import sys
import xray_check as X

root = sys.argv[1] if len(sys.argv) > 1 else '.'
total = rejected = 0
for folder, _, files in os.walk(root):
    for name in files:
        if name.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(folder, name)
            with open(path, 'rb') as f:
                ok, msg, m = X.check_xray_like(f.read())
            total += 1
            rejected += (not ok)
            if not ok:
                print('REJECT', path, {k: round(v, 3) for k, v in m.items()})
print(f'{total} images checked, {rejected} rejected')
