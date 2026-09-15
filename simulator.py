import os
import time
import json
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

# Build connection
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    ca_filepath=PATH_TO_ROOT_CA,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30
)

print(f"Connecting to {ENDPOINT}...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")

# Send data loop
try:
    while True:
        message = {"temperature": 25.6, "status": "active"}
        mqtt_connection.publish(topic=TOPIC, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
        print(f"Published: {message} to {TOPIC}")
        time.sleep(5)
except KeyboardInterrupt:
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()