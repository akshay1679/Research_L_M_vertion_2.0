# ort_nm/mqtt_sniffer.py

from scapy.all import sniff
from scapy.layers.inet import TCP, IP
import struct

MQTT_PORT = 1883

# MQTT Packet Types
MQTT_CONNECT = 1
MQTT_PUBLISH = 3
MQTT_SUBSCRIBE = 8


def parse_remaining_length(payload, idx):
    multiplier = 1
    value = 0
    while True:
        encoded = payload[idx]
        idx += 1
        value += (encoded & 127) * multiplier
        if (encoded & 128) == 0:
            break
        multiplier *= 128
    return value, idx


def parse_utf8(payload, idx):
    length = struct.unpack("!H", payload[idx:idx+2])[0]
    idx += 2
    value = payload[idx:idx+length].decode(errors="ignore")
    return value, idx + length


def parse_user_properties(payload, idx):
    props = {}
    prop_len, idx = parse_remaining_length(payload, idx)
    end = idx + prop_len

    while idx < end:
        prop_id = payload[idx]
        idx += 1

        # User Property (0x26)
        if prop_id == 0x26:
            key, idx = parse_utf8(payload, idx)
            val, idx = parse_utf8(payload, idx)
            props[key] = val
        else:
            # Skip unknown property safely
            break

    return props


def mqtt_packet_handler(pkt, ort_nm):
    if not pkt.haslayer(TCP):
        return

    if pkt[TCP].dport != MQTT_PORT:
        return

    payload = bytes(pkt[TCP].payload)
    if len(payload) < 2:
        return

    pkt_type = payload[0] >> 4
    idx = 1
    _, idx = parse_remaining_length(payload, idx)

    # ---------------- CONNECT ----------------
    if pkt_type == MQTT_CONNECT:
        _, idx = parse_utf8(payload, idx)  # Protocol Name
        idx += 1  # Version
        idx += 1  # Flags
        idx += 2  # Keepalive

        # Properties (v5)
        _, idx = parse_remaining_length(payload, idx)

        client_id, _ = parse_utf8(payload, idx)
        ort_nm.handle_connect(client_id)

    # ---------------- SUBSCRIBE ----------------
    elif pkt_type == MQTT_SUBSCRIBE:
        idx += 2  # Packet Identifier
        _, idx = parse_remaining_length(payload, idx)

        topic, _ = parse_utf8(payload, idx)
        subscriber_ip = pkt[IP].src if pkt.haslayer("IP") else "UNKNOWN"
        ort_nm.handle_subscribe(topic, subscriber_ip)

    # ---------------- PUBLISH ----------------
    elif pkt_type == MQTT_PUBLISH:
        topic, idx = parse_utf8(payload, idx)
        props = parse_user_properties(payload, idx)
        src_ip = pkt[IP].src if pkt.haslayer("IP") else "UNKNOWN"

        ort_nm.handle_publish(topic, props, src_ip)


def start_sniffer(ort_nm):
    sniff(
        filter="tcp port 1883",
        prn=lambda pkt: mqtt_packet_handler(pkt, ort_nm),
        store=False
    )
