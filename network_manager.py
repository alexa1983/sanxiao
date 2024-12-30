import socket
import threading
import pickle
import queue
import json
from constants import GameState

class NetworkManager:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_host = False
        self.connected = False
        self.message_queue = queue.Queue()
        self.client_socket = None
        self.opponent_ready = False
        self.room_info = None
        
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个临时socket连接来获取本机IP
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def create_room(self, room_name, port=5555):
        """创建游戏房间"""
        try:
            local_ip = self.get_local_ip()
            self.socket.bind(('', port))
            self.socket.listen(1)
            self.is_host = True
            
            self.room_info = {
                "name": room_name,
                "ip": local_ip,
                "port": port,
                "host": True,
                "status": "等待玩家加入"
            }
            
            print(f"房间创建成功 - IP: {local_ip}, 端口: {port}")
            # 启动接受连接的线程
            threading.Thread(target=self.accept_connections, daemon=True).start()
            return True, self.room_info
            
        except Exception as e:
            print(f"创建房间失败: {e}")
            return False, None

    def join_room(self, ip, port=5555):
        """加入游戏房间"""
        try:
            self.socket.connect((ip, port))
            self.connected = True
            self.is_host = False
            
            self.room_info = {
                "ip": ip,
                "port": port,
                "host": False,
                "status": "已连接"
            }
            
            # 启动接收数据的线程
            threading.Thread(target=self.receive_data, daemon=True).start()
            print(f"成功加入房间 - IP: {ip}")
            return True
            
        except Exception as e:
            print(f"加入房间失败: {e}")
            return False

    def send_ready_state(self, is_ready):
        """发送准备状态"""
        self.send_data({
            'type': 'ready',
            'value': is_ready
        })

    def get_room_status(self):
        """获取房间状态信息"""
        if not self.room_info:
            return "未连接到房间"
        return self.room_info["status"]

    def start_server(self, port=5555):
        try:
            self.socket.bind(('', port))
            self.socket.listen(1)
            self.is_host = True
            print(f"服务器启动在端口 {port}")
            # 启动接受连接的线程
            threading.Thread(target=self.accept_connections, daemon=True).start()
            return True
        except Exception as e:
            print(f"服务器启动失败: {e}")
            return False
            
    def connect_to_server(self, ip, port=5555):
        try:
            self.socket.connect((ip, port))
            self.connected = True
            self.is_host = False
            # 启动接收数据的线程
            threading.Thread(target=self.receive_data, daemon=True).start()
            print("成功连接到服务器")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
            
    def accept_connections(self):
        try:
            self.client_socket, addr = self.socket.accept()
            self.connected = True
            print(f"玩家已连接: {addr}")
            self.receive_data()
        except Exception as e:
            print(f"接受连接失败: {e}")
            
    def send_data(self, data):
        try:
            if self.is_host and self.client_socket:
                self.client_socket.send(pickle.dumps(data))
            elif not self.is_host:
                self.socket.send(pickle.dumps(data))
        except Exception as e:
            print(f"发送数据失败: {e}")
            self.handle_disconnect()
            
    def receive_data(self):
        while self.connected:
            try:
                socket_to_read = self.client_socket if self.is_host else self.socket
                data = pickle.loads(socket_to_read.recv(2048))
                self.message_queue.put(data)
            except Exception as e:
                print(f"接收数据失败: {e}")
                self.handle_disconnect()
                break
                
    def handle_disconnect(self):
        self.connected = False
        if self.client_socket:
            self.client_socket.close()
        self.socket.close()
        
    def get_message(self):
        if not self.message_queue.empty():
            return self.message_queue.get()
        return None 

    def broadcast_presence(self):
        """广播自己的存在"""
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            message = {
                'type': 'presence',
                'name': socket.gethostname(),
                'ip': self.get_local_ip()
            }
            
            broadcast_socket.sendto(pickle.dumps(message), ('<broadcast>', 5555))
            broadcast_socket.close()
        except Exception as e:
            print(f"广播失败: {e}")
            
    def send_invite(self, target_ip):
        """发送邀请"""
        self.send_data({
            'type': 'invite',
            'from_ip': self.get_local_ip()
        }, target_ip) 