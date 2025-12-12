"""
Test script for Image Measurement API
Creates a test image and tests all endpoints
"""

import cv2
import numpy as np
import requests
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a test image with drawn lines/boundary."""
    print("📝 Creating test image...")
    
    # Create a white background
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw a rectangular boundary (simulating a yard/garden)
    # Using blue color (BGR format)
    points = np.array([
        [100, 100],
        [700, 100],
        [700, 500],
        [100, 500],
        [100, 100]  # Close the polygon
    ], np.int32)
    
    # Draw thick blue lines
    cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=5)
    
    # Also draw a smaller inner shape
    inner_points = np.array([
        [200, 200],
        [600, 200],
        [600, 400],
        [200, 400],
        [200, 200]
    ], np.int32)
    
    cv2.polylines(img, [inner_points], isClosed=True, color=(0, 0, 255), thickness=4)
    
    # Save test image
    test_image_path = "test_image.jpg"
    cv2.imwrite(test_image_path, img)
    print(f"✅ Test image created: {test_image_path}")
    print(f"   - Outer rectangle: 600x400 pixels")
    print(f"   - Inner rectangle: 400x200 pixels")
    
    return test_image_path

def test_basic_measurement(image_path):
    """Test the basic measurement endpoint."""
    print("\n" + "="*60)
    print("🧪 Test 1: Basic Measurement Endpoint")
    print("="*60)
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            response = requests.post(f"{BASE_URL}/api/measure", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print("\n📊 Results:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_measurement_with_scale(image_path):
    """Test measurement with manual scale input."""
    print("\n" + "="*60)
    print("🧪 Test 2: Measurement with Scale Reference")
    print("="*60)
    
    try:
        # Assume 600 pixels = 10 meters (for the outer rectangle width)
        reference_pixels = 600
        reference_length = 10
        reference_unit = "meters"
        
        with open(image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            params = {
                'reference_pixels': reference_pixels,
                'reference_length': reference_length,
                'reference_unit': reference_unit
            }
            response = requests.post(
                f"{BASE_URL}/api/measure-with-scale",
                files=files,
                params=params
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"\n📏 Scale: {reference_pixels} pixels = {reference_length} {reference_unit}")
            print("\n📊 Results:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_visualization_endpoint(image_path):
    """Test the visualization endpoint."""
    print("\n" + "="*60)
    print("🧪 Test 3: Visualization Endpoint")
    print("="*60)
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            response = requests.post(
                f"{BASE_URL}/api/measure-with-visualization",
                files=files
            )
        
        if response.status_code == 200:
            # Save visualization
            output_path = "test_result_visualization.png"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print("✅ Request successful!")
            print(f"📸 Visualization saved to: {output_path}")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_docs():
    """Test if API docs are accessible."""
    print("\n" + "="*60)
    print("🧪 Test 4: API Documentation")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation is accessible")
            print(f"📚 Open in browser: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ API docs not accessible. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "🚀"*30)
    print("IMAGE MEASUREMENT API - TEST SUITE")
    print("🚀"*30 + "\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print("✅ Server is running\n")
    except:
        print("❌ Server is not running!")
        print("Please start the server first: python api.py")
        return
    
    # Create test image
    test_image = create_test_image()
    
    # Run tests
    results = []
    results.append(("Basic Measurement", test_basic_measurement(test_image)))
    results.append(("Measurement with Scale", test_measurement_with_scale(test_image)))
    results.append(("Visualization", test_visualization_endpoint(test_image)))
    results.append(("API Documentation", test_api_docs()))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("\n" + "="*60)
    print("💡 Next steps:")
    print(f"   - Open web UI: {BASE_URL}/static/index.html")
    print(f"   - View API docs: {BASE_URL}/docs")
    print(f"   - Check visualization: test_result_visualization.png")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()


