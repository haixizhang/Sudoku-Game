# solver.py
import numpy as np

def is_valid(board, row, col, num):
    """
    Check if it's valid to place 'num' at position (row, col) on the board.
    
    Parameters:
    - board: 9x9 numpy array representing the Sudoku board.
    - row: Row index (0-8).
    - col: Column index (0-8).
    - num: Number to place (1-9).
    
    Returns:
    - True if valid, False otherwise.
    """
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
    """
    Solves the Sudoku puzzle using backtracking.
    
    Parameters:
    - board: 9x9 numpy array representing the Sudoku board.
    
    Returns:
    - True if the puzzle is solvable, False otherwise. The board is modified in place.
    """
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

                # If no number is valid in this cell, trigger backtracking
                return False

    # If no empty cell is found, the puzzle is solved
    return True

def get_solution(puzzle):
    """
    Solves the given Sudoku puzzle and returns the solution.
    
    Parameters:
    - puzzle: 9x9 numpy array with 0 representing empty cells.
    
    Returns:
    - solution: 9x9 numpy array representing the solved puzzle if solvable.
    - None: If the puzzle has no solution.
    """
    # Make a copy of the puzzle to solve
    solution = np.copy(puzzle)
    
    if solve_sudoku(solution):
        return solution
    else:
        return None

if __name__ == "__main__":
    # Example usage
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

    puzzle = np.array(puzzle)

    print("Original Sudoku Puzzle:")
    print(puzzle)

    solution = get_solution(puzzle)

    if solution is not None:
        print("\nSolved Sudoku Puzzle:")
        print(solution)
    else:
        print("\nNo solution exists for the given Sudoku puzzle.")
