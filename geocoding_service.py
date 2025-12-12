"""
Geocoding Service for US Addresses
Uses Nominatim (OpenStreetMap) for free geocoding
"""

import requests
from typing import Dict, Optional, Tuple
import time


class GeocodingService:
    """Geocoding service using Nominatim (OpenStreetMap)."""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'ImageMeasurementApp/1.0'  # Required by Nominatim
        }
    
    def geocode_address(self, address: str) -> Dict:
        """
        Geocode a US address to get coordinates.
        
        Args:
            address: US address string
            
        Returns:
            Dict with lat, lon, display_name, and bounding box
        """
        # Validate it's a US address (basic check)
        if not self._is_us_address(address):
            raise ValueError("Please provide a valid US address")
        
        # Format address for Nominatim
        formatted_address = self._format_address(address)
        
        params = {
            'q': formatted_address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us',  # Restrict to US
            'addressdetails': 1
        }
        
        try:
            # Respect rate limiting (Nominatim allows 1 request per second)
            time.sleep(1)
            
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise ValueError(f"Address not found: {address}")
            
            result = data[0]
            
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result.get('display_name', address),
                'boundingbox': [
                    float(result['boundingbox'][0]),  # min lat
                    float(result['boundingbox'][1]),  # max lat
                    float(result['boundingbox'][2]),  # min lon
                    float(result['boundingbox'][3])   # max lon
                ],
                'address': {
                    'house_number': result.get('address', {}).get('house_number', ''),
                    'road': result.get('address', {}).get('road', ''),
                    'city': result.get('address', {}).get('city', ''),
                    'state': result.get('address', {}).get('state', ''),
                    'postcode': result.get('address', {}).get('postcode', ''),
                    'country': result.get('address', {}).get('country', '')
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error geocoding address: {str(e)}")
    
    def _is_us_address(self, address: str) -> bool:
        """Basic validation to check if address appears to be US-based."""
        # Check for common US indicators
        us_indicators = ['usa', 'united states', 'us', 'u.s.']
        address_lower = address.lower()
        
        # Check if contains US state abbreviations or full names
        us_states = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id',
                    'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms',
                    'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok',
                    'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv',
                    'wi', 'wy']
        
        # Simple check - if contains state abbreviation or US indicators
        for indicator in us_indicators:
            if indicator in address_lower:
                return True
        
        # Check for 5-digit zip code pattern
        import re
        if re.search(r'\b\d{5}(-\d{4})?\b', address):
            return True
        
        # If no clear indicators, assume it might be US (user will see if wrong)
        return True
    
    def _format_address(self, address: str) -> str:
        """Format address for Nominatim search."""
        # Add "USA" if not present
        address_clean = address.strip()
        if not any(term in address_clean.lower() for term in ['usa', 'united states', ' us ', ' u.s.']):
            address_clean += ", USA"
        
        return address_clean
    
    def reverse_geocode(self, lat: float, lon: float) -> Dict:
        """
        Reverse geocode coordinates to get address.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with address information
        """
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1
        }
        
        try:
            time.sleep(1)  # Rate limiting
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'display_name': data.get('display_name', ''),
                'address': data.get('address', {})
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error reverse geocoding: {str(e)}")

