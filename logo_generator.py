import replicate
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import json

# Load environment variables from .env file
load_dotenv()

def generate_logo(prompt, num_variations=1, style_suffix=""):
    """
    Generate logo using Replicate API
    :param prompt: The text prompt for logo generation
    :param num_variations: Number of variations to generate
    :param style_suffix: Optional style modifier to append to the prompt
    """
    # Enhance prompt with style suffix if provided
    full_prompt = f"{prompt} {style_suffix}".strip()
    
    # List to store all generated URLs
    all_outputs = []
    
    # Generate specified number of variations
    for _ in range(num_variations):
        input_params = {
            "prompt": full_prompt,
        }
        
        try:
            output = replicate.run(
                "mejiabrayan/logoai:67ed00e8999fecd32035074fa0f2e9a31ee03b57a8415e6a5e2f93a242ddd8d2",
                input=input_params
            )
            # Convert the output to a list of strings if it isn't already
            if isinstance(output, (list, tuple)):
                all_outputs.extend([str(url) for url in output])
            else:
                all_outputs.append(str(output))
        except Exception as e:
            print(f"Error generating logo: {e}")
    
    return all_outputs

def save_image(url, folder, prefix="logo"):
    """Save an image from URL to the specified folder"""
    response = requests.get(url)
    if response.status_code == 200:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Logo saved: {filepath}")
        return filepath
    else:
        print(f"Failed to download logo from {url}")
        return None

def save_request_log(log_data, logs_folder="logs", log_file_name="logo_generation_log.json"):
    """
    Save the request log to a single JSON file in the logs folder.
    Appends new data to existing log file.
    """
    # Create logs folder if it doesn't exist
    os.makedirs(logs_folder, exist_ok=True)
    
    log_file_path = os.path.join(logs_folder, log_file_name)

    # Convert datetime to string if it exists in log_data
    if isinstance(log_data.get('timestamp'), datetime):
        log_data['timestamp'] = log_data['timestamp'].isoformat()
    
    # Ensure all data is JSON serializable
    def sanitize_for_json(obj):
        if isinstance(obj, (datetime, bytes)):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [sanitize_for_json(item) for item in obj]
        else:
            return str(obj) if hasattr(obj, '__dict__') else obj

    # Sanitize the log data
    log_data = sanitize_for_json(log_data)

    try:
        # Load existing data or create empty list
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Existing log file was corrupted. Creating new log.")
                existing_data = []
        else:
            existing_data = []
        
        # Append new data
        existing_data.append(log_data)
        
        # Write updated data back to file
        with open(log_file_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"Request log saved to {log_file_path}")
    except Exception as e:
        print(f"Error saving log: {e}")

def get_style_choice():
    """Present a menu for logo style selection"""
    style_options = {
        1: "",  # Default, no style suffix
        2: "minimalistic, clean, modern",
        3: "luxurious, elegant, high-end",
        4: "playful, creative, bold",
        5: "tech, futuristic, innovative",
        6: "professional, corporate, trustworthy"
    }
    
    while True:
        print("\nChoose a logo style:")
        for num, style in style_options.items():
            style_name = "Default" if style == "" else style
            print(f"{num}. {style_name}")
        
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
    logo_folder = "all_output/generated_logos"
    logs_folder = "logs"
    os.makedirs(logo_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)

    # Get generation parameters
    base_prompt = input("Enter your logo description: ")
    style_suffix = get_style_choice()
    num_variations = int(input("Enter number of variations to generate (1-5): "))
    
    # Validate number of variations
    num_variations = max(1, min(5, num_variations))  # Clamp between 1 and 5

    print("\nGenerating logos...")
    logo_urls = generate_logo(base_prompt, num_variations, style_suffix)

    # Save generated logos
    saved_logos = []
    for url in logo_urls:
        saved_path = save_image(url, logo_folder)
        if saved_path:
            saved_logos.append(saved_path)

    print(f"\nSaved {len(saved_logos)} logos in the '{logo_folder}' folder.")

    # Prepare and save log data
    log_data = {
        "timestamp": datetime.now(),
        "base_prompt": base_prompt,
        "style_suffix": style_suffix,
        "num_variations": num_variations,
        "output_images": saved_logos,
        "generation_urls": logo_urls
    }
    save_request_log(log_data)