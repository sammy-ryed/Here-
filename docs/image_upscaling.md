Image Upscaling and Resizing — How it works in this project
=============================================================

This document explains exactly how and where images and face regions are resized/upscaled in the project, what modules are used, and which parameters control the behavior. Use this when preparing your presentation or when changing/updating image-processing behavior.

Contents
--------
- Summary (quick)
- Code locations
- Detailed explanation (step-by-step)
- Parameters & thresholds
- Examples
- Notes, discrepancies, and recommendations

Summary (quick)
----------------
- The project performs two main kinds of resizing:
  1. Image downscaling in `preprocess_image()` to limit very large input images (to 640x480 by default).
  2. Smart face-level upscaling in `FaceRecognizer.get_embedding()` for small face crops (to ensure face regions are effectively at or above 224px in their smaller dimension).
- Upscaling for faces uses OpenCV `cv2.resize(..., interpolation=cv2.INTER_CUBIC)` followed by `cv2.fastNlMeansDenoisingColored()` for denoising (only for upscaled/small faces).
- DeepFace embedding extraction is then run on the upscaled face image with `enforce_detection=False`, `detector_backend='skip'`, and `align=False` to avoid redundant detection/alignment overhead.

Code locations
--------------
- `python_backend/utils/face_recognizer.py`
  - Function: `FaceRecognizer.get_embedding()`
  - Lines: the smart upscaling branch starts near where face width/height are measured (face_w/face_h checks; look for condition `if face_w < 112 or face_h < 112`).

- `python_backend/utils/image_utils.py`
  - Function: `preprocess_image(image_path, target_size=(640,480))`
  - Purpose: downscale images larger than target_size to reduce processing time (uses `cv2.INTER_AREA`).

- `java_app/src/main/java/com/attendance/util/CameraCapture.java`
  - UI capture preview uses `ImageView.fitWidth=640` and `fitHeight=480` for display. The saved frame is the original capture written with `Imgcodecs.imwrite()` (no forced resize before saving in that class).

Detailed explanation (step-by-step)
-----------------------------------
1. Input image arrives (either captured via camera or uploaded):
   - `CameraCapture.capturePhoto()` saves captured frames using OpenCV (`Imgcodecs.imwrite`). The JavaFX `ImageView` uses fitWidth/fitHeight for display only.
   - Uploaded images processed by `preprocess_image()` will be downscaled if larger than `(640,480)` using `cv2.INTER_AREA` (which is good for downscaling).

2. Face detection (varies by flow):
   - In some flows RetinaFace detects faces in the backend; in live recognition, Java/OpenCV Haar cascade may detect faces in the frontend.
   - Once a face bbox is available, the backend crops the face region.

3. Smart face upscaling (in `FaceRecognizer.get_embedding()`):
   - Compute `face_w` and `face_h` from the bbox.
   - If either dimension is less than `112` px, the code upscales the face:
     - Compute `scale = max(224 / face_w, 224 / face_h)` so the smaller side becomes at least 224 px.
     - Compute `new_w = int(face_w * scale)` and `new_h = int(face_h * scale)`.
     - Perform `cv2.resize(face_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)`.
     - Apply `cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)` to denoise the upscaled face (improves embedding quality).
   - For faces >= 112 px on both sides, the code skips enhancements (fast path).

4. Embedding extraction and speed optimizations:
   - The upscaled face is saved to a temporary JPEG file (per-thread unique name) and passed to `DeepFace.represent()` with the following options:
     - `enforce_detection=False` (we already have the cropped face)
     - `detector_backend='skip'` (skip face detection inside DeepFace)
     - `align=False` (skip alignment — saves time in live flows)
   - Embeddings are normalized (L2 norm) and cached in memory using a hash of the input and bbox.

Parameters & thresholds
-----------------------
- Small-face detection threshold: `112` px (if face width OR height is below this, upscaling triggers).
- Upscale target: `224` px on the smaller dimension (scale = max(224/face_w, 224/face_h)).
- Upscale interpolation: `cv2.INTER_CUBIC`.
- Denoising for upscaled faces: `cv2.fastNlMeansDenoisingColored` with parameters `(None, 10, 10, 7, 21)`.
- Global preprocess image max size: `target_size=(640,480)` using `cv2.INTER_AREA` (downscale only).

Why these choices?
-------------------
- A face smaller than ~112 px often gives poor embeddings; ensuring at least ~224 px on the smaller side improves embedding stability.
- `INTER_CUBIC` balances quality and speed for upscaling (higher quality than `INTER_LINEAR`, lower computational cost than some advanced super-resolution models).
- Denoising after upscaling reduces artifacts that could confuse the embedding model.
- Skipping internal detection/alignment in DeepFace avoids duplicate work and saves significant time in live or pre-cropped workflows.

Examples (quick math)
---------------------
- Example 1: face_w=80, face_h=60
  - scale = max(224/80=2.8, 224/60≈3.733) → scale ≈ 3.733
  - new_w ≈ int(80 * 3.733) = 298
  - new_h ≈ int(60 * 3.733) = 223
  - The smaller side (new_h) is ≈223 → close to target 224 (integer rounding applies)

- Example 2: face_w=100, face_h=140
  - face_w < 112 triggers upscale
  - scale = max(224/100=2.24, 224/140≈1.6) → scale = 2.24
  - new_w = 224, new_h = int(140 * 2.24) = 313

Notes, discrepancies & recommendations
--------------------------------------
- README references an "image-wide" auto-upscale (e.g., 2x for images >800px) and constants like `AUTO_UPSCALE_THRESHOLD=800` and `UPSCALE_FACTOR=2.0`. I did not find code that implements a global upscale of images beyond the face-level upscaling and the downscale to `(640,480)` in `preprocess_image()`.
  - Recommendation: remove stale README notes or implement the documented global behavior in `image_utils.py` if desired.

- Interpolation choices:
  - `INTER_CUBIC` is a good default for upscaling. If you need even better visual quality (at a performance cost), `INTER_LANCZOS4` is slightly better but slower.

- Super-resolution option:
  - If you must extract embeddings from very tiny faces (e.g., 32px), consider integrating a lightweight super-resolution model (Real-ESRGAN or a small EDSR variant). That will increase accuracy but add complexity and runtime cost (likely GPU required for decent speed).

- Caching and temporary files:
  - Embeddings are cached by a face-hash to avoid repeated DeepFace calls. The temporary face image is removed after embedding extraction.

Want changes or additions?
--------------------------
I can do any of the following now (pick one or more):
- Implement the README-described global 2x upscale for images > 800px inside `image_utils.py`.
- Add a configuration-driven control (constants in a config file) for the thresholds (112, 224, 640x480), so you can tweak at runtime without editing code.
- Replace `INTER_CUBIC` with `INTER_LANCZOS4` (optionally configurable) and measure performance.
- Implement a lightweight super-resolution path (Real-ESRGAN integration) for tiny faces — I can add an opt-in pipeline branch.

If you want, I will also add this markdown file to `docs/` (already saved) and link to code lines for quick reference in your presentation.
