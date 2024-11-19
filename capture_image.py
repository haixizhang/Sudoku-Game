from picamera2 import Picamera2
from libcamera import controls
import time

# Initialize the camera
picam2 = Picamera2()

# Function to capture an image of the Sudoku puzzle
def capture_sudoku_image(output_path="sudoku_puzzle.jpg"):
    try:
        # Start the camera preview (optional, to help with alignment)
        picam2.start(show_preview=True)
        
        # Set auto-focus to continuous and speed to fast for better performance
        picam2.set_controls({
            "AfMode": controls.AfModeEnum.Continuous,
            "AfSpeed": controls.AfSpeedEnum.Fast
        })
        time.sleep(2)
        # Wait until the user is ready to capture
        user_input = input("Type 'ok' and press Enter when you are ready to capture the image: ")
        while user_input.strip().lower() != 'ok':
            user_input = input("Please type 'ok' when you are ready: ")

        # Capture the image
        picam2.capture_file(output_path)
        print(f"Image captured and saved at {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Stop the camera preview and release resources
        picam2.stop_preview()
        picam2.stop()

# Main entry point for testing the image capture
if __name__ == "__main__":
    capture_sudoku_image("sudoku_puzzle.jpg")