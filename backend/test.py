import os
from typing_extensions import Annotated

from fastapi import FastAPI, Request

import cv2
import numpy as np
from tqdm import tqdm
import decord
import io
from PIL import Image
import matplotlib.pyplot as plt

from find import load_gd, find
import utils as utils

FILE_PATH = "files"

def get_video_from_path(video_name: str) -> str:
    base_name = video_name.split(".")[0]
    file_path = os.path.join(FILE_PATH, base_name, video_name)
    return file_path


model = load_gd()


video_path = get_video_from_path("ukraine_cut.mp4")
print(f"Running Grounding Dino on video path: {video_path}")

cap = cv2.VideoCapture(video_path)
while(cap.isOpened()):
    ret, frame = cap.read()

    print(frame)
    image = Image.fromarray(frame.astype(np.uint8))
    output_path = "image.jpg"
    image.save(output_path)
    im = Image.open(output_path).convert("RGB")
    print(im)
    boxes, logits, phrases = find(model, im, "soldier")
    print(boxes)
    success, frame = cap.read()