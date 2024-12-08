import cv2
import numpy as np
import pytesseract
import time

def order_points(pts):
    """Order the points of a contour into a top-left, top-right, bottom-right, bottom-left format."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # Top-left
    rect[2] = pts[np.argmax(s)]       # Bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]    # Top-right
    rect[3] = pts[np.argmax(diff)]    # Bottom-left

    return rect

def four_point_transform(image, pts):
    """Perform a perspective transform to obtain a top-down view of the Sudoku grid."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute the width and height of the new image
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped



def scan_puzzle(image_path="puzzle.jpg"):
    """
    Scans the Sudoku puzzle from the given image and returns a 9x9 numpy array
    of the puzzle, with 0 for empty cells.
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image from {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Blur and threshold
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    thresh = cv2.bitwise_not(thresh)

    # Find contours to detect the largest square (the Sudoku grid)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found. Check the image quality.")

    # Assume largest contour is the Sudoku puzzle
    contour = max(contours, key=cv2.contourArea)

    # Approximate the contour to a polygon
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
    if len(approx) != 4:
        raise ValueError("Sudoku grid not detected as a 4-sided polygon.")

    # Warp perspective to get a top-down view of the puzzle
    warped = four_point_transform(image, approx.reshape(4, 2))

    # The warped image should now contain a clean, top-down Sudoku grid
    # Split into 9x9 cells
    puzzle = np.zeros((9, 9), dtype=int)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # Dimensions of each cell
    h, w = warped_gray.shape
    cell_height = h // 9
    cell_width = w // 9

    for row in range(9):
        for col in range(9):
            x_start = col * cell_width
            y_start = row * cell_height
            cell = warped[y_start:y_start+cell_height, x_start:x_start+cell_width]
            digit = extract_digit(cell)
            puzzle[row, col] = digit

    return puzzle

if __name__ == "__main__":
    # Example usage:
    # Ensure you have a "puzzle.jpg" image in the same directory:
    # The image should contain a sudoku puzzle.
    puzzle_matrix = scan_puzzle("sudoku_puzzle1.jpg")
    print("Scanned Puzzle:")
    print(puzzle_matrix)
