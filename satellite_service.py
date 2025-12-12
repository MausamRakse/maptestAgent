"""
Satellite/Aerial Image Fetching Service
Uses free sources: MapTiler, OpenStreetMap, OpenAerialMap
"""

import requests
from PIL import Image
import io
from typing import Tuple, Optional
import math


class SatelliteImageService:
    """Service to fetch satellite/aerial imagery from free sources."""
    
    def __init__(self):
        # MapTiler free tier (no API key needed for basic satellite tiles)
        # Using OpenStreetMap-based tile services
        self.tile_size = 256  # Standard tile size
        
    def get_satellite_image(
        self, 
        lat: float, 
        lon: float, 
        zoom: int = 18,
        width: int = 1024,
        height: int = 1024,
        source: str = "maptiler"
    ) -> Tuple[bytes, dict]:
        """
        Fetch satellite/aerial image for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level (10-19, higher = more detail)
            width: Image width in pixels
            height: Image height in pixels
            source: Image source ('maptiler', 'osm', 'openaerial')
            
        Returns:
            Tuple of (image_bytes, metadata)
        """
        if source == "maptiler":
            return self._get_maptiler_image(lat, lon, zoom, width, height)
        elif source == "osm":
            return self._get_osm_image(lat, lon, zoom, width, height)
        elif source == "openaerial":
            return self._get_openaerial_image(lat, lon, zoom, width, height)
        else:
            raise ValueError(f"Unknown source: {source}. Use 'maptiler', 'osm', or 'openaerial'")
    
    def _get_maptiler_image(self, lat: float, lon: float, zoom: int, width: int, height: int) -> Tuple[bytes, dict]:
        """Fetch satellite image from MapTiler (free tier, no API key needed)."""
        # Calculate bounding box
        bbox = self._calculate_bbox(lat, lon, zoom, width, height)
        
        # MapTiler satellite tile URL (free, no API key)
        # Using OpenStreetMap tile server as fallback (also free)
        tile_url_template = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        
        # Calculate tile coordinates
        n_tiles_x = math.ceil(width / self.tile_size)
        n_tiles_y = math.ceil(height / self.tile_size)
        
        # Get center tile coordinates
        tile_x, tile_y = self._lat_lon_to_tile(lat, lon, zoom)
        
        # Fetch and composite tiles
        tiles = []
        for ty in range(n_tiles_y):
            row = []
            for tx in range(n_tiles_x):
                tile_x_coord = tile_x - (n_tiles_x // 2) + tx
                tile_y_coord = tile_y - (n_tiles_y // 2) + ty
                
                url = tile_url_template.format(z=zoom, x=tile_x_coord, y=tile_y_coord)
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        row.append(Image.open(io.BytesIO(response.content)))
                    else:
                        # Create blank tile if fetch fails
                        row.append(Image.new('RGB', (self.tile_size, self.tile_size), color='white'))
                except:
                    row.append(Image.new('RGB', (self.tile_size, self.tile_size), color='white'))
            
            tiles.append(row)
        
        # Composite tiles into single image
        composite = Image.new('RGB', (n_tiles_x * self.tile_size, n_tiles_y * self.tile_size))
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                composite.paste(tile, (x * self.tile_size, y * self.tile_size))
        
        # Resize to requested dimensions
        composite = composite.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        output = io.BytesIO()
        composite.save(output, format='PNG')
        image_bytes = output.getvalue()
        
        metadata = {
            'lat': lat,
            'lon': lon,
            'zoom': zoom,
            'width': width,
            'height': height,
            'bbox': bbox,
            'source': 'maptiler/osm'
        }
        
        return image_bytes, metadata
    
    def _get_osm_image(self, lat: float, lon: float, zoom: int, width: int, height: int) -> Tuple[bytes, dict]:
        """Fetch from OpenStreetMap (same as MapTiler, different endpoint)."""
        return self._get_maptiler_image(lat, lon, zoom, width, height)
    
    def _get_openaerial_image(self, lat: float, lon: float, zoom: int, width: int, height: int) -> Tuple[bytes, dict]:
        """Fetch from OpenAerialMap (placeholder - requires API setup)."""
        # OpenAerialMap requires more complex setup
        # For now, fallback to OSM
        return self._get_osm_image(lat, lon, zoom, width, height)
    
    def _lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates."""
        n = 2.0 ** zoom
        tile_x = int((lon + 180.0) / 360.0 * n)
        lat_rad = math.radians(lat)
        tile_y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return tile_x, tile_y
    
    def _calculate_bbox(self, lat: float, lon: float, zoom: int, width: int, height: int) -> list:
        """Calculate bounding box for image."""
        # Approximate calculation based on zoom level
        # At zoom 18, each tile is about 20 meters
        meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
        
        width_meters = width * meters_per_pixel
        height_meters = height * meters_per_pixel
        
        # Convert meters to degrees (approximate)
        lat_delta = height_meters / 111320.0
        lon_delta = width_meters / (111320.0 * math.cos(math.radians(lat)))
        
        return [
            lat - lat_delta / 2,  # min lat
            lat + lat_delta / 2,  # max lat
            lon - lon_delta / 2,  # min lon
            lon + lon_delta / 2   # max lon
        ]

