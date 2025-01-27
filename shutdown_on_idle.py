## ----------------------------------------------------------------------- ##
# Script to shut down workstations on idle                                  #
# Author      : Bairaktaris Emmanuel                                        #
# Date        : January 4, 2025                                             #
# Last version: January 7, 2025                                             #
# Link        : https://sonam.dev                                           #
## ----------------------------------------------------------------------- ##
import ctypes
import os
import time
import requests
from datetime import datetime
from win11toast import toast

# Threshold for idle time in minutes
IDLE_THRESHOLD = 120  # Change this to your desired idle time in minutes

# Log file path
LOG_FILE = "C:\\tools\\scripts\\idle_shutdown_log.txt"

# Telegram bot token and chat ID
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def log_activity(message):
    """Log activity with a timestamp to a file and print to console."""
    # Get the current date for the log file name
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file_path = f"C:\\tools\\scripts\\idle_shutdown_log_{current_date}.txt"

    # Get the current timestamp for logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"{timestamp} - {message}"
    print(log_message)  # Print to console

    # Write the log message to the file for the current date
    with open(log_file_path, "a") as log_file:
        log_file.write(log_message + "\n")  # Write to log file
        
def get_idle_duration():
    """Get the system's idle time in minutes."""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]

    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info))
    millis = ctypes.windll.kernel32.GetTickCount() - last_input_info.dwTime
    return millis / 1000 / 60  # Convert milliseconds to minutes

def send_toast_notification():
    """Send a toast notification about the impending shutdown."""
    toast(app_id='Your app Header Title', 
          title='Idle Shutdown Warning',
          body='Your system has been idle for too long and will shut down in 30 seconds.', 
          audio='ms-winsoundevent:Notification.Looping.Alarm', 
          icon='C:\\tools\\scripts\\alert.ico',
          duration='long',
          button='Cancel Shutdown')

def send_telegram_message(message):
    """Send a message to a specified Telegram chat using a bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            log_activity("Telegram message sent successfully.")
        else:
            log_activity(f"Failed to send Telegram message. Status code: {response.status_code}")
    except Exception as e:
        log_activity(f"Error sending Telegram message: {e}")

def main():
    """Main function to monitor idle time and shut down if necessary."""
    log_activity("Script started. Monitoring idle time.")

    while True:
        idle_time = get_idle_duration()
        log_activity(f"Calculated idle time: {idle_time:.2f} minutes.")

        if idle_time >= IDLE_THRESHOLD:
            computer_name = os.getenv('COMPUTERNAME')
            log_activity("Idle time exceeded threshold. Preparing to shut down.")
            send_toast_notification()

            # Wait 30 seconds to allow user to cancel the shutdown
            for _ in range(30):
                time.sleep(1)
                idle_time = get_idle_duration()
                if idle_time < IDLE_THRESHOLD:
                    log_activity("Shutdown canceled. Continuing to monitor idle time.")
                    break
            else:
                shutdown_message = f"System '{computer_name}' is shutting down due to inactivity."
                send_telegram_message(shutdown_message)
                log_activity("Workstation is shutting down.")
                os.system("shutdown /s /f /t 0")  # Initiates immediate shutdown
                break
        else:
            log_activity(f"System has been idle for {idle_time:.2f} minutes. No action taken.")
            time.sleep(60)  # Check idle time every 60 seconds

if __name__ == "__main__":
    main()
