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

# Set environment variables for PiTFT
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
BLUE = (0, 0, 255)    # Initial numbers
GREEN = (0, 255, 0)    # Hint and reveal numbers

# Define fonts
font = pygame.font.Font(None, 30)
num_font = pygame.font.Font(None, 40)

# Example of a predefined puzzle and its solution
# 0 represents empty cells
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

# Corresponding solution
answer = np.array([
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9]
])

# Initialize cell types: 0 = empty, 1 = initial, 2 = user, 3 = hint/reveal
cell_types = np.zeros((9, 9), dtype=int)
for row in range(9):
    for col in range(9):
        if puzzle[row, col] != 0:
            cell_types[row, col] = 1  # Initial numbers

user_moves = []  # To keep track of user moves for reverse functionality
hint_moves = []  # To keep track of hint moves for reverse functionality

# Draw Sudoku grid with numbers
GRID_SIZE = 240  # The size allocated for the Sudoku grid (left side of the screen)
CELL_SIZE = GRID_SIZE // 9
selected_cell = None

def draw_grid():
    lcd.fill(BLACK)  # Clear screen with black background
    # Draw Sudoku grid cells and numbers
    for row in range(9):
        for col in range(9):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(lcd, WHITE, rect, 1)  # Draw grid cell borders
            
            if puzzle[row, col] != 0:
                if cell_types[row, col] == 1:
                    color = BLUE  # Initial numbers in blue
                elif cell_types[row, col] == 2:
                    color = WHITE  # User inserted numbers in white
                elif cell_types[row, col] == 3:
                    color = GREEN  # Hint and reveal inserted numbers in green
                else:
                    color = WHITE  # Default to white if undefined

                text = num_font.render(str(puzzle[row, col]), True, color)
                text_rect = text.get_rect(center=rect.center)
                lcd.blit(text, text_rect)
    
    # Highlight selected cell if any
    if selected_cell:
        sel_x, sel_y = selected_cell
        highlight_rect = pygame.Rect(sel_x * CELL_SIZE, sel_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(lcd, RED, highlight_rect, 3)
    
    # Draw number pad on the right side
    draw_num_pad()
    pygame.display.update()

# Draw number pad on the right side of the screen
def draw_num_pad():
    num_pad_size = 25  # Adjust size to fit on the right
    pad_start_x = 260  # Starting X position for num pad (right side of screen)
    pad_start_y = 10  # Starting Y position
    button_width = 60  # Width of each number pad button
    button_height = 20  # Height of each number pad button
    spacing = 5  # Spacing between buttons

    for num in range(1, 10):
        y = pad_start_y + (num - 1) * (button_height + spacing)
        rect = pygame.Rect(pad_start_x, y, button_width, button_height)
        pygame.draw.rect(lcd, GRAY, rect)
        text = num_font.render(str(num), True, BLACK)
        text_rect = text.get_rect(center=rect.center)
        lcd.blit(text, text_rect)
        # Draw horizontal line between number pad entries except after the last one
        if num < 9:
            pygame.draw.line(lcd, WHITE, (pad_start_x, y + button_height), 
                             (pad_start_x + button_width, y + button_height), 1)

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
            # Provide a reveal by filling in all empty cells as hints (green)
            for row in range(9):
                for col in range(9):
                    if puzzle[row, col] == 0:
                        puzzle[row, col] = answer[row, col]
                        cell_types[row, col] = 3  # Mark as hint/reveal
                        hint_moves.append((col, row))  # Store as (x, y)
            draw_grid()

        if GPIO.input(BUTTONS["HINT"]) == GPIO.LOW:
            print("Hint button pressed")
            # Provide a hint by filling in one empty cell
            empty_cells = [(r, c) for r in range(9) for c in range(9) if puzzle[r, c] == 0]
            if empty_cells:
                hint_cell = random.choice(empty_cells)
                r, c = hint_cell
                puzzle[r, c] = answer[r, c]
                cell_types[r, c] = 3  # Mark as hint
                hint_moves.append((c, r))  # Store as (x, y)
                draw_grid()

        if GPIO.input(BUTTONS["REVERSE"]) == GPIO.LOW:
            print("Reverse button pressed")
            # Reverse the last move (user or hint)
            if user_moves:
                last_move = user_moves.pop()
                x, y, num = last_move
                puzzle[y, x] = 0
                cell_types[y, x] = 0  # Reset to empty
                draw_grid()
            elif hint_moves:
                last_hint = hint_moves.pop()
                x, y = last_hint
                puzzle[y, x] = 0
                cell_types[y, x] = 0  # Reset to empty
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
                        pad_start_y = 10
                        pad_spacing = 25
                        pad_width = 60
                        pad_height = 20
                        relative_y = y - pad_start_y
                        if 0 <= relative_y < 225:  # 9 buttons * 25 spacing = 225
                            pad_num = relative_y // (pad_height + 5) + 1
                            if 1 <= pad_num <= 9:
                                if selected_cell:
                                    sel_x, sel_y = selected_cell
                                    puzzle[sel_y, sel_x] = pad_num
                                    cell_types[sel_y, sel_x] = 2  # Mark as user move
                                    user_moves.append((sel_x, sel_y, pad_num))  # Keep track of moves for reverse
                                    print(f"Number {pad_num} placed at ({sel_x}, {sel_y})")
                                    selected_cell = None
                                    draw_grid()
                elif mode == "RPI_SOLVE":
                    # In Raspberry Pi Solve Mode, simply display the solved puzzle
                    for row in range(9):
                        for col in range(9):
                            if puzzle[row, col] == 0:
                                puzzle[row, col] = answer[row, col]
                                cell_types[row, col] = 3  # Mark as hint/reveal
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
