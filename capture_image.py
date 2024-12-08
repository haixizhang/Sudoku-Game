import os
import pygame
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
import threading
import logging

# ----------------------------
# Configuration Constants
# ----------------------------
SDL_FBDEV = "/dev/fb0"  # Framebuffer device for piTFT
PI_TFT_WIDTH = 320       # piTFT width
PI_TFT_HEIGHT = 240      # piTFT height
PREVIEW_RESOLUTION = (640, 480)
PREVIEW_FORMAT = "RGB888"
CAPTURE_OUTPUT = "sudoku_puzzle.jpg"
FRAME_RATE = 20          # Frames per second

# ----------------------------
# Setup Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

# ----------------------------
# Initialize Pygame
# ----------------------------
os.environ["SDL_FBDEV"] = SDL_FBDEV  # Direct Pygame to use piTFT framebuffer

pygame.init()
pygame.mouse.set_visible(False)  # Hide the mouse cursor

# Set up the display
screen = pygame.display.set_mode((PI_TFT_WIDTH, PI_TFT_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Sudoku Capture Preview")

# Create a clock to manage frame rate
clock = pygame.time.Clock()

# ----------------------------
# Initialize Camera
# ----------------------------
picam2 = Picamera2()

# Configure the camera for preview
preview_config = picam2.create_preview_configuration(
    main={"size": PREVIEW_RESOLUTION, "format": PREVIEW_FORMAT}
)
picam2.configure(preview_config)
picam2.start()

# Flag to control the preview loop
running = True

# ----------------------------
# Frame Processing Function
# ----------------------------
def process_frame(frame):
    """
    Process the captured frame to make it suitable for Pygame.

    Steps:
    1. Convert RGBA to RGB if necessary.
    2. Ensure the array is contiguous.
    3. Optionally flip the frame horizontally.
    4. Rotate the frame to match piTFT orientation.
    5. Convert to Pygame surface.
    6. Resize to fit piTFT screen.

    Returns:
        pygame.Surface or None
    """
    try:
        # Check frame dimensions and channels
        if frame.ndim != 3 or frame.shape[2] not in (3, 4):
            logging.warning("Captured frame is not in RGB/RGBA format.")
            return None

        # Convert RGBA to RGB by dropping the alpha channel if present
        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        # Ensure the array is contiguous in memory
        frame = np.ascontiguousarray(frame)

        # Optional: Convert BGR to RGB if colors appear incorrect
        # Uncomment the following line if needed
        # frame = frame[:, :, ::-1]

        # Rotate the frame if necessary (90 degrees clockwise)
        frame = np.rot90(frame)

        # Convert the NumPy array to a Pygame surface
        surface = pygame.surfarray.make_surface(frame)

        # Apply horizontal flip if desired
        surface = pygame.transform.flip(surface, True, False)

        # Resize the surface to fit the piTFT screen
        surface = pygame.transform.scale(surface, (PI_TFT_WIDTH, PI_TFT_HEIGHT))

        return surface

    except Exception as e:
        logging.error(f"Error processing frame: {e}")
        return None

# ----------------------------
# Preview Loop Function
# ----------------------------
def preview_loop():
    global running
    try:
        while running:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Capture a frame as a NumPy array
            frame = picam2.capture_array()

            # Process the frame
            surface = process_frame(frame)
            if surface:
                # Blit the surface to the screen
                screen.blit(surface, (0, 0))
                pygame.display.flip()

            # Control the frame rate
            clock.tick(FRAME_RATE)

    except Exception as e:
        logging.error(f"An error occurred in preview_loop: {e}")
    finally:
        running = False

# ----------------------------
# Capture Function
# ----------------------------
def capture_sudoku_image(output_path=CAPTURE_OUTPUT):
    global running
    try:
        # Set auto-focus to continuous and speed to fast for better performance
        picam2.set_controls({
            "AfMode": controls.AfModeEnum.Continuous,
            "AfSpeed": controls.AfSpeedEnum.Fast
        })

        logging.info("Auto-focus set to continuous and fast speed.")
        
        # Allow time for auto-focus to adjust
        logging.info("Adjusting auto-focus...")
        clock.tick(2)  # Wait for ~0.5 seconds

        # Prompt the user to capture the image
        while True:
            user_input = input("Type 'ok' and press Enter when you are ready to capture the image: ")
            if user_input.strip().lower() == 'ok':
                break
            else:
                logging.info("Please type 'ok' when you are ready.")

        # Capture and save the image
        picam2.capture_file(output_path)
        logging.info(f"Image captured and saved at {output_path}")

    except Exception as e:
        logging.error(f"An error occurred during image capture: {e}")
    finally:
        # Signal the preview loop to stop
        running = False

# ----------------------------
# Main Execution
# ----------------------------
def main():
    global running
    try:
        # Start the preview loop in a separate thread
        preview_thread = threading.Thread(target=preview_loop, daemon=True)
        preview_thread.start()
        logging.info("Preview started. Press 'ESC' to exit.")

        # Start the capture process
        capture_sudoku_image()

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Exiting...")
    finally:
        # Ensure the preview loop is stopped
        running = False
        preview_thread.join()

        # Clean up resources
        picam2.stop()
        pygame.quit()
        logging.info("Resources have been cleaned up. Goodbye!")

if __name__ == "__main__":
    main()
