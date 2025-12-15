# How to Run MRT-MQTT

This guide provides instructions on setting up the environment and running the MRT-MQTT framework.

## Prerequisites

Ensure you have the following installed on your Linux system:
-   **Python 3.9+**
-   **Mininet** (requires root privileges)
-   **Open vSwitch (OVS)**
-   **Mosquitto MQTT Broker**

## 1. Installation

1.  **Create and Activate Virtual Environment**:
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    Install the required Python packages including Ryu, NetworkX, and Paho-MQTT.
    ```bash
    pip install -r requirements.txt
    # Or manually:
    pip install ryu networkx paho-mqtt requests numpy scipy matplotlib scapy
    ```

    > **Note**: If `requirements.txt` is missing, use the manual command above.

## 2. Running the Full Simulation (Recommended)

The easiest way to verify the system is to run the automated experiment runner. This script sets up a Mininet topology, starts the SDN controller, initializes the MQTT broker and agents, and runs a test flow.

**Command**:
```bash
sudo python3 simulation/experiment_runner.py
```
*(Note: `sudo` is required for Mininet to create virtual network interfaces)*

**What this does**:
1.  Creates a network topology with 3 switches and 3 hosts (Publisher, Broker, Subscriber).
2.  Starts the Ryu SDN Controller on `localhost`.
3.  Starts Mosquitto and the Broker Agent on the Broker host.
4.  Starts ORT-NM.
5.  Simulates a Publisher sending a delay-sensitive flow.
6.  Generates `experiment_results.csv` with admission status.

## 3. Manual Component Startup

If you wish to run components individually (e.g., across real hardware or custom Mininet scripts), follow this order:

### Step 1: Start the SDN Controller
The controller must be running to handle network events and API requests.
```bash
ryu-manager sdn_controller/ryu_mrt_app.py
```

### Step 2: Start the Broker & Agent
On the machine acting as the MQTT Broker:
```bash
# Start Mosquitto in background
mosquitto -d -p 1883

# Start the Broker Agent
python3 mqtt_clients/broker_agent.py
```

### Step 3: Start ORT-NM
Run the Network Manager which acts as the interception proxy.
```bash
python3 ort_nm/ort_nm.py
```

### Step 4: Run Clients
**Subscriber**:
```bash
mosquitto_sub -h <BROKER_IP> -t "sensor/data"
```

**Publisher** (with Real-Time Attributes):
```bash
python3 mqtt_clients/publisher.py \
  --host <BROKER_IP> \
  --topic sensor/data \
  --priority 10 \
  --trans_time 20 \
  --period 1000 \
  --deadline 500 \
  --min_bw 1Mbps \
  --qos 1
```

## Troubleshooting

-   **Mininet Failures**: If Mininet doesn't start or clean up properly, run `sudo mn -c` to clean the topology state.
-   **Controller Connection**: Ensure port 6633 (OpenFlow) and 8080 (REST API) are not blocked.
-   **Python Version**: Ryu can be sensitive to Python versions. Ensure you are using Python 3.9 if you encounter `eventlet` or `greenlet` issues.
