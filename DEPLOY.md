# Deployment notes

## Important: TensorFlow and Vercel
Vercel Python functions have a size limit (250 MB standard; larger bundles only on its "large function" /
Fluid Compute option, depending on plan). A TensorFlow install is over 1 GB (Vercel's own troubleshooting
guide shows a TensorFlow bundle of about 2 GB), so `pip install tensorflow` will normally FAIL on a standard
Vercel build. The model file itself (22 MB) is not the problem; the TensorFlow library is.

Options:
1. Host the unchanged project where TensorFlow fits (Hugging Face Spaces with Docker, Render, a VM).
2. Stay on Vercel: convert the model to a small format (TFLite / ONNX) and run it with a light runtime.
   This changes the inference code, so predictions must be compared against the original `.keras` model
   on the same images before using it.
3. Try Vercel's large-function option (check your plan first).

## Push to GitHub (needed for any host)
```
git init
git add .
git commit -m "Pneumonia detection website"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```
The model (22 MB) is under GitHub's 100 MB file limit.
