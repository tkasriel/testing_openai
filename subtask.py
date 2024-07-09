import asyncio
import glob
import os
import random
from requests import GPT
from dotenv import load_dotenv
from utils import combine_images_four, combine_images_horizontally, combine_images_three, draw_arrows_on_image, encode_file
from openai.types.chat import ChatCompletionMessageParam

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

FIX_TOP_PROMPT = """You are a skilled robot planner for a robot with a suction grip. The image shows a sideview of stacked blocks. You must answer the following questions:
Identify the top block. What color is it? What shape is it? Make sure not to confuse it with the block below.
Is the stacked block stable? A stacked block is considered stable when the blocks are perfectly aligned in the center and the orientation of the blocks are perfectly aligned. Answer only Yes or No and give the reason.
The top block can be moved in 9 ways: left, left back. back. right back, right, right front, front, left front and no move. If the stacked block is unstable, how should the top block be moved to make the stack more stable? Answer the index of the direction and the reason.
The top block can be rotated in 3 ways: counter clockwise, clockwise and no rotation.  If the stacked block is unstable, how should the top block be rotated to make the stack more stable? Answer the index of the rotation directions and the reason."""

WHERE_MISTAKE_PROMPT = """You are a skilled robot planner controlling a robot with suction. On executing some of the instructions given, the robot may have made a mistake in its task. T
First, you must identify if all instructions were performed correctly without causing problems to the stability of the tower. On the first line, reply to this question with either True or False. 
On the second line [if applicable], refer to the instruction that was performed incorrectly, by number. 
On the third line [if applicable], refer to the block that is misplaced by the name used in the instructions. 
On the fourth and fifth line, give the translation [in direction, in cm approx], and rotation [in degrees clockwise or counter-clockwise] needed to fix the block in question. The instructions used to build this object were: 1. Move the large yellow cube to stacking area 2. Move the flat green block on top of the large yellow cube 3. Move the flat red block on top of the flat green block 4. Move the long flat yellow block on top of the flat red block 5. Move the large yellow cube on top of the long flat yellow block 6. Move the red triangular prism on top of the large yellow cube
"""
MISTAKE_STEPS = [
"""1. Move the large yellow cube to stacking area
2. Move the flat green block on top of the large yellow cube
3. Move the flat red block on top of the flat green block
4. Move the long flat yellow block on top of the flat red block
5. Move the large yellow cube on top of the long flat yellow block
6. Move the red triangular prism on top of the large yellow cube
""",
"""1. Move the large yellow cube to stacking area
2. Move the flat green block on top of the large yellow cube
3. Move the flat red block on top of the flat green block
4. Move the large yellow cube on top of the flat red block
5. Move the red triangular prism on top of the large yellow cube
""",
"""1. Move the large yellow cube to stacking area
2. Move the flat beige block on top of the large yellow cube
3. Move the flat red block on top of the flat beige block
4. Move the green block on top of the flat red block""",
"""1. Move the flat beige block to the stack area
2. Move the large yellow cube on top of the flat beige block
3. Move the flat red block on top of the large yellow cube
4. Move the green block on the flat red block
"""
]

ORDER_PROMPT = """You are a skilled robot controlling a robot with suction. Your task is to stack the blocks in a way that forms the most stable tower possible.

Instructions:
1. Refer to objects by their labeled number, writing them in brackets, e.g., [1], [2].
2. Do not use ranges; if you need to refer to multiple items, write them in a list format, e.g., [1], [2], [3].
3. Note that not all labels refer to manipulable objects, and some objects may have multiple labels referring to different parts.
4. Identify only the labels corresponding to manipulable blocks.
5. Provide the best order to stack these blocks in a list format, with the first item in the list being the bottommost block in the stack.

Please list the blocks in the most stable order for stacking.

Example answer:
[1], [2], [3], [4], [5]
"""

RAVEN_PROMPT = """ The image below shows two vertically stacked blocks. Which option below results in a more aligned or stable block stacks. 
(A) move the top block towards the left of the image 
(B) move the top block towards the right of the image 
(C) move the top block towards the camera 
(D) move the top block away from the camera. 
(E) move the top block towards the left and top of the image 
(F) move the top block towards the left and bottom of the image 
(G) move the top block towards the right and top of the image 
(H) move the top block towards the right and bottom of the image
On the first line, give the answer only.
On the second line, please a sequence of 10 random characters"""

ORDER_GOTO_PROMPT = """You are a skilled robot controlling a robot with suction. Your task is to stack the blocks seen in image 1 to obtain the stack found in image 2
Instructions:
1. Refer to objects by their labeled number, writing them in brackets, e.g., [1], [2].
2. Do not use ranges; if you need to refer to multiple items, write them in a list format, e.g., [1], [2], [3].
3. Note that not all labels refer to manipulable objects, and some objects may have multiple labels referring to different parts.
4. Identify only the labels corresponding to manipulable blocks.
5. Provide the best order to stack these blocks in a list format, with the first item in the list being the bottommost block in the stack.

Please list the blocks that should be manipulated in order to achieve the task. You may reason about each block, but if you want to refer to labels other than those included in the correct order, write them without brackets.
"""

INSERT_BLOCKS = """You are a skilled robot planner in charge of packing objects. Your task is to identify the best place to insert the block seen in image 2 into a slot in image 1.
Refer to objects by their labeled number, writing them in brackets, eg. [1], [2].
You are allowed to explain your reasoning before giving an answer, but avoid using labels other than the one that you have identified as the best location for insertion.
"""


MESAURE_PROMPT = """Using the indicated rulers, measure the dimensions of this / these objects. Give the result in cm."""
NO_RULER_PROMPT = """Measure / estimate the dimensions of this / these blocks. Give the result in cm."""

LOCATE_PROMPT = """Using the rulers as a coordinate system, locate the centers of this / these objects. Give the coordinates in cm."""
# FIX_TOP_LR_PROMPT = """You are a skilled robot planner in charge of stacking objects. Your task is to identify whether the top block is not properly aligned with the block underneath and whether it needs to be readjusted.
# You don't need to consider depth in this case. We're only concerned about whether the top block should be moved to the left or right. You should respond either left or right only. 
# Explain your reasoning first, and then you should say [left], [right] or [none] in brackets as your final answer (don't write left or right in brackets unless it's your final answer).
# """

COMPARE_TOWERS_PROMPT = """You are provided two different tower stacks. Explain which of the two towers is more stable. A tower is more stable if its blocks are aligned on top of each other, and their centers of mass are aligned. There should be minimal overhangs, unless these overhangs still make a stable tower.
"""

def write_example_top(meta_prompt):
    hash1 = encode_file("imgs/examples/example_1.jpg")
    hash2 = encode_file("imgs/examples/example_2.jpg")
    hash3 = encode_file("imgs/examples/example_3.jpg")
    ctx = {"role": "user",
           "content":[
               {
                   "type": "text",
                   "text": meta_prompt + "\nHere are a few examples. Example 1:\n"
               },
               {
                   "type": "image",
                   "image_url": {
                       "url": f"data:image/jpeg;base64,{hash1}"
                   }
               },
               {
                    "type": "text",
                    "text": """For this example image, the answer should be:
The top block is a flat red block.
In order to see if the red block center is correctly stacked, I want to look at how the objects 
False, because the red block center is not perfectly aligned with the yellow block center.
direction: front, because the red block needs to be moved to front (towards the camera) to align with the yellow block
rotation: no rotation, because the red block orientation is already aligned with the yellow block"""
    },
                {
                    "type": "image",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{hash2}"
                    }
                },
                {
                    "type": "text",
                    "text": """For this example image, the answer should be:
The top block is a yellow cube.
True, because the yellow cube is aligned with the red block (while we can't see the back of the red block, we can follow its edges to guess that it is roughly in the center)
direction: no move, the yellow cube is aligned with the red block.
rotation: no rotation, because the yellow block is already aligned with the red block.
                    """
                },
                {
                    "type": "image",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{hash3}"
                    }
                },
                {
                    "type": "text",
                    "text": """For this example image, the answer should be:
The top block is a flat green block.
False, because the green block is not centered over the yellow block, and it is not aligned with the yellow block.
direction: left front, because the green block needs to be moved to the left and towards the camera in order to be aligned with the yellow block.
rotation: 45 degrees clockwise, because the green block is not aligned with the yellow block.
"""
}
    ]}
    return ctx

def write_example_insert_into(meta_prompt):
    hash1 = encode_file("imgs/examples/insert_into_ex1.jpg")
    hash2 = encode_file("imgs/examples/insert_into_ex2.jpg")
    ctx = {"role": "user",
           "content":[
               {
                   "type": "text",
                   "text": meta_prompt + "\nHere are a few examples. Example 1:\n"
               },
               {
                   "type": "image",
                   "image_url": {
                       "url": f"data:image/jpeg;base64,{hash1}"
                   }
               },
               {
                    "type": "text",
                    "text": """For this example image, the answer should be:
In this image, we're looking for a rectangular hole long enough to hold the block. While there are other spaces in the box, the only space long enough to contain it would be at [26]. While the hole is thin, the block is thin enough to fit."""
    },
                {
                    "type": "image",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{hash2}"
                    }
                },
                {
                    "type": "text",
                    "text": """For this example image, the answer should be:
In this image, we're looking for a square hole large enough to fit a square block. The only location for this is at [28]"""
                }
    ]}
    return ctx

def write_example_goto(meta_prompt):
    hash1 = encode_file("imgs/examples/goto_order_ex1.jpg")
    hash2 = encode_file("imgs/examples/goto_order_ex2.jpg")
    ctx = {"role": "user",
           "content":[
               {
                   "type": "text",
                   "text": meta_prompt + "\nHere are a few examples. Example 1:\n"
               },
               {
                   "type": "image",
                   "image_url": {
                       "url": f"data:image/jpeg;base64,{hash1}"
                   }
               },
               {
                    "type": "text",
                    "text": """For this example image, the answer should be:
In image 2, I see a stack consisting of the following: 
- a red flat block
- a green flat block
- a large yellow cube
- a green cube

In order to recreate the same image, I should stack the labels in the following order:
[6] as this is a red flat block
[7], as this was the block on 6 in image 2
[8], as this is a large yellow cube
[9] as this is a green cube as needed."""
    },
                {
                    "type": "image",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{hash2}"
                    }
                },
                {
                    "type": "text",
                    "text": """For this example image, the answer should be:
In image 2, I see a stack consisting of a blue block resting on a green cube and a yellow cube.
The apple is in the correct place, and so does not need to be moved

I notice that I don't need a majority of the blocks in image 1, but I can focus on the blocks I do need:
[16], and [17] to make the foundation of the stack
[10], which is the blue block that will rest on objects 16 and 17."""
                }
    ]}
    return ctx

def write_example_top_lr(meta_prompt):
    hash1 = encode_file("imgs/examples/fix_top_lr_ex1.jpg")
    hash2 = encode_file("imgs/examples/fix_top_lr_ex2.jpg")
    ctx = {"role": "user",
           "content":[
               {
                   "type": "text",
                   "text": meta_prompt + "\nHere are a few examples. Example 1:\n"
               },
               {
                   "type": "image",
                   "image_url": {
                       "url": f"data:image/jpeg;base64,{hash1}"
                   }
               },
               {
                    "type": "text",
                    "text": """For this example image, the answer should be:
In this image, I see a blue block stacked on top of a green block.
The blue block is the top block, and so I should consider whether the block forms more of an overhang in one direction as opposed to the other.
I can see that there is the same amount of overhang on both sides, so I don't need to move the blue block either left or right.
It should therefore be moved in no direction: [none]
"""
    },
                {
                    "type": "image",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{hash2}"
                    }
                },
                {
                    "type": "text",
                    "text": """For this example image, the answer should be:
I notice that in this example, we have a blue block stacked on top of a green block.
The blue block is the top block, and I should consider whether it is too far to the side compared to the green block.
I can see that a majority of the green block is to the left of the blue block, and the blue block is overhanging over the right side of the stack.
This means I should push the block [left]."""
                }
    ]}
    return ctx

async def get_subtasks(task: str, image_filenames: list[str], gpt: GPT) -> str:
    # gpt.clear_convo()
    return await gpt.send_images(image_filenames, task)#SOM + f"\nYour task is: {task}")

async def get_write_subtasks(task: str, image_filename: str | list[str], out_folder: str, gpt: GPT) -> None:
    
    if isinstance(image_filename, str):
        name = os.path.basename(image_filename)
        out = await get_subtasks(task, [image_filename], gpt)
    else:
        name = "-".join(map(os.path.basename, image_filename))
        out = await get_subtasks(task, image_filename, gpt)
    with open(f"{out_folder}/{name}.txt", 'w') as file:
        file.write(out)

async def it_gs (task: str, names: list[str], out_path: str, gpt: GPT) -> None:
    res = []
    for fn in names:
        res.append(get_write_subtasks(task, fn, out_path, gpt))
    await asyncio.wait(res)

async def it_gs_examples(examples_dict: dict, task: str, names: str | list[str], out_path: str, gpt: GPT) -> None:
    res = []
    for fn in names:
        gpt.convo.append(examples_dict) # type: ignore
        res.append(get_write_subtasks(task, fn, out_path, gpt))
        gpt.clear_convo()
    await asyncio.wait(res)

if __name__ == "__main__":
    gpt = GPT()


    img_folder = "imgs/subtasks_part_2"

    out_folder = "out/stable_2"

    
    
    # blocks = glob.glob(f"{img_folder}/*_block*")
    # # teas = glob.glob(f"{img_folder}/*_tea*")
    # # envelopes = glob.glob(f"{img_folder}/*_envelope*")
    # perspectives = glob.glob(f"{img_folder}/perspective*")
    # fixes = glob.glob(f"{img_folder}/fix_*")
    # fix_perspectives = glob.glob(f"{img_folder}/fix_tower_perspective*")
    # books = glob.glob(f"{img_folder}/books*")
    # tops = glob.glob(f"imgs/small_pinwheel_marked/*")
    # mistakes = glob.glob(f"{img_folder}/mistake*")
    # orders = glob.glob(f"imgs/marked_part_2/stack_order*")
    # no_tops = glob.glob(f"imgs/subtasks_part_2/no_top_*")
    # stack_gotos = glob.glob(f"imgs/combined/goto_order*")
    # insert_blocks = glob.glob(f"imgs/combined/insert_into*")
    # tops_lr = glob.glob("imgs/fix_top_exps/fix_top_lr*")
    # all_rulers = glob.glob("imgs/small_rulers/(locate_|measure_)*")
    # no_rulers = glob.glob("imgs/small_rulers/no_ruler*")
    # locate = glob.glob("imgs/small_rulers/locate_*")
    # progress = glob.glob("imgs/fix_top_exps/progress*")
    # tower_images = random.sample(list(glob.glob("imgs/tower_images/tower4/*")), 5)
    # stable_images = glob.glob("imgs/tower_stability/stable*")
    # stable_pairs = [(f"{i}_{j}", stable_images[i],stable_images[j]) for i in range(len(stable_images)) for j in range(i+1, len(stable_images))]
    # stable_combined_images = glob.glob("imgs/combined/stable_*")
    stable_images2 = glob.glob("imgs/tower_stability2/*")
    stable_pairs2 = [(f"{i}_{j}", stable_images2[i],stable_images2[j]) for i in range(len(stable_images2)) for j in range(i+1, len(stable_images2))]
    

    # combine_images_three(fix_perspectives, "imgs/combined/fix_tower.jpg")
    # combine_images_four(books, "imgs/combined/books.jpg")
    # combine_images_four(progress, "imgs/combined/progress_1.jpg")
    # combine_images_four(tower_images, f"imgs/combined/tower_comparisons_{random.randint(0,99)}.jpg")

    # combine_images_horizontally("imgs/marked/current.png", "imgs/small_subtasking/get_to_here.JPG", "imgs/combined/goto.jpg")
    # combine_images_horizontally("imgs/marked/current_2.png", "imgs/small_subtasking/get_to_here_2.JPG", "imgs/combined/goto_2.jpg")
    # combine_images_horizontally("imgs/marked/get_to_here_2.png", "imgs/small_subtasking/current_2.JPG", "imgs/combined/goto_2_reversed.jpg")
    # combine_images_horizontally("imgs/marked/lunch_1.png", "imgs/marked/lunch_2.png", "imgs/combined/lunch.png")
    # combine_images_horizontally(f"{img_folder}/current_2.jpg", f"{img_folder}/target_2.jpg", "imgs/combined/goto_3.jpg")
    # combine_images_horizontally(f"imgs/marked_part_2/stack_goto_start.png", f"imgs/small_subtasks_part_2/stack_goto_goal.jpg", "imgs/combined/goto_order_1.jpg")
    # combine_images_horizontally(f"imgs/marked_part_2/stack_goto_start_2.png", f"imgs/small_subtasks_part_2/stack_goto_goal_2.jpg", "imgs/combined/goto_order_2.jpg")
    # combine_images_horizontally(f"imgs/marked_part_2/stack_goto_start_3.png", f"imgs/small_subtasks_part_2/stack_goto_goal_3.jpg", "imgs/combined/goto_order_3.jpg")
    # combine_images_horizontally(f"imgs/marked_part_2/stack_goto_start_4.png", f"imgs/small_subtasks_part_2/stack_goto_goal_4.jpg", "imgs/combined/goto_order_4.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_5.png", f"imgs/small_subtasks_part_3/stack_goto_goal_5.jpg", "imgs/combined/goto_order_5.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_6.png", f"imgs/small_subtasks_part_3/stack_goto_end_6.jpg", "imgs/combined/goto_order_6.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_6.png", f"imgs/small_subtasks_part_3/stack_goto_end_6.5.jpg", "imgs/combined/goto_order_6.5.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_7.png", f"imgs/small_subtasks_part_3/stack_goto_end_7.jpg", "imgs/combined/goto_order_7.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_8.png", f"imgs/small_subtasks_part_3/stack_goto_end_8.jpg", "imgs/combined/goto_order_8.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_8.png", f"imgs/small_subtasks_part_3/stack_goto_end_8.5.jpg", "imgs/combined/goto_order_8.5.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/stack_goto_start_9.png", f"imgs/small_subtasks_part_3/stack_goto_end_9.jpg", "imgs/combined/goto_order_9.jpg")


    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_1.png", f"imgs/small_subtasks_part_3/block_4.jpg", "imgs/combined/insert_into_1.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_2.png", f"imgs/small_subtasks_part_3/block_2.jpg", "imgs/combined/insert_into_2.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_3.png", f"imgs/small_subtasks_part_3/block_3.jpg", "imgs/combined/insert_into_3.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_3.png", f"imgs/small_subtasks_part_3/block_1.jpg", "imgs/combined/insert_into_3.5.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_4.png", f"imgs/small_subtasks_part_3/block_2.jpg", "imgs/combined/insert_into_4.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_5.png", f"imgs/small_subtasks_part_3/block_4.jpg", "imgs/combined/insert_into_5.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_ex1.png", f"imgs/small_subtasks_part_3/block_1.jpg", "imgs/examples/insert_into_ex1.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/insert_into_ex2.png", f"imgs/small_subtasks_part_3/block_2.jpg", "imgs/examples/insert_into_ex2.jpg")

    # combine_images_horizontally(f"imgs/marked_part_3/cup_start.png", f"imgs/small_subtasks_part_3/cup_end.jpg", "imgs/combined/goto_cup.jpg")
    # combine_images_horizontally(f"imgs/marked_part_3/cup_start_2.png", f"imgs/small_subtasks_part_3/cup_end_2.jpg", "imgs/combined/goto_cup_2.jpg")

    # combine_images_horizontally(f"imgs/fix_top_exps/img_1.png", f"imgs/fix_top_exps/img_2.png", "imgs/combined/combined_arrows.jpg")

    # for stable_pair in stable_pairs:
    #     combine_images_horizontally(stable_pair[1], stable_pair[2], f"imgs/combined/stable_{stable_pair[0]}.jpg")
    for stable_pair in random.sample(stable_pairs2, 30):
        combine_images_horizontally(stable_pair[1], stable_pair[2], f"imgs/combined_2/stable_{stable_pair[0]}.jpg")
    
    # it_gs(FIX_TOP_PROMPT, tops, "out/pinwheel_marked", gpt)
    # it_gs(ORDER_PROMPT, orders, out_folder, gpt)
    # it_gs(MESAURE_PROMPT, all_rulers, out_folder, gpt)
    # it_gs(NO_RULER_PROMPT, no_rulers, out_folder, gpt)
    # it_gs(LOCATE_PROMPT, locate, out_folder, gpt)
    # it_gs(COMPARE_TOWERS_PROMPT, stable_combined_images, out_folder, gpt)
    
    # it_gs_examples(write_example_goto(ORDER_GOTO_PROMPT), "", stack_gotos, out_folder, gpt)
    # it_gs_examples(write_example_top(FIX_TOP_PROMPT), "", no_tops, out_folder, gpt)
    # it_gs_examples(write_example_insert_into(INSERT_BLOCKS), "", insert_blocks, out_folder, gpt)
    # it_gs_examples(write_example_top_lr(FIX_TOP_LR_PROMPT), "", tops_lr, out_folder, gpt)
    # it_gs("Ignoring depth, is the top block centered? If not, in what direction (left or right) is it offset?", tops_lr, out_folder, gpt)
    # it_gs(RAVEN_PROMPT, no_tops, out_folder, gpt)
    
    # it_gs("Stack the blocks", blocks, out_folder, gpt)
    # it_gs("Where should I interact with the tower to stabilize it?", fixes, out_folder, gpt)
    # it_gs("Make some tea", teas, out_folder, gpt)
    # it_gs("Put my paperwork in the envelope and close it.", envelopes, out_folder, gpt)
    

    # for i, mistake in enumerate(sorted(mistakes)):
    #     print(f"i: {i}, {os.path.basename(mistake)}")
    #     get_write_subtasks(WHERE_MISTAKE_PROMPT + MISTAKE_STEPS[i], mistake, out_folder, gpt)

    # get_write_subtasks(ORDER_GOTO_PROMPT, f"imgs/combined/goto_order_1.jpg", out_folder, gpt)
    # get_write_subtasks(ORDER_PROMPT, f"{img_folder}/stack_order_3.png", out_folder, gpt)
    # get_write_subtasks(WHERE_MISTAKE_PROMPT + MISTAKE_STEPS[1], f"{img_folder}/mistake_2.jpg", out_folder, gpt)
    # get_write_subtasks("Make me lunch" + MULTI_VIEW_WARNING, "imgs/combined/lunch.png", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto.jpg", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto_2.jpg", out_folder, gpt)
    # get_write_subtasks(GOTO_PROMPT, "imgs/combined/goto_2_reversed.jpg", out_folder, gpt)
    # get_write_subtasks("Where should I push, pull or rotate to stabilize the tower?" + MULTI_VIEW_WARNING, "imgs/combined/fix_tower.jpg", out_folder, gpt)    
    # get_write_subtasks("Where should I push to align the books?" + MULTI_VIEW_WARNING, books, out_folder, gpt)
    # get_write_subtasks("Stack the blocks without breaking the glass.", f"{img_folder}/glass-block.png", out_folder, gpt)
    # get_write_subtasks("Arrange the pens in a figure 8 pattern.", f"{img_folder}/pens.png", out_folder, gpt)
    # get_write_subtasks("Stack the blocks", perspectives, out_folder, gpt)
    # get_write_subtasks("Where should I interact with the books to align them?", books, out_folder, gpt)

    # get_write_subtasks(ORDER_GOTO_PROMPT, "imgs/combined/goto_cup_2.jpg", out_folder, gpt)

    # get_write_subtasks("Put the shark to bed", f"{img_folder}/shark.png", out_folder, gpt)
    # get_write_subtasks("I'm hungry", f"{img_folder}/shark.png", out_folder, gpt)
    # it_gs("Make me lunch", [[f"{img_folder}/lunch1.png",f"{img_folder}/lunch2.png"], f"{img_folder}/lunch2.png"], out_folder, gpt) # type: ignore
    

    # curr_img = "block_envelope"
    # img_folder = "imgs/subtasking/"
    # out = get_subtasks("Put my paperwork into the envelope and close it.", f"{img_folder}{curr_img}.jpg", gpt)
    # # out = get_subtasks("Make me lunch", [f"{img_folder}lunch1.jpg", f"{img_folder}lunch2.jpg"], gpt)
    # print(out)
    #     file.write(out)
    # with open(f"out/subtasks/{curr_img}.txt", 'w') as file: