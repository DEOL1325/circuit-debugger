import base64
import io
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError

from .circuit import Circuit, check

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.environ.get("CIRCUIT_MODEL_PATH", str(ROOT / "models/best.pt")))
app = FastAPI(title="Circuit Debugger", version="0.1.0")
_model = None


@app.get("/api/health")
def health():
    import importlib.util
    return {"ok": True, "vision_ready": MODEL_PATH.is_file() and importlib.util.find_spec("ultralytics") is not None,
            "version": "0.1.0", "supported_circuit": "series_led"}


@app.post("/api/check")
def check_circuit(circuit: Circuit):
    return check(circuit)


class ImageRequest(BaseModel):
    image: str = Field(max_length=11_200_000)


@app.post("/api/detect")
def detect(payload: ImageRequest):
    """Optional pose model: returns proposals, never silently assigns hole numbers."""
    global _model
    if not MODEL_PATH.is_file():
        raise HTTPException(503, "No trained vision model is installed. Mark and confirm connections manually, or train the Colab notebook first.")
    try:
        from ultralytics import YOLO
    except ImportError:
        raise HTTPException(503, "Install the optional ultralytics package to enable the trained vision model.")
    try:
        encoded = payload.image.split(",", 1)[-1]
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > 8 * 1024 * 1024:
            raise HTTPException(413, "Please use an image smaller than 8 MB.")
        with Image.open(io.BytesIO(raw)) as source:
            if source.width * source.height > 20_000_000:
                raise HTTPException(413, "Please use an image smaller than 20 megapixels.")
            image = ImageOps.exif_transpose(source).convert("RGB")
    except HTTPException:
        raise
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(422, "Upload a valid JPEG, PNG, or WebP image.")
    if _model is None:
        _model = YOLO(str(MODEL_PATH))
    result = _model.predict(image, conf=0.35, verbose=False)[0]
    proposals = []
    for i, box in enumerate(result.boxes):
        item = {"kind": result.names[int(box.cls[0])], "confidence": float(box.conf[0]),
                "box": box.xyxyn[0].tolist(), "keypoints": []}
        if result.keypoints is not None:
            points = result.keypoints.xyn[i].tolist()
            scores = result.keypoints.conf[i].tolist() if result.keypoints.conf is not None else [1] * len(points)
            item["keypoints"] = [dict(x=p[0], y=p[1], confidence=s) for p, s in zip(points, scores)]
        proposals.append(item)
    return {"proposals": proposals, "basis": "Model proposals only. Confirm component identity, LED polarity, and breadboard hole numbers before checking."}


DIST = ROOT / "frontend/dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
