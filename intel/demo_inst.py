import os
import cv2
from SegTracker import SegTracker
from model_args import aot_args, sam_args, segtracker_args
from PIL import Image
from aot_tracker import _palette
import numpy as np
import torch
import imageio
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation
import gc
from tqdm import tqdm
import pickle


def save_prediction(pred_mask, output_dir, file_name):
    save_mask = Image.fromarray(pred_mask.astype(np.uint8))
    save_mask = save_mask.convert(mode="P")
    save_mask.putpalette(_palette)
    save_mask.save(os.path.join(output_dir, file_name))


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


# Set Text args
"""
parameter:
    grounding_caption: Text prompt to detect objects in key-frames
    box_threshold: threshold for box
    text_threshold: threshold for label(text)
    box_size_threshold: If the size ratio between the box and the frame is larger than the box_size_threshold, the box will be ignored. This is used to filter out large boxes.
    reset_image: reset the image embeddings for SAM
"""
#grounding_caption = "vehicle.car.tank"
#grounding_caption = "smoke.steam.fire"
grounding_caption = os.environ["CAPTION"]
simple_caption = grounding_caption.split(".")[0]
box_threshold, text_threshold, box_size_threshold, reset_image = 0.35, 0.5, 0.5, True
#box_threshold, text_threshold, box_size_threshold, reset_image = 0.25, 0.15, 0.15, True

video_name = os.environ["VIDEO"] # "ukraine_cut"
io_args = {
    "input_video": f"./assets/{video_name}.mp4",
    "output_mask_dir": f"./assets/output/{video_name}_masks",  # save pred masks
    "output_video": f"./assets/output/{video_name}_seg.mp4",  # mask+frame vizualization, mp4 or avi, else the same as input video
    "output_gif": f"./assets/output/{video_name}_seg.gif",  # mask visualization
    "output_json": f"./assets/output/{video_name}_{simple_caption}_output.pkl",
    "output_masks": f"./assets/output/{video_name}_{simple_caption}_masks.npy",
    "append_previous": False,
}

# choose good parameters in sam_args based on the first frame segmentation result
# other arguments can be modified in model_args.py
# note the object number limit is 255 by default, which requires < 10GB GPU memory with amp
sam_args['generator_args'] = {
        'points_per_side': 30,
        'pred_iou_thresh': 0.8,
        'stability_score_thresh': 0.9,
        'crop_n_layers': 1,
        'crop_n_points_downscale_factor': 2,
        'min_mask_region_area': 200,
    }

# For every sam_gap frames, we use SAM to find new objects and add them for tracking
# larger sam_gap is faster but may not spot new objects in time
segtracker_args = {
    'sam_gap': 15, # the interval to run sam to segment new objects
    'min_area': 125, # minimal mask area to add a new mask as a new object
    'max_obj_num': 255, # maximal object number to track in a video
    'min_new_obj_iou': 0.8, # the area of a new object in the background should > 80% 
}

# source video to segment
cap = cv2.VideoCapture(io_args["input_video"])
fps = cap.get(cv2.CAP_PROP_FPS)
# output masks
output_dir = io_args["output_mask_dir"]
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
pred_list = []
masked_pred_list = []

torch.cuda.empty_cache()
gc.collect()
sam_gap = segtracker_args["sam_gap"]
frame_idx = 0
segtracker = SegTracker(segtracker_args, sam_args, aot_args)
segtracker.restart_tracker()


with tqdm() as pbar:
    with torch.cuda.amp.autocast():
        while cap.isOpened():
            ret, frame = cap.read()
            if frame_idx == 0:
                segtracker.init(frame)
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if frame_idx == 0:
                pred_mask, _ = segtracker.detect_and_seg(
                    frame,
                    grounding_caption,
                    box_threshold,
                    text_threshold,
                    box_size_threshold,
                    reset_image,
                )
                # pred_mask = cv2.imread('./debug/first_frame_mask.png', 0)
                torch.cuda.empty_cache()
                gc.collect()
                segtracker.add_reference(frame, pred_mask)
            elif (frame_idx % sam_gap) == 0:
                seg_mask, _ = segtracker.detect_and_seg(
                    frame,
                    grounding_caption,
                    box_threshold,
                    text_threshold,
                    box_size_threshold,
                    reset_image,
                )

                #save_prediction(seg_mask, "./debug/seg_result", str(frame_idx) + ".png")
                torch.cuda.empty_cache()
                gc.collect()
                track_mask = segtracker.track(frame)
                #save_prediction(track_mask, "./debug/aot_result", str(frame_idx) + ".png")
                # find new objects, and update tracker with new objects
                new_obj_mask = segtracker.find_new_objs(track_mask, seg_mask)
                if np.sum(new_obj_mask > 0) > frame.shape[0] * frame.shape[1] * 0.4:
                    new_obj_mask = np.zeros_like(new_obj_mask)
                #save_prediction(new_obj_mask, output_dir, str(frame_idx) + "_new.png")
                pred_mask = track_mask + new_obj_mask
                # segtracker.restart_tracker()
                segtracker.add_reference(frame, pred_mask)
            else:
                pred_mask = segtracker.track(frame, update_memory=True)
            torch.cuda.empty_cache()
            gc.collect()

            # save_prediction(pred_mask, output_dir, str(frame_idx) + ".png")
            # masked_frame = draw_mask(frame,pred_mask)
            # masked_pred_list.append(masked_frame)
            # plt.imshow(masked_frame)
            # plt.show()

            pred_list.append(pred_mask)

            print(
                "processed frame {}, obj_num {}".format(
                    frame_idx, segtracker.get_obj_num()
                ),
                # end = '\r'
            )
            pbar.update(1)
            frame_idx += 1
        cap.release()
        print("\nfinished")


# draw pred mask on frame and save as a video
cap = cv2.VideoCapture(io_args["input_video"])
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

object_states = []

# setup text fonts
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
color = (0, 255, 170)  # Blue color in BGR
thickness = 10
line_space = 30

masks = []

frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pred_mask = pred_list[frame_idx]
    masks.append(pred_mask)
    
    array = np.array(pred_mask)
    flat_array = array.flatten()
    unique_values = np.unique(flat_array)
    object_stats = {}
    for value in unique_values:
        if value == 0:
            continue
        indices = np.argwhere(array == value) 
        average_location = indices.mean(axis=0)
        # Calculate size of the mask (number of occurrences)
        size = len(indices)
        # Store stats in dictionary
        object_stats[value] = {
            "id": int(value), 
            "centroid": (int(average_location[1]), int(average_location[0])), 
            "size": float(size), 
            "prompt": simple_caption,
        }

    object_states.append(list(object_stats.values()))

    # masked_frame = masked_pred_list[frame_idx]
    print("frame {} writed".format(frame_idx), end="\r")
    frame_idx += 1

import json
with open(io_args["output_json"], "wb") as f:
    pickle.dump(object_states, f)
    print("Data written to JSON")

with open(io_args["output_masks"], "wb") as f:
    np.save(f, np.array(masks))
    print("Data written to npy")

cap.release()
print("\n{} saved".format(io_args["output_video"]))
print("\nfinished")
