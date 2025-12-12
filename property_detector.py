"""
Property Boundary and Zone Detection
Detects property boundaries, house area, and yard zones
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from image_processor import ImageMeasurementProcessor


class PropertyDetector:
    """Detects property boundaries and zones (house, front yard, back yard, etc.)."""
    
    def __init__(self):
        self.processor = ImageMeasurementProcessor()
    
    def detect_property_boundaries(self, image: np.ndarray) -> Dict:
        """
        Detect property boundaries from satellite/aerial image.
        
        Returns:
            Dict with property boundary coordinates and zones
        """
        # Preprocess image
        processed, original = self.processor.preprocess_image(image)
        
        # Detect boundaries (fences, walls, property lines)
        contours, _ = self.processor.detect_drawn_lines(processed, original)
        
        if not contours:
            return {
                'property_boundary': None,
                'zones': {},
                'notes': 'No property boundaries detected. Please draw manually.'
            }
        
        # Get main property boundary (largest contour)
        main_boundary = max(contours, key=cv2.contourArea)
        
        # Convert contour to list of points
        boundary_points = [[int(pt[0][0]), int(pt[0][1])] for pt in main_boundary]
        
        # Detect zones
        zones = self._detect_zones(image, main_boundary, contours)
        
        return {
            'property_boundary': boundary_points,
            'zones': zones,
            'total_contours': len(contours)
        }
    
    def _detect_zones(self, image: np.ndarray, main_boundary: np.ndarray, all_contours: List) -> Dict:
        """
        Detect different zones: house, front yard, back yard, side yards, garden.
        
        This is a simplified detection - in production, you'd use ML models or
        more sophisticated image analysis.
        """
        zones = {}
        
        # Get image dimensions
        h, w = image.shape[:2]
        
        # Split image into regions
        center_x, center_y = w // 2, h // 2
        
        # House area (typically in center, has rectangular structures)
        # This is a heuristic - in real implementation, use object detection
        house_region = self._detect_house_structure(image, center_x, center_y)
        if house_region:
            zones['house'] = {
                'boundary': house_region,
                'area_pixels': cv2.contourArea(np.array(house_region, dtype=np.int32))
            }
        
        # Divide property into front/back/side yards
        # Front yard (bottom half of property)
        front_yard_boundary = self._get_yard_region(main_boundary, 'front', h, w)
        if front_yard_boundary:
            zones['front_yard'] = {
                'boundary': front_yard_boundary,
                'area_pixels': cv2.contourArea(np.array(front_yard_boundary, dtype=np.int32))
            }
        
        # Back yard (top half of property)
        back_yard_boundary = self._get_yard_region(main_boundary, 'back', h, w)
        if back_yard_boundary:
            zones['back_yard'] = {
                'boundary': back_yard_boundary,
                'area_pixels': cv2.contourArea(np.array(back_yard_boundary, dtype=np.int32))
            }
        
        # Side yards
        left_yard = self._get_yard_region(main_boundary, 'left', h, w)
        if left_yard:
            zones['left_yard'] = {
                'boundary': left_yard,
                'area_pixels': cv2.contourArea(np.array(left_yard, dtype=np.int32))
            }
        
        right_yard = self._get_yard_region(main_boundary, 'right', h, w)
        if right_yard:
            zones['right_yard'] = {
                'boundary': right_yard,
                'area_pixels': cv2.contourArea(np.array(right_yard, dtype=np.int32))
            }
        
        return zones
    
    def _detect_house_structure(self, image: np.ndarray, center_x: int, center_y: int) -> Optional[List]:
        """
        Detect house structure (simplified - looks for rectangular structures).
        In production, use object detection models.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for rectangular structures near center
        house_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 5000 < area < 50000:  # Reasonable house size range in pixels
                # Check if near center
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Check if within center region
                    if abs(cx - center_x) < image.shape[1] * 0.3 and abs(cy - center_y) < image.shape[0] * 0.3:
                        # Check if roughly rectangular
                        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                        if len(approx) >= 4:
                            house_contours.append(contour)
        
        if house_contours:
            # Return largest house-like structure
            largest = max(house_contours, key=cv2.contourArea)
            return [[int(pt[0][0]), int(pt[0][1])] for pt in largest]
        
        return None
    
    def _get_yard_region(self, boundary: np.ndarray, region: str, height: int, width: int) -> Optional[List]:
        """
        Get yard region boundary (front, back, left, right).
        This divides the property boundary into zones.
        """
        # Get bounding box of property
        x, y, w, h = cv2.boundingRect(boundary)
        
        boundary_points = [[int(pt[0][0]), int(pt[0][1])] for pt in boundary]
        
        # Create region polygon based on direction
        if region == 'front':
            # Front yard: bottom half
            region_points = [
                [x, y + h // 2],
                [x + w, y + h // 2],
                [x + w, y + h],
                [x, y + h]
            ]
        elif region == 'back':
            # Back yard: top half
            region_points = [
                [x, y],
                [x + w, y],
                [x + w, y + h // 2],
                [x, y + h // 2]
            ]
        elif region == 'left':
            # Left yard: left half
            region_points = [
                [x, y],
                [x + w // 2, y],
                [x + w // 2, y + h],
                [x, y + h]
            ]
        elif region == 'right':
            # Right yard: right half
            region_points = [
                [x + w // 2, y],
                [x + w, y],
                [x + w, y + h],
                [x + w // 2, y + h]
            ]
        else:
            return None
        
        # Intersect with property boundary (simplified - just return region)
        return region_points
    
    def calculate_garden_area(self, manual_points: List[List[int]]) -> float:
        """
        Calculate garden area from manually drawn points.
        
        Args:
            manual_points: List of [x, y] coordinates
            
        Returns:
            Area in square pixels
        """
        if len(manual_points) < 3:
            return 0.0
        
        points_array = np.array(manual_points, dtype=np.int32)
        area = cv2.contourArea(points_array)
        
        return abs(area)
    
    def calculate_perimeter_pixels(self, points: List[List[int]]) -> float:
        """Calculate perimeter from points in pixels."""
        return self.processor.calculate_line_length(
            np.array(points, dtype=np.float32).reshape(-1, 1, 2)
        )

