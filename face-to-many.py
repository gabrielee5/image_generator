import replicate
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json
from glob import glob
import base64

# Load environment variables from .env file
load_dotenv()

def get_images_from_folder(folder_path):
    """Get list of images from the specified folder"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = []
    for ext in image_extensions:
        images.extend(glob(os.path.join(folder_path, ext)))
    return sorted(images)

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

def generate_transformed_face(
    image_path,
    style="3D",
    prompt="a person",
    seed=None,
    lora_scale=1.0,
    custom_lora_url=None,
    negative_prompt=None,
    prompt_strength=4.5,
    denoising_strength=0.65,
    instant_id_strength=1.0,
    control_depth_strength=0.8
):
    """
    Generate transformed face using Replicate API
    """
    try:
        # Read and encode the image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            image_uri = f"data:image/jpeg;base64,{image_data}"
        
        # Build input parameters
        input_params = {
            "image": image_uri,
            "style": style,
            "prompt": prompt,
            "instant_id_strength": float(instant_id_strength),
            "prompt_strength": float(prompt_strength),
            "denoising_strength": float(denoising_strength),
            "control_depth_strength": float(control_depth_strength),
            "lora_scale": float(lora_scale)
        }

        # Add optional parameters if provided
        if seed is not None:
            input_params["seed"] = int(seed)
        if custom_lora_url:
            input_params["custom_lora_url"] = custom_lora_url
        if negative_prompt:
            input_params["negative_prompt"] = negative_prompt
        
        output = replicate.run(
            "fofr/face-to-many:a07f252abbbd832009640b27f063ea52d87d7a23a185ca165bec23b5adc8deaf",
            input=input_params
        )
        
        # Handle the output properly
        if isinstance(output, list):
            # If output is a list, take the first URL
            return output[0] if output else None
        elif hasattr(output, 'url'):
            # If output has a url attribute
            return output.url
        else:
            # Convert the output to string if it's something else
            return str(output)
    except Exception as e:
        print(f"Error generating transformed image: {e}")
        return None

def save_image(url, folder, prefix="transformed"):
    """Save an image from URL to the specified folder"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            filepath = os.path.join(folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Image saved: {filepath}")
            return filepath
        else:
            print(f"Failed to download image from {url}")
            return None
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def save_request_log(log_data, logs_folder="logs", log_file_name="face_transformation_log.json"):
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
        elif hasattr(obj, 'url'):  # Handle FileOutput objects
            return obj.url
        else:
            return str(obj) if hasattr(obj, '__dict__') else obj

    log_data = sanitize_for_json(log_data)

    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        existing_data.append(log_data)
        
        with open(log_file_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"Request log saved to {log_file_path}")
    except Exception as e:
        print(f"Error saving log: {e}")

def get_style_choice():
    """Present a menu for transformation style selection"""
    style_options = {
        1: "3D",
        2: "Pixels",  # Changed from "Pixel"
        3: "Clay",
        4: "Video game",  # Changed from "Digital Art"
        5: "Emoji",  # Changed from "Neon"
        6: "Toy",    # Changed from "Anime"
    }
    
    while True:
        print("\nChoose a transformation style:")
        print("Available styles:")
        for num, style in style_options.items():
            print(f"{num}. {style}")
        
        try:
            choice = int(input("Enter the number of your choice: "))
            if choice in style_options:
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
    output_folder = "all_output/transformed_images"
    upload_folder = "images_to_upload"
    logs_folder = "logs"
    
    os.makedirs(output_folder, exist_ok=True)
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

    # Get transformation parameters
    style = get_style_choice()
    prompt = input("\nEnter prompt (default: 'a person'): ") or "a person"
    
    # Optional parameters with defaults
    try:
        print("\nOptional parameters (press Enter for defaults):")
        seed = input("Random seed for reproducibility (optional): ") or None
        if seed:
            seed = int(seed)
        
        lora_scale = float(input("LoRA strength (0-1, default 1.0): ") or 1.0)
        custom_lora_url = input("Custom LoRA URL (optional): ") or None
        negative_prompt = input("Negative prompt (optional): ") or None
        prompt_strength = float(input("Prompt strength (0-20, default 4.5): ") or 4.5)
        denoising_strength = float(input("Denoising strength (0-1, default 0.65): ") or 0.65)
        instant_id_strength = float(input("InstantID strength (0-1, default 1.0): ") or 1.0)
        control_depth_strength = float(input("Depth control strength (0-1, default 0.8): ") or 0.8)
        
    except ValueError:
        print("Invalid input. Using default values.")
        seed = None
        lora_scale = 1.0
        custom_lora_url = None
        negative_prompt = None
        prompt_strength = 4.5
        denoising_strength = 0.65
        instant_id_strength = 1.0
        control_depth_strength = 0.8

    print("\nGenerating transformed image...")
    output_url = generate_transformed_face(
        selected_image,
        style=style,
        prompt=prompt,
        seed=seed,
        lora_scale=lora_scale,
        custom_lora_url=custom_lora_url,
        negative_prompt=negative_prompt,
        prompt_strength=prompt_strength,
        denoising_strength=denoising_strength,
        instant_id_strength=instant_id_strength,
        control_depth_strength=control_depth_strength
    )

    print(f"Generated URL: {output_url}")  # Debug line

    if output_url:
        # Save generated image
        saved_path = save_image(output_url, output_folder)
        
        if saved_path:
            print(f"\nTransformed image saved successfully to: {saved_path}")
            
            # Prepare and save log data
            log_data = {
                "timestamp": datetime.now(),
                "input_image": selected_image,
                "style": style,
                "prompt": prompt,
                "seed": seed,
                "lora_scale": lora_scale,
                "custom_lora_url": custom_lora_url,
                "negative_prompt": negative_prompt,
                "prompt_strength": prompt_strength,
                "denoising_strength": denoising_strength,
                "instant_id_strength": instant_id_strength,
                "control_depth_strength": control_depth_strength,
                "output_image": saved_path,
                "output_url": output_url
            }
            save_request_log(log_data)
    else:
        print("Failed to generate transformed image.")