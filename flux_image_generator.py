import fal_client
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import base64
from glob import glob
import json

# Load environment variables from .env file
load_dotenv()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_images_from_folder(folder_path):
    # Supported image formats
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    images = []
    for ext in image_extensions:
        images.extend(glob(os.path.join(folder_path, ext)))
    return images

def generate_image(prompt, input_images=None, image_size="landscape_4_3", num_images=1):
    """
    :param prompt: The text prompt for image generation
    :param input_images: List of paths to input images
    :param image_size: options: square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9
    :param num_images: Number of images to generate
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
        "safety_tolerance": "6" # max freedom
    }

    if input_images:
        # If multiple images are provided, we'll use the first one
        # You might want to implement a strategy for handling multiple images
        base64_image = encode_image_to_base64(input_images[0])
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

def save_request_log(log_data, log_file="request_log.json"):
    """
    Save the request log to a JSON file.
    If the file exists, it appends the new data to the existing log.
    """
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    existing_data.append(log_data)
    
    with open(log_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"Request log saved to {log_file}")

def get_image_size_choice():
    """
    Present a menu for image size selection and return the chosen size.
    """
    size_options = [
        "square_hd",
        "square",
        "portrait_4_3",
        "portrait_16_9",
        "landscape_4_3",
        "landscape_16_9"
    ]
    
    while True:
        print("\nChoose an image size:")
        for i, size in enumerate(size_options, 1):
            print(f"{i}. {size}")
        
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(size_options):
                return size_options[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("FAL_KEY not found in environment variables. Please check your .env file.")
        exit(1)

    image_folder = "generated_images"
    os.makedirs(image_folder, exist_ok=True)

    upload_folder = "images_to_upload"
    use_uploaded_images = input("Do you want to use uploaded images? (yes/no): ").lower() == 'yes'

    input_images = None
    if use_uploaded_images:
        if os.path.exists(upload_folder):
            subfolder = input(f"Enter the name of the subfolder within '{upload_folder}' (or press Enter for root): ").strip()
            full_path = os.path.join(upload_folder, subfolder) if subfolder else upload_folder
            
            if os.path.exists(full_path):
                input_images = get_images_from_folder(full_path)
                if not input_images:
                    print(f"No images found in {full_path}. Proceeding without input images.")
            else:
                print(f"Folder {full_path} not found. Proceeding without input images.")
        else:
            print(f"Folder {upload_folder} not found. Proceeding without input images.")

    prompt = input("Insert Prompt: ")
    image_size = get_image_size_choice()
    num_images = int(input("Enter number of images to generate: "))

    result = generate_image(prompt, input_images, image_size, num_images)

    print(result)

    saved_images = []
    for image in result['images']:
        saved_path = save_image(image['url'], image_folder)
        if saved_path:
            saved_images.append(saved_path)

    print(f"\nSaved {len(saved_images)} images in the '{image_folder}' folder.")

    # Prepare log data
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images,
        "input_images": input_images,
        "output_images": saved_images,
        "api_response": result
    }

    # Save log data
    save_request_log(log_data)