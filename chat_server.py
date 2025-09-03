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
        self.user_info: Dict[str, str] = {}  # user_id -> username 映射
        
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
        self.user_info[user_id] = username
        
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
            if user_id in self.user_info:
                del self.user_info[user_id]
            
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
    
    async def send_private_message(self, sender_id: str, target_id: str, message: dict):
        """发送私聊消息给特定用户"""
        if target_id in self.clients:
            try:
                await self.clients[target_id].send(json.dumps(message))
                # 同时发送给发送者确认
                if sender_id in self.clients and sender_id != target_id:
                    await self.clients[sender_id].send(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"发送私聊消息失败: {e}")
                return False
        return False
    
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
                    
                    elif message_type == "private_chat":
                        if user_id and user_id in self.clients:
                            target_user_id = data.get("target_user_id")
                            if not target_user_id:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": "缺少目标用户ID"
                                }))
                                continue
                            
                            if target_user_id not in self.clients:
                                await websocket.send(json.dumps({
                                    "type": "error", 
                                    "message": f"用户 {target_user_id} 不在线"
                                }))
                                continue
                            
                            private_message = {
                                "type": "private_chat",
                                "user_id": user_id,
                                "username": data.get("username", ""),
                                "target_user_id": target_user_id,
                                "message": data.get("message", ""),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            success = await self.send_private_message(user_id, target_user_id, private_message)
                            if not success:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": "发送私聊消息失败"
                                }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "请先加入聊天室"
                            }))
                    
                    elif message_type == "get_user_info":
                        if user_id and user_id in self.clients:
                            target_user_id = data.get("target_user_id")
                            if target_user_id in self.user_info:
                                await websocket.send(json.dumps({
                                    "type": "user_info",
                                    "user_id": target_user_id,
                                    "username": self.user_info[target_user_id],
                                    "online": target_user_id in self.clients
                                }))
                            else:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": "用户不存在"
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
    import os
    
    # 检查证书文件是否存在
    if not os.path.exists(cert_file):
        raise FileNotFoundError(f"SSL证书文件不存在: {cert_file}")
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"SSL私钥文件不存在: {key_file}")
    
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_file, key_file)
        logger.info(f"SSL证书加载成功: {cert_file}")
        return ssl_context
    except ssl.SSLError as e:
        logger.error(f"SSL证书加载失败: {e}")
        logger.error("可能的原因:")
        logger.error("1. 证书文件格式不正确（需要PEM格式）")
        logger.error("2. 证书和私钥不匹配")
        logger.error("3. 证书文件损坏")
        logger.error("4. 私钥文件需要密码但未提供")
        raise

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
            logger.error("使用方法: python3 chat_server.py --ssl --cert 证书文件.pem --key 私钥文件.pem")
            return
        
        try:
            ssl_context = create_ssl_context(args.cert, args.key)
            protocol = "wss"
        except FileNotFoundError as e:
            logger.error(f"文件不存在: {e}")
            logger.error("请检查证书和私钥文件路径是否正确")
            return
        except ssl.SSLError as e:
            logger.error("SSL证书加载失败，请尝试以下解决方案:")
            logger.error("1. 使用HTTP模式（不使用--ssl参数）: python3 chat_server.py --host 0.0.0.0 --port 11900")
            logger.error("2. 重新生成SSL证书: python3 generate_ssl_cert.py")
            logger.error("3. 检查证书文件格式是否为PEM格式")
            return
        except Exception as e:
            logger.error(f"SSL配置失败: {e}")
            return
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