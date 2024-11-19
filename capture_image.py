import time
from picamera import PiCamera

# Initialize the PiCamera
camera = PiCamera()

# Camera configuration (optional adjustments for your needs)
camera.resolution = (1920, 1080)  # Set resolution to full HD
camera.framerate = 15  # Set framerate
camera.brightness = 55  # Adjust brightness if necessary

# Function to capture an image of the Sudoku puzzle
def capture_sudoku_image(output_path='/home/pi/sudoku_capture.jpg'):
    try:
        print("Starting camera preview...")
        camera.start_preview()  # Start camera preview for user alignment
        time.sleep(5)  # Wait for 5 seconds to allow user to adjust the printed puzzle
        
        print("Capturing image...")
        camera.capture(output_path)  # Capture the image and save it to the specified path
        
        print(f"Image saved to {output_path}")
        camera.stop_preview()  # Stop camera preview
    except Exception as e:
        print(f"An error occurred while capturing the image: {e}")
    finally:
        camera.close()  # Always close the camera after use

# Example usage
if __name__ == "__main__":
    capture_sudoku_image()
