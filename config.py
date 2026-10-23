"""Central configuration for model choice and editable label normalization."""
import os

APP_TITLE = "WasteVision AI"
TAGLINE = "Smart waste intelligence platform"
MODEL_PROVIDER = os.getenv("WASTEVISION_MODEL_PROVIDER", "ultralytics")  # ultralytics | roboflow
MODEL_PATH = os.getenv("WASTEVISION_MODEL_PATH", "yolov8s-worldv2.pt")
YOLO_IMAGE_SIZE = int(os.getenv("WASTEVISION_YOLO_IMAGE_SIZE", "960"))
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "")
DB_PATH = os.getenv("WASTEVISION_DB", "wastevision.db")
UPLOAD_DIR = "uploads"
CLASS_MAPPING = {
    "plastic": "plastic", "bottle": "plastic", "plastic bottle": "plastic", "pet bottle": "plastic",
    "plastic bag": "plastic", "bag": "plastic", "wrapper": "plastic", "packaging": "plastic", "plastic wrapper": "plastic", "plastic cup": "plastic", "cup": "general",
    "paper": "paper", "cardboard": "paper", "cardboard box": "paper", "carton": "paper", "newspaper": "paper", "book": "paper", "paper cup": "paper",
    "metal": "metal", "can": "metal", "aluminum can": "metal", "aluminium can": "metal", "tin": "metal", "tin can": "metal", "metal can": "metal",
    "glass": "glass", "glass bottle": "glass", "wine glass": "glass", "jar": "glass",
    "organic": "organic", "food": "organic", "food waste": "organic", "banana": "organic", "banana peel": "organic", "apple": "organic", "orange": "organic", "broccoli": "organic", "carrot": "organic", "compost": "organic",
    "trash": "general", "garbage": "general", "waste": "general", "rubbish": "general", "litter": "general", "dumped waste": "general", "general": "general", "other": "general",
}
CATEGORIES = ["plastic", "paper", "metal", "glass", "organic", "general"]
WORLD_PROMPTS = {
    "plastic bottle": "plastic", "plastic bag": "plastic", "plastic wrapper": "plastic", "plastic cup": "plastic",
    "cardboard box": "paper", "newspaper": "paper", "paper cup": "paper",
    "metal can": "metal", "aluminum can": "metal",
    "glass bottle": "glass", "glass jar": "glass", "broken glass": "glass",
    "food scraps": "organic", "banana peel": "organic", "apple core": "organic", "food waste": "organic",
    "mixed trash pile": "general", "garbage bag": "general", "litter on ground": "general",
}
