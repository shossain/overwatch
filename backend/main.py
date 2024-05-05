import json
import logging
import os
from typing import List

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from GroundingDINO.groundingdino.util.inference import (
    annotate,
    load_image_from_path,
    predict,
)
from PIL import Image
from pydantic import BaseModel
from tqdm import tqdm

FILE_PATH = "files"


app = FastAPI()
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO)

logging.info("Loading grounding-dino")
# try:
#     model = load_model(
#         "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py",
#         "GroundingDINO/weights/groundingdino_swint_ogc.pth",
#     ).to("cuda")
# except Exception as e:
#     logging.error(f"Failed to load model: {e}")
#     raise


@app.get("/video/{video_name}")
async def get_video(video_name: str) -> StreamingResponse:
    base_name = video_name.split(".")[0]
    video_file_path = os.path.join(FILE_PATH, base_name, f"{base_name}_seg.mp4")

    if not os.path.exists(video_file_path):
        raise HTTPException(status_code=404, detail="Video file not found.")

    def iterfile():
        with open(video_file_path, "rb") as file:
            yield from file

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"attachment;filename={base_name}_seg.mp4",
        },
    )


@app.get("/metadata/{video_name}")
async def get_metadata(video_name: str) -> List[str]:
    base_name = video_name.split(".")[0]
    metadata_file_path = os.path.join(
        FILE_PATH, base_name, f"{base_name}_qualitative_log.json"
    )

    if not os.path.exists(metadata_file_path):
        raise HTTPException(status_code=404, detail="Metadata file not found.")

    with open(metadata_file_path, "r") as file:
        metadata = json.load(file)

    return metadata


# @app.post("/grounding_dino")
# async def run_grounding_dino(target_video: str, query: str):
#     video = get_video_from_path(target_video)
#     video_path = video.file
#     logging.info(f"Running Grounding Dino on video path: {video_path}")

#     vr = decord.VideoReader(video_path)
#     frames = vr.get_batch(range(0, len(vr), 10)).asnumpy()

#     results = []
#     for frame in tqdm(frames):
#         image = Image.fromarray(frame.astype(np.uint8))
#         output_path = "image.jpg"
#         image.save(output_path)
#         image_source, processed_image = load_image_from_path(output_path)
#         # image_source, processed_image = load_image(image)

#         boxes, logits, phrases = predict(
#             model=model,
#             image=processed_image,
#             caption=query,
#             box_threshold=0.35,
#             text_threshold=0.25,
#         )

#         annotated_frame = annotate(
#             image_source=image_source, boxes=boxes, logits=logits, phrases=phrases
#         )
#         results.append(annotated_frame)

#     return results
