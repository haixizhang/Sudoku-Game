# main.py
import pygame
import pigame  # Ensure pigame.py is in the same directory
from pygame.locals import *
import os
import sys
import time
import RPi.GPIO as GPIO  # For button interactions
import numpy as np

# Import the run_gui function from Gui.py
from Gui import run_gui

# Import the get_solution function from solver.py
from Solver import get_solution

# Set up GPIO for buttons
GPIO.setmode(GPIO.BCM)
BUTTONS = {
    "BAILOUT": 17,  # Quit button
}
for button in BUTTONS.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set environment variables for PiTFT
os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY', '')

# Initialize Pygame and touchscreen
pygame.init()
pygame.mouse.set_visible(False)  # Hide the mouse cursor
pitft = pigame.PiTft()

# Set up the display
lcd = pygame.display.set_mode((320, 240))
lcd.fill((0, 0, 0))  # Black background
pygame.display.update()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Define fonts
font = pygame.font.Font(None, 30)
title_font = pygame.font.Font(None, 40)
button_font = pygame.font.Font(None, 35)

# Define button dimensions
SCAN_BUTTON_RECT = pygame.Rect(60, 100, 200, 40)

# Set up the timeout for main menu
MAIN_MENU_TIMEOUT = 180  # 3 minutes in seconds

def draw_main_menu():
    lcd.fill(BLACK)  # Clear screen
    # Render the title
    title_text = title_font.render("Interactive Sudoku Solver", True, WHITE)
    title_rect = title_text.get_rect(center=(160, 40))  # Top middle
    lcd.blit(title_text, title_rect)
    
    # Draw the "Scan the Puzzle" button
    pygame.draw.rect(lcd, GRAY, SCAN_BUTTON_RECT)
    scan_text = button_font.render("Scan the Puzzle", True, BLACK)
    scan_text_rect = scan_text.get_rect(center=SCAN_BUTTON_RECT.center)
    lcd.blit(scan_text, scan_text_rect)
    
    pygame.display.update()

def scan_puzzle_via_OCR():
    """
    Simulates scanning the Sudoku puzzle by returning a predefined matrix.
    Replace this with actual OCR functionality when available.
    """
    try:
        # Simulated scanned puzzle (list of lists)
        puzzle = [
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
        # Convert to NumPy array
        puzzle = np.array(puzzle)
        print("Simulated OCR: Returning predefined puzzle.")
        print(puzzle)
        return puzzle
    except Exception as e:
        print(f"Error scanning puzzle: {e}")
        return None

def main():
    global pitft  # Declare pitft as global to modify it within the function
    draw_main_menu()
    start_time = time.time()
    
    try:
        running = True
        while running:
            pitft.update()
            # Check for button presses
            if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                print("Quit button pressed from main menu")
                running = False
                break
            
            # Implement timeout functionality
            if time.time() - start_time > MAIN_MENU_TIMEOUT:
                print("Main menu timed out")
                running = False
                break
            
            # Handle touch events
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    print(f"Touch detected at ({x}, {y})")
                    if SCAN_BUTTON_RECT.collidepoint(x, y):
                        print("Scan the Puzzle button pressed")
                        # Call OCR.py to scan the puzzle
                        puzzle = scan_puzzle_via_OCR()
                        if puzzle is not None and isinstance(puzzle, np.ndarray) and puzzle.shape == (9, 9):
                            print("Puzzle scanned successfully.")
                            # Solve the puzzle
                            solution = get_solution(puzzle)
                            if solution is not None:
                                print("Puzzle solved successfully.")
                                print(solution)
                                # Launch the interactive GUI
                                run_gui(puzzle, solution)
                                # After returning from GUI, redraw the main menu
                                draw_main_menu()
                                start_time = time.time()  # Reset the timeout
                            else:
                                # Handle unsolvable puzzle
                                error_text = font.render("Puzzle Unsolvable. Try Again.", True, RED)
                                error_rect = error_text.get_rect(center=(160, 200))
                                lcd.blit(error_text, error_rect)
                                pygame.display.update()
                                time.sleep(2)  # Wait for 2 seconds
                                draw_main_menu()
                                start_time = time.time()  # Reset the timeout
                        else:
                            # Handle OCR failure (e.g., show an error message)
                            error_text = font.render("OCR Failed. Try Again.", True, RED)
                            error_rect = error_text.get_rect(center=(160, 200))
                            lcd.blit(error_text, error_rect)
                            pygame.display.update()
                            time.sleep(2)  # Wait for 2 seconds
                            draw_main_menu()
                            start_time = time.time()  # Reset the timeout
            
            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        pass

    finally:
        # Clean up resources
        del pitft
        GPIO.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
