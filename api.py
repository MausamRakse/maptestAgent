"""
FastAPI Backend for Image Measurement Service
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from PIL import Image
import cv2
import numpy as np
import io
import os
from pydantic import BaseModel
from image_processor import ImageMeasurementProcessor
from scale_detector import ScaleDetector
from geocoding_service import GeocodingService
from satellite_service import SatelliteImageService
from property_detector import PropertyDetector
from area_calculator import AreaCalculator
import json

app = FastAPI(title="Image Area & Line Measurement API")

# Enable CORS for frontend - MUST be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    if os.path.exists("static/index.html"):
        return "static/index.html"
    return {"message": "Frontend not found. Please ensure static/index.html exists."}

processor = ImageMeasurementProcessor()
scale_detector = ScaleDetector()
geocoding_service = GeocodingService()
satellite_service = SatelliteImageService()
property_detector = PropertyDetector()

class CoordinatesRequest(BaseModel):
    """Payload for coordinate-based measurement."""

    points: list
    reference_pixels: float | None = None
    reference_length: float | None = None
    reference_unit: str = "meters"

    def normalized_points(self) -> list:
        """Ensure points are list of [x, y] floats."""
        norm_points = []
        for p in self.points:
            if isinstance(p, dict):
                # Support {"x": .., "y": ..}
                x = p.get("x")
                y = p.get("y")
            else:
                try:
                    x, y = p[0], p[1]
                except Exception as exc:  # pragma: no cover - defensive
                    raise ValueError(f"Invalid point format: {p}") from exc
            if x is None or y is None:
                raise ValueError(f"Point missing coordinates: {p}")
            norm_points.append([float(x), float(y)])
        return norm_points


class AddressRequest(BaseModel):
    """Request for geocoding."""
    address: str


class SatelliteImageRequest(BaseModel):
    """Request for satellite image."""
    lat: float
    lon: float
    zoom: int = 18
    width: int = 1024
    height: int = 1024
    source: str = "maptiler"


class ZoneMeasurementRequest(BaseModel):
    """Request for zone measurement."""
    points: list
    zone_type: str  # 'property', 'house', 'front_yard', 'back_yard', 'left_yard', 'right_yard', 'garden'
    pixels_per_meter: float | None = None
    reference_pixels: float | None = None
    reference_length: float | None = None
    reference_unit: str = "meters"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Image Area & Line Measurement API", "status": "running"}


@app.post("/api/measure")
async def measure_image(file: UploadFile = File(...)):
    """
    Main endpoint for image measurement.
    Accepts an image file and returns measurements.
    """
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image file")
        
        # Process image
        result = processor.process_image_array(image)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/api/measure-coordinates")
async def measure_coordinates(payload: CoordinatesRequest):
    """
    Calculate length and area from user-provided coordinates.
    Accepts points as list of [x, y] or [{"x":..,"y":..}].
    Optional: reference_pixels, reference_length, reference_unit for scaling.
    """
    try:
        points = payload.normalized_points()
        if len(points) < 2:
            raise HTTPException(status_code=400, detail="At least two points are required.")

        points_np = np.array(points, dtype=np.float32)

        # Check closure and close if needed
        is_closed = np.allclose(points_np[0], points_np[-1])
        if not is_closed:
            points_np = np.vstack([points_np, points_np[0]])

        contour_cv = points_np.reshape(-1, 1, 2)

        # Measurements in pixels
        line_length_px = processor.calculate_line_length(contour_cv)
        area_px = processor.calculate_area(contour_cv)

        notes = []
        if not is_closed:
            notes.append("Boundary was open and was auto-closed.")

        # Apply scale if provided
        if payload.reference_pixels and payload.reference_length:
            scale_factor = scale_detector.manual_scale_input(
                payload.reference_pixels,
                payload.reference_length,
                payload.reference_unit,
            )
            if scale_factor:
                line_length_m = line_length_px / scale_factor
                area_sq_m = area_px / (scale_factor**2)
                notes.append(
                    f"Scale applied: {payload.reference_length} {payload.reference_unit} = {payload.reference_pixels} pixels"
                )
                return JSONResponse(
                    content={
                        "line_length": f"{line_length_m:.2f}",
                        "area": f"{area_sq_m:.2f}",
                        "unit": "meters",
                        "notes": " ".join(notes) if notes else "Processing completed successfully.",
                    }
                )

        # Default: pixels
        notes.append("No reference scale provided. Measurements in pixels only.")
        return JSONResponse(
            content={
                "line_length": f"{line_length_px:.2f}",
                "area": f"{area_px:.2f}",
                "unit": "pixels",
                "notes": " ".join(notes) if notes else "Processing completed successfully.",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing coordinates: {str(e)}")


@app.post("/api/measure-with-visualization")
async def measure_with_visualization(file: UploadFile = File(...)):
    """
    Endpoint that returns both measurements and a visualization overlay.
    """
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image file")
        
        # Process image
        result = processor.process_image_array(image)
        
        # Generate visualization (reprocess to get contours)
        processed, original_color = processor.preprocess_image(image)
        contours, _ = processor.detect_drawn_lines(processed, original_color)
        
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            is_closed = processor.is_contour_closed(main_contour)
            if not is_closed:
                main_contour = processor.auto_close_contour(main_contour)
            
            # Draw overlay
            overlay = image.copy()
            
            # Draw line in blue
            cv2.drawContours(overlay, [main_contour], -1, (255, 0, 0), 2)
            
            # Fill area in green with transparency
            overlay_area = image.copy()
            cv2.fillPoly(overlay_area, [main_contour], (0, 255, 0))
            overlay = cv2.addWeighted(overlay, 0.7, overlay_area, 0.3, 0)
            
            # Add text labels
            length_text = f"Length: {result['line_length']} {result['unit']}"
            area_text = f"Area: {result['area']} sq {result['unit']}"
            
            cv2.putText(overlay, length_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(overlay, area_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Encode image
            _, buffer = cv2.imencode('.png', overlay)
            image_bytes = io.BytesIO(buffer.tobytes())
            
            return StreamingResponse(image_bytes, media_type="image/png")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/api/measure-with-scale")
async def measure_with_scale(
    file: UploadFile = File(...),
    reference_pixels: float = None,
    reference_length: float = None,
    reference_unit: str = "meters"
):
    """
    Endpoint that allows manual scale input.
    If reference_pixels and reference_length are provided, uses them for conversion.
    """
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image file")
        
        # Process image
        processed, original_color = processor.preprocess_image(image)
        contours, _ = processor.detect_drawn_lines(processed, original_color)
        
        if not contours:
            return JSONResponse(content={
                "line_length": "0",
                "area": "0",
                "unit": "meters" if reference_pixels else "pixels",
                "notes": "No drawn lines detected in the image."
            })
        
        main_contour = max(contours, key=cv2.contourArea)
        is_closed = processor.is_contour_closed(main_contour)
        if not is_closed:
            main_contour = processor.auto_close_contour(main_contour)
        
        # Calculate measurements
        line_length_px = processor.calculate_line_length(main_contour)
        area_px = processor.calculate_area(main_contour)
        
        # Apply scale if provided
        if reference_pixels and reference_length:
            scale_factor = scale_detector.manual_scale_input(
                reference_pixels, reference_length, reference_unit
            )
            
            if scale_factor:
                line_length_m = line_length_px / scale_factor
                area_sq_m = area_px / (scale_factor ** 2)
                
                notes_list = []
                if not is_closed:
                    notes_list.append("Boundary was open and was auto-closed.")
                if len(contours) > 1:
                    notes_list.append(f"Detected {len(contours)} separate line segments. Using the largest as main boundary.")
                notes_list.append(f"Scale applied: {reference_length} {reference_unit} = {reference_pixels} pixels")
                
                return JSONResponse(content={
                    "line_length": f"{line_length_m:.2f}",
                    "area": f"{area_sq_m:.2f}",
                    "unit": "meters",
                    "notes": " ".join(notes_list)
                })
        
        # No scale provided, return pixel measurements
        notes_list = []
        if not is_closed:
            notes_list.append("Boundary was open and was auto-closed.")
        if len(contours) > 1:
            notes_list.append(f"Detected {len(contours)} separate line segments. Using the largest as main boundary.")
        notes_list.append("No reference scale provided. Measurements in pixels only.")
        
        return JSONResponse(content={
            "line_length": f"{line_length_px:.2f}",
            "area": f"{area_px:.2f}",
            "unit": "pixels",
            "notes": " ".join(notes_list)
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/api/geocode")
async def geocode_address(request: AddressRequest):
    """
    Geocode a US address to get coordinates.
    """
    try:
        result = geocoding_service.geocode_address(request.address)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error geocoding address: {str(e)}")


@app.post("/api/satellite-image")
async def get_satellite_image(request: SatelliteImageRequest):
    """
    Fetch satellite/aerial image for given coordinates.
    Returns image as PNG.
    """
    try:
        image_bytes, metadata = satellite_service.get_satellite_image(
            lat=request.lat,
            lon=request.lon,
            zoom=request.zoom,
            width=request.width,
            height=request.height,
            source=request.source
        )
        
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type="image/png",
            headers={
                "X-Image-Metadata": json.dumps(metadata)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satellite image: {str(e)}")


@app.post("/api/property-detect")
async def detect_property(file: UploadFile = File(...)):
    """
    Detect property boundaries and zones from satellite image.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image file")
        
        result = property_detector.detect_property_boundaries(image)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting property: {str(e)}")


@app.post("/api/measure-zones")
async def measure_zones(request: ZoneMeasurementRequest):
    """
    Measure specific zones (house, yards, garden) from coordinates.
    Returns measurements in multiple units.
    """
    try:
        points = request.points
        if len(points) < 3:
            raise HTTPException(status_code=400, detail="At least 3 points required for area calculation")
        
        # Calculate area in pixels
        points_np = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
        area_px = cv2.contourArea(points_np)
        
        # Calculate perimeter
        perimeter_px = processor.calculate_line_length(points_np)
        
        # Determine pixels per meter
        pixels_per_meter = None
        if request.pixels_per_meter:
            pixels_per_meter = request.pixels_per_meter
        elif request.reference_pixels and request.reference_length:
            calculator = AreaCalculator()
            pixels_per_meter = calculator.calculate_scale_from_reference(
                request.reference_pixels,
                request.reference_length,
                request.reference_unit
            )
        
        # Convert to real units
        if pixels_per_meter:
            area_sq_m = area_px / (pixels_per_meter ** 2)
            calculator = AreaCalculator(pixels_per_meter)
            all_units = calculator.convert_to_all_units(area_sq_m)
            
            # Distance conversions
            perimeter_m = perimeter_px / pixels_per_meter
            perimeter_units = calculator.convert_distance(perimeter_px, 'meters')
            
            return JSONResponse(content={
                'zone_type': request.zone_type,
                'area': all_units,
                'perimeter': perimeter_units,
                'pixels_per_meter': pixels_per_meter,
                'area_sq_pixels': round(area_px, 2),
                'perimeter_pixels': round(perimeter_px, 2)
            })
        else:
            return JSONResponse(content={
                'zone_type': request.zone_type,
                'area_sq_pixels': round(area_px, 2),
                'perimeter_pixels': round(perimeter_px, 2),
                'note': 'No scale provided. Measurements in pixels only.'
            })
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error measuring zones: {str(e)}")


@app.post("/api/property-measurement-summary")
async def property_measurement_summary(request: dict):
    """
    Get complete property measurement summary with all zones.
    Expects a dict with zone measurements and pixels_per_meter.
    """
    try:
        zones = request.get('zones', {})
        pixels_per_meter = request.get('pixels_per_meter')
        
        if not pixels_per_meter:
            raise HTTPException(status_code=400, detail="pixels_per_meter is required")
        
        calculator = AreaCalculator(pixels_per_meter)
        
        summary = {
            'property_total': {'area': {'sq_meters': 0, 'sq_feet': 0, 'acres': 0}},
            'zones': {}
        }
        
        total_area_sq_m = 0
        
        for zone_name, zone_data in zones.items():
            area_px = zone_data.get('area_pixels', 0)
            area_sq_m = area_px / (pixels_per_meter ** 2)
            total_area_sq_m += area_sq_m
            
            zone_summary = {
                'area': calculator.convert_to_all_units(area_sq_m)
            }
            
            if 'perimeter_pixels' in zone_data:
                perimeter_units = calculator.convert_distance(zone_data['perimeter_pixels'], 'meters')
                zone_summary['perimeter'] = perimeter_units
            
            summary['zones'][zone_name] = zone_summary
        
        summary['property_total']['area'] = calculator.convert_to_all_units(total_area_sq_m)
        
        return JSONResponse(content=summary)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

