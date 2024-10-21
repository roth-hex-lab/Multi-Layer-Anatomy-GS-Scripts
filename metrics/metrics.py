import argparse
import statistics
import sys
from pathlib import Path

import torch
import lpips
import numpy as np
import torchvision.transforms as transforms
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Calculate a set of metrics between two files or average between multiple files")
    parser.add_argument("files_a", help="First image or folder of images", type=str)
    parser.add_argument("files_b", help="Second image or folder of images", type=str)
    args = parser.parse_args()

    files_a = []
    files_b = []

    path_a = Path(args.files_a)
    path_b = Path(args.files_b)

    if not path_a.exists():
        sys.exit("Path to files a invalid")

    if not path_b.exists():
        sys.exit("Path to files b invalid")

    for (files, path) in zip([files_a, files_b], [path_a, path_b]):
        elements = []
        if path.is_file():
            elements.append(path)
        elif path.is_dir():
            elements = path.glob("*")

        for element in elements:
            try:
                img = Image.open(element)
                files.append(img)
            except:
                pass

    if len(files_a) != len(files_b):
        sys.exit(f"Unbalanced number of images: a={len(files_a)}, b={len(files_b)}")

    if not files_a:
        sys.exit("No valid images specified")

    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    lpips_model = lpips.LPIPS(net='vgg')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ssim_scores = []
    psnr_scores = []
    lpips_scores = []

    for (img_a, img_b) in tqdm(zip(files_a, files_b), total=len(files_a)):
        img_a_rgb = img_a.convert('RGB')
        img_b_rgb = img_b.convert('RGB')
        img_a_arr = np.array(img_a_rgb)
        img_b_arr = np.array(img_b_rgb)

        ssim_scores.append(ssim(img_a_arr, img_b_arr, channel_axis=-1))
        psnr_scores.append(psnr(img_a_arr, img_b_arr))

        a_tensor = transform(img_a_rgb).unsqueeze(0)
        b_tensor = transform(img_b_rgb).unsqueeze(0)
        lpips_scores.append(lpips_model(a_tensor, b_tensor).item())
 

    ssim_stdev = 0
    psnr_stdev = 0
    lpips_stdev = 0
    if len(files_a) > 1:
        ssim_stdev = statistics.stdev(ssim_scores)
        psnr_stdev = statistics.stdev(psnr_scores)
        lpips_stdev = statistics.stdev(lpips_scores)
        pass

    print(f"Comparing {len(files_a)} images:")
    print(f"SSIM:  {statistics.mean(ssim_scores):>7.4f}±{ssim_stdev:.4f}")
    print(f"PSNR:  {statistics.mean(psnr_scores):>7.4f}±{psnr_stdev:.4f}")
    print(f"LPIPS: {statistics.mean(lpips_scores):>7.4f}±{lpips_stdev:.4f}")