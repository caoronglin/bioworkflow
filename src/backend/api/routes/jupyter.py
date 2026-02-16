"""
Jupyter 内核 API 路由 - 最小化解耦实现

提供 REST API 和 WebSocket 接口与 Jupyter 内核通信
"""

from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core.container import get_jupyter_kernel_service
from backend.core.interfaces import JupyterKernelService
from backend.core.logging import get_logger

logger = get_logger("jupyter")
router = APIRouter()


# 请求模型
class ExecuteRequest(BaseModel):
    code: str
    execution_id: str | None = None


class KernelCreateRequest(BaseModel):
    kernel_name: str = "python3"


# REST API 端点
@router.post("/kernels", response_model=dict[str, str])
async def create_kernel(
    request: KernelCreateRequest,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
) -> dict[str, str]:
    """创建新内核"""
    kernel_id = await service.start_kernel(request.kernel_name)
    return {"kernel_id": kernel_id, "status": "created"}


@router.delete("/kernels/{kernel_id}")
async def shutdown_kernel(
    kernel_id: str,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
) -> dict[str, Any]:
    """关闭内核"""
    success = await service.shutdown_kernel(kernel_id)
    return {"kernel_id": kernel_id, "shutdown": success}


@router.get("/kernels")
async def list_kernels(
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
) -> dict[str, list[dict[str, Any]]]:
    """列出所有内核"""
    kernels = await service.list_kernels()
    return {"kernels": kernels}


@router.get("/kernels/{kernel_id}/status")
async def get_kernel_status(
    kernel_id: str,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
) -> dict[str, Any]:
    """获取内核状态"""
    status = await service.get_kernel_status(kernel_id)
    return status


@router.post("/kernels/{kernel_id}/interrupt")
async def interrupt_kernel(
    kernel_id: str,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
) -> dict[str, Any]:
    """中断内核"""
    success = await service.interrupt_kernel(kernel_id)
    return {"kernel_id": kernel_id, "interrupted": success}


# WebSocket 端点
@router.websocket("/ws/kernels/{kernel_id}")
async def kernel_websocket(
    websocket: WebSocket,
    kernel_id: str,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
):
    """
    WebSocket 连接用于实时代码执行

    消息格式:
    - 客户端 -> 服务器: {"type": "execute", "code": "...", "execution_id": "..."}
    - 服务器 -> 客户端: {"type": "status|stream|display_data|execute_result|error", "content": {...}, "execution_id": "..."}
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for kernel: {kernel_id}")

    try:
        while True:
            # 接收消息
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "execute":
                code = message.get("code", "")
                execution_id = message.get("execution_id")

                # 执行代码并流式返回结果
                async for result in service.execute_code(kernel_id, code, execution_id):
                    await websocket.send_json(result)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "content": {"message": f"Unknown message type: {msg_type}"},
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for kernel: {kernel_id}")
    except Exception as e:
        logger.error(f"WebSocket error for kernel {kernel_id}: {e}")
        await websocket.close()


@router.websocket("/ws/kernels")
async def kernel_management_websocket(
    websocket: WebSocket,
    service: JupyterKernelService = Depends(get_jupyter_kernel_service),
):
    """
    WebSocket 连接用于内核管理

    支持操作:
    - start_kernel
    - shutdown_kernel
    - list_kernels
    - get_status
    """
    await websocket.accept()
    logger.info("Kernel management WebSocket connected")

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "start_kernel":
                kernel_name = message.get("kernel_name", "python3")
                kernel_id = await service.start_kernel(kernel_name)
                await websocket.send_json({
                    "type": "kernel_started",
                    "kernel_id": kernel_id,
                    "kernel_name": kernel_name,
                })

            elif action == "shutdown_kernel":
                kernel_id = message.get("kernel_id")
                success = await service.shutdown_kernel(kernel_id)
                await websocket.send_json({
                    "type": "kernel_shutdown",
                    "kernel_id": kernel_id,
                    "success": success,
                })

            elif action == "list_kernels":
                kernels = await service.list_kernels()
                await websocket.send_json({
                    "type": "kernel_list",
                    "kernels": kernels,
                })

            elif action == "get_status":
                kernel_id = message.get("kernel_id")
                status = await service.get_kernel_status(kernel_id)
                await websocket.send_json({
                    "type": "kernel_status",
                    "status": status,
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "content": {"message": f"Unknown action: {action}"},
                })

    except WebSocketDisconnect:
        logger.info("Kernel management WebSocket disconnected")
    except Exception as e:
        logger.error(f"Kernel management WebSocket error: {e}")
        await websocket.close()
