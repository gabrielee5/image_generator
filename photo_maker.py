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

def get_subfolders(base_folder):
    """Get list of subfolders from the base folder"""
    try:
        subfolders = [f for f in os.listdir(base_folder) 
                     if os.path.isdir(os.path.join(base_folder, f))]
        return sorted(subfolders)
    except Exception as e:
        print(f"Error reading subfolders: {e}")
        return []

def select_folder(subfolders):
    """Present a menu for folder selection"""
    if not subfolders:
        raise Exception("No subfolders found in the upload folder")
    
    print("\nAvailable folders:")
    for i, folder in enumerate(subfolders, 1):
        print(f"{i}. {folder}")
    
    while True:
        try:
            choice = int(input("Enter the number of the folder to use: "))
            if 1 <= choice <= len(subfolders):
                return subfolders[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_images_from_folder(folder_path):
    """Get all images from the specified folder"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = []
    for ext in image_extensions:
        images.extend(glob(os.path.join(folder_path, ext)))
    return sorted(images)

def encode_image_to_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"

def generate_photo(
    input_images,
    prompt="A photo of a person img",
    num_steps=20,
    style_name="Photographic (Default)",
    num_outputs=1,
    guidance_scale=5,
    negative_prompt=None,
    style_strength_ratio=20,
    seed=None,
    disable_safety_checker=False
):
    """Generate photos using Replicate's PhotoMaker API"""
    try:
        # Take up to first 4 images from the folder
        input_images = input_images[:4]
        print(f"Using {len(input_images)} images from the folder")

        # Prepare input parameters
        input_params = {
            "prompt": prompt,
            "num_steps": num_steps,
            "style_name": style_name,
            "num_outputs": num_outputs,
            "guidance_scale": guidance_scale,
            "style_strength_ratio": style_strength_ratio,
            "disable_safety_checker": disable_safety_checker
        }

        # Add main input image
        input_params["input_image"] = encode_image_to_base64(input_images[0])
        
        # Add additional images if available
        for i, img_path in enumerate(input_images[1:], 2):
            input_params[f"input_image{i}"] = encode_image_to_base64(img_path)

        # Add optional parameters
        if seed is not None:
            input_params["seed"] = seed
        if negative_prompt:
            input_params["negative_prompt"] = negative_prompt
        
        output = replicate.run(
            "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4",
            input=input_params
        )
        
        return output
    except Exception as e:
        print(f"Error generating photo: {e}")
        return None

def save_image(url, folder, prefix="photomaker"):
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

def save_request_log(log_data, logs_folder="logs", log_file_name="photomaker_log.json"):
    """Save the request log to a JSON file"""
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
    """Present a menu for style selection"""
    styles = [
        "Photographic (Default)",
        "(No style)",
        "Cinematic",
        "Disney Charactor",
        "Digital Art",
        "Fantasy art",
        "Neonpunk",
        "Enhance",
        "Comic book",
        "Lowpoly",
        "Line art"
    ]
    
    print("\nAvailable styles:")
    for i, style in enumerate(styles, 1):
        print(f"{i}. {style}")
    
    while True:
        try:
            choice = int(input("Enter the number of your style choice: "))
            if 1 <= choice <= len(styles):
                return styles[choice - 1]
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
    output_folder = "all_output/photo_maker"
    upload_folder = "images_to_upload"
    logs_folder = "logs"
    
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)

    try:
        # Get available subfolders
        subfolders = get_subfolders(upload_folder)
        if not subfolders:
            print(f"No subfolders found in {upload_folder}. Please create subfolders with images and try again.")
            exit(1)
        
        # Select folder
        selected_folder = select_folder(subfolders)
        folder_path = os.path.join(upload_folder, selected_folder)
        
        # Get all images from selected folder
        images = get_images_from_folder(folder_path)
        if not images:
            print(f"No images found in {folder_path}. Please add images and try again.")
            exit(1)
            
        print(f"\nFound {len(images)} images in {selected_folder}")
        if len(images) > 4:
            print("Note: Only the first 4 images will be used due to API limitations")
        
        # Get generation parameters
        prompt = input("\nEnter prompt (default: 'A photo of a person img'): ") or "A photo of a person img"
        if "img" not in prompt:
            print("Warning: Adding 'img' trigger word to prompt")
            prompt += " img"
            
        style_name = get_style_choice()
        
        # Get optional parameters
        print("\nOptional parameters (press Enter for defaults):")
        
        try:
            num_steps = int(input("Number of steps (1-100, default 20): ") or 20)
            num_outputs = int(input("Number of outputs (1-4, default 1): ") or 1)
            guidance_scale = float(input("Guidance scale (1-10, default 5): ") or 5)
            style_strength_ratio = float(input("Style strength % (15-50, default 20): ") or 20)
            seed = input("Seed (optional, press Enter for random): ")
            seed = int(seed) if seed else None
            
            default_negative = "nsfw, lowres, bad anatomy, bad hands, bad eyes, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
            use_default_negative = input("Use default negative prompt? (y/n, default: y): ").lower() != 'n'
            negative_prompt = default_negative if use_default_negative else input("Enter custom negative prompt: ")
            
            disable_safety = input("Disable safety checker? (y/n, default: n): ").lower() == 'y'
            
        except ValueError:
            print("Invalid input. Using default values.")
            num_steps = 20
            num_outputs = 1
            guidance_scale = 5
            style_strength_ratio = 20
            seed = None
            negative_prompt = default_negative
            disable_safety = False

        print("\nGenerating photos...")
        output_urls = generate_photo(
            images,
            prompt=prompt,
            num_steps=num_steps,
            style_name=style_name,
            num_outputs=num_outputs,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
            style_strength_ratio=style_strength_ratio,
            seed=seed,
            disable_safety_checker=disable_safety
        )

        if output_urls:
            saved_paths = []
            for i, url in enumerate(output_urls, 1):
                saved_path = save_image(url, output_folder, f"photomaker_{selected_folder}_{i}")
                if saved_path:
                    saved_paths.append(saved_path)

            if saved_paths:
                print(f"\nSaved {len(saved_paths)} images successfully.")
                
                # Prepare and save log data
                log_data = {
                    "timestamp": datetime.now(),
                    "input_folder": selected_folder,
                    "input_images": images[:4],  # Log only the used images
                    "prompt": prompt,
                    "style_name": style_name,
                    "num_steps": num_steps,
                    "num_outputs": num_outputs,
                    "guidance_scale": guidance_scale,
                    "style_strength_ratio": style_strength_ratio,
                    "seed": seed,
                    "negative_prompt": negative_prompt,
                    "disable_safety_checker": disable_safety,
                    "output_images": saved_paths,
                    "output_urls": output_urls
                }
                save_request_log(log_data)
            else:
                print("Failed to save any generated images.")
        else:
            print("Failed to generate photos.")
            
    except Exception as e:
        print(f"An error occurred: {e}")