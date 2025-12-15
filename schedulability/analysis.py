# schedulability/analysis.py

import math
from typing import List, Dict


# -------------------------------------------------
# Utility: Interfering Flow Identification
# -------------------------------------------------
class SchedulabilityUtils:

    @staticmethod
    def get_interfering_flows(subject_flow, all_flows, link):
        """
        Paper definition:
        Interfering flows share the same link and have
        priority >= subject flow priority
        """
        interfering = []
        for flow in all_flows:
            if flow == subject_flow:
                continue
            if link in flow.route_links and flow.pi >= subject_flow.pi:
                interfering.append(flow)
        return interfering


# -------------------------------------------------
# Holistic Analysis (HA) – Paper Eq. (9)
# -------------------------------------------------
class HolisticApproach:

    @staticmethod
    def calculate_wcrt(flow, all_flows):
        """
        Implements Equation (9) of the paper.

        R_i = C_i + B_i + Sum(interference) + Sum(link delays) + J_i
        """

        # -----------------------------
        # Blocking Time B_i
        # -----------------------------
        blocking = max(
            [f.ci for f in all_flows if f.pi < flow.pi],
            default=0.0
        )

        # -----------------------------
        # Static Delay Components
        # -----------------------------
        static_delay = 0.0
        for link in flow.route_links:
            static_delay += (
                link.prop_delay +
                link.switch_delay +
                link.proc_delay +
                link.queuing_delay
            )

        # -----------------------------
        # Fixed-Point Iteration
        # -----------------------------
        prev_w = 0.0
        w = flow.ci + blocking + static_delay

        for _ in range(100):  # bounded convergence
            if abs(w - prev_w) < 1e-6:
                break

            prev_w = w
            interference = 0.0

            for link in flow.route_links:
                interfering_flows = SchedulabilityUtils.get_interfering_flows(
                    flow, all_flows, link
                )

                for f_j in interfering_flows:
                    interference += math.ceil(
                        (prev_w + f_j.measured_jitter) / f_j.ti
                    ) * f_j.ci

            w = (
                flow.ci +
                blocking +
                static_delay +
                interference +
                flow.measured_jitter +
                flow.processing_delay
            )

            if w > flow.di:
                break

        return w


# -------------------------------------------------
# Trajectory Analysis (TA) – Paper Section IV-B
# -------------------------------------------------
class TrajectoryApproach:

    @staticmethod
    def calculate_branch_wcrt(flow, branch_links, all_flows):
        """
        Computes WCRT for a single multicast branch
        """
        w = 0.0

        for link in branch_links:
            # Transmission + static delay
            w += (
                flow.ci +
                link.propagation_delay +
                link.switching_delay +
                link.processing_delay +
                link.queuing_delay
            )

            # Interference at this hop
            interfering_flows = SchedulabilityUtils.get_interfering_flows(
                flow, all_flows, link
            )

            for f_j in interfering_flows:
                w += math.ceil(w / f_j.ti) * f_j.ci

            if w > flow.di:
                return w

        return w + flow.broker_processing_delay + flow.measured_jitter

    @staticmethod
    def calculate_wcrt(flow, all_flows):
        """
        For multicast:
        WCRT = max over all destination branches
        """
        branch_wcrts = []

        for dst in flow.dst_ips:
            branch_links = [
                l for l in flow.route_links
                if l.dst == dst or l.src == flow.src_ip
            ]

            wcrt = TrajectoryApproach.calculate_branch_wcrt(
                flow, branch_links, all_flows
            )
            branch_wcrts.append(wcrt)

        return max(branch_wcrts, default=0.0)


# -------------------------------------------------
# Admission Control – Paper Section VI
# -------------------------------------------------
class AdmissionControl:

    @staticmethod
    def check_admissibility(new_flow, existing_flows):
        """
        Admission control using Trajectory Analysis (TA)
        """

        candidate_set = existing_flows + [new_flow]

        # Check new flow
        wcrt_new = TrajectoryApproach.calculate_wcrt(
            new_flow, candidate_set
        )

        if wcrt_new > new_flow.di:
            return False

        # Check existing flows not violated
        for flow in existing_flows:
            wcrt = TrajectoryApproach.calculate_wcrt(
                flow, candidate_set
            )
            if wcrt > flow.di:
                return False

        return True
