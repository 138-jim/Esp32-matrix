#!/usr/bin/env python3
"""
Web API Server for LED Display Driver
FastAPI server with REST + WebSocket endpoints and static file serving
"""

import logging
import threading
import queue
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config_manager import ConfigManager
from .frame_receiver import validate_frame_data, bytes_to_frame
from .led_driver import LEDDriver
from .coordinate_mapper import CoordinateMapper
from .display_controller import DisplayController
from . import test_patterns

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class PanelUpdate(BaseModel):
    position: List[int]  # [x, y]
    rotation: int  # 0, 90, 180, 270


class ConfigUpdate(BaseModel):
    config: Dict[str, Any]


class BrightnessUpdate(BaseModel):
    brightness: int  # 0-255


class TestPatternRequest(BaseModel):
    pattern: str
    duration: Optional[float] = 0  # 0 = indefinite


class StatusResponse(BaseModel):
    fps: float
    queue_size: int
    brightness: int
    width: int
    height: int
    led_count: int
    config_path: str


class WebAPIServer:
    """
    Web API server for LED display control

    Provides REST API, WebSocket endpoints, and serves static web UI
    """

    def __init__(self,
                 frame_queue: queue.Queue,
                 config_reload_event: threading.Event,
                 led_driver: LEDDriver,
                 mapper: CoordinateMapper,
                 display_controller: DisplayController,
                 config_path: str,
                 static_dir: str = "static"):
        """
        Initialize web API server

        Args:
            frame_queue: Queue for submitting frames
            config_reload_event: Event to trigger config reload
            led_driver: LED driver instance
            mapper: Coordinate mapper instance
            display_controller: Display controller instance
            config_path: Path to configuration file
            static_dir: Directory containing static web files
        """
        self.frame_queue = frame_queue
        self.config_reload_event = config_reload_event
        self.led_driver = led_driver
        self.mapper = mapper
        self.display_controller = display_controller
        self.config_path = config_path
        self.static_dir = Path(static_dir)

        self.config_manager = ConfigManager()

        # Create FastAPI app
        self.app = FastAPI(title="LED Display Driver API", version="1.0.0")

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # WebSocket connections
        self.preview_connections: List[WebSocket] = []
        self.frame_connections: List[WebSocket] = []

        # Setup routes
        self._setup_routes()

        logger.info("Web API server initialized")

    def _setup_routes(self) -> None:
        """Setup all API routes"""

        # Serve static files
        if self.static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        # Root endpoint - serve web UI
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse("<h1>LED Display Driver</h1><p>Web UI not found</p>")

        # Configuration endpoints
        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration"""
            try:
                config = self.config_manager.load_config(self.config_path)
                return JSONResponse(content=config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/config")
        async def update_config(update: ConfigUpdate):
            """Update configuration"""
            try:
                new_config = update.config

                # Validate configuration
                is_valid, error_msg = self.config_manager.validate_config(new_config)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=f"Invalid configuration: {error_msg}")

                # Save configuration
                self.config_manager.save_config(new_config, self.config_path, create_backup=True)

                # Trigger reload
                self.config_reload_event.set()

                return {"status": "success", "message": "Configuration updated"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Panel endpoints
        @self.app.get("/api/panels")
        async def get_panels():
            """Get list of all panels"""
            try:
                config = self.config_manager.load_config(self.config_path)
                return JSONResponse(content={"panels": config["panels"]})
            except Exception as e:
                logger.error(f"Error getting panels: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/api/panels/{panel_id}")
        async def update_panel(panel_id: int, update: PanelUpdate):
            """Update single panel position/rotation"""
            try:
                config = self.config_manager.load_config(self.config_path)

                # Find panel
                panel_found = False
                for panel in config["panels"]:
                    if panel["id"] == panel_id:
                        panel["position"] = update.position
                        panel["rotation"] = update.rotation
                        panel_found = True
                        break

                if not panel_found:
                    raise HTTPException(status_code=404, detail=f"Panel {panel_id} not found")

                # Validate and save
                is_valid, error_msg = self.config_manager.validate_config(config)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=f"Invalid configuration: {error_msg}")

                self.config_manager.save_config(config, self.config_path, create_backup=True)

                # Trigger reload
                self.config_reload_event.set()

                return {"status": "success", "message": f"Panel {panel_id} updated"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating panel: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Frame submission endpoint
        @self.app.post("/api/frame")
        async def submit_frame(request: Request):
            """Submit frame via HTTP POST"""
            try:
                # Read binary data
                data = await request.body()

                # Get dimensions from mapper
                width, height = self.mapper.get_dimensions()

                # Validate frame data
                is_valid, error_msg = validate_frame_data(data, width, height)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=error_msg)

                # Convert to frame array
                frame = bytes_to_frame(data, width, height)

                # Add to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    raise HTTPException(status_code=503, detail="Frame queue full")

                return {"status": "success"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error submitting frame: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Brightness control
        @self.app.post("/api/brightness")
        async def set_brightness(update: BrightnessUpdate):
            """Set LED brightness"""
            try:
                brightness = update.brightness

                if not (0 <= brightness <= 255):
                    raise HTTPException(status_code=400, detail="Brightness must be 0-255")

                self.led_driver.set_brightness(brightness)

                return {"status": "success", "brightness": brightness}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error setting brightness: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Test pattern endpoint
        @self.app.post("/api/test-pattern")
        async def test_pattern(request: TestPatternRequest):
            """Display test pattern"""
            try:
                pattern_name = request.pattern
                width, height = self.mapper.get_dimensions()

                # Generate pattern
                frame = test_patterns.get_pattern(pattern_name, width, height, 0)

                # Add to queue
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    raise HTTPException(status_code=503, detail="Frame queue full")

                return {"status": "success", "pattern": pattern_name}

            except Exception as e:
                logger.error(f"Error displaying test pattern: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Status endpoint
        @self.app.get("/api/status")
        async def get_status():
            """Get system status"""
            try:
                width, height = self.mapper.get_dimensions()

                status = StatusResponse(
                    fps=self.display_controller.get_fps(),
                    queue_size=self.display_controller.get_queue_size(),
                    brightness=self.led_driver.get_brightness(),
                    width=width,
                    height=height,
                    led_count=self.mapper.get_led_count(),
                    config_path=self.config_path
                )

                return status

            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Available patterns endpoint
        @self.app.get("/api/patterns")
        async def get_patterns():
            """Get list of available test patterns"""
            return {"patterns": test_patterns.list_patterns()}

        # WebSocket for frame streaming
        @self.app.websocket("/ws/frames")
        async def websocket_frames(websocket: WebSocket):
            """WebSocket endpoint for streaming frames"""
            await websocket.accept()
            self.frame_connections.append(websocket)
            logger.info("Frame WebSocket client connected")

            try:
                while True:
                    # Receive binary frame data
                    data = await websocket.receive_bytes()

                    # Get dimensions
                    width, height = self.mapper.get_dimensions()

                    # Validate and parse
                    is_valid, error_msg = validate_frame_data(data, width, height)
                    if is_valid:
                        frame = bytes_to_frame(data, width, height)

                        try:
                            self.frame_queue.put_nowait(frame)
                        except queue.Full:
                            logger.warning("Frame queue full, dropping WebSocket frame")
                    else:
                        await websocket.send_json({"error": error_msg})

            except WebSocketDisconnect:
                logger.info("Frame WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.frame_connections:
                    self.frame_connections.remove(websocket)

        # WebSocket for live preview
        @self.app.websocket("/ws/preview")
        async def websocket_preview(websocket: WebSocket):
            """WebSocket endpoint for live preview feed"""
            await websocket.accept()
            self.preview_connections.append(websocket)
            logger.info("Preview WebSocket client connected")

            try:
                # Keep connection alive, send periodic updates
                while True:
                    await websocket.receive_text()  # Wait for ping

            except WebSocketDisconnect:
                logger.info("Preview WebSocket client disconnected")
            except Exception as e:
                logger.error(f"Preview WebSocket error: {e}")
            finally:
                if websocket in self.preview_connections:
                    self.preview_connections.remove(websocket)

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app
