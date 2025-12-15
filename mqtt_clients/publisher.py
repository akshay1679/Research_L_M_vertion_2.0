import argparse
import sys
import time
import paho.mqtt.client as mqtt
from ort_nm.ort_nm import ORTNM

# ---------------------------
# Argument Parsing
# ---------------------------
parser = argparse.ArgumentParser(description="RT-Aware MQTT Publisher")
parser.add_argument("--host", required=True, help="MQTT Broker IP")
parser.add_argument("--topic", required=True)
parser.add_argument("--qos", type=int, default=1)
parser.add_argument("--priority", type=int, required=True)
parser.add_argument("--trans_time", type=float, required=True)
parser.add_argument("--period", type=float, required=True)
parser.add_argument("--deadline", type=float, required=True)
parser.add_argument("--min_bw", required=True)

args = parser.parse_args()

# ---------------------------
# RT-NM Interaction (Paper Fig.10)
# ---------------------------
ort_nm = ORTNM(broker_ip=args.host)

rt_attributes = {
    "qi": args.qos,
    "pi": args.priority,
    "ci": args.trans_time,
    "ti": args.period,
    "di": args.deadline,
    "bwi": args.min_bw
}

admitted = ort_nm.handle_publish(
    topic=args.topic,
    rt_attributes=rt_attributes,
    src_ip="PUBLISHER"
)

if not admitted:
    print("[Publisher] Flow rejected by Admission Control")
    sys.exit(1)

print("[Publisher] Flow admitted, publishing data...")

# ---------------------------
# MQTT Publish (Only after Admission)
# ---------------------------
client = mqtt.Client(protocol=mqtt.MQTTv5)

client.connect(args.host, 1883, 60)
client.loop_start()

seq = 0
while True:
    payload = f"DATA {seq}"
    client.publish(args.topic, payload, qos=args.qos)
    seq += 1
    time.sleep(args.period / 1000.0)
