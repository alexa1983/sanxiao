import socket
import pickle
import threading
import os
import time

class Player:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.status = "在线"  # 在线、游戏中、离线
        self.last_seen = time.time()
        
    def __str__(self):
        return f"Player({self.name}, {self.ip}, {self.status})"

class Room:
    def __init__(self, host_player):
        self.host = host_player
        self.guest = None
        self.status = "等待中"  # 等待中、准备中、游戏中
        self.room_id = str(int(time.time()))  # 使用时间戳作为房间ID
        self.host_ready = False   # 添加房主准备状态
        self.guest_ready = False  # 添加客人准备状态
        
    def __str__(self):
        return f"Room({self.room_id}, host={self.host.name}, guest={self.guest.name if self.guest else 'None'})"

class NetworkManager:
    def __init__(self):
        self.connected = False
        self.players = []  # 存储在线玩家列表
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket用于广播
        
        # 添加监听socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind(('', 5555))  # 绑定到所有网卡
        
        # 启动监听线程
        self.listen_thread = threading.Thread(target=self.listen_for_broadcasts, daemon=True)
        self.listen_thread.start()
        
        print("NetworkManager initialized")

        self.rooms = {}  # 存储所有可见的房间
        self.current_room = None  # 当前所在的房间
        self.is_ready = False  # 添加准备状态
        self.opponent_ready = False  # 添加对手准备状态
        self.last_cleanup = time.time()
        self.cleanup_interval = 5.0  # 每5秒清理一次
        
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def broadcast_presence(self):
        """广播自己的存在"""
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # 修改广播地址为局域网广播地址
            broadcast_address = '255.255.255.255'  # 全网广播
            port = 5555
            
            message = {
                'type': 'presence',
                'name': socket.gethostname(),
                'ip': self.get_local_ip()
            }
            
            broadcast_socket.sendto(pickle.dumps(message), (broadcast_address, port))
            broadcast_socket.close()
            print(f"已广播在线状态: {message}")
        except Exception as e:
            print(f"广播失败: {e}")
    
    def request_player_list(self):
        """
        请求获取在线玩家列表
        返回: 玩家列表
        """
        try:
            # 这里应该是实际的网络请求逻辑
            # 目前返回模拟数据用于测试
            self.players = [
                {"id": 1, "name": "Player 1"},
                {"id": 2, "name": "Player 2"},
                {"id": 3, "name": "Player 3"}
            ]
            return self.players
        except Exception as e:
            print(f"获取玩家列表失败: {e}")
            return []

    def connect(self):
        """建立网络连接"""
        try:
            # 实际的连接逻辑
            self.connected = True
            self.broadcast_presence()  # 连接后广播在线状态
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开网络连接"""
        try:
            # 实际的断开连接逻辑
            self.connected = False
            if self.socket:
                self.socket.close()
            return True
        except Exception as e:
            print(f"断开连接失败: {e}")
            return False

    def is_connected(self):
        """检查连接状态"""
        return self.connected

    def send_challenge(self, player_id):
        """
        发送对战邀请
        参数:
            player_id: 目标玩家ID
        """
        try:
            # 实际的发送邀请逻辑
            print(f"已发送对战邀请给玩家 {player_id}")
            return True
        except Exception as e:
            print(f"发送邀请失败: {e}")
            return False

    def accept_challenge(self, player_id):
        """
        接受对战邀请
        参数:
            player_id: 发起邀请的玩家ID
        """
        try:
            # 实际的接受邀请逻辑
            print(f"已接受玩家 {player_id} 的对战邀请")
            return True
        except Exception as e:
            print(f"接受邀请失败: {e}")
            return False

    def decline_challenge(self, player_id):
        """
        拒绝对战邀请
        参数:
            player_id: 发起邀请的玩家ID
        """
        try:
            # 实际的拒绝邀请逻辑
            print(f"已拒绝玩家 {player_id} 的对战邀请")
            return True
        except Exception as e:
            print(f"拒绝邀请失败: {e}")
            return False

    def broadcast_room(self, room):
        """广播房间信息"""
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            message = {
                'type': 'room',
                'room_id': room.room_id,
                'host_name': room.host.name,
                'host_ip': room.host.ip,
                'status': room.status,
                'guest': room.guest.name if room.guest else None,
                'host_ready': room.host_ready,  # 添加准备状态
                'guest_ready': room.guest_ready  # 添加准备状态
            }
            
            broadcast_socket.sendto(pickle.dumps(message), ('255.255.255.255', 5555))
            broadcast_socket.close()
            print(f"已广播房间信息: {message}")
        except Exception as e:
            print(f"广播房间失败: {e}")
    
    def create_room(self):
        """创建新房间"""
        try:
            local_player = Player(socket.gethostname(), self.get_local_ip())
            room = Room(local_player)
            room.status = "等待中"
            self.rooms[room.room_id] = room
            self.current_room = room
            
            # 立即广播新房间信息
            self.broadcast_room(room)
            print(f"创建房间成功: {room.room_id}")
            return room
        except Exception as e:
            print(f"创建房间失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def join_room(self, room_id, host_ip):
        """加入房间"""
        try:
            if room_id in self.rooms:
                room = self.rooms[room_id]
                if room.status != "等待中":
                    print(f"房间 {room_id} 不可加入：状态为 {room.status}")
                    return False
                    
                # 重置准备状态
                self.is_ready = False
                self.opponent_ready = False
                
                # 发送加入请求
                message = {
                    'type': 'join_request',
                    'room_id': room_id,
                    'player_name': socket.gethostname(),
                    'player_ip': self.get_local_ip()
                }
                
                # 创建新的socket发送请求
                join_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                join_socket.sendto(pickle.dumps(message), (host_ip, 5555))
                join_socket.close()
                
                # 更新本地房间状态
                self.current_room = room
                print(f"发送加入房间请求: {room_id}")
                return True
                
            print(f"房间 {room_id} 不存在")
            return False
            
        except Exception as e:
            print(f"加入房间失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def handle_join_request(self, message):
        """处理加入房间请求"""
        if self.current_room and message['room_id'] == self.current_room.room_id:
            if not self.current_room.guest:
                guest = Player(message['player_name'], message['player_ip'])
                self.current_room.guest = guest
                self.current_room.status = "准备中"
                self.broadcast_room(self.current_room)
                print(f"玩家 {guest.name} 加入房间")
                return True
        return False

    def send_data(self, data):
        """发送通用数据"""
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            broadcast_socket.sendto(pickle.dumps(data), ('255.255.255.255', 5555))
            broadcast_socket.close()
            print(f"发送数据: {data}")
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False
    
    def send_ready_state(self, is_ready):
        """发送准备状态"""
        try:
            if self.current_room:
                self.is_ready = is_ready
                # 更新本地房间状态
                if self.current_room.host.ip == self.get_local_ip():
                    self.current_room.host_ready = is_ready
                elif self.current_room.guest and self.current_room.guest.ip == self.get_local_ip():
                    self.current_room.guest_ready = is_ready

                # 发送准备状态消息
                ready_message = {
                    'type': 'ready_state',
                    'room_id': self.current_room.room_id,
                    'player_ip': self.get_local_ip(),
                    'is_ready': is_ready,
                    'is_host': self.current_room.host.ip == self.get_local_ip()
                }
                self.send_data(ready_message)

                # 更新房间状态
                if self.current_room.host_ready and self.current_room.guest_ready:
                    self.current_room.status = "准备完成"
                else:
                    self.current_room.status = "准备中"

                # 广播房间状态（包含完整的准备状态）
                room_message = {
                    'type': 'room',
                    'room_id': self.current_room.room_id,
                    'host_name': self.current_room.host.name,
                    'host_ip': self.current_room.host.ip,
                    'status': self.current_room.status,
                    'guest': self.current_room.guest.name if self.current_room.guest else None,
                    'guest_ip': self.current_room.guest.ip if self.current_room.guest else None,
                    'host_ready': self.current_room.host_ready,
                    'guest_ready': self.current_room.guest_ready
                }
                self.send_data(room_message)
                
                print(f"发送准备状态: {'已准备' if is_ready else '未准备'}")
                print(f"当前房间状态: 房主{'已' if self.current_room.host_ready else '未'}准备, "
                      f"客人{'已' if self.current_room.guest_ready else '未'}准备")
                return True
        except Exception as e:
            print(f"发送准备状态失败: {e}")
            return False
    
    def cleanup_stale_data(self):
        """清理过期的玩家和房间数据"""
        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            self.last_cleanup = current_time
            
            # 清理离线玩家
            self.players = [player for player in self.players 
                          if current_time - player.last_seen < 10]
            
            # 清理空房间或过期房间
            stale_rooms = []
            for room_id, room in self.rooms.items():
                try:
                    # 检查房主是否在线
                    host_online = any(p.ip == room.host.ip for p in self.players)
                    if not host_online:
                        stale_rooms.append(room_id)
                        print(f"标记清理房间 {room_id}: 房主离线")
                        continue
                    
                    # 检查空房间
                    if not room.guest and current_time - room.last_active > 30:
                        stale_rooms.append(room_id)
                        print(f"标记清理房间 {room_id}: 空房间超时")
                        
                except Exception as e:
                    print(f"检查房间 {room_id} 状态失败: {e}")
                    stale_rooms.append(room_id)
            
            # 删除过期房间
            for room_id in stale_rooms:
                if room_id in self.rooms:
                    del self.rooms[room_id]
                    if self.current_room and self.current_room.room_id == room_id:
                        self.current_room = None
                    print(f"清理房间: {room_id}")

    def listen_for_broadcasts(self):
        """监听其他玩家的广播"""
        while True:
            try:
                data, addr = self.listen_socket.recvfrom(1024)
                message = pickle.loads(data)
                
                if message['type'] == 'start_game':
                    # 处理开始游戏消息
                    if (self.current_room and 
                        message['room_id'] == self.current_room.room_id):
                        self.current_room.status = "游戏中"
                        # 添加一个回调函数来通知游戏状态改变
                        if hasattr(self, 'on_game_start'):
                            self.on_game_start()
                        print("收到开始游戏消息，准备进入游戏")
                
                elif message['type'] == 'game_state':
                    # 处理游戏状态更新
                    if (self.current_room and 
                        message['room_id'] == self.current_room.room_id and
                        message['player_ip'] != self.get_local_ip()):
                        # 更新对手的游戏状态
                        self.opponent_score = message['score']
                        self.opponent_moves = message['moves_left']
                        print(f"对手状态更新 - 分数: {self.opponent_score}, 步数: {self.opponent_moves}")
                
                elif message['type'] == 'room':
                    # 处理房间广播
                    room_id = message['room_id']
                    # 创建或更新房间
                    if room_id not in self.rooms:
                        # 创建新房间
                        host = Player(message['host_name'], message['host_ip'])
                        room = Room(host)
                        room.room_id = room_id
                        room.status = message['status']
                        room.host_ready = message.get('host_ready', False)
                        room.guest_ready = message.get('guest_ready', False)
                        if message.get('guest'):
                            room.guest = Player(message['guest'], message.get('guest_ip'))
                        self.rooms[room_id] = room
                        print(f"发现新房间: {room_id}")
                    else:
                        # 更新现有房间
                        room = self.rooms[room_id]
                        room.status = message['status']
                        room.host_ready = message.get('host_ready', False)
                        room.guest_ready = message.get('guest_ready', False)
                        if message.get('guest'):
                            if not room.guest:
                                room.guest = Player(message['guest'], message.get('guest_ip'))
                            else:
                                room.guest.ip = message.get('guest_ip')
                        else:
                            room.guest = None
                    
                    # 如果是当前房间，同步状态
                    if self.current_room and room_id == self.current_room.room_id:
                        self.current_room = room
                        if self.current_room.guest and self.current_room.guest.ip == self.get_local_ip():
                            self.opponent_ready = room.host_ready
                        else:
                            self.opponent_ready = room.guest_ready if room.guest else False
                        
                    print(f"房间状态更新: {room_id} - {room.status}")

                elif message['type'] == 'presence':
                    # 检查是否是自己发出的广播
                    if message['ip'] != self.get_local_ip():
                        # 更新或添加玩家
                        new_player = Player(message['name'], message['ip'])
                        
                        # 检查玩家是否已存在
                        existing_player = next(
                            (p for p in self.players if p.ip == message['ip']), 
                            None
                        )
                        
                        if existing_player:
                            existing_player.last_seen = time.time()
                            existing_player.status = "在线"
                        else:
                            self.players.append(new_player)
                            
                        print(f"收到玩家广播: {message}")
                        print(f"当前在线玩家数: {len(self.players)}")
                    
                elif message['type'] == 'join_request':
                    # 处理加入请求
                    if self.current_room and message['room_id'] == self.current_room.room_id:
                        guest = Player(message['player_name'], message['player_ip'])
                        self.current_room.guest = guest
                        self.broadcast_room(self.current_room)
                        print(f"玩家加入房间: {guest.name}")
                
                elif message['type'] == 'ready_state':
                    # 处理准备状态更新
                    self.handle_ready_state(message)
                    
                elif message['type'] == 'leave_room':
                    # 处理离开房间
                    if (self.current_room and 
                        message['room_id'] == self.current_room.room_id):
                        if message['player_ip'] == self.current_room.host.ip:
                            # 房主离开，解散房间
                            self.current_room = None
                            print("房主离开，房间已解散")
                        elif self.current_room.guest and message['player_ip'] == self.current_room.guest.ip:
                            # 客人离开
                            self.current_room.guest = None
                            self.opponent_ready = False
                            print("玩家离开房间")
                        self.broadcast_room(self.current_room)
                
            except Exception as e:
                print(f"监听广播错误: {e}")
                import traceback
                traceback.print_exc()

    def check_firewall(self):
        """检查防火墙设置"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            test_socket.sendto(b"test", ('255.255.255.255', 5555))
            test_socket.close()
            print("防火墙测试通过")
            return True
        except Exception as e:
            print(f"防火墙可能阻止了广播: {e}")
            print("请检查防火墙设置，确保允许程序进行网络通信")
            return False

    def get_network_interfaces(self):
        """获取所有可用的网络接口"""
        try:
            interfaces = []
            if os.name == 'nt':  # Windows
                # 使用ipconfig命令
                output = os.popen('ipconfig').read()
                # 解析输出获取接口信息
            else:  # Unix/Linux/Mac
                import netifaces
                interfaces = netifaces.interfaces()
            
            print(f"可用网络接口: {interfaces}")
            return interfaces
        except Exception as e:
            print(f"获取网络接口失败: {e}")
            return []

    def get_broadcast_address(self):
        """获取正确的广播地址"""
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        if 'broadcast' in addr:
                            return addr['broadcast']
            return '255.255.255.255'
        except Exception:
            return '255.255.255.255'

    def log_network_status(self):
        """记录网络状态"""
        try:
            print("\n=== 网络状态诊断 ===")
            print(f"本机IP: {self.get_local_ip()}")
            print(f"广播地址: {self.get_broadcast_address()}")
            print(f"已发现玩家数: {len(self.players)}")
            print(f"网络接口: {self.get_network_interfaces()}")
            print("==================\n")
        except Exception as e:
            print(f"状态记录错误: {e}")

    def handle_leave_room(self, message):
        """处理离开房间消息"""
        room_id = message.get('room_id')
        player_ip = message.get('player_ip')
        
        if room_id in self.rooms:
            room = self.rooms[room_id]
            
            # 如果是房主离开，删除房间
            if player_ip == room.host.ip:
                del self.rooms[room_id]
                if self.current_room and self.current_room.room_id == room_id:
                    self.current_room = None
                print(f"房间 {room_id} 已解散")
                
            # 如果是客人离开，更新房间状态
            elif room.guest and player_ip == room.guest.ip:
                room.guest = None
                room.guest_ready = False  # 重置客人准备状态
                room.status = "等待中"
                print(f"玩家离开房间 {room_id}")
                
                # 重置当前房间状态
                if self.current_room and self.current_room.room_id == room_id:
                    self.current_room = None
                    self.is_ready = False
                    self.opponent_ready = False
            
            # 广播房间状态更新
            if room_id in self.rooms:
                self.broadcast_room(self.rooms[room_id])

    def broadcast_game_state(self, score, moves_left):
        """广播游戏状态"""
        if self.current_room:
            message = {
                'type': 'game_state',
                'room_id': self.current_room.room_id,
                'player_ip': self.get_local_ip(),
                'score': score,
                'moves_left': moves_left
            }
            self.send_data(message)

    def broadcast_game_result(self, is_winner):
        """广播游戏结果"""
        if self.current_room:
            message = {
                'type': 'game_result',
                'room_id': self.current_room.room_id,
                'player_ip': self.get_local_ip(),
                'is_winner': is_winner
            }
            self.send_data(message)

    def handle_ready_state(self, message):
        """处理准备状态消息"""
        try:
            if (self.current_room and 
                message['room_id'] == self.current_room.room_id):
                
                player_ip = message['player_ip']
                is_ready = message['is_ready']
                is_host = message.get('is_host', False)
                
                # 更新房间中的准备状态
                if is_host:
                    self.current_room.host_ready = is_ready
                    if player_ip != self.get_local_ip():
                        self.opponent_ready = is_ready
                    print(f"房主准备状态更新: {'已准备' if is_ready else '未准备'}")
                else:
                    self.current_room.guest_ready = is_ready
                    if player_ip != self.get_local_ip():
                        self.opponent_ready = is_ready
                    print(f"客人准备状态更新: {'已准备' if is_ready else '未准备'}")
                
                # 更新房间状态
                if self.current_room.host_ready and self.current_room.guest_ready:
                    self.current_room.status = "准备完成"
                else:
                    self.current_room.status = "准备中"
                
                print(f"房间状态更新 - 房主: {'已准备' if self.current_room.host_ready else '未准备'}, "
                      f"客人: {'已准备' if self.current_room.guest_ready else '未准备'}")

        except Exception as e:
            print(f"处理准备状态错误: {e}")
            import traceback
            traceback.print_exc()