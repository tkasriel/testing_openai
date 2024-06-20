from requests import GPT
from dotenv import load_dotenv

load_dotenv()
JUDGE_TOWER_PROMPT = """On a scale of 1-10, how stable is this tower?
On the first line, give the score
On the next N lines, explain your reasoning, referring to objects numerically with 1 being the bottommost element.
"""
COMPARE_TOWERS_PROMPT = """Which of these towers is more stable? 
Consider that these images might be taken from different angles"""
IMPROVE_TOWER_PROMPT = """Explain how the objects should be moved to obtain a more stable structure.
Refer to objects numerically with 1 being the bottommost element."""


def judge_tower(filename: str, gpt: GPT) -> str | None:
    gpt.clear_convo()
    return gpt.send_image(filename, JUDGE_TOWER_PROMPT)


def compare_towers(filename: str, gpt: GPT) -> str | None:
    gpt.clear_convo()
    return gpt.send_image(filename, COMPARE_TOWERS_PROMPT)


def improve_tower(gpt: GPT) -> str | None:
    return gpt.send_message(IMPROVE_TOWER_PROMPT)


if __name__ == "__main__":

    image_folder = "imgs/towers/"
    gpt = GPT()
    # print(improve_tower(gpt))
    print("====== Judging towers =====")
    for img in ["tower_1.jpg", "tower_2.jpg", "tower_2_other.jpg"]:
        print(f"# {img}:")
        print(judge_tower(image_folder + img, gpt))
        print("")
        print(improve_tower(gpt))
        print("\n")

    print("====== Comparing towers =====")
    for img in ["comparison_t1_t2.png", "comparison_t1_t2_other.png"]:
        print(f"# {img}:")
        print(compare_towers(image_folder + img, gpt))
        print("\n")
