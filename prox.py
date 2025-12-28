import requests
import concurrent.futures
import os
import time
import sys
import uuid
import platform
import random
import re
import threading
from colorama import Fore, Style, init

# ================= SECURITY CONFIGURATION =================

# 1. BOT TOKEN
bt_part1 = "8534411619"
bt_part2 = "AAF9XBcgqXolE9BblhfHrRkazNOibw_93jk"
BOT_TOKEN = f"{bt_part1}:{bt_part2}"

# 2. ADMIN CHAT ID
ADMIN_CHAT_ID = "5844050724"

# 3. AUTH GROUP ID
AUTH_GROUP_ID = "-1003470466158"

# ==========================================================

init(autoreset=True)
sys.stderr = open(os.devnull, 'w') # Hide Errors

# GLOBAL VARIABLES
MAX_PING = 500
RESET_REQUESTED = False
CURRENT_IP = "Checking..."

class SecuritySystem:
    def __init__(self):
        self.device_info = platform.uname()
        self.key_file = "license_key.txt" 
    
    def get_hwid(self):
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "r") as f:
                    return f.read().strip()
            except: pass
        try:
            rand_part = str(random.randint(100000, 999999))
            node = uuid.getnode()
            raw_id = f"{node}-{platform.machine()}-{rand_part}"
            hwid = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
            with open(self.key_file, "w") as f:
                f.write(hwid)
            return hwid
        except: return "UNKNOWN-DEVICE-ID"

    def get_ip(self):
        global CURRENT_IP
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
            CURRENT_IP = ip
            return ip
        except: return "Unknown IP"

    def get_pinned_msg(self):
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={AUTH_GROUP_ID}"
            r = requests.get(url, timeout=10)
            if r.json().get("ok"):
                return r.json()["result"].get("pinned_message", {}).get("text", "")
        except: pass
        return ""

    def check_approval(self):
        hwid = self.get_hwid()
        ip = self.get_ip()
        approved_text = self.get_pinned_msg()
        
        if approved_text:
            if hwid in approved_text:
                return True
            else:
                self.send_request_to_admin(hwid, ip)
                self.block_user(hwid)
        else:
            sys.exit() 

    def send_request_to_admin(self, hwid, ip):
        try:
            msg = (f"🔒 **LOGIN REQUEST**\n👤 IP: `{ip}`\n🔑 Key: `{hwid}`")
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          data={"chat_id": ADMIN_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except: pass

    def block_user(self, hwid):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.RED}⛔ ACCESS DENIED ⛔{Style.RESET_ALL}")
        sys.exit()

# ================= COMMAND LISTENER (THREAD) =================
def telegram_command_listener():
    """Listens for /live and /reset commands"""
    global RESET_REQUESTED, MAX_PING
    last_update_id = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            r = requests.get(url, timeout=35)
            data = r.json()
            
            if data.get("ok"):
                for result in data["result"]:
                    last_update_id = result["update_id"]
                    
                    if "message" in result and "text" in result["message"]:
                        chat_id = result["message"]["chat"]["id"]
                        text = result["message"]["text"].strip().lower()
                        
                        if str(chat_id) == ADMIN_CHAT_ID:
                            if text == "/live":
                                status_msg = (
                                    f"🟢 **Tool is ONLINE**\n"
                                    f"📡 **IP:** `{CURRENT_IP}`\n"
                                    f"⚡ **Ping Limit:** {MAX_PING}ms\n"
                                    f"✅ **System:** Active"
                                )
                                requests.post(
                                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                    data={"chat_id": ADMIN_CHAT_ID, "text": status_msg, "parse_mode": "Markdown"}
                                )
                            elif text in ["/reset", "/rest"]:
                                requests.post(
                                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                    data={"chat_id": ADMIN_CHAT_ID, "text": "♻️ **Restarting Scan...**"}
                                )
                                RESET_REQUESTED = True
        except: pass
        time.sleep(2)

# ================= MAIN LOGIC =================

PROXY_SOURCES = [
    "https://cdn.jsdelivr.net/gh/databay-labs/free-proxy-list/socks5.txt",
    "https://cdn.jsdelivr.net/gh/databay-labs/free-proxy-list/https.txt",
    "https://cdn.jsdelivr.net/gh/databay-labs/free-proxy-list/http.txt"
]

BASE_DIR = "/sdcard/prox"
if not os.path.exists(BASE_DIR):
    try: os.makedirs(BASE_DIR, exist_ok=True)
    except: pass

FILE_HISTORY = os.path.join(BASE_DIR, "test_prox.txt") 
FILE_GOOD = os.path.join(BASE_DIR, "goodprox.txt")     

TIMEOUT = 3         
THREADS = 100       
TARGET_URL = "https://m.facebook.com"
CHECK_INTERVAL = 15  
FORCE_RESCAN_TIME = 180 

saved_history_set = set()      
session_sent_ips = set()       
good_proxies_list = []         

def load_history():
    global saved_history_set
    if os.path.exists(FILE_HISTORY):
        with open(FILE_HISTORY, "r", encoding="utf-8") as f:
            for line in f:
                ip_part = line.split("|")[0].strip()
                if ip_part: saved_history_set.add(ip_part)

def save_to_history(ip, full_info):
    if ip not in saved_history_set:
        try:
            with open(FILE_HISTORY, "a", encoding='utf-8') as f:
                f.write(full_info + "\n")
            saved_history_set.add(ip)
            return True 
        except: return False
    return False 

def check_remote_config():
    """Live Update for MS Limit (Fixed regex for spaces)"""
    global MAX_PING
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={AUTH_GROUP_ID}"
        r = requests.get(url, timeout=5)
        if r.json().get("ok"):
            text = r.json()["result"].get("pinned_message", {}).get("text", "")
            # FIX: Added \s* to allow spaces like "MS: 3000"
            match = re.search(r"MS:\s*(\d+)", text, re.IGNORECASE)
            if match:
                MAX_PING = int(match.group(1))
    except: pass

def send_single_msg_to_telegram(text, ip_for_check):
    global session_sent_ips
    if ip_for_check in session_sent_ips: return 
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": ADMIN_CHAT_ID, "text": f"🚀 {text}"}
        )
        session_sent_ips.add(ip_for_check)
    except: pass

def send_file_to_telegram():
    if not os.path.exists(FILE_GOOD) or os.path.getsize(FILE_GOOD) == 0: return 
    try:
        with open(FILE_GOOD, 'rb') as f:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            data = {"chat_id": ADMIN_CHAT_ID, "caption": f"✅ **Scan Complete (Limit: {MAX_PING}ms)**"}
            files = {"document": ("goodprox.txt", f)}
            requests.post(url, data=data, files=files)
    except: pass

def update_good_proxies(formatted_data):
    global good_proxies_list
    if formatted_data not in good_proxies_list:
        good_proxies_list.append(formatted_data)

def write_and_send_results():
    global good_proxies_list
    if not good_proxies_list: return
    try:
        unique_list = list(set(good_proxies_list))
        with open(FILE_GOOD, "w", encoding='utf-8') as f:
            for line in unique_list:
                f.write(line + "\n")
        send_file_to_telegram()
    except: pass
    good_proxies_list = []

def get_ip_info(ip):
    try:
        clean = ip.split(":")[0]
        r = requests.get(f"http://ip-api.com/json/{clean}?fields=country,proxy,hosting", timeout=5)
        if r.status_code == 200:
            d = r.json()
            sc = 0
            if not d.get('proxy'): sc += 50
            if not d.get('hosting'): sc += 50
            return d.get('country', 'Unknown'), sc
    except: pass
    return "Unknown", "N/A"

def get_source_proxies():
    proxies = set()
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    ip = line.strip()
                    if ip: proxies.add(ip)
        except: pass
    return proxies

def check_proxy(proxy_ip):
    try:
        proxy_ip = proxy_ip.strip()
        for proto in ['socks5', 'https', 'http']:
            try:
                url = f"{proto}://{proxy_ip}"
                start_t = time.time()
                with requests.Session() as session:
                    session.get(TARGET_URL, proxies={'http': url, 'https': url}, timeout=TIMEOUT)
                
                ping = int((time.time() - start_t) * 1000)

                if ping <= MAX_PING:
                    cntry, score = get_ip_info(proxy_ip)
                    history_format = f"{proxy_ip} | {cntry} | {ping}ms | {proto.upper()} | Score: {score}"
                    file_format = f"{proxy_ip}:{cntry}:{ping}ms"
                    
                    is_new_globally = save_to_history(proxy_ip, history_format)
                    update_good_proxies(file_format)
                    
                    if is_new_globally:
                        send_single_msg_to_telegram(file_format, proxy_ip)
                    return 
            except: pass
    except: pass

def main_tool():
    global MAX_PING, good_proxies_list, last_proxies_set, last_force_time, RESET_REQUESTED
    
    load_history()
    last_proxies_set = set()
    last_force_time = time.time()

    threading.Thread(target=telegram_command_listener, daemon=True).start()

    while True:
        try:
            check_remote_config()
            # Dynamic Output
            sys.stdout.write(f"\r{Fore.GREEN}Server Active: ON | Limit: {Fore.YELLOW}{MAX_PING}ms{Style.RESET_ALL}   ")
            sys.stdout.flush()
            
            if RESET_REQUESTED:
                last_proxies_set = set()
                last_force_time = time.time()
                good_proxies_list = []
                RESET_REQUESTED = False
                sys.stdout.write(f"\r{Fore.CYAN}Server Active: RESETTING...       {Style.RESET_ALL}")
                sys.stdout.flush()
                time.sleep(2)
                continue 

            current_proxies_set = get_source_proxies()
            if not current_proxies_set:
                time.sleep(CHECK_INTERVAL)
                continue

            has_changed = current_proxies_set != last_proxies_set
            time_diff = time.time() - last_force_time
            is_force_time = time_diff >= FORCE_RESCAN_TIME
            
            if has_changed:
                new_ips_only = current_proxies_set - last_proxies_set
                if new_ips_only:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
                        ex.map(check_proxy, list(new_ips_only))
                    
                    if good_proxies_list:
                        write_and_send_results()
                        
                last_proxies_set = current_proxies_set
                last_force_time = time.time() 

            elif is_force_time:
                good_proxies_list = [] 
                with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
                    ex.map(check_proxy, list(current_proxies_set))
                
                write_and_send_results()

                last_force_time = time.time()
                last_proxies_set = current_proxies_set

        except Exception:
            pass

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        sec = SecuritySystem()
        if sec.check_approval():
            main_tool()
    except: pass
