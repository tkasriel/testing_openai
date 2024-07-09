import glob
import os
from utils import resize_image
if __name__ == "__main__":
    in_folder = "imgs/rulers/*"
    out_folder = "imgs/small_rulers/"
    imgs = glob.glob(in_folder)
    for img in imgs:
        name = os.path.basename(img)
        resize_image(img, f"{out_folder}{name}")