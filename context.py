import pygame
import subprocess
import webbrowser
from config import *
from ui import create_font
import os

class ContextMenu:
    def __init__(self):
        self.font = create_font(16)
        self.small_font = create_font(14)
        self.is_visible = False
        self.position = (0, 0)
        self.ip_str = ""
        self.ip_int = 0
        self.options = []
        self.ping_results = {}
        self.active_pings = {}  
    def show(self, pos, ip_str, ip_int):
        self.is_visible = True
        self.position = pos
        self.ip_str = ip_str
        self.ip_int = ip_int
        self._generate_options()
        
    def hide(self):
        self.is_visible = False
        
    def _generate_options(self):
        self.options = []
        
        self.options.append(("Copy IP " + self.ip_str, "copy_ip"))
        
        subnets = self._get_subnets()
        for subnet_str, subnet_cidr in subnets:
            self.options.append((f"Copy Subnet {subnet_str}", f"copy_subnet_{subnet_cidr}"))
        
        self.options.append(("---", "separator"))
        
        ping_status = self._get_ping_status(self.ip_str)
        self.options.append((f"Ping IP {self.ip_str} ({ping_status})", "ping_ip"))
        
        self.options.append(("---", "separator"))
        
        rdap_subnets = self._get_rdap_subnets()
        for rdap_text, rdap_action in rdap_subnets:
            self.options.append((rdap_text, rdap_action))
    
    def _get_subnets(self):
        """Generate subnet strings for /24, /16, and /8"""
        octets = self.ip_str.split('.')
        subnets = [
            (f"{octets[0]}.{octets[1]}.{octets[2]}.0/24", 24),
            (f"{octets[0]}.{octets[1]}.0.0/16", 16),
            (f"{octets[0]}.0.0.0/8", 8)
        ]
        return subnets
    
    def _get_rdap_subnets(self):
        """Generate RDAP visit options"""
        octets = self.ip_str.split('.')
        rdap_options = [
            (f"Visit RDAP on IP {self.ip_str}", "rdap_ip"),
            (f"Visit RDAP on Subnet {octets[0]}.{octets[1]}.{octets[2]}.0/24", "rdap_24"),
            (f"Visit RDAP on Subnet {octets[0]}.{octets[1]}.0.0/16", "rdap_16"),
            (f"Visit RDAP on Subnet {octets[0]}.0.0.0/8", "rdap_8")
        ]
        return rdap_options
    
    def _get_ping_status(self, ip_str):
        """Get current ping status for an IP"""
        if ip_str in self.ping_results:
            result = self.ping_results[ip_str]
            if result == "pending":
                return "Pinging..."
            elif result.startswith("success"):
                return f"Ping Successful ({result.split(': ')[1]})"
            elif result == "failed":
                return "Ping Failed"
        return "Ping"
    
    def handle_click(self, pos):
        if not self.is_visible:
            return False
            
        x, y = self.position
        option_height = 28
        menu_width = 300
        
        for i, (text, action) in enumerate(self.options):
            if text == "---":
                continue
                
            option_rect = pygame.Rect(x, y + i * option_height, menu_width, option_height)
            if option_rect.collidepoint(pos):
                self._execute_action(action)
                self.hide()
                return True
                
        self.hide()
        return False
    
    def _execute_action(self, action):
        if action.startswith("copy_ip"):
            self._copy_to_clipboard(self.ip_str)
            
        elif action.startswith("copy_subnet_"):
            cidr = int(action.split("_")[2])
            subnet_str = self._get_subnet_string(cidr)
            self._copy_to_clipboard(subnet_str)
            
        elif action == "ping_ip":
            self._ping_ip(self.ip_str)
            
        elif action.startswith("rdap_"):
            self._visit_rdap(action)
    
    def _get_subnet_string(self, cidr):
        octets = self.ip_str.split('.')
        if cidr == 24:
            return f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
        elif cidr == 16:
            return f"{octets[0]}.{octets[1]}.0.0/16"
        elif cidr == 8:
            return f"{octets[0]}.0.0.0/8"
        return self.ip_str
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard using pygame"""
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
        except:
            print(f"Copied to clipboard: {text}")
    
    def _ping_ip(self, ip_str):
        """Start a ping process for the given IP"""
        if ip_str in self.active_pings:
            return  
        self.ping_results[ip_str] = "pending"
        self.active_pings[ip_str] = True
        
        def ping_thread(ip):
            try:
                param = "-n" if os.name == "nt" else "-c"
                result = subprocess.run(
                    ["ping", param, "1", ip], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    time_str = "unknown"
                    for line in result.stdout.split('\n'):
                        if "time=" in line:
                            time_part = line.split("time=")[1].split(" ")[0]
                            time_str = time_part
                            break
                    self.ping_results[ip] = f"success: {time_str}"
                else:
                    self.ping_results[ip] = "failed"
                    
            except subprocess.TimeoutExpired:
                self.ping_results[ip] = "failed"
            except Exception:
                self.ping_results[ip] = "failed"
            finally:
                self.active_pings.pop(ip, None)
        
        import threading
        thread = threading.Thread(target=ping_thread, args=(ip_str,))
        thread.daemon = True
        thread.start()
    
    def _visit_rdap(self, action_type):
        """Visit RDAP page for IP or subnet"""
        if action_type == "rdap_ip":
            target = self.ip_str
        else:
            cidr = int(action_type.split("_")[1])
            target = self._get_subnet_string(cidr)
        
        rdap_servers = [
            f"https://rdap.arin.net/registry/ip/{target}",
            f"https://rdap.db.ripe.net/ip/{target}",
            f"https://rdap.apnic.net/ip/{target}",
            f"https://rdap.lacnic.net/rdap/ip/{target}",
            f"https://rdap.afrinic.net/rdap/ip/{target}"
        ]
        
        if rdap_servers:
            webbrowser.open(rdap_servers[0])
    
    def update(self):
        """Update ping statuses"""
        if self.is_visible:
            self._generate_options()
    
    def draw(self, screen):
        if not self.is_visible:
            return
            
        x, y = self.position
        option_height = 28
        menu_width = 300
        border_color = (100, 100, 100)
        bg_color = (30, 30, 30)
        text_color = (220, 220, 220)
        hover_color = (60, 60, 60)
        separator_color = (80, 80, 80)
        
        mouse_pos = pygame.mouse.get_pos()
        
        total_height = len(self.options) * option_height
        
        menu_rect = pygame.Rect(x, y, menu_width, total_height)
        pygame.draw.rect(screen, bg_color, menu_rect)
        pygame.draw.rect(screen, border_color, menu_rect, 1)
        
        for i, (text, action) in enumerate(self.options):
            option_rect = pygame.Rect(x, y + i * option_height, menu_width, option_height)
            
            if text == "---":
                sep_y = y + i * option_height + option_height // 2
                pygame.draw.line(screen, separator_color, (x, sep_y), (x + menu_width, sep_y), 1)
                continue
            
            if option_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, hover_color, option_rect)
            
            font = self.small_font if len(text) > 40 else self.font
            text_surf = font.render(text, True, text_color)
            text_rect = text_surf.get_rect(midleft=(x + 10, y + i * option_height + option_height // 2))
            screen.blit(text_surf, text_rect)