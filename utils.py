from PIL import Image, ImageDraw, ImageFont
from typing import Tuple

def combine_images_horizontally(
    img1_path: str, 
    img2_path: str, 
    output_path: str
) -> None:
    """
    Combines two images horizontally and labels them with numbers '1' and '2' 
    in the top left corner of each image.
    
    Parameters:
    img1_path (str): Path to the first image.
    img2_path (str): Path to the second image.
    output_path (str): Path to save the combined image.
    
    Returns:
    None
    """
    
    # Open the images
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    # Get the dimensions of the images
    width1, height1 = img1.size
    width2, height2 = img2.size

    # Create a new image with a width that is the sum of both images' widths and the height of the tallest image
    combined_width = width1 + width2
    combined_height = max(height1, height2)
    combined_img = Image.new('RGB', (combined_width, combined_height))

    # Paste the images into the new image
    combined_img.paste(img1, (0, 0))
    combined_img.paste(img2, (width1, 0))

    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", 300)
    except IOError:
        font = ImageFont.load_default(300)

    # Create a draw object
    draw = ImageDraw.Draw(combined_img)

    # Draw the labels on the images with a background rectangle for visibility
    def draw_label(draw: ImageDraw.ImageDraw, position: Tuple[int, int], text: str) -> None:
        x, y = position
        text_bbox = draw.textbbox((x, y), text, font=font)
        draw.rectangle(text_bbox, fill="white")
        draw.text((x, y), text, font=font, fill="black")

    draw_label(draw, (10, 10), "1")
    draw_label(draw, (width1 + 10, 10), "2")

    # Save the combined image
    combined_img.save(output_path)

def resize_image(input_path, output_path, target_height=1024):
    # Open an image file
    with Image.open(input_path) as img:
        # Calculate the new width to maintain the aspect ratio
        aspect_ratio = img.width / img.height
        new_width = int(target_height * aspect_ratio)
        
        # Resize the image
        img = img.resize((new_width, target_height))
        
        # Save the resized image
        img.save(output_path)


def combine_images_four(image_paths, output_path):
    # Open the images
    images = [Image.open(path) for path in image_paths]

    # Find the maximum width and height of all images
    widths, heights = zip(*(img.size for img in images))
    max_width = max(widths)
    max_height = max(heights)

    # Create a new blank image with the size to fit 2x2 grid of images
    combined_image = Image.new('RGB', (2 * max_width, 2 * max_height), (255, 255, 255))

    # Define positions for each image
    positions = [(0, 0), (max_width, 0), (0, max_height), (max_width, max_height)]

    # Paste images and label them
    for i, (img, pos) in enumerate(zip(images, positions)):
        combined_image.paste(img, pos)
        draw = ImageDraw.Draw(combined_image)
        label = str(i + 1)

        # Font and size for the label
        try:
            font = ImageFont.truetype("arial.ttf", 200)
        except IOError:
            font = ImageFont.load_default(200)

        # Calculate the bounding box for the text
        text_position = (pos[0] + 10, pos[1] + 10)
        bbox = draw.textbbox(text_position, label, font=font)
        
        # Draw white rectangle behind the label
        draw.rectangle(bbox, fill="white")
        
        # Draw the label
        draw.text(text_position, label, fill="black", font=font)

    # Save the combined image
    combined_image.save(output_path)
    print(f"Combined image saved as {output_path}")

def combine_images_three(image_paths, output_path):
    # Open the images
    images = [Image.open(path) for path in image_paths]

    # Find the maximum width and the total height of all images
    widths, heights = zip(*(img.size for img in images))
    max_width = max(widths)
    total_height = sum(heights)

    # Create a new blank image with the size to fit all images vertically
    combined_image = Image.new('RGB', (max_width, total_height), (255, 255, 255))

    # Define the starting y position for each image
    y_offset = 0

    for i, img in enumerate(images):
        combined_image.paste(img, (0, y_offset))
        draw = ImageDraw.Draw(combined_image)
        label = str(i + 1)

        # Font and size for the label
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default(200)

        # Calculate the bounding box for the text
        text_position = (10, y_offset + 10)
        bbox = draw.textbbox(text_position, label, font=font)
        
        # Draw white rectangle behind the label
        draw.rectangle(bbox, fill="white")
        
        # Draw the label
        draw.text(text_position, label, fill="black", font=font)

        # Update the y position for the next image
        y_offset += img.height

    # Save the combined image
    combined_image.save(output_path)
    print(f"Combined image saved as {output_path}")