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
import random

from Gui import run_gui
from Solver import get_solution
from sudoku_recognition import SudokuRecognition

# ----------------------------
# Configuration Constants
# ----------------------------
BUTTONS = {
    "BAILOUT": 17,   # Quit/Back button
    "CAPTURE": 18    # Capture button
}

SDL_FBDEV = "/dev/fb0"
PI_TFT_WIDTH = 320
PI_TFT_HEIGHT = 240

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

FONT_SIZE = 30
TITLE_FONT_SIZE = 40
BUTTON_FONT_SIZE = 35

MAIN_MENU_TIMEOUT = 180  # 3 minutes
FRAME_RATE = 20  # FPS

CAPTURE_OUTPUT = "/home/pi/Sudoku-Game/sudoku_puzzle.jpg"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

GPIO.setmode(GPIO.BCM)
for button in BUTTONS.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', SDL_FBDEV)
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY', '')

logging.info("Initializing Pygame...")
pygame.init()
pygame.mouse.set_visible(False)
logging.info("Pygame initialized.")

pitft = pigame.PiTft()
lcd = pygame.display.set_mode((PI_TFT_WIDTH, PI_TFT_HEIGHT))
lcd.fill(BLACK)
pygame.display.update()

font = pygame.font.Font(None, FONT_SIZE)
title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)

# Main menu buttons
SCAN_BUTTON_RECT = pygame.Rect(60, 100, 200, 40)
RANDOM_BUTTON_RECT = pygame.Rect(60, 160, 200, 40)

# Difficulty selection buttons
EASY_BUTTON_RECT = pygame.Rect(60, 60, 200, 40)
MEDIUM_BUTTON_RECT = pygame.Rect(60, 120, 200, 40)
HARD_BUTTON_RECT = pygame.Rect(60, 180, 200, 40)

picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(preview_config)
picam2.start()
logging.info("Camera initialized and started.")

picam2.set_controls({
    "AfMode": controls.AfModeEnum.Continuous,
    "AfSpeed": controls.AfSpeedEnum.Fast
})

running = True
preview_active = False

# Define single puzzle for each difficulty
EASY_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

MEDIUM_PUZZLE = [
    [0, 0, 6, 5, 0, 0, 0, 7, 9],
    [0, 0, 0, 0, 7, 3, 0, 0, 0],
    [0, 0, 0, 0, 0, 6, 5, 0, 0],
    [0, 3, 2, 0, 0, 0, 0, 9, 0],
    [0, 9, 0, 7, 0, 1, 0, 4, 0],
    [0, 8, 0, 0, 0, 0, 1, 3, 0],
    [0, 0, 3, 9, 0, 0, 0, 0, 0],
    [0, 0, 0, 6, 3, 0, 0, 0, 0],
    [1, 6, 0, 0, 0, 2, 7, 0, 0]
]

HARD_PUZZLE = [
    [0, 0, 0, 0, 0, 7, 0, 2, 0],
    [0, 0, 0, 4, 0, 0, 5, 0, 0],
    [0, 2, 7, 0, 9, 0, 0, 0, 0],
    [3, 0, 0, 0, 0, 0, 0, 1, 9],
    [0, 0, 9, 0, 0, 0, 7, 0, 0],
    [1, 7, 0, 0, 0, 0, 0, 0, 3],
    [0, 0, 0, 0, 7, 0, 9, 4, 0],
    [0, 0, 2, 0, 0, 6, 0, 0, 0],
    [0, 1, 0, 2, 0, 0, 0, 0, 0]
]

# ----------------------------
# Mode Stack for Navigation
# ----------------------------
mode_stack = ["MAIN_MENU"]  # Initialize with MAIN_MENU

def process_frame(frame):
    try:
        if frame.ndim != 3 or frame.shape[2] not in (3, 4):
            logging.warning("Captured frame is not in RGB/RGBA format.")
            return None

        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        frame = np.ascontiguousarray(frame)
        surface = pygame.surfarray.make_surface(frame)
        surface = pygame.transform.flip(surface, True, False)
        surface = pygame.transform.scale(surface, (PI_TFT_WIDTH, PI_TFT_HEIGHT))
        return surface
    except Exception as e:
        logging.error(f"Error processing frame: {e}")
        return None

def preview_loop():
    global running, preview_active
    clock = pygame.time.Clock()
    try:
        while running and preview_active:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                    preview_active = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                        preview_active = False

            frame = picam2.capture_array()
            surface = process_frame(frame)
            if surface:
                lcd.blit(surface, (0, 0))
                pygame.display.flip()

            clock.tick(FRAME_RATE)

    except Exception as e:
        logging.error(f"An error occurred in preview_loop: {e}")
    finally:
        preview_active = False

def draw_main_menu():
    lcd.fill(BLACK)
    title_text = title_font.render("Interactive Sudoku Solver", True, WHITE)
    title_rect = title_text.get_rect(center=(PI_TFT_WIDTH // 2, 40))
    lcd.blit(title_text, title_rect)

    pygame.draw.rect(lcd, GRAY, SCAN_BUTTON_RECT)
    scan_text = button_font.render("Scan the Puzzle", True, BLACK)
    scan_text_rect = scan_text.get_rect(center=SCAN_BUTTON_RECT.center)
    lcd.blit(scan_text, scan_text_rect)

    pygame.draw.rect(lcd, GRAY, RANDOM_BUTTON_RECT)
    random_text = button_font.render("Random Puzzle", True, BLACK)
    random_text_rect = random_text.get_rect(center=RANDOM_BUTTON_RECT.center)
    lcd.blit(random_text, random_text_rect)

    pygame.display.update()
    logging.info("Main menu drawn.")

def draw_difficulty_menu():
    lcd.fill(BLACK)
    title_text = title_font.render("Select Difficulty", True, WHITE)
    title_rect = title_text.get_rect(center=(PI_TFT_WIDTH // 2, 20))
    lcd.blit(title_text, title_rect)

    pygame.draw.rect(lcd, GRAY, EASY_BUTTON_RECT)
    easy_text = button_font.render("Easy", True, BLACK)
    easy_text_rect = easy_text.get_rect(center=EASY_BUTTON_RECT.center)
    lcd.blit(easy_text, easy_text_rect)

    pygame.draw.rect(lcd, GRAY, MEDIUM_BUTTON_RECT)
    medium_text = button_font.render("Medium", True, BLACK)
    medium_text_rect = medium_text.get_rect(center=MEDIUM_BUTTON_RECT.center)
    lcd.blit(medium_text, medium_text_rect)

    pygame.draw.rect(lcd, GRAY, HARD_BUTTON_RECT)
    hard_text = button_font.render("Hard", True, BLACK)
    hard_text_rect = hard_text.get_rect(center=HARD_BUTTON_RECT.center)
    lcd.blit(hard_text, hard_text_rect)

    pygame.display.update()
    logging.info("Difficulty menu drawn.")

def display_error(message):
    lcd.fill(BLACK)
    error_text = font.render(message, True, RED)
    error_rect = error_text.get_rect(center=(PI_TFT_WIDTH // 2, PI_TFT_HEIGHT // 2))
    lcd.blit(error_text, error_rect)
    pygame.display.update()
    logging.info(message)
    time.sleep(2)
    # After displaying error, return to the previous mode
    if len(mode_stack) > 1:
        mode_stack.pop()
        current_mode = mode_stack[-1]
        logging.info(f"Returning to {current_mode}.")
        if current_mode == "MAIN_MENU":
            draw_main_menu()
        elif current_mode == "DIFFICULTY_MENU":
            draw_difficulty_menu()

def capture_save_process_image():
    global running, preview_active
    captured = False
    try:
        logging.info("Starting live preview...")
        preview_active = True
        preview_thread = threading.Thread(target=preview_loop)
        preview_thread.start()

        logging.info("Live preview active. Press Capture button to take a picture or BAILOUT to go back.")

        while preview_active and running:
            # Check if Capture button is pressed
            if GPIO.input(BUTTONS["CAPTURE"]) == GPIO.LOW:
                logging.info("Capture button pressed. Capturing image...")
                picam2.capture_file(CAPTURE_OUTPUT)
                logging.info(f"Image captured and saved at {CAPTURE_OUTPUT}")
                captured = True
                preview_active = False
                break

            # Check if BAILOUT button is pressed
            if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                logging.info("BAILOUT button pressed during capture. Returning to previous menu.")
                preview_active = False  # Stop the preview
                break  # Exit the capture loop to return to previous menu

            time.sleep(0.1)

        preview_active = False
        preview_thread.join()

        if not captured:
            logging.info("Image capture was canceled. Exiting capture mode.")
            return

        logging.info("Running Sudoku Recognition on the captured image...")
        im = cv2.imread(CAPTURE_OUTPUT)
        if im is None:
            logging.error("Failed to read captured image.")
            display_error("Capture Failed. Try Again.")
            return

        puzzle = SudokuRecognition.recognize(im)
        if puzzle is not None:
            puzzle = np.array(puzzle)
            logging.info("OCR scanned puzzle:")
            logging.info(puzzle)
            if puzzle.shape == (9, 9):
                logging.info("Puzzle scanned successfully.")
                solution = get_solution(puzzle)
                if solution is not None:
                    logging.info("Puzzle solved successfully.")
                    logging.info(solution)
                    run_gui(puzzle, solution)  # Run the GUI
                    # After GUI exits, return to main menu
                    mode_stack.pop()  # Remove "CAPTURE_MODE"
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
        logging.error(f"Error during capture, save, and process: {e}")
        display_error("Error Occurred. Try Again.")
    finally:
        preview_active = False

def start_random_puzzle_mode(difficulty):
    # Based on the difficulty selected, choose the puzzle
    if difficulty == 'easy':
        puzzle = np.array(EASY_PUZZLE)
    elif difficulty == 'medium':
        puzzle = np.array(MEDIUM_PUZZLE)
    else:
        puzzle = np.array(HARD_PUZZLE)

    solution = get_solution(puzzle)
    if solution is not None:
        run_gui(puzzle, solution)
    else:
        # This should rarely happen if your puzzles are known solvable
        display_error("Selected puzzle is unsolvable. Try Again.")
    # After solving, return to main menu
    mode_stack.pop()  # Remove "PLAYING_*" mode
    draw_main_menu()

def handle_back_button():
    if len(mode_stack) > 1:
        # Pop the current mode
        popped_mode = mode_stack.pop()
        current_mode = mode_stack[-1]
        logging.info(f"Returning from {popped_mode} to {current_mode}.")

        # Redraw the previous mode's screen
        if current_mode == "MAIN_MENU":
            draw_main_menu()
        elif current_mode == "DIFFICULTY_MENU":
            draw_difficulty_menu()
        elif current_mode == "CAPTURE_MODE":
            # If you have other modes, handle them here
            pass
        else:
            logging.warning(f"Unhandled mode: {current_mode}")
    else:
        # If only MAIN_MENU is in the stack, exit the program
        logging.info("BAILOUT pressed on MAIN_MENU. Exiting program.")
        global running
        running = False

def main():
    global running
    draw_main_menu()
    mode_stack.append("MAIN_MENU")
    start_time = time.time()

    try:
        while running:
            pitft.update()

            # Handle BAILOUT button as "back"
            if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                logging.info("BAILOUT button pressed.")
                handle_back_button()
                time.sleep(0.2)  # Debounce delay

            # Implement timeout functionality based on the current mode
            current_mode = mode_stack[-1]
            if current_mode == "MAIN_MENU" and (time.time() - start_time > MAIN_MENU_TIMEOUT):
                logging.info("Main menu timed out.")
                running = False
                break

            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    logging.info(f"Touch detected at ({x}, {y})")
                    current_mode = mode_stack[-1]

                    if current_mode == "MAIN_MENU":
                        if SCAN_BUTTON_RECT.collidepoint(x, y):
                            logging.info("Scan the Puzzle button pressed.")
                            mode_stack.append("CAPTURE_MODE")
                            draw_main_menu()  # Optional: clear any previous selections
                            capture_save_process_image()
                            start_time = time.time()
                        elif RANDOM_BUTTON_RECT.collidepoint(x, y):
                            logging.info("Random Puzzle button pressed.")
                            mode_stack.append("DIFFICULTY_MENU")
                            draw_difficulty_menu()
                            start_time = time.time()

                    elif current_mode == "DIFFICULTY_MENU":
                        if EASY_BUTTON_RECT.collidepoint(x, y):
                            logging.info("Easy selected.")
                            mode_stack.append("PLAYING_EASY")
                            start_random_puzzle_mode('easy')
                            start_time = time.time()
                        elif MEDIUM_BUTTON_RECT.collidepoint(x, y):
                            logging.info("Medium selected.")
                            mode_stack.append("PLAYING_MEDIUM")
                            start_random_puzzle_mode('medium')
                            start_time = time.time()
                        elif HARD_BUTTON_RECT.collidepoint(x, y):
                            logging.info("Hard selected.")
                            mode_stack.append("PLAYING_HARD")
                            start_random_puzzle_mode('hard')
                            start_time = time.time()

                    # Add more conditions if you have more modes

            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Exiting...")
    finally:
        logging.info("Cleaning up resources...")
        GPIO.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
