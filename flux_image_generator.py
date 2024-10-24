import fal_client
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json

# Load environment variables from .env file
load_dotenv()

def generate_image(prompt, image_size="landscape_4_3", num_images=1, seed=None):
    """
    Generate images using fal.ai API
    :param prompt: The text prompt for image generation
    :param image_size: options: square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9
    :param num_images: Number of images to generate
    :param seed: Random number. With the same seed and the same prompt the image is always the same
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
        "safety_tolerance": "6",  # max freedom
        "seed": seed
    }

    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1",
        arguments=arguments,
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    
    return result

def save_image(url, folder):
    """Save an image from URL to the specified folder"""
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

def save_request_log(log_data, log_file="request_log.json", logs_folder="logs"):
    """
    Save the request log to a JSON file.
    If the file exists, it appends the new data to the existing log.
    """
    # Create logs folder if it doesn't exist
    os.makedirs(logs_folder, exist_ok=True)

    log_file_path = os.path.join(logs_folder, log_file)

    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    existing_data.append(log_data)
    
    with open(log_file_path, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"Request log saved to {log_file_path}")

def get_image_size_choice():
    """Present a menu for image size selection and return the chosen size"""
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
    # Check for API key
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("FAL_KEY not found in environment variables. Please check your .env file.")
        exit(1)

    # Create output folder
    image_folder = "all_output/generated_images"
    os.makedirs(image_folder, exist_ok=True)

    # Get generation parameters
    prompt = input("Insert Prompt: ")
    image_size = get_image_size_choice()
    num_images = int(input("Enter number of images to generate: "))

    # Generate images
    result = generate_image(prompt, image_size, num_images)
    print(result)

    # Save generated images
    saved_images = []
    for image in result['images']:
        saved_path = save_image(image['url'], image_folder)
        if saved_path:
            saved_images.append(saved_path)

    print(f"\nSaved {len(saved_images)} images in the '{image_folder}' folder.")

    # Prepare and save log data
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images,
        "output_images": saved_images,
        "api_response": result
    }
    save_request_log(log_data)