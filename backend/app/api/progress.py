"""
AdTicks — Scan Progress WebSocket Router.

Provides real-time progress updates for running scans via WebSocket.
Clients connect with a task_id and receive live updates.

Usage:
    WS /api/ws/scan/progress/{task_id}?auth_token={bearer_token}
"""

import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.models.user import User
from app.core.progress import ScanProgress
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws/scan", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections for progress updates."""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        """Register a new client."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"Client connected to task {task_id}")
    
    async def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        """Unregister a client."""
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"Client disconnected from task {task_id}")
    
    async def broadcast(self, task_id: str, message: dict) -> None:
        """Send message to all clients listening to a task."""
        if task_id not in self.active_connections:
            return
        
        dead_connections = []
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            await self.disconnect(task_id, conn)


manager = ConnectionManager()


@router.websocket("/progress/{task_id}")
async def websocket_progress_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time scan progress.
    """
    await websocket.accept()
    logger.info(f"WebSocket client connected for task {task_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Connected to progress stream"
        })
        
        last_progress = -1
        
        # Poll Redis for this specific task's progress
        while True:
            try:
                progress_data = await ScanProgress.get_progress_for_task(task_id)
                
                if progress_data:
                    current_progress = progress_data.get("progress", 0)
                    # Only send if progress changed or it's a heartbeat (every 5 polls)
                    await websocket.send_json({
                        "type": "progress",
                        **progress_data
                    })
                    last_progress = current_progress
                    
                    if current_progress == 100 or progress_data.get("stage") == "completed":
                        logger.info(f"Task {task_id} completed, closing WebSocket")
                        break
                
                # Wait before next poll
                await asyncio.sleep(1.5)
                
                # Check if client is still there by trying to receive
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except asyncio.TimeoutError:
                    pass
                    
            except (asyncio.CancelledError, WebSocketDisconnect):
                break
            except Exception as e:
                logger.warning(f"Error in progress WebSocket loop: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"WebSocket connection finished for task {task_id}")


@router.get("/progress/{task_id}")
async def get_scan_progress(
    task_id: str,
    current_user: User = Depends(lambda: None)  # Optional auth
) -> dict:
    """
    HTTP endpoint to get current scan progress (REST alternative to WebSocket).
    
    Useful for polling clients that can't use WebSocket.
    
    Returns:
    {
        "task_id": "uuid",
        "stage": "rank_tracking",
        "progress": 45,
        "message": "Checked 45/100 keywords",
        "elapsed_seconds": 320,
        "estimated_completion_at": "2026-04-24T22:30:00Z"
    }
    """
    progress_data = await ScanProgress.get_progress_for_task(task_id)
    
    if progress_data:
        return {
            "status": "in_progress",
            **progress_data
        }
    else:
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "Progress data not found (task may be completed or failed)"
        }
