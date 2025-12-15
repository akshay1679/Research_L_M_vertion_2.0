# sdn_controller/msdp.py

import threading
import json
import socket
import logging
import time

logging.basicConfig(level=logging.INFO, format='[MSDP] %(message)s')


class MSDP_Signaling:
    """
    MSDP-like Source Active (SA) signaling.
    Paper Section V-B (Inter-domain multicast).
    Control-plane abstraction only (paper assumption).
    """

    def __init__(self, my_ip: str, peers: list):
        self.my_ip = my_ip
        self.peers = peers
        self.active_sources = {}   # topic -> src_ip
        self.running = False
        self.sock = None

    # ---------------------------------------
    # Listener (Receive SA messages)
    # ---------------------------------------
    def start_listener(self, port=1791):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(5)

        t = threading.Thread(target=self._listen_loop, daemon=True)
        t.start()
        logging.info(f"MSDP listener running on port {port}")

    def _listen_loop(self):
        while self.running:
            try:
                client, addr = self.sock.accept()
                threading.Thread(
                    target=self._handle_peer,
                    args=(client, addr),
                    daemon=True
                ).start()
            except Exception as e:
                logging.error(f"Listener error: {e}")

    def _handle_peer(self, client, addr):
        try:
            data = client.recv(2048).decode()
            if not data:
                return
            msg = json.loads(data)
            self._process_sa(msg, addr[0])
        except Exception as e:
            logging.error(f"Peer error {addr}: {e}")
        finally:
            client.close()

    # ---------------------------------------
    # SA Processing (Paper-defined behavior)
    # ---------------------------------------
    def _process_sa(self, msg, peer_ip):
        if msg.get("type") != "SA":
            return

        topic = msg.get("topic")
        src_ip = msg.get("src_ip")

        if not topic or not src_ip:
            return

        if topic not in self.active_sources:
            self.active_sources[topic] = src_ip
            logging.info(
                f"Discovered remote source for topic '{topic}' at {src_ip} via {peer_ip}"
            )

    # ---------------------------------------
    # SA Advertisement
    # ---------------------------------------
    def send_sa(self, topic: str, src_ip: str):
        msg = {
            "type": "SA",
            "topic": topic,
            "src_ip": src_ip,
            "origin": self.my_ip,
            "timestamp": time.time()
        }

        for peer in self.peers:
            self._send(peer, msg)

    def _send(self, peer_ip, msg, port=1791):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((peer_ip, port))
            s.send(json.dumps(msg).encode())
            s.close()
            logging.info(f"Sent SA({msg['topic']}) to {peer_ip}")
        except Exception as e:
            logging.error(f"Failed to send SA to {peer_ip}: {e}")

    # ---------------------------------------
    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
