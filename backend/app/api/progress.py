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

logger = logging.getLogger(__name__)

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
    
    Clients connect and receive progress updates as the scan runs.
    
    Message Format:
    {
        "type": "progress",
        "task_id": "uuid",
        "project_id": "uuid",
        "stage": "rank_tracking",
        "progress": 45,
        "message": "Checked 45/100 keywords",
        "elapsed_seconds": 320,
        "estimated_completion_at": "2026-04-24T22:30:00Z"
    }
    """
    await manager.connect(task_id, websocket)
    
    try:
        # Send initial message
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Connected to progress stream"
        })
        
        # Poll for progress updates every 2 seconds
        while True:
            try:
                # Get current progress
                progress_data = await ScanProgress.get_progress_for_task(task_id)
                
                if progress_data:
                    # Send to all clients listening to this task
                    await manager.broadcast(task_id, {
                        "type": "progress",
                        **progress_data
                    })
                
                # Wait before next poll
                await asyncio.sleep(2)
                
                # Check for client disconnect (this will raise if client closed)
                # We do this by trying to receive with a timeout
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=0.1
                    )
                    # If we get here, client sent a message (shouldn't happen)
                    # but we can handle ping/pong or other commands here
                except asyncio.TimeoutError:
                    # This is expected - no message from client
                    pass
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Error in progress polling: {e}")
                break
    
    except WebSocketDisconnect:
        await manager.disconnect(task_id, websocket)
        logger.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(task_id, websocket)


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
