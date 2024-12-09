# main.py

import os
import pygame
import pigame  # Ensure pigame.py is in the same directory
from pygame.locals import *
import sys
import time
import RPi.GPIO as GPIO  # For button interactions
import numpy as np
import cv2
from picamera2 import Picamera2
from libcamera import controls
import threading
import logging

# Import the run_gui function from Gui.py
from Gui import run_gui

# Import the get_solution function from solver.py
from Solver import get_solution

from sudoku_recognition import SudokuRecognition

# ----------------------------
# Configuration Constants
# ----------------------------
# GPIO Pins
BUTTONS = {
    "BAILOUT": 17,   # Quit button
    "CAPTURE": 18    # Capture button
}

# Framebuffer for PiTFT
SDL_FBDEV = "/dev/fb0"  # Adjust if your piTFT uses a different framebuffer

# PiTFT Resolution
PI_TFT_WIDTH = 320
PI_TFT_HEIGHT = 240

# Camera Configuration
PREVIEW_RESOLUTION = (640, 480)
PREVIEW_FORMAT = "RGB888"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Fonts
FONT_SIZE = 30
TITLE_FONT_SIZE = 40
BUTTON_FONT_SIZE = 35

# Timeout for Main Menu (in seconds)
MAIN_MENU_TIMEOUT = 180  # 3 minutes

# Frame Rate for Preview
FRAME_RATE = 20  # FPS

# Image Capture Path
CAPTURE_OUTPUT = "/home/pi/Sudoku-Game/sudoku_puzzle.jpg"

# ----------------------------
# Setup Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

# ----------------------------
# GPIO Setup
# ----------------------------
GPIO.setmode(GPIO.BCM)
for button in BUTTONS.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ----------------------------
# Environment Variables for PiTFT
# ----------------------------
os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', SDL_FBDEV)
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY', '')

# ----------------------------
# Initialize Pygame and Touchscreen
# ----------------------------
logging.info("Initializing Pygame...")
pygame.init()
pygame.mouse.set_visible(False)  # Hide the mouse cursor
logging.info("Pygame initialized.")

# Initialize PiTFT using pigame module
pitft = pigame.PiTft()

# Set up the display
lcd = pygame.display.set_mode((PI_TFT_WIDTH, PI_TFT_HEIGHT))
lcd.fill(BLACK)  # Black background
pygame.display.update()

# Define fonts
font = pygame.font.Font(None, FONT_SIZE)
title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)

# Define button dimensions
SCAN_BUTTON_RECT = pygame.Rect(60, 100, 200, 40)

# ----------------------------
# Initialize Camera
# ----------------------------
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(
    main={"size": PREVIEW_RESOLUTION, "format": PREVIEW_FORMAT}
)
picam2.configure(preview_config)
picam2.start()
logging.info("Camera initialized and started.")

# Set auto-focus to continuous and speed to fast for better performance
picam2.set_controls({
    "AfMode": controls.AfModeEnum.Continuous,
    "AfSpeed": controls.AfSpeedEnum.Fast
})

# Flag to control the preview loop
running = True
preview_active = False

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
        # Uncomment the following line if rotation is needed
        # frame = np.rot90(frame)

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
    global running, preview_active
    clock = pygame.time.Clock()
    try:
        while running and preview_active:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                    preview_active = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                        preview_active = False

            # Capture a frame as a NumPy array
            frame = picam2.capture_array()

            # Process the frame
            surface = process_frame(frame)
            if surface:
                # Blit the surface to the screen
                lcd.blit(surface, (0, 0))
                pygame.display.flip()

            # Control the frame rate
            clock.tick(FRAME_RATE)

    except Exception as e:
        logging.error(f"An error occurred in preview_loop: {e}")
    finally:
        preview_active = False

# ----------------------------
# Draw Main Menu Function
# ----------------------------
def draw_main_menu():
    lcd.fill(BLACK)  # Clear screen
    # Render the title
    title_text = title_font.render("Interactive Sudoku Solver", True, WHITE)
    title_rect = title_text.get_rect(center=(PI_TFT_WIDTH // 2, 40))  # Top middle
    lcd.blit(title_text, title_rect)

    # Draw the "Scan the Puzzle" button
    pygame.draw.rect(lcd, GRAY, SCAN_BUTTON_RECT)
    scan_text = button_font.render("Scan the Puzzle", True, BLACK)
    scan_text_rect = scan_text.get_rect(center=SCAN_BUTTON_RECT.center)
    lcd.blit(scan_text, scan_text_rect)

    pygame.display.update()
    logging.info("Main menu drawn.")

# ----------------------------
# Capture, Save, and Process Image Function
# ----------------------------
def capture_save_process_image():
    global running, preview_active
    captured = False  # Flag to indicate if image was captured
    try:
        logging.info("Starting live preview...")
        preview_active = True
        # Start the preview loop in a separate thread
        preview_thread = threading.Thread(target=preview_loop)
        preview_thread.start()

        logging.info("Live preview active. Press Capture button to take a picture or Quit button to exit.")

        while preview_active and running:
            # Check if Capture button is pressed
            if GPIO.input(BUTTONS["CAPTURE"]) == GPIO.LOW:
                logging.info("Capture button pressed. Capturing image...")
                # Capture and save the image
                picam2.capture_file(CAPTURE_OUTPUT)
                logging.info(f"Image captured and saved at {CAPTURE_OUTPUT}")
                captured = True
                preview_active = False
                break

            # Check if Quit button is pressed
            if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                logging.info("Quit button pressed during capture.")
                running = False
                preview_active = False
                break

            time.sleep(0.1)  # Debounce delay

        # Ensure the preview loop is stopped
        preview_active = False
        preview_thread.join()

        if not captured:
            logging.info("Image capture was canceled. Exiting capture mode.")
            return  # Exit without processing the image

        # Run Sudoku Recognition functionality
        logging.info("Running Sudoku Recognition on the captured image...")
        im = cv2.imread(CAPTURE_OUTPUT)
        if im is None:
            logging.error("Failed to read captured image.")
            display_error("Capture Failed. Try Again.")
            return

        # Recognize Sudoku puzzle
        puzzle = SudokuRecognition.recognize(im)
        if puzzle is not None:
            puzzle = np.array(puzzle)
            logging.info("OCR scanned puzzle:")
            logging.info(puzzle)
            if puzzle.shape == (9, 9):
                logging.info("Puzzle scanned successfully.")
                # Solve the puzzle
                solution = get_solution(puzzle)
                if solution is not None:
                    logging.info("Puzzle solved successfully.")
                    logging.info(solution)
                    # Launch interactive GUI
                    run_gui(puzzle, solution)
                    # After GUI, redraw the main menu
                    draw_main_menu()
                else:
                    logging.error("Puzzle is unsolvable.")
                    display_error("Puzzle Unsolvable. Try Again.")
            else:
                logging.error("Invalid puzzle shape.")
                display_error("Invalid Puzzle. Try Again.")
        else:
            logging.error("OCR failed to recognize puzzle.")
            display_error("OCR Failed. Try Again.")

    except Exception as e:
        logging.error(f"An error occurred during capture, save, and process: {e}")
        display_error("Error Occurred. Try Again.")
    finally:
        preview_active = False

# ----------------------------
# Display Error Message Function
# ----------------------------
def display_error(message):
    lcd.fill(BLACK)  # Clear screen
    error_text = font.render(message, True, RED)
    error_rect = error_text.get_rect(center=(PI_TFT_WIDTH // 2, PI_TFT_HEIGHT // 2))
    lcd.blit(error_text, error_rect)
    pygame.display.update()
    logging.info(message)
    time.sleep(2)  # Wait for 2 seconds
    draw_main_menu()

# ----------------------------
# Main Function
# ----------------------------
def main():
    global running
    draw_main_menu()
    start_time = time.time()

    try:
        while running:
            pitft.update()

            # Check for bailout button press
            if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                logging.info("Quit button pressed from main menu.")
                running = False
                break

            # Implement timeout functionality
            if time.time() - start_time > MAIN_MENU_TIMEOUT:
                logging.info("Main menu timed out.")
                running = False
                break

            # Handle touch events
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    logging.info(f"Touch detected at ({x}, {y})")
                    if SCAN_BUTTON_RECT.collidepoint(x, y):
                        logging.info("Scan the Puzzle button pressed.")
                        capture_save_process_image()  # Call the capture, save, and process function
                        start_time = time.time()  # Reset the timeout

            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Exiting...")
    finally:
        # Clean up resources
        logging.info("Cleaning up resources...")
        GPIO.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
