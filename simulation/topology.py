from mininet.topo import Topo

class MRTTopo(Topo):
    """
    Multi-edge evaluation topology.
    """

    def build(self):
        core = self.addSwitch("s100")

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")

        self.addLink(s1, core, bw=100, delay="1ms")
        self.addLink(s2, core, bw=100, delay="1ms")
        self.addLink(s3, core, bw=100, delay="1ms")

        h1 = self.addHost("h1", ip="10.0.0.1")
        h2 = self.addHost("h2", ip="10.0.0.2")
        h3 = self.addHost("h3", ip="10.0.0.3")

        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
