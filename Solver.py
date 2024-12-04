import numpy as np

def is_valid(board, row, col, num):
    # Check if the number is in the same row
    for i in range(9):
        if board[row][i] == num:
            return False

    # Check if the number is in the same column
    for i in range(9):
        if board[i][col] == num:
            return False

    # Check if the number is in the same 3x3 box
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                return False

    return True

def solve_sudoku(board):
    # Find an empty cell
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                # Try placing numbers 1-9
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num

                        # Recursively attempt to solve the rest of the board
                        if solve_sudoku(board):
                            return True

                        # Backtrack if solution was not found
                        board[row][col] = 0

                return False

    # If no empty cell is found, the puzzle is solved
    return True

if __name__ == "__main__":
    # Example 9x9 Sudoku puzzle with some empty cells represented by 0
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

    # Convert puzzle to a numpy array
    puzzle = np.array(puzzle)

    print("Original Sudoku Puzzle:")
    print(puzzle)

    if solve_sudoku(puzzle):
        print("\nSolved Sudoku Puzzle:")
        print(puzzle)
    else:
        print("\nNo solution exists for the given Sudoku puzzle.")
