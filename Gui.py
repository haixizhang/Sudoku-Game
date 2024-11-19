import tkinter as tk
from tkinter import messagebox

# Define the dimensions of the display for the PiTFT
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480

# Initialize a sample Sudoku grid (replace this with OCR output later)
sudoku_grid = [
    [0, 0, 8, 0, 0, 1, 0, 0, 0],
    [0, 6, 1, 0, 0, 0, 0, 0, 7],
    [2, 0, 0, 4, 9, 8, 0, 0, 0],
    [6, 0, 2, 0, 9, 1, 0, 1, 7],
    [9, 5, 8, 0, 7, 0, 0, 0, 3],
    [4, 0, 0, 0, 5, 0, 0, 0, 0],
    [0, 1, 4, 0, 5, 2, 0, 0, 0],
    [4, 3, 0, 6, 0, 0, 0, 0, 8],
    [0, 0, 0, 0, 0, 0, 0, 1, 0]
]

selected_cell = [None, None]  # Stores selected row and column

# Function to handle cell selection
def select_cell(row, col):
    global selected_cell
    selected_cell = [row, col]
    update_grid_display()

# Function to handle number input from keypad
def handle_number_input(number):
    row, col = selected_cell
    if row is not None and col is not None:
        sudoku_grid[row][col] = number
    update_grid_display()

# Function to update the Sudoku grid display
def update_grid_display():
    for row in range(9):
        for col in range(9):
            value = sudoku_grid[row][col]
            text = str(value) if value != 0 else ""
            grid_buttons[row][col].config(text=text)

# Function to create the main GUI
def create_gui():
    root = tk.Tk()
    root.geometry(f"{DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    root.title("Sudoku Solver")

    # Define frame for Sudoku grid
    grid_frame = tk.Frame(root, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT//2, bg='white')
    grid_frame.pack_propagate(0)
    grid_frame.pack(side=tk.TOP, fill=tk.BOTH)

    # Define frame for number pad
    keypad_frame = tk.Frame(root, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT//2, bg='lightgray')
    keypad_frame.pack_propagate(0)
    keypad_frame.pack(side=tk.BOTTOM, fill=tk.BOTH)

    # Create Sudoku grid buttons
    global grid_buttons
    grid_buttons = [[None for _ in range(9)] for _ in range(9)]
    for row in range(9):
        for col in range(9):
            btn = tk.Button(grid_frame, text="", width=3, height=2,
                            font=('Arial', 16), command=lambda r=row, c=col: select_cell(r, c))
            btn.grid(row=row, column=col, padx=2, pady=2)
            grid_buttons[row][col] = btn

    # Create number pad buttons (1-9)
    for num in range(1, 10):
        btn = tk.Button(keypad_frame, text=str(num), width=5, height=2,
                        font=('Arial', 16), command=lambda n=num: handle_number_input(n))
        btn.grid(row=(num-1)//3, column=(num-1)%3, padx=5, pady=5)

    # Create a button to reset the selected cell
    reset_btn = tk.Button(keypad_frame, text="Reset", width=15, height=2,
                          font=('Arial', 16), command=lambda: handle_number_input(0))
    reset_btn.grid(row=3, column=0, columnspan=3, pady=5)

    update_grid_display()
    root.mainloop()

if __name__ == "__main__":
    create_gui()
