import cv2
import pytesseract
import numpy as np
import os

def preprocess_image(image_path, output_dir='processing_steps'):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create cells directory
    cells_dir = os.path.join(output_dir, '08_cells')
    if not os.path.exists(cells_dir):
        os.makedirs(cells_dir)

    # Load the image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image at path '{image_path}' not found.")
    
    # Display and save grayscale image
    cv2.imshow('01_grayscale.jpg', img)
    cv2.imwrite(os.path.join(output_dir, '01_grayscale.jpg'), img)
    cv2.waitKey(500)  # Display for 0.5 seconds
    cv2.destroyWindow('01_grayscale.jpg')

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    cv2.imshow('02_blurred.jpg', blurred)
    cv2.imwrite(os.path.join(output_dir, '02_blurred.jpg'), blurred)
    cv2.waitKey(500)
    cv2.destroyWindow('02_blurred.jpg')

    # Adaptive thresholding to create a binary image
    thresh = cv2.adaptiveThreshold(blurred, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    cv2.imshow('03_threshold.jpg', thresh)
    cv2.imwrite(os.path.join(output_dir, '03_threshold.jpg'), thresh)
    cv2.waitKey(500)
    cv2.destroyWindow('03_threshold.jpg')

    # Find contours to locate the Sudoku grid
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found in the image.")
    
    # Find the largest contour assuming it's the Sudoku grid
    largest_contour = max(contours, key=cv2.contourArea)
    img_contour = img.copy()
    cv2.drawContours(img_contour, [largest_contour], -1, (255, 0, 0), 2)
    cv2.imshow('04_largest_contour.jpg', img_contour)
    cv2.imwrite(os.path.join(output_dir, '04_largest_contour.jpg'), img_contour)
    cv2.waitKey(500)
    cv2.destroyWindow('04_largest_contour.jpg')

    # Approximate the contour to a polygon
    peri = cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)

    if len(approx) != 4:
        raise ValueError("Sudoku grid not detected. Ensure the grid is clear and prominent.")

    # Perform perspective transform to get a top-down view
    pts = approx.reshape(4, 2)
    rect = order_points(pts)
    (top_left, top_right, bottom_right, bottom_left) = rect

    # Compute the width and height of the new image
    width_a = np.linalg.norm(bottom_right - bottom_left)
    width_b = np.linalg.norm(top_right - top_left)
    max_width = max(int(width_a), int(width_b))

    height_a = np.linalg.norm(top_right - bottom_right)
    height_b = np.linalg.norm(top_left - bottom_left)
    max_height = max(int(height_a), int(height_b))

    # Destination points for the perspective transform
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    # Compute the perspective transform matrix and apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (max_width, max_height))
    cv2.imshow('05_warped.jpg', warped)
    cv2.imwrite(os.path.join(output_dir, '05_warped.jpg'), warped)
    cv2.waitKey(500)
    cv2.destroyWindow('05_warped.jpg')

    # Further thresholding on the warped image
    warped_blur = cv2.GaussianBlur(warped, (5, 5), 0)
    cv2.imshow('06_warped_blur.jpg', warped_blur)
    cv2.imwrite(os.path.join(output_dir, '06_warped_blur.jpg'), warped_blur)
    cv2.waitKey(500)
    cv2.destroyWindow('06_warped_blur.jpg')

    warped_thresh = cv2.adaptiveThreshold(warped_blur, 255, 
                                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
    cv2.imshow('07_warped_threshold.jpg', warped_thresh)
    cv2.imwrite(os.path.join(output_dir, '07_warped_threshold.jpg'), warped_thresh)
    cv2.waitKey(500)
    cv2.destroyWindow('07_warped_threshold.jpg')

    return warped_thresh

def order_points(pts):
    # Initialize a list of coordinates that will be ordered
    rect = np.zeros((4, 2), dtype="float32")
    
    # The top-left point will have the smallest sum, whereas the bottom-right will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Compute the difference between the points
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def extract_digits(warped_thresh, output_dir='processing_steps'):
    # Create cells directory
    cells_dir = os.path.join(output_dir, '08_cells')
    if not os.path.exists(cells_dir):
        os.makedirs(cells_dir)

    # Dimensions of the warped image
    height, width = warped_thresh.shape
    cell_height = height // 9
    cell_width = width // 9
    
    sudoku_grid = []
    
    for i in range(9):
        row = []
        for j in range(9):
            # Extract the cell image
            x_start = j * cell_width
            y_start = i * cell_height
            cell = warped_thresh[y_start:y_start + cell_height, x_start:x_start + cell_width]
            
            # Save the cell image for debugging
            cell_filename = f'cell_{i+1}_{j+1}.jpg'
            cell_path = os.path.join(cells_dir, cell_filename)
            cv2.imwrite(cell_path, cell)
            
            # Display the cell image briefly
            cv2.imshow(cell_filename, cell)
            cv2.waitKey(500)
            cv2.destroyWindow(cell_filename)
            
            # Preprocess the cell for better OCR
            digit = recognize_digit(cell)
            row.append(digit)
        sudoku_grid.append(row)
    
    return sudoku_grid

def recognize_digit(cell):
    # Further thresholding to make sure the digit is clear
    cell = cv2.resize(cell, (28, 28))  # Resize to a standard size
    cell = cv2.GaussianBlur(cell, (3, 3), 0)
    _, cell = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours to detect if there's any digit in the cell
    contours, _ = cv2.findContours(cell, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0  # Empty cell
    
    # Assume the largest contour is the digit
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    # Filter out noise by setting a minimum area threshold
    if area < 50:
        return 0  # Considered as empty
    
    # Invert the cell image for OCR (black text on white background)
    cell = cv2.bitwise_not(cell)
    
    # Use pytesseract to recognize the digit
    config = "--psm 10 --oem 3 -c tessedit_char_whitelist=123456789"
    text = pytesseract.image_to_string(cell, config=config)
    
    # Extract the digit
    try:
        digit = int(text.strip())
    except:
        digit = 0  # Unrecognized or empty
    
    return digit

def display_grid(grid, title="Sudoku Grid"):
    # Create an image to display the grid
    display = np.zeros((450, 450), dtype="uint8")
    cell_size = 50
    for i in range(10):
        thickness = 2 if i % 3 == 0 else 1
        # Horizontal lines
        cv2.line(display, (0, i * cell_size), (450, i * cell_size), 255, thickness)
        # Vertical lines
        cv2.line(display, (i * cell_size, 0), (i * cell_size, 450), 255, thickness)
    
    for i in range(9):
        for j in range(9):
            digit = grid[i][j]
            if digit != 0:
                cv2.putText(display, str(digit), (j * cell_size + 15, i * cell_size + 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    
    cv2.imshow(title, display)
    cv2.imwrite('recognized_sudoku_grid.jpg', display)
    cv2.waitKey(1000)
    cv2.destroyWindow(title)

def main(image_path):
    output_dir = 'processing_steps'
    cells_dir = os.path.join(output_dir, '08_cells')
    if not os.path.exists(cells_dir):
        os.makedirs(cells_dir)
    
    try:
        # Preprocess the image to get a thresholded, warped Sudoku grid
        warped_thresh = preprocess_image(image_path, output_dir)
        
        # Extract digits from the preprocessed grid
        grid = extract_digits(warped_thresh, output_dir)
        
        # Display the recognized grid for verification
        display_grid(grid)
        
        # Print the grid to the console
        print("Recognized Sudoku Grid:")
        for row in grid:
            print(row)
        
        # Optionally, you can save the grid to a file or proceed with solving
        return grid
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    image_path = 'sudoku_puzzle.jpg'  # Use forward slash for paths
    grid = main(image_path)
    cv2.destroyAllWindows()
