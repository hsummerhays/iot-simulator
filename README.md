# IoT Simulator

A lightweight Python client and container setup for simulating an IoT device publishing telemetry data to **AWS IoT Core** over MQTT with mutual TLS (mTLS).

---

## Overview

- **Protocol**: MQTT (via AWS CRT / AWS IoT Device SDK v2)
- **Authentication**: Mutual TLS (X.509 client certificate and private key)
- **Endpoint**: ATS (Amazon Trust Services) endpoint (`<id>-ats.iot.<region>.amazonaws.com`)
- **Default Topic**: `sdk/test/python`
- **Default Client ID**: `basicPubSub`
- **Dynamic Telemetry**: Emulates sensor temperature drift (`SIM_BASE_TEMP`, `SIM_TEMP_VARIATION`), sequence indexing (`seq`), timestamps, and device status
- **Delivery Guarantee**: MQTT QoS 1 (`AT_LEAST_ONCE`) with explicit broker acknowledgement (`PUBACK`) tracking
- **Resilience**: Automatic reconnection with exponential backoff and SDK lifecycle callbacks (`on_connection_interrupted`, `on_connection_resumed`)
- **Graceful Shutdown**: `finally` block ensuring proper disconnection on termination signals or unexpected errors

---

## Project Structure

```text
iot-simulator/
├── .dockerignore          # Prevents certs, keys, and secrets from entering Docker build context
├── .env.example            # Template for environment variables
├── .gitignore              # Ignores certs/, .env, policy*.json, python caches
├── Dockerfile              # Containerized runner
├── README.md               # Project documentation
├── CHANGELOG.md            # Change log
├── check_iot_config.ps1    # PowerShell diagnostics for AWS CLI, cert, policies, and endpoint
├── policy_template.json    # Sanitized reference AWS IoT policy template
├── requirements.txt        # Python dependencies (awsiotsdk, python-dotenv)
├── simulator.py            # Main MQTT publishing script
├── start.sh                # Sample launch script for SDK reference
└── certs/                  # AWS IoT certificates & keys (git-ignored)
    ├── <cert-id>-certificate.pem.crt
    ├── <cert-id>-private.pem.key
    ├── <cert-id>-public.pem.key
    ├── AmazonRootCA1.pem
    └── AmazonRootCA3.pem
```

---

## Prerequisites

- **Python 3.9+**
- **AWS IoT Certificates**: Placed inside the `certs/` directory:
  - Device certificate (`*-certificate.pem.crt`)
  - Private key (`*-private.pem.key`)
  - Root CA (`AmazonRootCA1.pem`)
- **AWS Permissions / IoT Policy**: Ensure your policy permits:
  - `iot:Connect` for your Client ID (`basicPubSub`)
  - `iot:Publish` to the target topic (`sdk/test/python`)
  - Reference [policy_template.json](policy_template.json) for resource formatting.

---

## Setup & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (.env)

Copy the `.env.example` file to create your local `.env` (which is excluded from Git):

```bash
cp .env.example .env
```

Configure your parameters:
- `AWS_IOT_ENDPOINT`: Your AWS IoT Core Data-ATS endpoint
- `AWS_IOT_CLIENT_ID`: The MQTT client identifier registered or permitted in your policy
- `AWS_IOT_TOPIC`: Target MQTT topic
- `AWS_IOT_CERT_FILE`, `AWS_IOT_KEY_FILE`, `AWS_IOT_ROOT_CA_FILE`: Filenames matching your files in `certs/`
- `AWS_IOT_CERT_ID` & `AWS_REGION`: Used for the PowerShell diagnostics script
- `SIM_PUBLISH_INTERVAL_SECS`: Telemetry publish cadence in seconds (default: `5.0`)
- `SIM_BASE_TEMP`: Baseline simulation temperature in Celsius (default: `25.0`)
- `SIM_TEMP_VARIATION`: Random temperature variance range `±Δ` (default: `1.5`)

### 3. Verify Configuration (PowerShell)

Run the included verification script to validate AWS CLI access, certificate status, attached policies, and endpoint:

```powershell
.\check_iot_config.ps1
```

### 4. Run Locally

```bash
python simulator.py
```

Expected output:
```text
Connecting to <your-ats-endpoint>.iot.us-east-1.amazonaws.com with Client ID 'basicPubSub'...
[INFO] Connection successfully established to <your-ats-endpoint>.iot.us-east-1.amazonaws.com.
Connected!
Publishing packet #1 (seq 1): {"device_id": "basicPubSub", "seq": 1, "timestamp": 1726415500, "temperature": 25.82, "status": "active"}
  --> [ACK] Packet #1 confirmed by broker (QoS 1 PUBACK received).
Publishing packet #2 (seq 2): {"device_id": "basicPubSub", "seq": 2, "timestamp": 1726415505, "temperature": 24.64, "status": "active"}
  --> [ACK] Packet #2 confirmed by broker (QoS 1 PUBACK received).
^C
Interrupt signal received. Initiating graceful shutdown...
Disconnecting from AWS IoT Core...
[INFO] Connection closed cleanly.
Disconnected cleanly.
```

---

## Running with Docker

Build the simulator container (note: certificates and local secrets are excluded via `.dockerignore`):

```bash
# Build the Docker image
docker build -t iot-simulator .
```

Run the container, mounting the `certs/` directory as **read-only** (`:ro`) and supplying configuration via `.env`:

```bash
# Run container with read-only volume mount for certs
docker run --rm -it \
  --env-file .env \
  -v "${PWD}/certs:/app/certs:ro" \
  iot-simulator
```

On PowerShell:
```powershell
docker run --rm -it --env-file .env -v "${PWD}/certs:/app/certs:ro" iot-simulator
```

> **Security Note**:
> - Never bake sensitive certificates, private keys, or `.env` files into Docker images.
> - `.dockerignore` blocks credentials from build context, and certificates should always be mounted read-only at runtime (`/app/certs:ro`).
