import time
from typing import Any

from mcp.server.fastmcp import FastMCP
from transformers import pipeline


DEFAULT_OBJDET_MODEL = "google/owlvit-base-patch32"

global objdet_model
objdet_model = None

mcp = FastMCP("mcp-vision")


# TODO: cache instead of using global
def load_hf_objdet_pipeline(model_name: str, device: str = "cpu"):
    global objdet_model
    start = time.time()
    objdet_model = pipeline(task="zero-shot-object-detection", model=model_name)
    print(f"Loaded zero-shot object detection pipline for {model_name} in {time.time() - start:.2f} seconds.")
    return objdet_model


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
    global objdet_model 
    try:
        return objdet_model(image_path, candidate_labels=candidate_labels)
    except Exception as e:
        print(f"Error while calling model with image: {e}")
        return None


# TODO: cache instead of using global, add filtering by object name?
@mcp.tool()
def locate_objects(image_path: str, candidate_labels: list[str], hf_model: str | None = None) -> str:
    """Detect, find and/or locate objects in the image found at image_path.

    Args:
        image_path: path to the image
        candidate_labels: list of candidate object labels as strings
        hf_model (optional): huggingface zero-shot object detection model (default = "google/owlvit-base-patch32")
    """
    global objdet_model

    if objdet_model is None:
        if hf_model is None:
            hf_model = DEFAULT_OBJDET_MODEL
        objdet_model = load_hf_objdet_pipeline(model_name=hf_model)

    bboxes = locate_object_bboxes(image_path, candidate_labels=candidate_labels)
    if not bboxes or len(bboxes) == 0:
        return f"No objects were located in the image."

    return f"{len(bboxes)} objects were found in the image at the following locations: {bboxes}."

