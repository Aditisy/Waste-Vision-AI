"""Pluggable detector adapter: Ultralytics YOLO by default; Roboflow optional."""
import streamlit as st
from config import MODEL_PATH, MODEL_PROVIDER, ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, YOLO_IMAGE_SIZE, CLASS_MAPPING, WORLD_PROMPTS

def _iou(box_a, box_b):
    x1=max(box_a[0],box_b[0]); y1=max(box_a[1],box_b[1])
    x2=min(box_a[2],box_b[2]); y2=min(box_a[3],box_b[3])
    intersection=max(0,x2-x1)*max(0,y2-y1)
    area_a=max(0,box_a[2]-box_a[0])*max(0,box_a[3]-box_a[1])
    area_b=max(0,box_b[2]-box_b[0])*max(0,box_b[3]-box_b[1])
    return intersection/max(area_a+area_b-intersection,1)

@st.cache_resource
def load_model(provider=MODEL_PROVIDER, model_path=MODEL_PATH):
    if provider == "ultralytics":
        from ultralytics import YOLO
        model = YOLO(model_path)
        # Ultralytics routes *-world.pt files to its open-vocabulary detector.
        # The prompts focus inference on waste instead of the generic COCO list.
        if hasattr(model, "set_classes") and "-world" in model_path.lower():
            model.set_classes(list(WORLD_PROMPTS))
        return model
    if provider == "roboflow":
        if not ROBOFLOW_API_KEY or not ROBOFLOW_MODEL_ID:
            raise RuntimeError("Set ROBOFLOW_API_KEY and ROBOFLOW_MODEL_ID to use Roboflow.")
        from inference_sdk import InferenceHTTPClient
        return InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=ROBOFLOW_API_KEY)
    raise ValueError(f"Unknown model provider: {provider}")

def detect(image, confidence=0.20):
    """Return only recognized waste classes as (annotated image, detections).

    Unknown detector classes are discarded instead of being mislabeled as waste.
    Add valid waste-model labels to CLASS_MAPPING in config.py to enable them.
    """
    import numpy as np
    from PIL import ImageDraw
    model = load_model()
    rgb = image.convert("RGB")
    if MODEL_PROVIDER == "roboflow":
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            rgb.save(f.name); temp_path = f.name
        try: result = model.infer(temp_path, model_id=ROBOFLOW_MODEL_ID)[0]
        finally: os.unlink(temp_path)
        predictions = [{"name": p["class"], "confidence": p["confidence"], "box": [p["x"]-p["width"]/2,p["y"]-p["height"]/2,p["x"]+p["width"]/2,p["y"]+p["height"]/2]} for p in result.get("predictions", [])]
    else:
        # Larger images and test-time augmentation help with small/irregular litter.
        # Keep the model's candidate threshold low, then apply the user's slider below.
        result = model.predict(np.array(rgb), conf=0.05, imgsz=YOLO_IMAGE_SIZE, augment=True, verbose=False)[0]
        predictions = []
        for box in result.boxes:
            cls = int(box.cls[0]); name = str(result.names[cls])
            predictions.append({"name": name, "confidence": float(box.conf[0]), "box": box.xyxy[0].tolist()})
    candidates = []
    for p in predictions:
        score = float(p["confidence"])
        if score < confidence: continue
        raw = " ".join(p["name"].strip().lower().replace("_", " ").replace("-", " ").split())
        category = WORLD_PROMPTS.get(raw) or CLASS_MAPPING.get(raw)
        if category is None:
            # Model background classes (person, car, furniture, etc.) are not waste.
            continue
        coords = tuple(int(v) for v in p["box"])
        candidates.append({"label":raw,"category":category,"confidence":score,"box":coords})

    # YOLO-World can describe one object with multiple nearby prompts. Suppress
    # highly overlapping boxes so reports do not over-count the same item.
    detections=[]
    for candidate in sorted(candidates,key=lambda item:item["confidence"],reverse=True):
        duplicate=False
        for kept in detections:
            overlap=_iou(candidate["box"],kept["box"])
            if overlap >= (0.72 if candidate["category"]==kept["category"] else 0.88):
                duplicate=True
                break
        if not duplicate: detections.append(candidate)

    draw = ImageDraw.Draw(rgb)
    for item in detections:
        coords=item["box"]; category=item["category"]; score=item["confidence"]
        draw.rectangle(coords, outline="#18a558", width=4)
        draw.text((coords[0]+3, max(0,coords[1]-18)), f"{category} {score:.0%}", fill="white", stroke_width=2, stroke_fill="#174b32")
    return rgb, detections
