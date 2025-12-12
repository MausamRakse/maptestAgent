"""
Area and Distance Calculation Utilities
Converts between different units and calculates measurements
"""

import math
from typing import Dict, List


class AreaCalculator:
    """Utilities for area and distance calculations with unit conversions."""
    
    # Conversion factors to square meters
    CONVERSIONS = {
        'sq_meters': 1.0,
        'sq_feet': 10.764,  # 1 sq meter = 10.764 sq feet
        'acres': 0.000247105,  # 1 sq meter = 0.000247105 acres
        'sq_pixels': 0.0  # Special case, requires scale
    }
    
    def __init__(self, pixels_per_meter: float = None):
        """
        Initialize calculator.
        
        Args:
            pixels_per_meter: Conversion factor from pixels to meters
        """
        self.pixels_per_meter = pixels_per_meter
    
    def calculate_area_sq_meters(self, area_sq_pixels: float) -> float:
        """Convert area from square pixels to square meters."""
        if not self.pixels_per_meter:
            raise ValueError("pixels_per_meter must be set for conversion")
        
        area_sq_meters = area_sq_pixels / (self.pixels_per_meter ** 2)
        return area_sq_meters
    
    def convert_to_all_units(self, area_sq_meters: float) -> Dict[str, float]:
        """
        Convert area to all supported units.
        
        Args:
            area_sq_meters: Area in square meters
            
        Returns:
            Dict with area in all units
        """
        return {
            'sq_meters': round(area_sq_meters, 2),
            'sq_feet': round(area_sq_meters * self.CONVERSIONS['sq_feet'], 2),
            'acres': round(area_sq_meters * self.CONVERSIONS['acres'], 4)
        }
    
    def calculate_perimeter(self, points: List[List[int]]) -> float:
        """
        Calculate perimeter from points (in pixels).
        
        Args:
            points: List of [x, y] coordinates
            
        Returns:
            Perimeter in pixels
        """
        if len(points) < 2:
            return 0.0
        
        perimeter = 0.0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            perimeter += distance
        
        return perimeter
    
    def convert_distance(self, distance_pixels: float, unit: str = 'meters') -> Dict[str, float]:
        """
        Convert distance from pixels to real-world units.
        
        Args:
            distance_pixels: Distance in pixels
            unit: Target unit ('meters', 'feet', 'yards')
            
        Returns:
            Dict with distance in different units
        """
        if not self.pixels_per_meter:
            return {'pixels': distance_pixels}
        
        distance_meters = distance_pixels / self.pixels_per_meter
        
        conversions = {
            'meters': distance_meters,
            'feet': distance_meters * 3.28084,
            'yards': distance_meters * 1.09361,
            'miles': distance_meters * 0.000621371
        }
        
        return {k: round(v, 2) for k, v in conversions.items()}
    
    def estimate_pixels_per_meter_from_zoom(self, lat: float, zoom: int) -> float:
        """
        Estimate pixels per meter based on zoom level and latitude.
        
        Args:
            lat: Latitude
            zoom: Zoom level
            
        Returns:
            Estimated pixels per meter
        """
        # Standard tile size
        tile_size_pixels = 256
        
        # Meters per pixel at equator for given zoom
        meters_per_pixel_at_equator = 156543.03392 / (2 ** zoom)
        
        # Adjust for latitude
        meters_per_pixel = meters_per_pixel_at_equator * math.cos(math.radians(lat))
        
        # Convert to pixels per meter
        pixels_per_meter = 1.0 / meters_per_pixel
        
        return pixels_per_meter
    
    def calculate_scale_from_reference(
        self, 
        reference_pixel_length: float, 
        reference_real_length: float, 
        unit: str = 'meters'
    ) -> float:
        """
        Calculate pixels_per_meter from a reference measurement.
        
        Args:
            reference_pixel_length: Length in pixels
            reference_real_length: Real-world length
            unit: Unit of real-world length
            
        Returns:
            Pixels per meter
        """
        # Convert to meters
        unit_to_meters = {
            'meters': 1.0,
            'feet': 0.3048,
            'yards': 0.9144,
            'inches': 0.0254,
            'cm': 0.01,
            'mm': 0.001
        }
        
        if unit.lower() not in unit_to_meters:
            raise ValueError(f"Unknown unit: {unit}")
        
        real_length_meters = reference_real_length * unit_to_meters[unit.lower()]
        
        if real_length_meters == 0:
            raise ValueError("Reference length cannot be zero")
        
        pixels_per_meter = reference_pixel_length / real_length_meters
        
        return pixels_per_meter

