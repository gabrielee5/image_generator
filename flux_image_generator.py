import fal_client
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import base64

# Load environment variables from .env file
load_dotenv()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def generate_image(prompt, input_image_path=None, image_size="landscape_4_3", num_images=1):
    """
    :param image_size: options: square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9
    """
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    arguments = {
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images,
        "enable_safety_checker": False,
        "safety_tolerance": "6"
    }

    if input_image_path:
        base64_image = encode_image_to_base64(input_image_path)
        arguments["image"] = f"data:image/jpeg;base64,{base64_image}"

    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1",
        arguments=arguments,
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    
    return result

def save_image(url, folder):
    response = requests.get(url)
    if response.status_code == 200:
        # Generate a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_image_{timestamp}.jpg"
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Image saved: {filepath}")
        return filepath
    else:
        print(f"Failed to download image from {url}")
        return None

if __name__ == "__main__":
    # Check if FAL_KEY is in the environment variables
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("FAL_KEY not found in environment variables. Please check your .env file.")
        exit(1)

    # Create a folder to store the images
    image_folder = "generated_images"
    os.makedirs(image_folder, exist_ok=True)

    prompt = input("Insert Prompt: ")
    input_image_path = "path/to/your/input/image.jpg"  # Replace with your input image path

    result = generate_image(prompt, 'portrait_16_9')
    
    # Print the result
    result = generate_image(prompt, input_image_path)

    print(result)

    saved_images = []
    for image in result['images']:
        saved_path = save_image(image['url'], image_folder)
        if saved_path:
            saved_images.append(saved_path)

    print(f"\nSaved {len(saved_images)} images in the '{image_folder}' folder.")