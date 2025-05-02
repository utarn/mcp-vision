import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from transformers import pipeline, PretrainedConfig


DEFAULT_OBJDET_MODEL = "google/owlvit-base-patch32"

global models
models = {}


mcp = FastMCP("mcp-vision")


def load_hf_objdet_pipeline(model_name: str, device: str = "cpu"):
    start = time.time()
    objdet_model = pipeline(task="zero-shot-object-detection", model=model_name)
    print(f"Loaded zero-shot object detection pipline for {model_name} in {time.time() - start:.2f} seconds.")
    return {"model_name": model_name, "model": objdet_model}


def locate_object_bboxes(image_path: str, candidate_labels: list[str]) -> list[dict[str, Any]] | None:
    """
    Locate objects in image, output list of dictionaries using HF object detection format
    Example:
    [
        {'score': 0.997, 'label': 'bird', 'box': {'xmin': 69, 'ymin': 171, 'xmax': 396, 'ymax': 507}}, 
        {'score': 0.999, 'label': 'bird', 'box': {'xmin': 398, 'ymin': 105, 'xmax': 767, 'ymax': 507}}
    ]

    :param image_path: local path or URL to image
    :param candidate_labels: list of candidate object labels as strings
    """
    global models
    objdet_model = models["object_detection"]["model"]
    try:
        return objdet_model(image_path, candidate_labels=candidate_labels)
    except Exception as e:
        print(f"Error while calling model with image: {e}")
        return None


@mcp.tool()
def locate_objects(image_path: str, candidate_labels: list[str], hf_model: str | None = None) -> str:
    """Detect, find and/or locate objects in the image found at image_path.

    Args:
        image_path: path to the image
        candidate_labels: list of candidate object labels as strings
        hf_model (optional): huggingface zero-shot object detection model (default = "google/owlvit-base-patch32")
    """
    global models

    if hf_model is None:
        hf_model = DEFAULT_OBJDET_MODEL

    objdet_config = models.get("object_detection", None)
    if not objdet_config:
        print("First time loading an object detection model")
        objdet_config = load_hf_objdet_pipeline(model_name=hf_model)
        models["object_detection"] = objdet_config

    objdet_model_name = objdet_config.get("model_name", None)    
    objdet_model = objdet_config.get("model", None)

    if not objdet_model_name or not objdet_model or objdet_model_name != hf_model:
        print(f"No object detection model exists for {hf_model=} (existing {objdet_model_name=}), reloading")
        objdet_config = load_hf_objdet_pipeline(model_name=hf_model)
        models["object_detection"] = objdet_config

    bboxes = locate_object_bboxes(image_path, candidate_labels=candidate_labels)
    if not bboxes or len(bboxes) == 0:
        return f"No objects were located in the image."

    return f"{len(bboxes)} objects were found in the image at the following locations: {bboxes}."

