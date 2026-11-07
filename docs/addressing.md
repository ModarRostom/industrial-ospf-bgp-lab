# IP Addressing Plan

All addresses are used in this isolated lab. The simulated "Internet" side consists only of additional autonomous systems (ASes) and is **not connected to the real Internet**. `198.51.100.0/24` is the documentation-only TEST-NET-2 range.

| Link | Side A | Side B | Routing |
|---|---|---|---|
| Core to Edge A | core eth1 `10.0.0.1/30` | edge-a eth1 `10.0.0.2/30` | OSPF Area 0 |
| Core to Edge B | core eth2 `10.0.0.5/30` | edge-b eth1 `10.0.0.6/30` | OSPF Area 0 |
| Edge A to Edge B | edge-a eth2 `10.0.0.9/30` | edge-b eth2 `10.0.0.10/30` | OSPF Area 0 |
| Plant LAN | core eth3 `10.70.10.1/24` | plant eth1 `10.70.10.10/24` | Passive OSPF interface |
| Edge A to ISP A | edge-a eth3 `172.16.0.1/30` | isp-a eth1 `172.16.0.2/30` | eBGP (AS 65010, AS 65110) |
| Edge B to ISP B | edge-b eth3 `172.16.0.5/30` | isp-b eth1 `172.16.0.6/30` | eBGP (AS 65010, AS 65120) |
| ISP A to Transit | isp-a eth2 `172.16.0.9/30` | transit eth1 `172.16.0.10/30` | eBGP (AS 65110, AS 65200) |
| ISP B to Transit | isp-b eth2 `172.16.0.13/30` | transit eth2 `172.16.0.14/30` | eBGP (AS 65120, AS 65200) |
| Service LAN | transit eth3 `198.51.100.1/24` | service eth1 `198.51.100.10/24` | Directly connected |

**Management network:** assigned automatically by Containerlab on `eth0`; it is separate from the data-plane routing design.
