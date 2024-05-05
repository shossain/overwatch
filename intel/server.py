from tool.detector import Detector

import os
import json
import logging
import numpy as np
from tqdm import tqdm

import decord
import uvicorn
import asyncio 
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, WebSocket, HTTPException

FILE_PATH = "files"
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

logging.info("Loading grounding-dino")
detector = Detector("cuda",
                config_file = "/home/parvus/src/hack/Segment-and-Track-Anything/src/groundingdino/groundingdino/config/GroundingDINO_SwinT_OGC.py",
                grounding_dino_ckpt = '/home/parvus/src/hack/Segment-and-Track-Anything/ckpt/groundingdino_swint_ogc.pth')
logging.info("Loaded grounding-dino")

def get_video_from_path(video_name: str):
    base_name = video_name.split(".")[0]
    file_path = os.path.join(FILE_PATH, base_name, video_name)
    return file_path

@app.get("/video")
async def get_video(video_name: str) -> StreamingResponse:
    base_name = video_name.split(".")[0]
    video_file_path = os.path.join(FILE_PATH, base_name, f"{base_name}_seg.mp4")
    logging.info(video_file_path)

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

@app.get("/metadata")
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

@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket, target_video:str, query:str, interval:int=5):
    await websocket.accept()
        
    video_path = get_video_from_path(target_video)
    logging.info(f"Running Grounding Dino on video path: {video_path}")

    vr = decord.VideoReader(video_path)
    frames = vr.get_batch(range(0, len(vr), interval)).asnumpy()

    frame_idx = 0
    for frame in tqdm(frames):
        image = frame.astype(np.uint8)

        annotated_frame, boxes, phrases, logits = detector.run_grounding(image, query, 0.25, 0.4, verbose=True)

        for box, phrase in zip(boxes, phrases):
            await websocket.send_text(json.dumps({
                "label": phrase,
                "bbox": box.tolist(),
                "frame_idx": frame_idx,
            }))
            await asyncio.sleep(0.005)

        frame_idx += interval

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)