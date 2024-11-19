import cv2
import pytesseract
import numpy as np

# Path to Tesseract executable if not added to PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to preprocess the captured Sudoku image
def preprocess_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding to get binary image
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    return binary

# Function to extract the digits from the Sudoku grid using OCR
def extract_digits_from_image(processed_image):
    # Find contours of all the cells
    contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Initialize the Sudoku grid to store recognized digits
    sudoku_grid = [[0 for _ in range(9)] for _ in range(9)]
    
    # Loop over each contour to identify potential cells
    for contour in contours:
        # Approximate the contour shape
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        
        # Ignore if not rectangular
        if len(approx) != 4:
            continue
        
        # Get bounding rectangle for the contour
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter by size to remove noise
        if w < 20 or h < 20:
            continue
        
        # Crop the detected cell from the original grayscale image
        cell = processed_image[y:y+h, x:x+w]
        
        # Resize cell to a fixed size for OCR
        cell_resized = cv2.resize(cell, (28, 28))
        
        # Perform OCR to recognize the digit in the cell
        digit = pytesseract.image_to_string(cell_resized, config='--psm 10 digits')
        
        # Check if the recognized character is a digit
        if digit.isdigit():
            # Convert string digit to integer
            recognized_digit = int(digit)
            
            # Determine row and column (simplified for now, additional logic needed for precise positioning)
            row, col = y // 100, x // 100  # This assumes a roughly 900x900 image size
            sudoku_grid[row][col] = recognized_digit
    
    return sudoku_grid

# Example usage
if __name__ == "__main__":
    # Define the image path (use the output path from the previous module)
    image_path = '/home/pi/sudoku_capture.jpg'
    
    # Preprocess the image
    processed_image = preprocess_image(image_path)
    
    # Extract Sudoku grid using OCR
    sudoku_grid = extract_digits_from_image(processed_image)
    
    # Print the extracted Sudoku grid
    for row in sudoku_grid:
        print(row)
