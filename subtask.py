import glob
import os
from requests import GPT
from dotenv import load_dotenv
from utils import combine_images_four, combine_images_horizontally, combine_images_three

load_dotenv()

# OBSERVE_PROMPT = """You are highly skilled in robotic task planning, breaking down intricate and long-term tasks into distinct primitive actions.
# If the object is in sight, you need to directly manipulate it. If the object is not in sight, you need to use primitive skills to find the object
# first. If the target object is blocked by other objects, you need to remove all the blocking objects before picking up the target object. At
# the same time, you need to ignore distracters that are not related to the task. And remember your last step plan needs to be "done".
# Consider skills a robotic arm with suction can perform.
# You are only allowed to use these provided skills. 
# If needed, you may ask for an image to be taken at a specific step in order to better see the scene.
# When creating a plan, replace these placeholders with specific items or positions without using square brackets or parentheses. You can first itemize the task-related
# objects to help you plan."""


SUBTASK_PROMPT = """You are highly skilled in robotic task planning, breaking down intricate and long-term tasks into distinct primitive actions.
If the object is in sight, you need to directly manipulate it. If the object is not in sight, you need to use primitive skills to find the object
first. If the target object is blocked by other objects, you need to remove all the blocking objects before picking up the target object. At
the same time, you need to ignore distracters that are not related to the task. And remember your last step plan needs to be "done".
Consider skills a robotic arm with suction can perform.
You are allowed rotate an item.
You are only allowed to use these provided skills. When creating a plan, replace
these placeholders with specific items or positions without using square brackets or parentheses. You can first itemize the task-related
objects to help you plan."""

SOM = """
You are highly skilled in robotic task planning, breaking down intricate and long-term tasks into distinct primitive actions.
If the object is in sight, you need to directly manipulate it. If the object is not in sight, you need to use primitive skills to find the object
first. If the target object is blocked by other objects, you need to remove all the blocking objects before picking up the target object. At
the same time, you need to ignore distracters that are not related to the task. And remember your last step plan needs to be "done".
Consider skills a robotic arm with suction can perform.
You are allowed rotate an item.
You are only allowed to use skills that a robot arm with suction could perform.
Refer to objects by their labeled number. When referring to the number labels, write them in brackets, like [1], [2]. 
Don't use ranges. If you need to refer to multiple items, write them in a list format, ex: [1], [2], [3].
Note that not all labels refer to a manipulateable object, and some objects may have more than one label attached to it referring to different parts of the object.
"""

IDENTIFY_PROMPT = """You are highly skilled in robotic task planning.
If the object is in sight, you need to directly manipulate it. If the object is not in sight, you need to use primitive skills to find the object
first. If the target object is blocked by other objects, you need to remove all the blocking objects before picking up the target object. At
the same time, you need to ignore distracters that are not related to the task. And remember your last step plan needs to be "done".
Consider skills a robotic arm with suction can perform.
You are allowed rotate an item.
Refer to objects by their labeled number. When referring to the number labels, write them in brackets, like [1], [2]. 
Don't use ranges. If you need to refer to multiple items, write them in a list format, ex: [1], [2], [3].
You will be given a task. You must identify all objects relevant to the task at hand, separating them into action items that will be directly manipulated, and relevant items that will not be directly manipulated.
You do not need to make a plan, only identify the objects with their labels.
"""

MULTI_VIEW_WARNING = """
You are shown the same scene from multiple angles.
There may be duplicate labels across images describing different objects. If you refer to an object, please say which view it originates from."""

GOTO_PROMPT = SOM + """
Image 1 is the current scene. Image 2 is the target scene.
Give a list of instructions to manipulate objects to obtain the target scene with the objects given.
"""

def get_subtasks(task: str, image_filenames: list[str], gpt: GPT) -> str:
    gpt.clear_convo()
    return gpt.send_images(image_filenames, SOM + f"\nYour task is: {task}")

def get_write_subtasks(task: str, image_filename: str | list[str], out_folder: str, gpt: GPT) -> None:
    
    if isinstance(image_filename, str):
        name = os.path.basename(image_filename)
        out = get_subtasks(task, [image_filename], gpt)
    else:
        name = "-".join(map(os.path.basename, image_filename))
        out = get_subtasks(task, image_filename, gpt)
    with open(f"{out_folder}/{name}.txt", 'w') as file:
        file.write(out)

def it_gs (task: str, names: list[str], out_path: str, gpt: GPT) -> None:
    for fn in names:
        get_write_subtasks(task, fn, out_path, gpt)
        



if __name__ == "__main__":
    gpt = GPT()


    img_folder = "imgs/marked"

    out_folder = "out/marked"

    
    
    # blocks = glob.glob(f"{img_folder}/*_block*")
    # # teas = glob.glob(f"{img_folder}/*_tea*")
    # # envelopes = glob.glob(f"{img_folder}/*_envelope*")
    # perspectives = glob.glob(f"{img_folder}/perspective*")
    # fixes = glob.glob(f"{img_folder}/fix_*")
    # fix_perspectives = glob.glob(f"{img_folder}/fix_tower_perspective*")
    
    # books = glob.glob(f"{img_folder}/books*")
    
    # combine_images_three(fix_perspectives, "imgs/combined/fix_tower.jpg")
    # combine_images_four(books, "imgs/combined/books.jpg")
    # combine_images_horizontally("imgs/marked/current.png", "imgs/small_subtasking/get_to_here.JPG", "imgs/combined/goto.jpg")
    # combine_images_horizontally("imgs/marked/current_2.png", "imgs/small_subtasking/get_to_here_2.JPG", "imgs/combined/goto_2.jpg")
    # combine_images_horizontally("imgs/marked/get_to_here_2.png", "imgs/small_subtasking/current_2.JPG", "imgs/combined/goto_2_reversed.jpg")
    # combine_images_horizontally("imgs/marked/lunch_1.png", "imgs/marked/lunch_2.png", "imgs/combined/lunch.png")

    # it_gs("Stack the blocks", blocks, out_folder, gpt)
    # it_gs("Where should I interact with the tower to stabilize it?", fixes, out_folder, gpt)
    # it_gs("Make some tea", teas, out_folder, gpt)
    # it_gs("Put my paperwork in the envelope and close it.", envelopes, out_folder, gpt)

    get_write_subtasks("Make me lunch" + MULTI_VIEW_WARNING, "imgs/combined/lunch.png", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto.jpg", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto_2.jpg", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto_2_reversed.jpg", out_folder, gpt)
    # get_write_subtasks("Where should I push, pull or rotate to stabilize the tower?" + MULTI_VIEW_WARNING, "imgs/combined/fix_tower.jpg", out_folder, gpt)    
    # get_write_subtasks("Where should I push to align the books?" + MULTI_VIEW_WARNING, books, out_folder, gpt)
    # get_write_subtasks("Stack the blocks without breaking the glass.", f"{img_folder}/glass-block.png", out_folder, gpt)
    # get_write_subtasks("Arrange the pens in a figure 8 pattern.", f"{img_folder}/pens.png", out_folder, gpt)
    # get_write_subtasks("Stack the blocks", perspectives, out_folder, gpt)
    # get_write_subtasks("Where should I interact with the books to align them?", books, out_folder, gpt)

    # get_write_subtasks("Put the shark to bed", f"{img_folder}/shark.png", out_folder, gpt)
    # get_write_subtasks("I'm hungry", f"{img_folder}/shark.png", out_folder, gpt)
    # it_gs("Make me lunch", [[f"{img_folder}/lunch1.png",f"{img_folder}/lunch2.png"], f"{img_folder}/lunch2.png"], out_folder, gpt) # type: ignore
    

    # curr_img = "block_envelope"
    # img_folder = "imgs/subtasking/"
    # out = get_subtasks("Put my paperwork into the envelope and close it.", f"{img_folder}{curr_img}.jpg", gpt)
    # # out = get_subtasks("Make me lunch", [f"{img_folder}lunch1.jpg", f"{img_folder}lunch2.jpg"], gpt)
    # print(out)
    # with open(f"out/subtasks/{curr_img}.txt", 'w') as file:
    #     file.write(out)