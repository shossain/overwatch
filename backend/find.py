import torch
import sys

sys.path.append("GroundingDINO")

from groundingdino.models import build_model
from groundingdino.util import box_ops
from groundingdino.util.inference import predict
from groundingdino.util.slconfig import SLConfig
from groundingdino.util.utils import clean_state_dict

from huggingface_hub import hf_hub_download

from utils import transform_image
import utils as utils


def load_model_hf(repo_id, filename, ckpt_config_filename, device='cpu'):
    cache_config_file = hf_hub_download(repo_id=repo_id, filename=ckpt_config_filename)
    args = SLConfig.fromfile(cache_config_file)
    model = build_model(args)
    args.device = device

    cache_file = hf_hub_download(repo_id=repo_id, filename=filename)
    checkpoint = torch.load(cache_file, map_location='cpu')
    log = model.load_state_dict(clean_state_dict(checkpoint['model']), strict=False)
    print(f"Model loaded from {cache_file} \n => {log}")
    model.eval()
    return model


def load_gd(repo_id:str="ShilongLiu/GroundingDINO",
            ckpt_filename:str="groundingdino_swinb_cogcoor.pth",
            ckpt_config_filename:str="GroundingDINO_SwinB.cfg.py",
            device="cuda:0"):
    return load_model_hf(repo_id, ckpt_filename, ckpt_config_filename, device=device)
    

def find(model, image_pil, text_prompt, box_threshold=0.4, text_threshold=0.45, device="cuda:0"):
    image_trans = transform_image(image_pil)
    boxes, logits, phrases = predict(
        model = model,
        image = image_trans,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        device=device
    )
    
    W, H = image_pil.size
    boxes = box_ops.box_cxcywh_to_xyxy(boxes) * torch.Tensor([W, H, W, H])
    return boxes, logits, phrases


if __name__ == "__main__":
    import time
    model = load_gd()
    print("loaded model")
    from PIL import Image
    import matplotlib.pyplot as plt
    im = Image.open(open("data/soldiers.jpg", "rb")).convert("RGB")

    start = time.time()
    boxes, logits, phrases = find(model, im, "soldiers")
    end = time.time()

    plt.imshow(im)
    utils.show_box(boxes[0], plt.gca())
    plt.axis('on')
    plt.savefig("out.png")

    print(boxes)
    print(f"Took {end - start} seconds")