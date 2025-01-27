# Shut down the workstation if the user has not logged on 
# in 30 minutes and send an alert on Telegram
# Author      : Bairaktaris Emmanuel
# Date        : January 27, 2025
# Last version: January 27, 2025
# Link        : https://sonam.dev

import os
import sys
import time
import socket
import logging
import requests
import win32api
import win32gui
import win32process
import psutil
import datetime

# Configuration
LOG_FOLDER = "C://tools//scripts//"  # Folder to store the log file

# Initialize logging with date in the log file name
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
LOG_FILE = f"{LOG_FOLDER}/login_monitor_{current_date}.log"

# Configuration
TELEGRAM_BOT_TOKEN = 'your_bot_token_key'
TELEGRAM_CHAT_ID = 'your_telegram_chat_id'
CHECK_INTERVAL = 60  # Check every minute

# Configure logging
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    filemode='a'
)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger('').addHandler(console)

def is_locked_or_login_screen():
    try:
        # Check if there are any logged-in users
        logged_in_users = [user.name for user in psutil.users()]
        if logged_in_users:
            logging.info(f"Logged in users: {logged_in_users}")
            return False  # User is logged in

        # Check desktop processes
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                # Check for lock screen or login-related processes
                process_name = proc.info['name'].lower()
                if process_name in ['logonui.exe', 'winlogon.exe']:
                    logging.info(f"Lock-related process found: {process_name}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Additional username and active window checks
        try:
            username = win32api.GetUserName()
            active_window = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(active_window)
            
            logging.info(f"Username: {username}, Active Window: {window_text}")
            
            # Check for specific login indicators
            login_indicators = [
                "sign in", "unlock", "windows security", 
                "lock screen", "login", "welcome"
            ]
            
            if any(indicator in window_text.lower() for indicator in login_indicators):
                return True
        
        except Exception as e:
            logging.error(f"Detection check error: {e}")
        
        return False
    
    except Exception as e:
        logging.error(f"Comprehensive login detection error: {e}")
        return False

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        requests.post(url, data=payload)
        logging.info(f"Telegram message sent: {message}")
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

def is_within_restricted_time():
    now = datetime.datetime.now()
    current_day = now.strftime("%A")  # Get the current day of the week
    current_time = now.time()  # Get the current time

    # Define restricted time periods
    if current_day == "Thursday":
        # Thursday from 19:00 to 00:30
        start_time = datetime.time(19, 0)
        end_time = datetime.time(22, 30)
        if start_time <= current_time or current_time <= end_time:
            return True

    elif current_day == "Friday":
        # Friday from 20:00 to 01:00
        start_time = datetime.time(19, 0)
        end_time = datetime.time(1, 0)
        if start_time <= current_time or current_time <= end_time:
            return True

    return False

def monitor_login_state():
    locked_duration = 0  # Duration in seconds
    check_interval = 60  # Check every 60 seconds
    max_locked_duration = 30 * 60  # 30 minutes in seconds
    pc_name = socket.gethostname()  # Get the computer name

    while True:
        if is_locked_or_login_screen():
            locked_duration += check_interval
            logging.info(f"Computer is in Login Screen/Locked for {locked_duration // 60} minutes.")
            
            if locked_duration >= max_locked_duration:
                if not is_within_restricted_time():  # Check if it's within restricted time
                    logging.warning("Computer has been in Login Screen/Locked for more than 30 minutes. Shutting down.")
                    message = f"The computer '{pc_name}' is shutting down due to inactivity."
                    send_telegram_message(message)
                    # Shutdown command
                    os.system("shutdown /s /t 1")
                    break  # Exit the loop after shutdown command
                else:
                    logging.info("Shutdown prevented due to restricted time.")

        else:
            logging.info("User is logged in. Resetting locked duration.")
            locked_duration = 0  # Reset the counter if the user is logged in

        time.sleep(check_interval)  # Wait for the next check

def main():
    pc_name = socket.gethostname()
    last_login_state = None
    logging.info(f"Login monitor started for PC: {pc_name}")

    while True:
        try:
            current_login_state = is_locked_or_login_screen()
            
            if current_login_state != last_login_state:
                message = f"PC: {pc_name} - User login state: {'Login Screen/Locked' if current_login_state else 'Logged In'}"
                logging.info(message)
                send_telegram_message(message)
                last_login_state = current_login_state

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_login_state()
