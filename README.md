# Interactive Sudoku Solver

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Objectives](#objectives)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Hardware Requirements](#hardware-requirements)
- Results
  - [CNN vs. OCR](#cnn-vs-ocr)
  - [Hardware Performance](#hardware-performance)
  - [User Feedback](#user-feedback)
  - [Limitations and Challenges](#limitations-and-challenges)
- [Future Work](#future-work)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

The **Interactive Sudoku Solver** is a comprehensive tool designed to recognize, solve, and interact with Sudoku puzzles using Raspberry Pi hardware. It allows users to input puzzles manually via a touch interface or capture them using a camera. The system processes the input, identifies the puzzle structure, solves it, and displays the solution interactively. This project integrates image processing, machine learning, software engineering, and hardware interfacing to provide a seamless user experience.

## Features

- **Sudoku Recognition**: Detects and extracts Sudoku puzzles from images, supporting both printed and handwritten digits.
- **Efficient Solving**: Utilizes a backtracking algorithm to solve puzzles accurately and efficiently.
- **Graphical User Interface (GUI)**: Intuitive interface developed for PiTFT with RPI, featuring touch interactions and color-coded elements.
- User Interaction Modes:
  - **Edit Mode**: Allows users to modify the puzzle.
  - **Self-Solve Mode**: Enables manual solving or provides hints.
- **Hardware Integration**: Incorporates Pi Camera, Pi TFT display, push buttons, and LED indicators for enhanced interactivity.

## Objectives

The primary objective of the Interactive Sudoku Solver is to develop a user-friendly application capable of:

- Recognizing printed and handwritten Sudoku puzzles.
- Solving puzzles efficiently.
- Providing an intuitive graphical interface for user interaction.
- Leveraging computer vision, machine learning, and hardware interfacing to enhance the traditional Sudoku-solving experience.

## System Architecture

The system architecture consists of the following components:

- **Python Modules**: Core logical units handling image processing, digit recognition, solving algorithms, and GUI management.

- **Hardware Components**: Raspberry Pi Camera, Pi TFT display, push buttons, and LED indicators.

- **Functional Processes**: Image capturing, Sudoku recognition, puzzle solving, and user interface management.

  ![System_arch](/img/System_arch.png)

## Installation

### Prerequisites

- **Raspberry Pi 4 Model B** with Raspberry Pi OS installed.
- **Raspberry Pi Camera 3**.
- **Adafruit PiTFT Plus 320x240 2.8" TFT + Capacitive Touchscreen**.
- **Python 3.7+** installed on Raspberry Pi.

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/interactive-sudoku-solver.git
   cd interactive-sudoku-solver
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Hardware**

   - Connect the Pi Camera to the Raspberry Pi.
   - Attach the PiTFT display following Adafruit's setup guide.
   - Connect push buttons and LEDs to the GPIO pins as per the parts list.

4. **Configure GPIO Pins**

   - Ensure the GPIO pins are correctly set up in the main configuration file.

5. **CNN Model**

   The `model` file is a pre-trained Convolutional Neural Network (CNN) model. Users can use it directly without training model.

## Usage

1. **Launch the Application**

   ```bash
   python main.py
   ```

2. **Main Menu**

   - **Scan Puzzle**: Capture an image of a Sudoku puzzle using the Pi Camera.
   - **Select Puzzle**: Choose a random puzzle from predefined difficulty levels (Easy, Medium, Hard).

3. **Solving the Puzzle**

   - After input, the system processes and solves the puzzle.
   - The solution is displayed interactively on the GUI.

4. **User Interaction**

   - **Edit Mode**: Modify the puzzle manually.
   - **Self-Solve Mode**: Solve the puzzle manually or request hints.
   - Buttons:
     - **Quit (BAILOUT)**: Exit the application or return to the previous menu.
     - **Hint**: Reveal correct numbers or submit the puzzle for solving.
     - **Reverse**: Undo the last move or clear a selected cell.
     - **Reveal**: Display the complete solution.

## Dependencies

- Python Libraries:
  - OpenCV (`cv2`)
  - Picamera2
  - Pygame
  - NumPy
  - PyTorch
  - Other dependencies listed in `requirements.txt`

## Hardware Requirements

| Part                                             |
| ------------------------------------------------ |
| Raspberry Pi                                     |
| Raspberry Pi Camera V2                           |
| Adafruit PiTFT Plus 320x240 2.8" TFT Touchscreen |
| Resistors                                        |
| LEDs                                             |

## Results

### CNN vs. OCR

- **OCR (Tesseract)**: Achieved an accuracy of ~58.7% in digit recognition.
- **CNN-Based Approach**: Achieved an accuracy of ~98.3% after 14 epochs of training.
- **Conclusion**: CNN significantly outperforms OCR in recognizing Sudoku digits, especially handwritten ones.

### Hardware Performance

- **Initial Usage**: Stable performance with no significant lag during image processing or puzzle-solving tasks.
- **Prolonged Usage**: Raspberry Pi overheated, causing performance degradation.
- **Mitigation**: Implemented heat sinks and improved ventilation, partially alleviating the issue.
- **Future Focus**: Optimize code for better thermal performance and explore more efficient algorithms.

### User Feedback

- **Positive**: High satisfaction with ease of use, reliability, intuitive GUI, and responsive touch interface.
- Enhancements Based on Feedback:
  - Integrated LED indicators for immediate feedback.
  - Added functionality to display total steps and solving time.
  - Planned improvements include customizable themes and interactive tutorials.

### Limitations and Challenges

- **Image Quality Dependence**: Recognition accuracy is affected by poor lighting or distorted images.
- **Puzzle Size**: Currently limited to 9x9 Sudoku puzzles.
- **Future Improvements**: Enhance image preprocessing techniques and expand solver capabilities for different puzzle sizes.

## Future Work

- **Advanced Machine Learning**: Incorporate more sophisticated models to improve digit recognition accuracy.
- **Mobile Integration**: Develop a mobile version leveraging smartphone cameras for puzzle input.
- **Additional Features**: Introduce puzzle difficulty adjustment, step-by-step solving explanations, and customizable GUI themes.
- **Performance Optimization**: Enhance application performance to handle higher-resolution images and more complex puzzles.
- **Expanded Puzzle Support**: Extend support to larger Sudoku variants (e.g., 16x16 grids).

**Team Members:**

- Haixi Zhang (hz733@cornell.edu)
- Shuchang Wen (sw2372@cornell.edu)

## **References**

1. [Picamera Documentation](https://picamera.readthedocs.io/en/release-1.13/)
2. [Pigame GitHub Repository](https://github.com/n4archive/pigame)
3. [Pitft Touchscreen GitHub Repository](https://github.com/n4archive/pitft_touchscreen)
4. LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). *Gradient-based learning applied to document recognition*. Proceedings of the IEEE, 86(11), 2278–2324. DOI
5. [OpenCV Tutorials](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)
6. [GeeksforGeeks: How to Use MNIST Dataset](https://www.geeksforgeeks.org/mnist-dataset/)
