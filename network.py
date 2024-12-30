class NetworkManager:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_ip = self.get_local_ip()
        self.server_address = None
        self.is_ready = False
        self.opponent_ready = False
        self.players = {}  # 存储在线玩家信息
        
        try:
            self.socket.bind((self.local_ip, 0))
            self.port = self.socket.getsockname()[1]
            print(f"绑定到端口: {self.port}")
        except Exception as e:
            print(f"端口绑定失败: {e}")
            raise
    
    def request_player_list(self):
        """请求在线玩家列表"""
        try:
            # 发送获取玩家列表的请求
            request = {
                'type': 'get_players',
                'sender': self.local_ip
            }
            self.send_data(request)
            print("已发送玩家列表请求")
            
            # 更新本地玩家列表
            self.update_player_list()
            
        except Exception as e:
            print(f"请求玩家列表失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_player_list(self):
        """更新在线玩家列表"""
        try:
            # 这里可以添加实际的玩家列表更新逻辑
            # 暂时使用模拟数据
            self.players = {
                'local': {
                    'name': '本地玩家',
                    'ip': self.local_ip,
                    'status': 'online'
                }
            }
            print("玩家列表已更新")
            
        except Exception as e:
            print(f"更新玩家列表失败: {e}")
            import traceback
            traceback.print_exc()
    
    def get_player_list(self):
        """获取当前在线玩家列表"""
        return self.players
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"获取本地IP失败: {e}")
            return "127.0.0.1"
    
    def send_data(self, data):
        """发送数据到服务器"""
        try:
            if self.server_address:
                message = json.dumps(data).encode()
                self.socket.sendto(message, self.server_address)
                print(f"数据已发送: {data}")
            else:
                print("未设置服务器地址")
        except Exception as e:
            print(f"发送数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def receive_data(self):
        """接收数据"""
        try:
            data, addr = self.socket.recvfrom(1024)
            return json.loads(data.decode()), addr
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"接收数据失败: {e}")
            return None, None
    
    def set_server_address(self, address):
        """设置服务器地址"""
        self.server_address = address
        print(f"服务器地址已设置为: {address}")
    
    def close(self):
        """关闭网络连接"""
        try:
            self.socket.close()
            print("网络连接已关闭")
        except Exception as e:
            print(f"关闭网络连接失败: {e}") 