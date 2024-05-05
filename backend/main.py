import json
import logging
import os

import cv2
import decord
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from GroundingDINO.groundingdino.util.inference import (
    annotate,
    load_image,
    load_model,
    predict,
)
from PIL import Image
from pydantic import BaseModel

FILE_PATH = "files"
app = FastAPI()
logging.basicConfig(level=logging.INFO)

logging.info("Loading grounding-dino")
try:
    model = load_model(
        "groundingdino/config/GroundingDINO_SwinT_OGC.py",
        "weights/groundingdino_swint_ogc.pth",
    )
except Exception as e:
    logging.error(f"Failed to load model: {e}")
    raise


class VideoMetadata(BaseModel):
    file: str
    metadata: dict


def get_video_from_path(video_name: str) -> VideoMetadata:
    base_name = video_name.split(".")[0]
    file_path = os.path.join(FILE_PATH, base_name, video_name)
    json_file_path = os.path.join(FILE_PATH, base_name, f"{base_name}.json")

    if not os.path.exists(file_path) or not os.path.exists(json_file_path):
        raise HTTPException(status_code=404, detail="Video file or metadata not found.")

    with open(json_file_path, "r") as json_file:
        json_data = json.load(json_file)

    return VideoMetadata(file=file_path, metadata=json_data)


@app.post("/drone_footage")
async def upload_drone_footage(file: UploadFile) -> VideoMetadata:
    logging.info(f"Received drone footage upload request: {file.filename}")
    if file.filename:
        if not file.filename.endswith(".mp4"):
            logging.warning("Invalid file format attempted to be uploaded.")
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only MP4 files are allowed.",
            )
        video = get_video_from_path(file.filename)
        logging.info(f"Processed video for file: {file.filename}")
        return video
    else:
        logging.error("No file found in the request.")
        raise HTTPException(status_code=400, detail="No file found")


@app.post("/grounding_dino")
async def run_grounding_dino(target_video: str, query: str):
    video = get_video_from_path(target_video)
    video_path = video.file
    logging.info(f"Running Grounding Dino on video path: {video_path}")

    vr = decord.VideoReader(video_path)
    frames = vr.get_batch(range(0, len(vr), 10)).asnumpy()  # Extract every 10th frame

    results = []
    for frame in frames:
        image = Image.fromarray(frame)
        image_source, processed_image = load_image(
            image
        )

        boxes, logits, phrases = predict(
            model=model,
            image=processed_image,
            caption=query,
            box_threshold=0.35,
            text_threshold=0.25,
        )

        annotated_frame = annotate(
            image_source=image_source, boxes=boxes, logits=logits, phrases=phrases
        )
        results.append(annotated_frame)

    return results


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
