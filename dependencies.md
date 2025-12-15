# Dependencies

This document lists the system requirements and Python dependencies necessary to run the MRT-MQTT framework.

## 1. System Requirements (Linux)

The framework relies on the following system-level tools. These must be installed on the host machine (typically Ubuntu/Debian).

-   **Python 3.9+**: The core language for the controller and scripts.
-   **Mininet**: For network emulation.
    ```bash
    sudo apt-get install mininet
    ```
-   **Open vSwitch (OVS)**: The software switch used by Mininet.
    ```bash
    sudo apt-get install openvswitch-switch
    ```
-   **Mosquitto MQTT Broker**: Standard MQTT broker.
    ```bash
    sudo apt-get install mosquitto mosquitto-clients
    ```
-   **git**: For version control (implicit).

## 2. Python Dependencies

These packages should be installed in your Python environment (e.g., via `pip`).

| Package | Purpose |
| :--- | :--- |
| **`ryu`** | The SDN Controller framework. |
| **`networkx`** | Used for graph modeling and path calculations (Dijkstra, etc.). |
| **`paho-mqtt`** | MQTT v5.0 client library for Publisher and Subscribers. |
| **`requests`** | Used by `ort_nm.py` to communicate with the REST API of the controller. |
| **`mininet`** | Python bindings for Mininet (often comes with system install, but can be pip installed). |
| **`numpy`** | *Recommended* (often used by Ryu/Matplotlib dependencies). |

### Optional / Verification Tools

The following are used for experiments and plotting, though strictly optional for the core runtime:

-   **`matplotlib`**: For generating `wcrt_plot.png`.
-   **`scapy`**: Mentioned in compliance docs for packet manipulation/monitoring, though default `monitor.py` uses simulation mode.

## 3. Installation Command

To install all Python dependencies at once:

```bash
pip install ryu networkx paho-mqtt requests numpy matplotlib scapy
```
