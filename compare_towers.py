import glob
import os
import random
from requests import GPT
from dotenv import load_dotenv
import utils

load_dotenv()
JUDGE_TOWER_PROMPT = """On a scale of 1-10, how stable is this tower?
On the first line, give the score
On the next N lines, explain your reasoning, referring to objects numerically with 1 being the bottommost element.
"""
COMPARE_TOWERS_PROMPT = """Which of these towers is more stable?
Consider that these images might be taken from different angles.
On the first line, give only the number of the more stable stack.
Only give the number without any symbols
On the next N lines, explain your reasoning, referring to objects numerically with 1 being the bottommost element."""
IMPROVE_TOWER_PROMPT = """Explain how the objects should be moved to obtain a more stable structure.
Refer to objects numerically with 1 being the bottommost element."""


def judge_tower(filename: str, gpt: GPT) -> str:
    gpt.clear_convo()
    return gpt.send_image(filename, JUDGE_TOWER_PROMPT)

def compare_towers_combined(tower: str, gpt: GPT) -> str | None:
    gpt.clear_convo()
    return gpt.send_image(tower, COMPARE_TOWERS_PROMPT)


def compare_towers(tower1: str, tower2: str, gpt: GPT) -> str | None:
    gpt.clear_convo()
    return gpt.send_images([tower1, tower2], COMPARE_TOWERS_PROMPT)


def improve_tower(gpt: GPT) -> str | None:
    return gpt.send_message(IMPROVE_TOWER_PROMPT)

def combine_images(tower1_files: list[str], tower2_files: list[str]) -> None:
    for t1 in tower1_files:
        for t2 in tower2_files:
            utils.combine_images_horizontally(f"{image_folder}{t1}", f"{image_folder}{t2}", f"imgs/combined/{t1}-{t2}.jpg")
            utils.combine_images_horizontally(f"{image_folder}{t2}", f"{image_folder}{t1}", f"imgs/flipped/{t1}-{t2}-flipped.jpg")


if __name__ == "__main__":
    # counts = [0, 0]
    # for file in os.listdir("out/compare_towers"):
        
    #     with open(f"out/compare_towers/{file}", "r") as file:
    #         file.readline()
    #         ans = int(file.readline())
    #         assert ans == 1 or ans == 2
    #         counts[ans-1]+= 1
    # print(counts)


    image_folder = "imgs/towers/"
    judge_folder = "out/judge_towers/"
    compare_folder = "out/compare_towers/"
    tower1 = list(map(os.path.basename, glob.glob("imgs/towers/tower1*")))
    tower2 = list(map(os.path.basename, glob.glob("imgs/towers/tower3*")))
    tower_comps = os.listdir("imgs/combined/")
    tower_comps_flipped = os.listdir("imgs/flipped/")
    gpt = GPT()

    # print("====== Judging towers =====")
    # for img in tower1 + tower2:
    #     print(f"Judging {img}...")
    #     with open(f"{judge_folder}{img}.txt", "w") as f:
    #         f.write(f"{judge_tower(image_folder + img, gpt)}\n\n")
    #         f.write(f"{improve_tower(gpt)}\n")

    print("====== Comparing towers =====")

    combine_images(tower1, tower2)
    better_counts = [0, 0]
    for tower in tower_comps + tower_comps_flipped:
            print(f"Comparing {tower}...")
            
            flip = tower in tower_comps_flipped
            if flip:
                # not flipped
                resp = compare_towers_combined(f"imgs/flipped/{tower}", gpt)
                better_counts[int(resp.split("\n")[0]) - 1] += 1 # type: ignore
            else:
                resp = compare_towers_combined(f"imgs/combined/{tower}", gpt)
                better_counts[2 - int(resp.split("\n")[0])] += 1 # type: ignore

            with open(f"{compare_folder}{tower}.txt", "w") as f:
                f.write(f"Flipped: {flip}\n")
                f.write(f"{resp}\n")
    print(better_counts)