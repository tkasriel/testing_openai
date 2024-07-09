import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple
import PIL
import cv2

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
        font = ImageFont.load_default(80)

    # Create a draw object
    draw = ImageDraw.Draw(combined_img)

    # Draw the labels on the images with a background rectangle for visibility
    def draw_label(draw: ImageDraw.ImageDraw, position: Tuple[int, int], text: str) -> None:
        x, y = position
        text_bbox = draw.textbbox((x, y), text, font=font)
        draw.rectangle(text_bbox, fill="white")
        draw.text((x, y), text, font=font, fill="black")

    draw_label(draw, (10, 0), "1")
    draw_label(draw, (width1 + 10, 0), "2")

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
            font = ImageFont.load_default(400)

        # Calculate the bounding box for the text
        text_position = (pos[0] + 40, pos[1] + 40)
        bbox = draw.textbbox(text_position, label, font=font)
        bbox = (bbox[0] - 50, bbox[1] - 50, bbox[2] + 50, bbox[3] + 50)

        # Draw white rectangle behind the label
        draw.rectangle(bbox, fill="white", outline="black", width=10)
        
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

def draw_arrows_on_image(input_file_path, output_file_path, arrow_length=300, label_offset=50):
    # Read the input image
    image = cv2.imread(input_file_path)

    # Check if the image was loaded correctly
    if image is None:
        raise FileNotFoundError(f"The image at {input_file_path} could not be loaded.")
    
    # Get the image dimensions
    height, width, _ = image.shape

    # Define the start point in the bottom left
    start_point = (150 + arrow_length, height - (150 + arrow_length))

    # Define the directions and their corresponding labels
    directions = {
        'A': (0, -arrow_length),    # Up
        'B': (arrow_length, -arrow_length),  # Up-Right
        'C': (arrow_length, 0),     # Right
        'D': (arrow_length, arrow_length),   # Down-Right
        'E': (0, arrow_length),     # Down
        'F': (-arrow_length, arrow_length),  # Down-Left
        'G': (-arrow_length, 0),    # Left
        'H': (-arrow_length, -arrow_length)  # Up-Left
    }

    # Determine the size of the rectangle based on arrow lengths
    rect_width = arrow_length * 2 + label_offset * 2
    rect_height = arrow_length * 2 + label_offset * 2

    # Draw a white rectangle as the background for the arrows and labels
    cv2.rectangle(image, (start_point[0] - arrow_length - label_offset, start_point[1] - arrow_length - label_offset), 
                  (start_point[0] + arrow_length + label_offset, start_point[1] + arrow_length + label_offset), (255, 255, 255), -1)

    # Draw the arrows and labels
    for label, (dx, dy) in directions.items():
        end_point = (start_point[0] + dx, start_point[1] + dy)
        image = cv2.arrowedLine(image, start_point, end_point, (0, 0, 0), 2, tipLength=0.3)
        label_position = (end_point[0] + dx // 5, end_point[1] + dy // 5)
        image = cv2.putText(image, label, label_position, cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 0), 2)

    # Save the image to the specified file path
    cv2.imwrite(output_file_path, image)

def encode_image(image: Image.Image):
    buffered = BytesIO()
    image.save(buffered, format='JPEG')
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def encode_file(image_file: str):
    image = Image.open(image_file)
    return encode_image(image)