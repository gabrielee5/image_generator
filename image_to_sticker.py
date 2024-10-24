import replicate
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json
from glob import glob
import base64

# FAILS TO GENERATE, same problem in the replicate webapp

# Load environment variables from .env file
load_dotenv()

def get_images_from_folder(folder_path):
    """Get list of images from the specified folder"""
    # Supported image formats
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = []
    for ext in image_extensions:
        images.extend(glob(os.path.join(folder_path, ext)))
    return sorted(images)  # Sort for consistent ordering

def select_image(images):
    """Present a menu for image selection"""
    if not images:
        raise Exception("No images found in the upload folder")
    
    print("\nAvailable images:")
    for i, image_path in enumerate(images, 1):
        print(f"{i}. {os.path.basename(image_path)}")
    
    while True:
        try:
            choice = int(input("Enter the number of the image to use: "))
            if 1 <= choice <= len(images):
                return images[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def generate_sticker(image_path, prompt, prompt_strength=4.5, instant_id_strength=0.7):
    """
    Generate sticker using Replicate API
    :param image_path: Path to the input image
    :param prompt: The text prompt for sticker style
    :param prompt_strength: Strength of the prompt (default: 4.5)
    :param instant_id_strength: Strength of identity preservation (default: 0.7)
    """
    try:
        # Read and encode the image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            image_uri = f"data:image/jpeg;base64,{image_data}"
        
        input_params = {
            "image": image_uri,
            "prompt": prompt,
            "prompt_strength": float(prompt_strength),
            "instant_id_strength": float(instant_id_strength)
        }
        
        output = replicate.run(
            "fofr/face-to-sticker:764d4827ea159608a07cdde8ddf1c6000019627515eb02b6b449695fd547e5ef",
            input=input_params
        )
        
        return str(output) if output else None
    except Exception as e:
        print(f"Error generating sticker: {e}")
        return None

def save_image(url, folder, prefix="sticker"):
    """Save an image from URL to the specified folder"""
    response = requests.get(url)
    if response.status_code == 200:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Sticker saved: {filepath}")
        return filepath
    else:
        print(f"Failed to download sticker from {url}")
        return None

def save_request_log(log_data, logs_folder="logs", log_file_name="sticker_generation_log.json"):
    """Save the request log to a single JSON file in the logs folder"""
    os.makedirs(logs_folder, exist_ok=True)
    log_file_path = os.path.join(logs_folder, log_file_name)

    if isinstance(log_data.get('timestamp'), datetime):
        log_data['timestamp'] = log_data['timestamp'].isoformat()
    
    def sanitize_for_json(obj):
        if isinstance(obj, (datetime, bytes)):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [sanitize_for_json(item) for item in obj]
        else:
            return str(obj) if hasattr(obj, '__dict__') else obj

    log_data = sanitize_for_json(log_data)

    try:
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Existing log file was corrupted. Creating new log.")
                existing_data = []
        else:
            existing_data = []
        
        existing_data.append(log_data)
        
        with open(log_file_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"Request log saved to {log_file_path}")
    except Exception as e:
        print(f"Error saving log: {e}")

def get_style_prompt():
    """Present a menu for sticker style selection"""
    style_options = {
        1: "cartoon",
        2: "anime",
        3: "pixar",
        4: "disney",
        5: "south park",
        6: "rick and morty",
        7: "custom"  # Allow custom prompt input
    }
    
    while True:
        print("\nChoose a sticker style:")
        for num, style in style_options.items():
            print(f"{num}. {style}")
        
        try:
            choice = int(input("Enter the number of your choice: "))
            if choice in style_options:
                if choice == 7:  # Custom prompt
                    return input("Enter your custom style prompt: ")
                return style_options[choice]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    # Check for API key
    replicate_api_key = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_api_key:
        print("REPLICATE_API_TOKEN not found in environment variables. Please check your .env file.")
        exit(1)

    # Create necessary folders
    sticker_folder = "all_output/generated_stickers"
    upload_folder = "images_to_upload"
    logs_folder = "logs"
    
    os.makedirs(sticker_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)

    # Get list of images from upload folder
    try:
        available_images = get_images_from_folder(upload_folder)
        if not available_images:
            print(f"No images found in {upload_folder}. Please add some images and try again.")
            exit(1)
            
        # Select image to process
        selected_image = select_image(available_images)
        print(f"\nSelected image: {os.path.basename(selected_image)}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    # Get generation parameters
    style_prompt = get_style_prompt()
    
    # Optional parameters with defaults
    try:
        prompt_strength = float(input("Enter prompt strength (0-10, default 4.5) or press Enter: ") or 4.5)
        instant_id_strength = float(input("Enter identity preservation strength (0-1, default 0.7) or press Enter: ") or 0.7)
    except ValueError:
        print("Invalid input. Using default values.")
        prompt_strength = 4.5
        instant_id_strength = 0.7

    print("\nGenerating sticker...")
    sticker_url = generate_sticker(
        selected_image, 
        style_prompt,
        prompt_strength,
        instant_id_strength
    )

    if sticker_url:
        # Save generated sticker
        saved_path = save_image(sticker_url, sticker_folder)
        
        if saved_path:
            print(f"\nSticker saved successfully to: {saved_path}")
            
            # Prepare and save log data
            log_data = {
                "timestamp": datetime.now(),
                "input_image": selected_image,
                "style_prompt": style_prompt,
                "prompt_strength": prompt_strength,
                "instant_id_strength": instant_id_strength,
                "output_image": saved_path,
                "sticker_url": sticker_url
            }
            save_request_log(log_data)
    else:
        print("Failed to generate sticker.")