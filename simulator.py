import os
import time
import json
import random
from awscrt import mqtt
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configuration from environment variables
ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
CLIENT_ID = os.getenv("AWS_IOT_CLIENT_ID", "basicPubSub")
TOPIC = os.getenv("AWS_IOT_TOPIC", "sdk/test/python")

CERTS_DIR = os.getenv("AWS_IOT_CERTS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs"))
CERT_FILE = os.getenv("AWS_IOT_CERT_FILE")
KEY_FILE = os.getenv("AWS_IOT_KEY_FILE")
ROOT_CA_FILE = os.getenv("AWS_IOT_ROOT_CA_FILE", "AmazonRootCA1.pem")

# Telemetry simulation settings
PUBLISH_INTERVAL_SECS = float(os.getenv("SIM_PUBLISH_INTERVAL_SECS", "5.0"))
BASE_TEMPERATURE = float(os.getenv("SIM_BASE_TEMP", "25.0"))
TEMP_VARIATION_RANGE = float(os.getenv("SIM_TEMP_VARIATION", "1.5"))

# Validate mandatory configuration
missing_configs = []
if not ENDPOINT:
    missing_configs.append("AWS_IOT_ENDPOINT")
if not CERT_FILE:
    missing_configs.append("AWS_IOT_CERT_FILE")
if not KEY_FILE:
    missing_configs.append("AWS_IOT_KEY_FILE")

if missing_configs:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_configs)}. "
        "Please check your .env file or environment settings (see .env.example)."
    )

PATH_TO_CERT = os.path.join(CERTS_DIR, CERT_FILE)
PATH_TO_KEY = os.path.join(CERTS_DIR, KEY_FILE)
PATH_TO_ROOT_CA = os.path.join(CERTS_DIR, ROOT_CA_FILE)

# Validate certificate files exist before attempting connection
for path, label in [(PATH_TO_CERT, "Certificate"), (PATH_TO_KEY, "Private Key"), (PATH_TO_ROOT_CA, "Root CA")]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{label} file not found at: {path}. Check certs directory and file names.")

# Lifecycle and reconnection callbacks (offline tolerance & intermittent network behavior)
def on_connection_interrupted(connection, error, **kwargs):
    print(f"[WARN] Connection interrupted: {error}. AWS CRT SDK reconnecting with exponential backoff...")

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(f"[INFO] Connection resumed (return_code={return_code}, session_present={session_present}).")

def on_connection_success(connection, callback_data):
    print(f"[INFO] Connection successfully established to {ENDPOINT}.")

def on_connection_failure(connection, callback_data):
    print(f"[ERROR] Connection failed: {callback_data.error}")

def on_connection_closed(connection, callback_data):
    print("[INFO] Connection closed cleanly.")

# Build connection with automatic reconnection and session persistence enabled
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    ca_filepath=PATH_TO_ROOT_CA,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30,
    on_connection_interrupted=on_connection_interrupted,
    on_connection_resumed=on_connection_resumed,
    on_connection_success=on_connection_success,
    on_connection_failure=on_connection_failure,
    on_connection_closed=on_connection_closed
)

print(f"Connecting to {ENDPOINT} with Client ID '{CLIENT_ID}'...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")

# Telemetry loop with graceful shutdown, dynamic telemetry, and QoS 1 publish ack tracking
sequence_number = 0
try:
    while True:
        sequence_number += 1
        # Realistic sensor drift around base temperature
        temp_delta = random.uniform(-TEMP_VARIATION_RANGE, TEMP_VARIATION_RANGE)
        current_temp = round(BASE_TEMPERATURE + temp_delta, 2)
        status = "active" if random.random() > 0.05 else "idle"

        message = {
            "device_id": CLIENT_ID,
            "seq": sequence_number,
            "timestamp": int(time.time()),
            "temperature": current_temp,
            "status": status
        }
        payload_str = json.dumps(message)

        # Publish with QoS 1 and track completion/acknowledgement (PUBACK)
        publish_future, packet_id = mqtt_connection.publish(
            topic=TOPIC,
            payload=payload_str,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print(f"Publishing packet #{packet_id} (seq {sequence_number}): {payload_str}")

        # Wait for PUBACK from AWS IoT Core broker
        publish_future.result(timeout=10)
        print(f"  --> [ACK] Packet #{packet_id} confirmed by broker (QoS 1 PUBACK received).")

        time.sleep(PUBLISH_INTERVAL_SECS)

except KeyboardInterrupt:
    print("\nInterrupt signal received. Initiating graceful shutdown...")
except Exception as e:
    print(f"\nUnexpected error occurred during execution: {e}")
finally:
    print("Disconnecting from AWS IoT Core...")
    try:
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result(timeout=5)
        print("Disconnected cleanly.")
    except Exception as e:
        print(f"Warning: Disconnect completed with notice: {e}")