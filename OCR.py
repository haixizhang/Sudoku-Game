import cv2
import numpy as np
import pytesseract

def preprocess_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian Blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2)
    
    # Invert colors: digits become black on white background
    inverted = cv2.bitwise_not(thresh)
    
    return inverted

def extract_digits(processed_image):
    # Configure Tesseract to recognize digits only
    config = "--psm 10 --oem 3 -c tessedit_char_whitelist=123456789"
    
    # Use pytesseract to do OCR on the processed image
    custom_config = r'--oem 3 --psm 6 outputbase digits'
    data = pytesseract.image_to_string(processed_image, config=custom_config)
    
    # Process the OCR data to extract digits
    digits = [int(char) for char in data if char.isdigit()]
    
    # Assuming a 9x9 Sudoku puzzle
    if len(digits) != 81:
        print("Warning: Detected digits count does not equal 81. Check the image quality.")
    
    # Convert to 9x9 grid
    grid = []
    for i in range(9):
        row = digits[i*9:(i+1)*9]
        grid.append(row)
    
    return grid

if __name__ == "__main__":
    processed = preprocess_image('sudoku_puzzle.jpg')
    grid = extract_digits(processed)
    print("Extracted Sudoku Grid:")
    for row in grid:
        print(row)
