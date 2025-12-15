import socket
import time
import json
import threading
import requests

CONTROLLER_URL = "http://localhost:8080/mrt"
BUFFER_SIZE = 65535

class BrokerAgent:
    """
    Broker Agent (BA_i)
    Paper Section V-A, Fig. 8

    Responsibilities:
    - Join multicast groups
    - Receive multicast traffic
    - Measure processing delay (T_proc)
    - Republish data to local MQTT broker (assumed)
    - Acknowledge reception to controller
    """

    def __init__(self, broker_ip: str):
        self.broker_ip = broker_ip
        self.running = True
        self.multicast_sockets = {}

    # ---------------------------
    # Multicast Join (Paper Step)
    # ---------------------------
    def join_multicast_group(self, mcast_ip: str, port: int):
        if mcast_ip in self.multicast_sockets:
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', port))
        mreq = socket.inet_aton(mcast_ip) + socket.inet_aton('0.0.0.0')
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.multicast_sockets[mcast_ip] = sock

        t = threading.Thread(target=self._listen_multicast, args=(mcast_ip, sock))
        t.daemon = True
        t.start()

        print(f"[BA] Joined multicast group {mcast_ip}:{port}")

    # ---------------------------------
    # Multicast Receive + Processing
    # ---------------------------------
    def _listen_multicast(self, mcast_ip: str, sock: socket.socket):
        while self.running:
            data, addr = sock.recvfrom(BUFFER_SIZE)

            recv_time = time.time()

            # --- Simulated Broker Processing ---
            self._process_message(data)

            proc_time = (time.time() - recv_time) * 1000.0  # ms

            # --- Notify Controller (Paper: feedback loop) ---
            self._send_processing_feedback(mcast_ip, proc_time)

    # ---------------------------------
    # Simulated Application Processing
    # ---------------------------------
    def _process_message(self, payload: bytes):
        """
        Paper: Broker processing delay T_proc
        Actual MQTT republish is assumed infrastructure
        """
        time.sleep(0.001)  # Simulated minimal processing

    # ---------------------------------
    # Feedback to Controller
    # ---------------------------------
    def _send_processing_feedback(self, topic: str, t_proc: float):
        payload = {
            "topic": topic,
            "broker_ip": self.broker_ip,
            "processing_delay": t_proc
        }

        try:
            requests.post(
                f"{CONTROLLER_URL}/broker_feedback",
                json=payload,
                timeout=1
            )
        except Exception:
            pass  # Paper assumes reliable control plane

    # ---------------------------------
    # Shutdown
    # ---------------------------------
    def stop(self):
        self.running = False
        for sock in self.multicast_sockets.values():
            sock.close()


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    # Broker IP is assumed known (paper assumption)
    agent = BrokerAgent(broker_ip="10.0.0.2")

    # NOTE:
    # Multicast join is triggered by controller logic
    # This file provides the BA_i behavior only
    while True:
        time.sleep(10)
