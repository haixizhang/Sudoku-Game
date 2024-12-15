# Owner: Haixi Zhang & Shuchang Wen
# Gui.py

import pygame
import pigame  # Ensure pigame.py is in the same directory
from pygame.locals import *
import os
import sys
import time
import RPi.GPIO as GPIO  # For button interactions
import numpy as np
import random
from Solver import get_solution  
import multiprocessing

def run_gui(puzzle, answer, TIMEOUT=120, editing=False):
    """
    Runs the Sudoku GUI.

    Modifications:
    1. In edit mode (EDIT_MODE), the REVERSE button clears the currently selected cell (sets it to 0).
    2. In edit mode, pressing the HINT button submits the solve. If the result is not obtained within 10 seconds,
       remain in edit mode and indicate unsolvable (blink red LED).

    If editing=True and answer=None, runs in edit mode:
      - User can modify puzzle.
      - Pressing the HINT button attempts to solve the puzzle.
        If not solved within 10 seconds or unsolvable, remain in edit mode and blink red LED.

    If not editing or answer is provided, runs in normal solve mode:
      - User solves puzzle manually or uses hints, reveal, etc.

    After puzzle is completed, shows a congratulations screen.
    """
    
    GPIO.setmode(GPIO.BCM)
    BUTTONS = {
        "BAILOUT": 17,  # Quit button
        "HINT": 22,     # Hint/Submit button in editing mode
        "REVERSE": 23,  # Reverse button or clear cell in edit mode
        "REVEAL": 27    # Reveal answers button
    }
    for name, pin in BUTTONS.items():
        try:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except Exception as e:
            print(f"Warning: Could not set up GPIO pin {pin} for {name}. {e}")
            BUTTONS[name] = None
    
    GREEN_LED_PIN = 6
    RED_LED_PIN = 5
    GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

    os.putenv('SDL_VIDEODRV', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_MOUSEDRV', 'dummy')
    os.putenv('SDL_MOUSEDEV', '/dev/null')
    os.putenv('DISPLAY', '')
    
    pygame.init()
    pygame.mouse.set_visible(False)
    pitft = pigame.PiTft()
    
    lcd = pygame.display.set_mode((320, 240))
    lcd.fill((0, 0, 0))
    pygame.display.update()
    
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (169, 169, 169)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    
    font = pygame.font.Font(None, 30)
    num_font = pygame.font.Font(None, 40)
    
    cell_types = np.zeros((9, 9), dtype=int)
    for row in range(9):
        for col in range(9):
            if puzzle[row, col] != 0:
                cell_types[row, col] = 1  # Initial numbers

    user_moves = []
    hint_moves = []

    GRID_SIZE = 240
    CELL_SIZE = GRID_SIZE // 9
    selected_cell = None

    def is_puzzle_complete():
        return not (0 in puzzle)

    def draw_grid():
        lcd.fill(BLACK)
        for row in range(9):
            for col in range(9):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(lcd, WHITE, rect, 1)
                
                if puzzle[row, col] != 0:
                    if cell_types[row, col] == 1:
                        color = BLUE
                    elif cell_types[row, col] == 2:
                        color = WHITE
                    elif cell_types[row, col] == 3:
                        color = GREEN
                    else:
                        color = WHITE

                    text = num_font.render(str(puzzle[row, col]), True, color)
                    text_rect = text.get_rect(center=rect.center)
                    lcd.blit(text, text_rect)
        
        if selected_cell:
            sel_x, sel_y = selected_cell
            highlight_rect = pygame.Rect(sel_x * CELL_SIZE, sel_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(lcd, RED, highlight_rect, 3)

        draw_num_pad()

    def draw_num_pad():
        pad_start_x = 260
        pad_start_y = 10
        button_width = 60
        button_height = 20
        spacing = 5
        for num in range(1, 10):
            y = pad_start_y + (num - 1) * (button_height + spacing)
            rect = pygame.Rect(pad_start_x, y, button_width, button_height)
            pygame.draw.rect(lcd, GRAY, rect)
            text = num_font.render(str(num), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            lcd.blit(text, text_rect)
            if num < 9:
                pygame.draw.line(lcd, WHITE, (pad_start_x, y + button_height), 
                                 (pad_start_x + button_width, y + button_height), 1)

    def blink_led(pin, times=3, delay=0.2):
        for _ in range(times):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(delay)

    def show_congrats_screen():
        lcd.fill(BLACK)
        try:
            congrats_img = pygame.image.load('congrats.png')
            congrats_img = pygame.transform.scale(congrats_img, (320, 80))
            lcd.blit(congrats_img, (0, 0))
        except Exception as e:
            print("Error loading congrats.png:", e)
            text = font.render("CONGRATULATIONS!", True, WHITE)
            text_rect = text.get_rect(center=(160, 40))
            lcd.blit(text, text_rect)

        total_steps = len(user_moves) + len(hint_moves)
        steps_text = font.render(f"Total Steps: {total_steps}", True, WHITE)
        steps_rect = steps_text.get_rect(center=(160, 120))
        lcd.blit(steps_text, steps_rect)

        time_used = time.time() - start_time
        time_text = font.render(f"Time Used: {int(time_used)}s", True, WHITE)
        time_rect = time_text.get_rect(center=(160, 180))
        lcd.blit(time_text, time_text_rect)

        pygame.display.update()

        waiting = True
        while waiting:
            if BUTTONS["BAILOUT"] is not None and GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                time.sleep(0.2)
                waiting = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    waiting = False
            time.sleep(0.1)

    def attempt_solve_with_timeout(p):
        # Use multiprocessing to implement 10-second solve timeout
        def solve_sudoku(p, q):
            sol = get_solution(p)
            q.put(sol)

        q = multiprocessing.Queue()
        proc = multiprocessing.Process(target=solve_sudoku, args=(p.copy(), q))
        proc.start()
        proc.join(timeout=10)
        if proc.is_alive():
            # Solving timed out, terminate process
            proc.terminate()
            proc.join()
            return None
        else:
            if not q.empty():
                return q.get()
            else:
                return None

    if editing or answer is None:
        mode = "EDIT_MODE"
    else:
        mode = "SELF_SOLVE"

    draw_grid()
    pygame.display.update()

    start_time = time.time()
    running_gui = True

    try:
        while running_gui:
            pitft.update()

            # Check BAILOUT
            if BUTTONS["BAILOUT"] is not None and GPIO.input(BUTTONS["BAILOUT"]) == GPIO.LOW:
                print("Quit button pressed in GUI")
                time.sleep(0.2)
                running_gui = False
                break

            if mode == "SELF_SOLVE":
                # NORMAL MODE LOGIC
                if BUTTONS["REVEAL"] is not None and GPIO.input(BUTTONS["REVEAL"]) == GPIO.LOW:
                    print("Reveal answers button pressed")
                    if answer is not None:
                        made_change = False
                        for row in range(9):
                            for col in range(9):
                                if puzzle[row, col] == 0:
                                    puzzle[row, col] = answer[row, col]
                                    cell_types[row, col] = 3
                                    hint_moves.append((col, row))
                                    made_change = True
                        if made_change:
                            draw_grid()
                            pygame.display.update()

                if BUTTONS["HINT"] is not None and GPIO.input(BUTTONS["HINT"]) == GPIO.LOW:
                    print("Hint button pressed (SELF_SOLVE mode)")
                    if answer is not None:
                        empty_cells = [(r, c) for r in range(9) for c in range(9) if puzzle[r, c] == 0]
                        if empty_cells:
                            hint_cell = random.choice(empty_cells)
                            r, c = hint_cell
                            puzzle[r, c] = answer[r, c]
                            cell_types[r, c] = 3
                            hint_moves.append((c, r))
                            draw_grid()
                            pygame.display.update()

                if BUTTONS["REVERSE"] is not None and GPIO.input(BUTTONS["REVERSE"]) == GPIO.LOW:
                    print("Reverse button pressed (SELF_SOLVE mode)")
                    if user_moves:
                        last_move = user_moves.pop()
                        x, y, num = last_move
                        puzzle[y, x] = 0
                        cell_types[y, x] = 0
                        draw_grid()
                        pygame.display.update()
                    elif hint_moves:
                        last_hint = hint_moves.pop()
                        x, y = last_hint
                        puzzle[y, x] = 0
                        cell_types[y, x] = 0
                        draw_grid()
                        pygame.display.update()

            elif mode == "EDIT_MODE":
                # EDIT MODE LOGIC:
                # 1. HINT button submits the solve with a 10-second timeout
                if BUTTONS["HINT"] is not None and GPIO.input(BUTTONS["HINT"]) == GPIO.LOW:
                    print("HINT button pressed (EDIT_MODE) - Attempt to solve puzzle with timeout")
                    solution_attempt = attempt_solve_with_timeout(puzzle)
                    if solution_attempt is not None:
                        print("Puzzle is now solvable.")
                        answer = solution_attempt
                        mode = "SELF_SOLVE"
                        draw_grid()
                        pygame.display.update()
                    else:
                        print("Still unsolvable or timed out, please modify more cells.")
                        blink_led(RED_LED_PIN)  # Remain in EDIT_MODE

                # 2. REVERSE button clears the selected cell
                if BUTTONS["REVERSE"] is not None and GPIO.input(BUTTONS["REVERSE"]) == GPIO.LOW:
                    print("Reverse button pressed (EDIT_MODE) - Clear selected cell")
                    if selected_cell is not None:
                        sel_x, sel_y = selected_cell
                        puzzle[sel_y, sel_x] = 0
                        cell_types[sel_y, sel_x] = 0
                        selected_cell = None
                        draw_grid()
                        pygame.display.update()
                        time.sleep(0.2)  # Debounce

            # Implement timeout
            if time.time() - start_time > TIMEOUT:
                print("GUI timed out")
                running_gui = False
                break

            # Check if puzzle is complete
            if mode == "SELF_SOLVE" and is_puzzle_complete():
                time.sleep(5)
                show_congrats_screen()
                running_gui = False
                break

            # Handle touch events
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    print(f"Touch detected at ({x}, {y})")
                    if mode == "SELF_SOLVE":
                        if x < GRID_SIZE and y < GRID_SIZE:
                            grid_x = x // CELL_SIZE
                            grid_y = y // CELL_SIZE
                            if puzzle[grid_y, grid_x] == 0:
                                selected_cell = (grid_x, grid_y)
                                draw_grid()
                                pygame.display.update()
                        elif x >= 260:
                            # Number pad input in SELF_SOLVE mode
                            pad_start_y = 10
                            button_height = 20
                            spacing = 5
                            relative_y = y - pad_start_y
                            if 0 <= relative_y < 225:
                                pad_num = relative_y // (button_height + spacing) + 1
                                if 1 <= pad_num <= 9 and selected_cell:
                                    sel_x, sel_y = selected_cell
                                    puzzle[sel_y, sel_x] = pad_num
                                    cell_types[sel_y, sel_x] = 2
                                    user_moves.append((sel_x, sel_y, pad_num))
                                    if answer is not None:
                                        if pad_num == answer[sel_y, sel_x]:
                                            blink_led(GREEN_LED_PIN)
                                            print("Correct input")
                                        else:
                                            blink_led(RED_LED_PIN)
                                            print("Incorrect input")
                                    selected_cell = None
                                    draw_grid()
                                    pygame.display.update()
                    
                    elif mode == "EDIT_MODE":
                        # In edit mode, user can change any cell directly
                        if x < GRID_SIZE and y < GRID_SIZE:
                            grid_x = x // CELL_SIZE
                            grid_y = y // CELL_SIZE
                            selected_cell = (grid_x, grid_y)
                            draw_grid()
                            pygame.display.update()
                        elif x >= 260:
                            # Number pad input in edit mode
                            pad_start_y = 10
                            button_height = 20
                            spacing = 5
                            relative_y = y - pad_start_y
                            if 0 <= relative_y < 225:
                                pad_num = relative_y // (button_height + spacing) + 1
                                if 1 <= pad_num <= 9 and selected_cell:
                                    sel_x, sel_y = selected_cell
                                    puzzle[sel_y, sel_x] = pad_num
                                    cell_types[sel_y, sel_x] = 2
                                    selected_cell = None
                                    draw_grid()
                                    pygame.display.update()

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        return
