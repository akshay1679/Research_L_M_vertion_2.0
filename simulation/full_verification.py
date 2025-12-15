import time
from common.rt_attributes import RTAttributes, Link, Switch
from common.of_db import of_db
from schedulability.analysis import HolisticApproach
from sdn_controller.routing import RoutingEngine
from simulation.monitor import NetworkMonitor

def run_verification():
    print("=== Full MRT-MQTT Verification ===")

    monitor = NetworkMonitor(simulation_mode=True)
    monitor.start_monitoring()

    s1 = Switch(1, "S1")
    s2 = Switch(2, "S2")

    of_db.add_switch(1, s1)
    of_db.add_switch(2, s2)

    l = Link("1", "2", 1, bw_capacity=100)
    of_db.add_link("1", "2", 1, l)

    time.sleep(6)

    flow = RTAttributes(
        ft_i="topic/alert",
        qi=1,
        ci=2.0,
        pi=10,
        ti=20.0,
        di=20.0,
        bwi=5.0
    )

    flow.src_ip = "1"
    flow.dst_ips = ["2"]
    flow.route_links = [l]

    wcrt = HolisticApproach.calculate_wcrt(flow, [flow])
    print(f"WCRT (Measured): {wcrt:.3f} ms")

    print("Admitted:", wcrt <= flow.di)


if __name__ == "__main__":
    run_verification()
