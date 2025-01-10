import socketio
import json
import serial
import re
import time
import random
import requests
import hmac
import hashlib

# Serial settings
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# Server URLs
TRIGGER_URL = "http://172.20.10.6:5000/trigger"
SECRET_KEY = b'Dr Mohammed alshorman is the king'
user_id = 2


def generate_nonce():
    """Generate a unique nonce using timestamp and random value."""
    timestamp = int(time.time() * 1000)  # Current time in milliseconds
    random_value = random.randint(0, 999999)
    return f"{timestamp}-{random_value}"


# Generate the HMAC signature
def generate_signature(data):
    """Generate HMAC signature for the payload."""
    payload_json = json.dumps(data, separators=(',', ':'))
    signature = hmac.new(SECRET_KEY, payload_json.encode(), hashlib.sha256).hexdigest()
    return payload_json, signature

def read_from_serial():
    """Read data from the serial port and calculate the average."""
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            readings = []
            start_time = time.time()
            while time.time() - start_time < 1.5:  # Read for 2 seconds
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    match = re.search(r'\d+', data)
                    if match:
                        number = int(match.group())
                        if number > 0:
                            readings.append(number)
            return sum(readings) / len(readings) if readings else 1000
    except Exception as e:
        print(f"Error reading serial data: {e}")
        return 0

def send_value_to_server(average):
    """Send the value to the server."""
    try:
        nonce = generate_nonce()
        payload = {"value": f"{average}", "user_id": f"{user_id}", "nonce":nonce}
        payload_json, signature = generate_signature(payload)
        print(signature)
        headers = {"X-Signature": signature, "Content-Type": "application/json","Nonce": nonce}
        response = requests.post(TRIGGER_URL, data=payload_json, headers=headers)
        print("Server response:", response.json())
    except Exception as e:
        print(f"Error sending value to server: {e}")

# Create a Socket.IO client instance
sio = socketio.Client()

@sio.event
def connect():
    """Handle connection event."""
    print("Connected to the server via WebSocket!")

@sio.event
def disconnect():
    """Handle disconnect event."""
    print("Disconnected from the server.")

@sio.event
def start_processing(data):
    """Handle the 'start_processing' message from the server."""
    print("Received start signal from server. Processing...")
    average = read_from_serial()
    print(f"Calculated average: {average}")
    send_value_to_server(average)

def on_error(e):
    """Handle errors in the WebSocket connection."""
    print(f"Error: {e}")

if __name__ == "__main__":
    # Connect to the server using WebSocket
    socket_url = "http://172.20.10.6:5000"  # Same URL as server
    
    sio.connect(socket_url)
    

    sio.wait()