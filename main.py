import numpy as np
import pygame
import os
import sys
import time
import subprocess
import RPi.GPIO as GPIO
from pygame.locals import *

# Set up GPIO for buttons
GPIO.setmode(GPIO.BCM)
BUTTONS = {
    "BAILOUT": 17,  # Quit button
    "SCAN": 22,     # Scan puzzle button
}
for button in BUTTONS.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set environment variables
os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY', '')

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)  # Hide the mouse cursor

# Set up the display
lcd = pygame.display.set_mode((320, 240))
lcd.fill((0, 0, 0))  # Black background
pygame.display.update()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
RED = (255, 0, 0)

# Define fonts
font = pygame.font.Font(None, 30)
num_font = pygame.font.Font(None, 40)

# Main function to start GUI
def main():
    def draw_main_screen():
        lcd.fill(BLACK)
        # Draw the title of the project
        title_text = font.render("Interactive Sudoku Solver", True, WHITE)
        title_rect = title_text.get_rect(center=(160, 50))
        lcd.blit(title_text, title_rect)

        # Draw the scan puzzle button
        scan_button_text = font.render("Scan the Puzzle", True, BLACK)
        scan_button_rect = pygame.Rect(110, 120, 100, 40)
        pygame.draw.rect(lcd, GRAY, scan_button_rect)
        lcd.blit(scan_button_text, scan_button_text.get_rect(center=scan_button_rect.center))
        pygame.display.update()

    draw_main_screen()

    start_time = time.time()
    running = True
    puzzle = None

    while running:
        # Check the physical buttons
        if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
            print("Quit button pressed")
            running = False

        if GPIO.input(BUTTONS["SCAN"]) == GPIO.LOW:
            print("Scan puzzle button pressed")
            # Run the OCR script to get the Sudoku puzzle
            try:
                #subprocess.run(["python3", "OCR.py"], check=True)
                # Placeholder: Here we simulate loading the puzzle from OCR
                puzzle = np.array([
                    [5, 3, 0, 0, 7, 0, 0, 0, 0],
                    [6, 0, 0, 1, 9, 5, 0, 0, 0],
                    [0, 9, 8, 0, 0, 0, 0, 6, 0],
                    [8, 0, 0, 0, 6, 0, 0, 0, 3],
                    [4, 0, 0, 8, 0, 3, 0, 0, 1],
                    [7, 0, 0, 0, 2, 0, 0, 0, 6],
                    [0, 6, 0, 0, 0, 0, 2, 8, 0],
                    [0, 0, 0, 4, 1, 9, 0, 0, 5],
                    [0, 0, 0, 0, 8, 0, 0, 7, 9]
                ])
                # After getting the puzzle, proceed to interactive GUI
                interactive_sudoku_gui(puzzle)
                draw_main_screen()  # After exiting the interactive GUI, return to main screen
            except subprocess.CalledProcessError as e:
                print(f"Error running OCR.py: {e}")

        # Implement timeout functionality (3 minutes)
        if time.time() - start_time > 180:
            print("Program timed out")
            running = False

        # Handle touch events for GUI buttons
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if 110 <= x <= 210 and 120 <= y <= 160:  # Scan Puzzle button touched
                    print("Scan puzzle button pressed via touch")
                    # Simulate button press action
                    subprocess.run(["python3", "OCR.py"], check=True)
                    puzzle = np.array([
                        [5, 3, 0, 0, 7, 0, 0, 0, 0],
                        [6, 0, 0, 1, 9, 5, 0, 0, 0],
                        [0, 9, 8, 0, 0, 0, 0, 6, 0],
                        [8, 0, 0, 0, 6, 0, 0, 0, 3],
                        [4, 0, 0, 8, 0, 3, 0, 0, 1],
                        [7, 0, 0, 0, 2, 0, 0, 0, 6],
                        [0, 6, 0, 0, 0, 0, 2, 8, 0],
                        [0, 0, 0, 4, 1, 9, 0, 0, 5],
                        [0, 0, 0, 0, 8, 0, 0, 7, 9]
                    ])
                    interactive_sudoku_gui(puzzle)
                    draw_main_screen()

        time.sleep(0.1)  # Small delay to reduce CPU usage

    pygame.quit()
    GPIO.cleanup()
    sys.exit()

# Interactive Sudoku GUI (calls previously written setup)
def interactive_sudoku_gui(puzzle):
    import Gui  # Import existing interactive GUI setup
    Gui.start_interactive(puzzle)  # Start the interactive GUI with the scanned puzzle

if __name__ == "__main__":
    main()
