"""
Scale Detection Module
Attempts to detect reference scales in images for unit conversion.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import re


class ScaleDetector:
    """Detects reference scales in images for pixel-to-real-world conversion."""
    
    def __init__(self):
        self.debug_mode = False
    
    def detect_scale_label(self, image: np.ndarray) -> Optional[Tuple[float, str]]:
        """
        Attempts to detect scale labels using OCR or pattern matching.
        Returns: (pixels_per_unit, unit_name) or None
        
        This is a placeholder for OCR integration. In production, you might use:
        - pytesseract (Tesseract OCR)
        - EasyOCR
        - AWS Textract
        """
        # Placeholder: Would use OCR here
        # For now, return None
        return None
    
    def detect_ruler(self, image: np.ndarray) -> Optional[float]:
        """
        Detects standard ruler markings to determine scale.
        Returns: pixels_per_unit or None
        """
        # This would detect ruler markings and known intervals
        # For now, return None
        return None
    
    def detect_reference_line(self, image: np.ndarray, contours: list) -> Optional[float]:
        """
        Looks for a labeled reference line (e.g., "1 meter" line).
        Compares contours to find potential reference lines.
        """
        # Look for small, straight line segments that might be reference markers
        for contour in contours:
            # Calculate bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Reference lines are typically small and straight
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, False)
            
            if perimeter > 0:
                # Compactness measure (circle = 1, line = very low)
                compactness = 4 * np.pi * area / (perimeter ** 2)
                
                # Lines have low compactness
                if compactness < 0.1 and area > 20:
                    # Check if it's roughly horizontal or vertical
                    aspect_ratio = max(w, h) / max(min(w, h), 1)
                    if aspect_ratio > 3:  # Line-like shape
                        # This could be a reference line
                        # Would need OCR or user input to determine actual length
                        pass
        
        return None
    
    def detect_scale(self, image: np.ndarray, contours: list) -> Optional[float]:
        """
        Main scale detection function.
        Tries multiple methods to detect a reference scale.
        Returns: pixels_per_meter or None
        """
        # Try OCR-based label detection
        label_result = self.detect_scale_label(image)
        if label_result:
            pixels_per_unit, unit = label_result
            # Convert to meters if needed
            if unit == "cm":
                return pixels_per_unit * 100
            elif unit == "mm":
                return pixels_per_unit * 1000
            elif unit == "m" or unit == "meter" or unit == "meters":
                return pixels_per_unit
            elif unit == "ft" or unit == "feet":
                return pixels_per_unit / 0.3048  # Convert feet to meters
            elif unit == "in" or unit == "inch":
                return pixels_per_unit / 0.0254  # Convert inches to meters
        
        # Try ruler detection
        ruler_result = self.detect_ruler(image)
        if ruler_result:
            return ruler_result
        
        # Try reference line detection
        ref_line_result = self.detect_reference_line(image, contours)
        if ref_line_result:
            return ref_line_result
        
        return None
    
    def manual_scale_input(self, pixel_length: float, real_length: float, unit: str = "meters") -> float:
        """
        Helper function for manual scale input.
        Given a pixel length and its real-world length, calculate pixels_per_meter.
        """
        if unit == "cm":
            real_length_m = real_length / 100
        elif unit == "mm":
            real_length_m = real_length / 1000
        elif unit == "m" or unit == "meter" or unit == "meters":
            real_length_m = real_length
        elif unit == "ft" or unit == "feet":
            real_length_m = real_length * 0.3048
        elif unit == "in" or unit == "inch":
            real_length_m = real_length * 0.0254
        else:
            real_length_m = real_length  # Assume meters
        
        if real_length_m > 0:
            return pixel_length / real_length_m
        
        return None


