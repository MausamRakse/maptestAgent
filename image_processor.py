"""
Image Area & Line Measurement Agent
Detects user-drawn lines/boundaries and calculates length and area.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import json


class ImageMeasurementProcessor:
    """Processes images to detect drawn lines and calculate measurements."""
    
    def __init__(self):
        self.debug_mode = False
        
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess image for better line detection.
        Returns grayscale and processed versions.
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            original_color = image.copy()
        else:
            gray = image.copy()
            original_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        
        return contrast, original_color
    
    def detect_drawn_lines(self, processed: np.ndarray, original: np.ndarray) -> List[np.ndarray]:
        """
        Detect user-drawn lines using multiple methods:
        1. Color filtering (for colored markers/pens)
        2. Edge detection
        3. Morphological operations
        """
        # Method 1: Try to detect colored lines (common pen/marker colors)
        if len(original.shape) == 3:
            hsv = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)
            
            # Common marker colors: blue, red, green, black
            masks = []
            
            # Blue marker range
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
            masks.append(mask_blue)
            
            # Red marker range (wrap around)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            mask_red = cv2.bitwise_or(
                cv2.inRange(hsv, lower_red1, upper_red1),
                cv2.inRange(hsv, lower_red2, upper_red2)
            )
            masks.append(mask_red)
            
            # Green marker range
            lower_green = np.array([40, 50, 50])
            upper_green = np.array([80, 255, 255])
            mask_green = cv2.inRange(hsv, lower_green, upper_green)
            masks.append(mask_green)
            
            # Black/dark marker (low brightness)
            mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
            masks.append(mask_black)
            
            # Combine all color masks
            color_mask = np.zeros_like(processed)
            for mask in masks:
                color_mask = cv2.bitwise_or(color_mask, mask)
        else:
            color_mask = np.zeros_like(processed)
        
        # Method 2: Edge detection on processed image
        edges = cv2.Canny(processed, 50, 150, apertureSize=3)
        
        # Method 3: Adaptive thresholding for high contrast lines
        thresh = cv2.adaptiveThreshold(
            processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Combine all detection methods
        combined = cv2.bitwise_or(edges, thresh)
        if color_mask.max() > 0:
            combined = cv2.bitwise_or(combined, color_mask)
        
        # Morphological operations to connect gaps in lines
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(combined, kernel, iterations=2)
        closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        # Filter contours by size (remove noise)
        min_area = 50  # Minimum contour area
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        
        return filtered_contours, combined
    
    def calculate_line_length(self, contour: np.ndarray) -> float:
        """
        Calculate the total length of a contour/polyline.
        Uses Euclidean distance between consecutive points.
        """
        if len(contour) < 2:
            return 0.0
        
        length = 0.0
        for i in range(len(contour)):
            pt1 = contour[i][0]
            pt2 = contour[(i + 1) % len(contour)][0]
            length += np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
        
        return length
    
    def calculate_area(self, contour: np.ndarray) -> float:
        """
        Calculate enclosed area using the Shoelace formula.
        Auto-closes the polygon if needed.
        """
        if len(contour) < 3:
            return 0.0
        
        # Use OpenCV's built-in area calculation
        area = cv2.contourArea(contour)
        
        # If area is negative, contour might be in wrong orientation
        area = abs(area)
        
        return area
    
    def is_contour_closed(self, contour: np.ndarray, threshold: float = 5.0) -> bool:
        """
        Check if a contour is closed by comparing first and last points.
        """
        if len(contour) < 3:
            return False
        
        first_point = contour[0][0]
        last_point = contour[-1][0]
        
        distance = np.sqrt(
            (last_point[0] - first_point[0])**2 + 
            (last_point[1] - first_point[1])**2
        )
        
        return distance < threshold
    
    def auto_close_contour(self, contour: np.ndarray) -> np.ndarray:
        """
        Close an open contour by adding the first point at the end.
        """
        if len(contour) == 0:
            return contour
        
        first_point = contour[0].copy()
        closed_contour = np.vstack([contour, first_point])
        
        return closed_contour
    
    def detect_scale_reference(self, image: np.ndarray, contours: List[np.ndarray]) -> Optional[float]:
        """
        Attempt to detect a reference scale (e.g., "1 meter" label or ruler).
        This is a simplified version - can be enhanced with OCR.
        Returns: scale_factor (pixels per meter) or None if not found.
        """
        # This is a placeholder - in a real implementation, you might:
        # 1. Use OCR to detect "1m", "1 meter" labels
        # 2. Detect standard ruler markings
        # 3. Look for labeled reference lines
        
        # For now, return None (pixel units only)
        return None
    
    def process_image(self, image_path: str) -> Dict:
        """
        Main processing function.
        Takes an image path, processes it, and returns measurements.
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Preprocess
        processed, original_color = self.preprocess_image(image)
        
        # Detect lines
        contours, detection_mask = self.detect_drawn_lines(processed, original_color)
        
        if not contours:
            return {
                "line_length": "0",
                "area": "0",
                "unit": "pixels",
                "notes": "No drawn lines detected in the image."
            }
        
        # Combine all contours into one main boundary
        # For now, we'll process the largest contour as the main boundary
        main_contour = max(contours, key=cv2.contourArea)
        
        # Check if closed
        is_closed = self.is_contour_closed(main_contour)
        
        if not is_closed:
            main_contour = self.auto_close_contour(main_contour)
        
        # Calculate measurements
        line_length = self.calculate_line_length(main_contour)
        area = self.calculate_area(main_contour)
        
        # Try to detect scale
        scale_factor = self.detect_scale_reference(image, contours)
        
        notes_list = []
        if not is_closed:
            notes_list.append("Boundary was open and was auto-closed.")
        if len(contours) > 1:
            notes_list.append(f"Detected {len(contours)} separate line segments. Using the largest as main boundary.")
        
        # Convert units if scale found
        if scale_factor:
            line_length_m = line_length / scale_factor
            area_sq_m = area / (scale_factor ** 2)
            unit = "meters"
            line_length_str = f"{line_length_m:.2f}"
            area_str = f"{area_sq_m:.2f}"
        else:
            unit = "pixels"
            line_length_str = f"{line_length:.2f}"
            area_str = f"{area:.2f}"
            notes_list.append("No reference scale detected. Measurements in pixels only.")
        
        notes = " ".join(notes_list) if notes_list else "Processing completed successfully."
        
        return {
            "line_length": line_length_str,
            "area": area_str,
            "unit": unit,
            "notes": notes
        }
    
    def process_image_array(self, image_array: np.ndarray) -> Dict:
        """
        Process image from numpy array (for API usage).
        """
        # Save temporarily or process directly
        # For now, we'll process directly
        processed, original_color = self.preprocess_image(image_array)
        
        # Detect lines
        contours, detection_mask = self.detect_drawn_lines(processed, original_color)
        
        if not contours:
            return {
                "line_length": "0",
                "area": "0",
                "unit": "pixels",
                "notes": "No drawn lines detected in the image."
            }
        
        # Combine all contours
        main_contour = max(contours, key=cv2.contourArea)
        
        # Check if closed
        is_closed = self.is_contour_closed(main_contour)
        
        if not is_closed:
            main_contour = self.auto_close_contour(main_contour)
        
        # Calculate measurements
        line_length = self.calculate_line_length(main_contour)
        area = self.calculate_area(main_contour)
        
        # Try to detect scale
        scale_factor = self.detect_scale_reference(image_array, contours)
        
        notes_list = []
        if not is_closed:
            notes_list.append("Boundary was open and was auto-closed.")
        if len(contours) > 1:
            notes_list.append(f"Detected {len(contours)} separate line segments. Using the largest as main boundary.")
        
        # Convert units if scale found
        if scale_factor:
            line_length_m = line_length / scale_factor
            area_sq_m = area / (scale_factor ** 2)
            unit = "meters"
            line_length_str = f"{line_length_m:.2f}"
            area_str = f"{area_sq_m:.2f}"
        else:
            unit = "pixels"
            line_length_str = f"{line_length:.2f}"
            area_str = f"{area:.2f}"
            notes_list.append("No reference scale detected. Measurements in pixels only.")
        
        notes = " ".join(notes_list) if notes_list else "Processing completed successfully."
        
        return {
            "line_length": line_length_str,
            "area": area_str,
            "unit": unit,
            "notes": notes
        }


if __name__ == "__main__":
    # Test code
    import sys
    
    if len(sys.argv) > 1:
        processor = ImageMeasurementProcessor()
        result = processor.process_image(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python image_processor.py <image_path>")


