# Image Area & Line Measurement Agent

A sophisticated image processing tool that detects user-drawn lines/boundaries in images and calculates their length and enclosed area. Supports automatic scale detection for converting pixel measurements to real-world units.

## 🎯 Features

### Core Capabilities

- **Address-Based Measurement**: Enter any US address to get satellite imagery and measurements
- **Satellite Image Fetching**: Free satellite/aerial imagery from OpenStreetMap and MapTiler
- **Property Boundary Detection**: Automatic detection of property boundaries and structures
- **Zone Measurement**: Measure different zones:
  - House area
  - Front yard
  - Back yard
  - Side yards (left/right)
  - Custom garden areas

### Measurement Tools

- **Interactive Drawing**: Draw polygons and lines directly on the map
- **Auto-Detection**: Automatic zone detection from satellite imagery
- **Multiple Units**: Results in square feet, square meters, and acres
- **Scale Setting**: Manual scale reference or automatic estimation

### Technical Features

- **Geocoding**: Free address geocoding using Nominatim (OpenStreetMap)
- **Image Processing**: OpenCV-based boundary and structure detection
- **Real-time Calculations**: Instant measurements with unit conversions
- **Download/Export**: Download satellite images and measurement results

### API & Frontend

- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Interactive Map UI**: Leaflet.js-based map with drawing tools
- **Responsive Design**: Works on desktop and mobile devices
- **Location Confirmation**: Preview and confirm location before measurement

## 📋 Requirements

- Python 3.8+
- OpenCV 4.8+
- NumPy
- FastAPI
- Pillow

## 🚀 Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd "length caluatero"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Option 1: Web UI (Recommended)

1. **Start the API server**:
   ```bash
   python api.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000/static/index.html`

3. **Upload an image**:
   - Drag and drop an image or click "Choose Image"
   - Optionally provide scale reference (pixel length and real-world length)
   - Click "Process Image"
   - View results with length, area, and notes

### Option 2: Command Line

Process a single image directly:

```bash
python image_processor.py path/to/your/image.jpg
```

Output will be in JSON format:
```json
{
  "line_length": "1234.56",
  "area": "45678.90",
  "unit": "pixels",
  "notes": "Processing completed successfully."
}
```

### Option 3: API Endpoints

#### Basic Measurement
```bash
curl -X POST "http://localhost:8000/api/measure" \
  -F "file=@your_image.jpg"
```

#### With Manual Scale
```bash
curl -X POST "http://localhost:8000/api/measure-with-scale?reference_pixels=150&reference_length=5&reference_unit=meters" \
  -F "file=@your_image.jpg"
```

#### With Visualization Overlay
```bash
curl -X POST "http://localhost:8000/api/measure-with-visualization" \
  -F "file=@your_image.jpg" \
  --output result_overlay.png
```

#### Measure From Coordinates (no image)
```bash
curl -X POST "http://localhost:8000/api/measure-coordinates" \
  -H "Content-Type: application/json" \
  -d '{
        "points": [[100,100],[700,100],[700,500],[100,500]],
        "reference_pixels": 600,
        "reference_length": 10,
        "reference_unit": "meters"
      }'
```

## 📊 Output Format

All endpoints return JSON in the following strict format:

```json
{
  "line_length": "<value in meters or pixels>",
  "area": "<value in sq. meters or sq. pixels>",
  "unit": "<meters or pixels>",
  "notes": "Any assumptions, detection notes, or warnings."
}
```

## 🔧 How It Works

### Processing Pipeline

1. **Preprocessing**:
   - Convert to grayscale
   - Denoise using Non-local Means
   - Enhance contrast with CLAHE
   - Apply adaptive thresholding

2. **Line Detection**:
   - Color filtering (HSV color space) for markers
   - Canny edge detection
   - Morphological operations (dilation, closing) to connect gaps
   - Contour extraction

3. **Calculation**:
   - Line length: Sum of Euclidean distances between consecutive points
   - Area: Shoelace formula via OpenCV's `contourArea()`
   - Auto-close open polygons if needed

4. **Scale Detection** (if available):
   - Attempts OCR-based label detection (placeholder)
   - Ruler detection (placeholder)
   - Manual scale input support

5. **Output**:
   - Generate JSON response
   - Optional visualization overlay with detected lines and area

## 🎨 Visualization

When using the visualization endpoint, the output image includes:
- **Blue overlay**: Detected line/boundary
- **Green overlay**: Enclosed area (with transparency)
- **Text labels**: Length and area measurements

## ⚙️ Configuration

You can modify detection parameters in `image_processor.py`:

- `min_area`: Minimum contour area to filter noise (default: 50)
- Canny edge detection thresholds (default: 50, 150)
- Morphological kernel size and iterations
- Color ranges for marker detection

## 📝 Notes & Assumptions

- The system detects the **largest contour** as the main boundary
- If multiple contours are detected, all are mentioned in notes, but only the largest is measured
- Open boundaries are automatically closed (noted in output)
- If no scale is detected, measurements are in pixels only
- The system focuses on user-drawn lines and attempts to ignore building edges, shadows, and objects

## 🚧 Future Enhancements

- **OCR Integration**: Full scale detection using Tesseract or EasyOCR
- **Multi-contour Support**: Measure multiple boundaries separately
- **Advanced Segmentation**: Better separation of drawn lines from background
- **Deep Learning**: ML-based detection of user-drawn vs. non-drawn elements
- **Export Options**: Export measurements to CSV, PDF reports
- **Batch Processing**: Process multiple images at once

## 🐛 Troubleshooting

**No lines detected**:
- Ensure the image has sufficient contrast
- Try adjusting the preprocessing parameters
- Check if lines are in supported colors (blue, red, green, black)

**Incorrect measurements**:
- Provide a manual scale reference for accuracy
- Ensure the boundary is clearly drawn
- Check if the image resolution is adequate

**API not responding**:
- Verify FastAPI server is running on port 8000
- Check for port conflicts
- Ensure all dependencies are installed

## 📄 License

This project is provided as-is for educational and practical use.

## 🤝 Contributing

Feel free to enhance this tool with:
- Better scale detection algorithms
- OCR integration
- Additional visualization options
- Performance optimizations

---

**Built with** OpenCV, FastAPI, NumPy, and modern web technologies.

