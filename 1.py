import pygame
import pigame  # Ensure pigame.py is in the same directory
from pygame.locals import *
import os
import sys
import time
import RPi.GPIO as GPIO  # For button interactions
import numpy as np
import random

# Set up GPIO for buttons
GPIO.setmode(GPIO.BCM)
BUTTONS = {
    "BAILOUT": 17,  # Quit button
    "HINT": 22,     # Hint button
    "REVERSE": 23,  # Reverse button
    "REVEAL": 27    # Reveal answers button
}
for button in BUTTONS.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set environment variables
os.putenv('SDL_VIDEODRV', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
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
BLUE = (0, 0, 255)  # Color for user inserted numbers

# Define fonts
font = pygame.font.Font(None, 30)
num_font = pygame.font.Font(None, 40)

# Generate a random 9x9 Sudoku puzzle (for demonstration purposes)
puzzle = np.array([[random.choice([0, random.randint(1, 9)]) for _ in range(9)] for _ in range(9)])
answer = np.array([[random.randint(1, 9) for _ in range(9)] for _ in range(9)])  # Placeholder for complete solution
user_moves = []  # To keep track of user moves for reverse functionality

# Draw Sudoku grid with numbers
GRID_SIZE = 240  # The size allocated for the Sudoku grid (left side of the screen)
CELL_SIZE = GRID_SIZE // 9
selected_cell = None

def draw_grid():
    lcd.fill((0, 0, 0))  # Clear screen
    # Draw Sudoku grid first
    for row in range(9):
        for col in range(9):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(lcd, WHITE, rect, 1)  # Draw grid cell borders
            if puzzle[row, col] != 0:
                color = WHITE if (row, col) not in [(move[0], move[1]) for move in user_moves] else BLUE
                text = num_font.render(str(puzzle[row, col]), True, color)
                lcd.blit(text, text.get_rect(center=rect.center))

    # Highlight selected cell if any
    if selected_cell:
        sel_x, sel_y = selected_cell
        rect = pygame.Rect(sel_x * CELL_SIZE, sel_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(lcd, RED, rect, 3)

    # Draw number pad after grid
    draw_num_pad()
    pygame.display.update()

# Draw number pad on the right side of the screen
def draw_num_pad():
    num_pad_size = 25  # Adjust size to fit on the right
    pad_start_x = 260  # Starting X position for num pad (right side of screen)
    for num in range(1, 10):
        y = (num - 1) * num_pad_size + 10
        rect = pygame.Rect(pad_start_x, y, num_pad_size * 3, num_pad_size)
        pygame.draw.rect(lcd, GRAY, rect)
        text = num_font.render(str(num), True, BLACK)
        lcd.blit(text, text.get_rect(center=rect.center))
        # Draw horizontal line between number pad entries except after the last one
        if num < 9:
            pygame.draw.line(lcd, WHITE, (pad_start_x, y + num_pad_size), (pad_start_x + num_pad_size * 3, y + num_pad_size), 1)

# Initial drawing of the grid and number pad
draw_grid()

# Set up the timeout
start_time = time.time()
TIMEOUT = 120  # Seconds for demo purposes

# Mode Selection
mode = "SELF_SOLVE"  # Default to Self Solve Mode

try:
    running = True
    while running:
        # Update touch events
        pitft.update()

        # Check the physical buttons
        if GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
            print("Quit button pressed")
            running = False

        if GPIO.input(BUTTONS["REVEAL"]) == GPIO.LOW:
            print("Reveal answers button pressed")
            puzzle = answer.copy()
            user_moves.clear()  # Clear user moves since we are revealing the solution
            draw_grid()

        if GPIO.input(BUTTONS["HINT"]) == GPIO.LOW:
            print("Hint button pressed")
            # Provide a hint by filling in one empty cell
            empty_cells = [(r, c) for r in range(9) for c in range(9) if puzzle[r, c] == 0]
            if empty_cells:
                hint_cell = random.choice(empty_cells)
                puzzle[hint_cell] = answer[hint_cell]
                draw_grid()

        if GPIO.input(BUTTONS["REVERSE"]) == GPIO.LOW:
            print("Reverse button pressed")
            if user_moves:
                last_move = user_moves.pop()
                puzzle[last_move[1], last_move[0]] = 0
                draw_grid()

        # Implement timeout functionality
        if time.time() - start_time > TIMEOUT:
            print("Program timed out")
            running = False

        # Handle touch events
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if mode == "SELF_SOLVE":
                    if x < GRID_SIZE and y < GRID_SIZE:  # User touched the Sudoku grid
                        grid_x = x // CELL_SIZE
                        grid_y = y // CELL_SIZE
                        if puzzle[grid_y, grid_x] == 0:  # Only allow selecting empty cells
                            selected_cell = (grid_x, grid_y)
                            print(f"Grid touched at ({grid_x}, {grid_y})")
                            draw_grid()
                    elif x >= 260:  # User touched the number pad
                        pad_y = (y - 10) // 25
                        if 0 <= pad_y < 9:
                            num = pad_y + 1
                            if selected_cell:
                                sel_x, sel_y = selected_cell
                                puzzle[sel_y, sel_x] = num
                                user_moves.append((sel_x, sel_y, num))  # Keep track of moves for reverse
                                print(f"Number {num} placed at ({sel_x}, {sel_y})")
                                selected_cell = None
                                draw_grid()
                elif mode == "RPI_SOLVE":
                    # In Raspberry Pi Solve Mode, simply display the solved puzzle
                    puzzle = answer.copy()
                    draw_grid()

        time.sleep(0.1)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    pass

finally:
    # Clean up resources
    del pitft
    GPIO.cleanup()
    pygame.quit()
    sys.exit()