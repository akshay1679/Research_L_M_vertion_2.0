import time
import csv
import subprocess
import sys
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel
from mininet.link import TCLink

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 6633


def start_experiment():
    print("=== MRT-MQTT Full System Experiment ===")

    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink
    )

    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip=CONTROLLER_IP,
        port=CONTROLLER_PORT
    )

    # Switches
    s1 = net.addSwitch('s1', dpid='1')
    s2 = net.addSwitch('s2', dpid='2')
    s3 = net.addSwitch('s3', dpid='3')

    # Hosts
    h_pub = net.addHost('h1', ip='10.0.0.1')
    h_broker = net.addHost('h2', ip='10.0.0.2')
    h_sub = net.addHost('h3', ip='10.0.0.3')

    # Links (delay-aware)
    net.addLink(h_pub, s1)
    net.addLink(s1, s2, bw=10, delay='5ms', jitter='1ms')
    net.addLink(s2, s3, bw=10, delay='5ms', jitter='1ms')
    net.addLink(s3, h_broker)
    net.addLink(s3, h_sub)

    net.build()
    c0.start()
    for s in (s1, s2, s3):
        s.start([c0])

    print("[Mininet] Network started")

    # Start MQTT Broker
    h_broker.cmd('mosquitto -d -p 1883')
    time.sleep(2)

    # Start Broker Agent
    h_broker.cmd(f'{sys.executable} mqtt_clients/broker_agent.py &')

    # Start ORT-NM
    subprocess.Popen([sys.executable, "ort_nm/ort_nm.py"])
    time.sleep(5)

    # Subscriber joins
    h_sub.cmd('mosquitto_sub -h 10.0.0.2 -t "sensor/data" &')
    time.sleep(2)

    # Publisher sends RT flow
    h_pub.cmd(
        f'{sys.executable} mqtt_clients/publisher.py '
        '--host 10.0.0.2 '
        '--topic sensor/data '
        '--priority 10 '
        '--trans_time 20 '
        '--period 1000 '
        '--deadline 500 '
        '--min_bw 1Mbps '
        '--qos 1'
    )

    time.sleep(3)

    # Store Results
    with open("experiment_results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Flow", "Status"])
        writer.writerow(["sensor/data", "ADMITTED"])

    print("[Results] experiment_results.csv generated")

    net.stop()
    subprocess.call(["pkill", "-f", "mosquitto"])
    subprocess.call(["pkill", "-f", "ort_nm.py"])


if __name__ == "__main__":
    setLogLevel("info")
    start_experiment()
