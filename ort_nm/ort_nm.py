# ort_nm/ort_nm.py

import requests
try:
    from ort_nm.mqtt_sniffer import start_sniffer
except ImportError:
    from mqtt_sniffer import start_sniffer

CONTROLLER_URL = "http://localhost:8080/mrt"


class ORTNM:
    """
    Optimized Real-Time Network Manager
    Paper Sections IV & V, Fig. 10
    """

    def __init__(self, broker_ip):
        self.broker_ip = broker_ip
        self.active_clients = set()
        self.admitted_flows = set()

    # ---------------- CONNECT ----------------
    def handle_connect(self, client_id):
        self.active_clients.add(client_id)
        print(f"[ORT-NM] CONNECT: {client_id}")

    # ---------------- SUBSCRIBE ----------------
    def handle_subscribe(self, topic, subscriber_ip):
        print(f"[ORT-NM] SUBSCRIBE: {topic} from {subscriber_ip}")

        payload = {
            "topic": topic,
            "subscriber_ip": subscriber_ip
        }

        requests.post(
            f"{CONTROLLER_URL}/register_subscriber",
            json=payload
        )

    # ---------------- PUBLISH ----------------
    def handle_publish(self, topic, user_props, src_ip):
        """
        Implements Fig.10 Steps 3–7
        """
        # Extract FiTS from User Properties (paper Eq.5)
        try:
            rt_attributes = {
                "qi": int(user_props["qi"]),
                "pi": int(user_props["pi"]),
                "ci": float(user_props["ci"]),
                "ti": float(user_props["ti"]),
                "di": float(user_props["di"]),
                "bwi": user_props["bwi"]
            }
        except KeyError:
            print("[ORT-NM] Missing RT attributes, ignoring publish")
            return False

        payload = {
            "topic": topic,
            "src_ip": src_ip,
            "broker_ip": self.broker_ip,
            "rt_attributes": rt_attributes
        }

        resp = requests.post(
            f"{CONTROLLER_URL}/register_flow",
            json=payload
        )

        if resp.status_code == 200:
            self.admitted_flows.add(topic)
            print(f"[ORT-NM] FLOW ADMITTED: {topic}")
            return True
        else:
            print(f"[ORT-NM] FLOW REJECTED: {topic}")
            return False


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    ort_nm = ORTNM(broker_ip="10.0.0.2")
    start_sniffer(ort_nm)
