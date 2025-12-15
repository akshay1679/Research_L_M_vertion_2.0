from common.rt_attributes import RTAttributes, Link, Switch
from common.of_db import of_db
from schedulability.analysis import HolisticApproach, TrajectoryApproach
from sdn_controller.routing import RoutingEngine

def run_experiment():
    print("=== Schedulability Validation Experiment ===")

    # Switches
    s1 = Switch(1, "S1")
    s2 = Switch(2, "S2")
    s3 = Switch(3, "S3")

    of_db.add_switch(1, s1)
    of_db.add_switch(2, s2)
    of_db.add_switch(3, s3)

    # Links
    l1 = Link("1", "2", 1, bw_capacity=100)
    l2 = Link("2", "3", 1, bw_capacity=100)

    of_db.add_link("1", "2", 1, l1)
    of_db.add_link("2", "3", 1, l2)

    # Flow
    flow = RTAttributes(
        ft_i="topic/test",
        qi=1,
        ci=2.0,
        pi=10,
        ti=20.0,
        di=15.0,
        bwi=5.0
    )

    flow.src_ip = "1"
    flow.dst_ips = ["3"]

    re = RoutingEngine(of_db)
    flow.route_links = re.compute_multicast_tree(flow.src_ip, flow.dst_ips)

    wcrt = TrajectoryApproach.calculate_wcrt(flow, [flow])
    print(f"WCRT = {wcrt:.3f} ms | Deadline = {flow.di} ms")

    print("Schedulable:", "YES" if wcrt <= flow.di else "NO")


if __name__ == "__main__":
    run_experiment()
