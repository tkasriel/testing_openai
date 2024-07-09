import base64
import glob
import os
from requests import GPT

if __name__ == "__main__":
    img_folder = "imgs/examples/"
    out_file = "out/examples/encodings.txt"
    files = glob.glob(f"{img_folder}*")
    with open(out_file, "w") as out_file:
        for img in files:
            with open(img, "rb") as image_file:
                hash = base64.b64encode(image_file.read()).decode("utf-8")
            out_file.write(f"{os.path.basename(img)}: {hash}\n")