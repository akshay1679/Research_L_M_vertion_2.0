# sdn_controller/ryu_mrt_app.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response

from common.of_db import OFDB
from common.rt_attributes import RTAttributes
from schedulability.analysis import AdmissionControl
from sdn_controller.routing import RoutingEngine

import json


class MRTController(app_manager.RyuApp):
    """
    MRT-MQTT SDN Controller
    Paper Fig. 9 & Fig. 10
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.of_db = OFDB()
        self.routing = RoutingEngine(self.of_db)

        wsgi = kwargs['wsgi']
        wsgi.register(MRTControllerREST, {'controller': self})

    # ---------------------------------------
    # Flow Registration (ORT-NM → Controller)
    # ---------------------------------------
    def register_flow(self, payload):
        rt = RTAttributes(**payload["rt_attributes"])
        rt.src_ip = payload["src_ip"]

        existing = list(self.of_db.flows.values())

        if not AdmissionControl.check_admissibility(rt, existing):
            return False

        self.of_db.add_flow(payload["topic"], rt)

        # Routing after admission
        rt.route_links = self.routing.compute_multicast_tree(
            rt.src_ip,
            rt.dst_ips
        )

        return True

    # ---------------------------------------
    # Subscriber Registration
    # ---------------------------------------
    def register_subscriber(self, payload):
        self.of_db.add_subscriber(
            payload["topic"],
            payload["subscriber_ip"]
        )

        flow = self.of_db.flows.get(payload["topic"])
        if not flow:
            return

        flow.route_links = self.routing.compute_multicast_tree(
            flow.src_ip,
            flow.dst_ips
        )

    # ---------------------------------------
    # Switch Features
    # ---------------------------------------
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                   ofproto.OFPCML_NO_BUFFER)
        ]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions
        )]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            match=match,
            instructions=inst
        )

        datapath.send_msg(mod)


# ---------------------------------------
# REST API (Paper Control Plane)
# ---------------------------------------
class MRTControllerREST(ControllerBase):

    def __init__(self, req, link, data, **config):
        super().__init__(req, link, data, **config)
        self.ctrl = data['controller']

    @route('mrt', '/mrt/register_flow', methods=['POST'])
    def register_flow(self, req, **kwargs):
        payload = json.loads(req.body)
        ok = self.ctrl.register_flow(payload)
        return self._response(ok)

    @route('mrt', '/mrt/register_subscriber', methods=['POST'])
    def register_subscriber(self, req, **kwargs):
        payload = json.loads(req.body)
        self.ctrl.register_subscriber(payload)
        return self._response(True)

    def _response(self, ok):
        body = json.dumps({"status": "ACCEPT" if ok else "REJECT"})
        return Response(
            content_type='application/json',
            body=body
        )
