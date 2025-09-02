#!/usr/bin/env python3
"""
简单的WebSocket聊天服务器
支持HTTP和HTTPS协议
"""

import asyncio
import websockets
import json
import ssl
import logging
from datetime import datetime
from typing import Dict, Set
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self):
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_ids: Set[str] = set()
        
    async def register_client(self, websocket, user_id: str, username: str):
        """注册新客户端"""
        if user_id in self.user_ids:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"用户ID '{user_id}' 已存在，请选择其他ID"
            }))
            return False
            
        self.clients[user_id] = websocket
        self.user_ids.add(user_id)
        
        # 通知所有客户端有新用户加入
        await self.broadcast_message({
            "type": "user_joined",
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "online_users": list(self.user_ids)
        })
        
        logger.info(f"用户 {username} (ID: {user_id}) 已连接")
        return True
    
    async def unregister_client(self, user_id: str):
        """注销客户端"""
        if user_id in self.clients:
            del self.clients[user_id]
            self.user_ids.remove(user_id)
            
            # 通知所有客户端用户离开
            await self.broadcast_message({
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "online_users": list(self.user_ids)
            })
            
            logger.info(f"用户 (ID: {user_id}) 已断开连接")
    
    async def broadcast_message(self, message: dict):
        """向所有客户端广播消息"""
        if self.clients:
            # 创建一个副本来避免在迭代时修改字典
            clients_copy = list(self.clients.values())
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in clients_copy],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket):
        """处理客户端连接"""
        user_id = None
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "join":
                        user_id = data.get("user_id")
                        username = data.get("username")
                        
                        if not user_id or not username:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "用户ID和用户名不能为空"
                            }))
                            continue
                            
                        success = await self.register_client(websocket, user_id, username)
                        if success:
                            await websocket.send(json.dumps({
                                "type": "join_success",
                                "message": "成功加入聊天室"
                            }))
                    
                    elif message_type == "chat":
                        if user_id and user_id in self.clients:
                            chat_message = {
                                "type": "chat",
                                "user_id": user_id,
                                "username": data.get("username", ""),
                                "message": data.get("message", ""),
                                "timestamp": datetime.now().isoformat()
                            }
                            await self.broadcast_message(chat_message)
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "请先加入聊天室"
                            }))
                    
                    elif message_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"处理客户端时发生错误: {e}")
        finally:
            if user_id:
                await self.unregister_client(user_id)

def create_ssl_context(cert_file: str, key_file: str):
    """创建SSL上下文"""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)
    return ssl_context

async def main():
    parser = argparse.ArgumentParser(description='聊天服务器')
    parser.add_argument('--host', default='localhost', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8765, help='服务器端口')
    parser.add_argument('--ssl', action='store_true', help='启用HTTPS/WSS')
    parser.add_argument('--cert', help='SSL证书文件路径')
    parser.add_argument('--key', help='SSL私钥文件路径')
    
    args = parser.parse_args()
    
    chat_server = ChatServer()
    
    # 设置SSL（如果需要）
    ssl_context = None
    if args.ssl:
        if not args.cert or not args.key:
            logger.error("使用HTTPS时需要提供证书和私钥文件")
            return
        ssl_context = create_ssl_context(args.cert, args.key)
        protocol = "wss"
    else:
        protocol = "ws"
    
    logger.info(f"启动聊天服务器: {protocol}://{args.host}:{args.port}")
    
    # 启动WebSocket服务器
    async with websockets.serve(
        chat_server.handle_client,
        args.host,
        args.port,
        ssl=ssl_context
    ):
        await asyncio.Future()  # 保持服务器运行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")