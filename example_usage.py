"""
Example usage of the Image Measurement Processor
Demonstrates how to use the processor programmatically.
"""

from image_processor import ImageMeasurementProcessor
import json


def example_basic_usage():
    """Basic example: Process an image and get measurements."""
    print("=" * 50)
    print("Example 1: Basic Image Processing")
    print("=" * 50)
    
    processor = ImageMeasurementProcessor()
    
    # Replace with your image path
    image_path = "path/to/your/image.jpg"
    
    try:
        result = processor.process_image(image_path)
        print("\nResults:")
        print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print(f"\n⚠️  Image not found: {image_path}")
        print("Please provide a valid image path.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def example_with_custom_parameters():
    """Example showing how to customize processing parameters."""
    print("\n" + "=" * 50)
    print("Example 2: Custom Processing")
    print("=" * 50)
    
    processor = ImageMeasurementProcessor()
    processor.debug_mode = True  # Enable debug mode if needed
    
    # You can modify the processor's detection parameters
    # in the image_processor.py file:
    # - min_area in detect_drawn_lines()
    # - Canny thresholds
    # - Morphological kernel sizes
    # - Color ranges for marker detection
    
    print("\nTo customize processing, modify parameters in image_processor.py:")
    print("  - min_area: Minimum contour area (default: 50)")
    print("  - Canny edge thresholds (default: 50, 150)")
    print("  - Morphological operations iterations")
    print("  - HSV color ranges for marker detection")


def example_manual_scale():
    """Example showing manual scale input for unit conversion."""
    print("\n" + "=" * 50)
    print("Example 3: Manual Scale Conversion")
    print("=" * 50)
    
    from scale_detector import ScaleDetector
    
    detector = ScaleDetector()
    
    # Example: If you know a 150-pixel line represents 5 meters
    pixels = 150
    real_length = 5
    unit = "meters"
    
    scale_factor = detector.manual_scale_input(pixels, real_length, unit)
    
    print(f"\nScale Factor: {scale_factor:.2f} pixels per meter")
    print(f"Meaning: {pixels} pixels = {real_length} {unit}")
    
    # Now you can convert any pixel measurement
    pixel_measurement = 750
    real_measurement = pixel_measurement / scale_factor
    print(f"\nExample conversion:")
    print(f"  {pixel_measurement} pixels = {real_measurement:.2f} meters")


if __name__ == "__main__":
    print("\n📐 Image Measurement Processor - Usage Examples\n")
    
    # Run examples
    example_basic_usage()
    example_with_custom_parameters()
    example_manual_scale()
    
    print("\n" + "=" * 50)
    print("For web UI, run: python start_server.py")
    print("Then open: http://localhost:8000/static/index.html")
    print("=" * 50 + "\n")


