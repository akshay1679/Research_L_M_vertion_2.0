# MRT-MQTT System Documentation

## Overview
**MRT-MQTT** (Scalable Real-Time SDN-Based MQTT) is a framework designed to provide deterministic latency and jitter guarantees for MQTT traffic in industrial environments. It leverages Software-Defined Networking (SDN) to separate the control plane from the data plane, allowing for dynamic, delay-aware routing and admission control.

## System Architecture

The system consists of three main planes:

1.  **Control Plane (SDN Controller)**: Centralized logic for network topology management, path calculation, and flow verification.
2.  **Management Plane (ORT-NM)**: Intercepts MQTT control packets to manage flow registration and user properties.
3.  **Data Plane (Switches & Brokers)**: Handles actual packet forwarding using OpenFlow rules and optimizes multicast distribution.

### Architecture Diagram

```mermaid
graph TD
    subgraph Control Plane
        Ryu[Ryu SDN Controller]
        Ryu -->|Routing| Path[Path Calc (Dijkstra/Steiner)]
        Ryu -->|Analysis| WCRT[WCRT Analysis (HA/TA)]
    end

    subgraph Management Plane
        ORT[ORT-NM]
        ORT -.->|Register Flow| Ryu
    end

    subgraph Data Plane
        Pub[Publisher] -->|MQTT| ORT
        ORT -->|Forward| Broker[MQTT Broker]
        Broker -->|Topics| BA[Broker Agent]
        BA -->|Multicast| Sub[Subscriber]
        
        Switch[OpenFlow Switch]
        Ryu -->|Flow Mods| Switch
        Switch -->|Traffic| Broker
    end
```

## Key Components

### 1. SDN Controller (`sdn_controller/`)
The core intelligence of the network, implemented using the Ryu framework.
-   **`ryu_mrt_app.py`**: The main application that handles OpenFlow events, topology discovery, and exposes REST APIs for flow registration (`/mrt/register_flow`).
-   **`routing.py`**: Implements delay-aware routing algorithms. It uses Dijkstra for unicast and a Steiner Tree approximation for multicast traffic. It selects the optimal Rendezvous Point (RP) for QoS 1/2 traffic based on network centrality.
-   **`msdp.py`**: Implements Multicast Source Discovery Protocol logic to allow topic discovery across different broker domains.

### 2. Schedulability Analysis (`schedulability/`)
Ensures that all admitted flows meet their deadlines ($D_i$).
-   **`analysis.py`**: Implements Worst-Case Response Time (WCRT) analysis.
    -   **Holistic Approach (HA)**: A pessimistic model considering all possible interference.
    -   **Trajectory Approach (TA)**: A tighter bound model that considers the specific path and pipelining effects.
-   **`admission.py`**: The gatekeeper that accepts or rejects flows based on the WCRT analysis results.

### 3. Optimized Real-Time Network Manager (ORT-NM) (`ort_nm/`)
Acts as a middleware between the MQTT clients and the SDN controller.
-   **`ort_nm.py`**: Transparently intercepts MQTT `CONNECT` and `PUBLISH` packets.
-   **Functionality**: Extracts custom Real-Time User Properties (Cost, Period, Time, Deadline, Bandwidth) defined in MQTT v5 packets and registers them with the SDN Controller.

### 4. MQTT Clients (`mqtt_clients/`)
Custom implementations and agents to support the MRT-MQTT protocol.
-   **`publisher.py`**: A modified MQTT publisher that injects the required real-time attributes into the MQTT User Properties.
-   **`broker_agent.py`**: A sidecar process for the standard MQTT broker. It handles UDP multicast group joining and local bridging of traffic to the application layer.

### 5. Simulation & Verification (`simulation/`)
Tools for running experiments and validating the system.
-   **`experiment_runner.py`**: Orchestrates a full Mininet experiment, spinning up a topology, controller, and clients to verify end-to-end functionality.
-   **`monitor.py`**: A background measuring tool that constantly probes link delays and jitter to update the controller's view of the network.

## Data Flow

1.  **Flow Advertisement**: A Publisher sends a message with RT attributes.
2.  **Interception**: ORT-NM captures the message, parses attributes ($C_i, T_i, D_i$), and queries the Controller.
3.  **Admission Control**: The Controller calculates WCRT. If $WCRT \leq D_i$, the flow is admitted.
4.  **Path Allocation**: The Controller calculates the optimal path (unicast or multicast tree) and installs OpenFlow rules (Queues, Meters) on switches.
5.  **Transmission**: The message is forwarded through the high-priority data plane paths.

## Compliance
This implementation is fully compliant with the "Scalable Real-Time SDN-Based MQTT" research paper, featuring:
-   Strict MQTT v5 User Property parsing.
-   Dynamic multicast tree calculation and "Grafting" for new subscribers.
-   Real-time jitter and delay monitoring.
-   Full implementation of Broker Agents for hybrid unicast/multicast delivery.
