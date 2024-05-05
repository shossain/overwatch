import os
import json
import cv2
from scipy.ndimage import binary_dilation
from aot_tracker import _palette
from PIL import Image
import numpy as np
import pickle

video_id = os.environ["VIDEO"]

video_file = f"./assets/{video_id}.mp4"
json_file = f"./assets/{video_id}.json"
output_video = f"./assets/output/{video_id}_seg.mp4"
label_files = [
    f"./assets/output/{video_id}_tank",
    f"./assets/output/{video_id}_smoke",
]

def colorize_mask(pred_mask):
    save_mask = Image.fromarray(pred_mask.astype(np.uint8))
    save_mask = save_mask.convert(mode="P")
    save_mask.putpalette(_palette)
    save_mask = save_mask.convert(mode="RGB")
    return np.array(save_mask)


def draw_mask(img, mask, alpha=0.7, id_countour=False):
    img_mask = np.zeros_like(img)
    img_mask = img
    if id_countour:
        # very slow ~ 1s per image
        obj_ids = np.unique(mask)
        obj_ids = obj_ids[obj_ids != 0]

        for id in obj_ids:
            # Overlay color on  binary mask
            if id <= 255:
                color = _palette[id * 3 : id * 3 + 3]
            else:
                color = [0, 0, 0]
            foreground = img * (1 - alpha) + np.ones_like(img) * alpha * np.array(color)
            binary_mask = mask == id

            # Compose image
            img_mask[binary_mask] = foreground[binary_mask]

            countours = binary_dilation(binary_mask, iterations=1) ^ binary_mask
            img_mask[countours, :] = 0
    else:
        binary_mask = mask != 0
        countours = binary_dilation(binary_mask, iterations=1) ^ binary_mask
        foreground = img * (1 - alpha) + colorize_mask(mask) * alpha
        img_mask[binary_mask] = foreground[binary_mask]
        img_mask[countours, :] = 0

    return img_mask.astype(img.dtype)

labels = []
masks = []
for file in label_files:
    with open(file + "_output.pkl", "rb") as f:
        labels.append(pickle.load(f))
    print(f"loaded labels for {file}")
    masks.append(np.load(file + "_masks.npy").tolist())
    print(f"loaded mesh for {file}")

cap = cv2.VideoCapture(video_file)

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

# setup text fonts
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
color = (0, 255, 170)  # Blue color in BGR
thickness = 5
line_space = 30

frame_idx = 0

merged_json = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    json_per_frame = []
    for all_label, mask in zip(labels, masks):
        frame = draw_mask(frame, np.array(mask[frame_idx]))
        one_labels = all_label[frame_idx]
        for label in one_labels:
            if "id" not in label:
                continue

            json_per_frame.append(label)
            id = label["id"]
            prompt = label["prompt"]
            centroid = label["centroid"]

            frame = cv2.putText(frame, f"{id} - {prompt}", centroid, font, font_scale, color, thickness)
    
    merged_json.append(json_per_frame)

    masked_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    out.write(masked_frame)
    print("frame {} written".format(frame_idx), end="\r")
    frame_idx += 1

with open(json_file, "w") as f:
    json.dump(merged_json, f)

print("finished writing JSON")

out.release()
cap.release()