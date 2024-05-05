import json
import os

import torch
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
import decord

FILE_PATH = "files"
app = FastAPI()

model_id = "IDEA-Research/grounding-dino-base"
device = "cuda"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)


class VideoMetadata(BaseModel):
    file: str
    metadata: dict


def get_video_from_path(video_name: str) -> VideoMetadata:
    file_path = os.path.join(FILE_PATH, video_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found.")

    processed_folder = video_name.split(".")[0]
    processed_video_path = os.path.join(FILE_PATH, processed_folder, video_name)
    json_file_path = os.path.join(
        FILE_PATH, processed_folder, f"{video_name.split('.')[0]}.json"
    )

    if os.path.exists(processed_video_path) and os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            json_data = json.load(json_file)

        return VideoMetadata(file=processed_video_path, metadata=json_data)
    else:
        raise HTTPException(
            status_code=404, detail="Processed video and metadata not found."
        )


@app.post("/drone_footage")
async def upload_drone_footage(file: UploadFile) -> VideoMetadata:
    if file.filename:
        if not file.filename.endswith(".mp4"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only MP4 files are allowed.",
            )
        return get_video_from_path(file.filename)
    else:
        raise HTTPException(status_code=400, detail="No file found")


@app.post("/grounding_dino")
async def run_grounding_dino(target_video: str, query: str):
    video = get_video_from_path(target_video)

    video_path = video.file

    video = decord.VideoReader(video_path)

    results = []

    for frame in video:
        image = Image.fromarray(frame.asnumpy())

        inputs = processor(images=image, text=query, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)

        frame_results = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=0.4,
            text_threshold=0.3,
            target_sizes=[image.size[::-1]]
        )

        results.append(frame_results)

    return results

