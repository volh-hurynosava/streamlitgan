import os
import shutil
from PIL import Image

MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_DIMENSION = 10240
MAX_PROCESSING_SIZE = 1024

def save_and_prepare_image(uploaded_file, dataroot):
    """Saves and prepares the image for processing"""
    try:
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return False, f"ФFile is too large({file_size/1024/1024:.1f} MB). Max: {MAX_FILE_SIZE/1024/1024:.1f} MB"
      
        uploaded_image = Image.open(uploaded_file)
        width, height = uploaded_image.size
        
        if max(width, height) > MAX_DIMENSION:
            return False, f"The image is too large ({width}×{height}). Max: {MAX_DIMENSION}×{MAX_DIMENSION} пикселей"
        
        cleanup_dataroot(dataroot)
       
        session_info = {
            'original_image': uploaded_image.copy(),
            'original_size': (width, height),
            'base_name': os.path.splitext(uploaded_file.name)[0],
            'current_filename': uploaded_file.name
        }
 
        if max(width, height) > MAX_PROCESSING_SIZE:
            resized_image, resize_info = resize_to_max_dimension(uploaded_image, MAX_PROCESSING_SIZE)
            session_info['scale_info'] = resize_info
            image_to_process = resized_image
        else:
            session_info['scale_info'] = {
                'original_size': (width, height),
                'scaled_size': (width, height),
                'scale_factor': 1.0,
                'was_resized': False
            }
            image_to_process = uploaded_image
   
        squared_image, square_info = pad_to_square(image_to_process, target_size=256)
       
        if session_info['scale_info']:
            session_info['scale_info'].update({
                'square_info': square_info,
                'final_processing_size': squared_image.size
            })
        
        save_path = os.path.join(dataroot, uploaded_file.name)
        squared_image.save(save_path, format="JPEG", quality=95, optimize=True)
        
        if os.path.exists(save_path):
            session_info['file_ready'] = True
            return True, session_info
        else:
            return False, "Failed to save file"
            
    except Exception as e:
        return False, f"Error while processing image: {str(e)}"

def resize_to_max_dimension(image, max_dimension=1024):
    """
    Reduces the image to its maximum size while maintaining its aspect ratio.
    If the image is smaller than max_dimension, it is returned unchanged
    """
    width, height = image.size

    if max(width, height) <= max_dimension:
        return image, {
            'original_size': (width, height),
            'scaled_size': (width, height),
            'scale_factor': 1.0,
            'was_resized': False
        }
    
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return resized_image, {
        'original_size': (width, height),
        'scaled_size': (new_width, new_height),
        'scale_factor': new_width / width,
        'was_resized': True
    }

def pad_to_square(image, target_size=256):
    """
    Adds padding to make the image square while maintaining its original proportions
    """
    width, height = image.size
    

    new_image = Image.new('RGB', (target_size, target_size), (255, 255, 255))
    scale = target_size / max(width, height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
   
    x_offset = (target_size - new_width) // 2
    y_offset = (target_size - new_height) // 2
    new_image.paste(resized, (x_offset, y_offset))
    
    return new_image, {
        'original_size': (width, height),     
        'scaled_size': (new_width, new_height), 
        'offset': (x_offset, y_offset),        
        'scale_factor': scale,                 
        'target_size': target_size,           
        'has_padding': new_width != target_size or new_height != target_size  
    }

def scale_back_to_original(image, scale_info):
    """
    Rescales the image back to its original size with proper padding trimming
    """
    if not scale_info or image is None:
        return image
    
    original_width, original_height = scale_info['original_size']
    
    if 'square_info' in scale_info:
        
        square_info = scale_info['square_info']
        scaled_width, scaled_height = square_info['scaled_size']
        x_offset, y_offset = square_info['offset']
        
        input_width, input_height = image.size
        if input_width != 256 or input_height != 256:
            image = image.resize((256, 256), Image.Resampling.LANCZOS)
        if scaled_width > 0 and scaled_height > 0 and x_offset >= 0 and y_offset >= 0:
            right_bound = min(x_offset + scaled_width, 256)
            bottom_bound = min(y_offset + scaled_height, 256)
            
            if right_bound > x_offset and bottom_bound > y_offset:
                cropped = image.crop((
                    x_offset, 
                    y_offset, 
                    right_bound, 
                    bottom_bound
                ))
                
                if 'scaled_size' in scale_info and scale_info['scaled_size'] != scale_info['original_size']:
                    intermediate_width, intermediate_height = scale_info['scaled_size']
                    if cropped.size != (intermediate_width, intermediate_height):
                        cropped = cropped.resize((intermediate_width, intermediate_height), 
                                                Image.Resampling.LANCZOS)
                
                if cropped.size != (original_width, original_height):
                    return cropped.resize((original_width, original_height), 
                                         Image.Resampling.LANCZOS)
                else:
                    return cropped
    
    return image.resize((original_width, original_height), Image.Resampling.LANCZOS)

def cleanup_dataroot(dataroot):
    """Clear the dataroot folder"""
    try:
        if os.path.exists(dataroot):
            for file in os.listdir(dataroot):
                file_path = os.path.join(dataroot, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except Exception as e:
        print(f"Error while clearing dataroot: {e}")

def cleanup_results(results_dir):
    """Clear the results folder"""
    try:
        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
    except Exception as e:
        print(f"Error clearing results: {e}")