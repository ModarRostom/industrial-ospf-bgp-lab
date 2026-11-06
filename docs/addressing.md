# Adressplan

Alle Adressen sind für dieses isolierte Lab reserviert. Die „Internet“-Seite simuliert ausschließlich weitere AS und ist **keine** Anbindung ans echte Internet. `198.51.100.0/24` ist ein Dokumentationsnetz (TEST-NET-2).

| Verbindung | Seite A | Seite B | Routing |
|---|---|---|---|
| Core - Edge A | core eth1 `10.0.0.1/30` | edge-a eth1 `10.0.0.2/30` | OSPF 0 |
| Core - Edge B | core eth2 `10.0.0.5/30` | edge-b eth1 `10.0.0.6/30` | OSPF 0 |
| Edge A - Edge B | edge-a eth2 `10.0.0.9/30` | edge-b eth2 `10.0.0.10/30` | OSPF 0 |
| Plant LAN | core eth3 `10.70.10.1/24` | plant eth1 `10.70.10.10/24` | OSPF passive |
| Edge A - ISP A | edge-a eth3 `172.16.0.1/30` | isp-a eth1 `172.16.0.2/30` | eBGP 65010/65110 |
| Edge B - ISP B | edge-b eth3 `172.16.0.5/30` | isp-b eth1 `172.16.0.6/30` | eBGP 65010/65120 |
| ISP A - Transit | isp-a eth2 `172.16.0.9/30` | transit eth1 `172.16.0.10/30` | eBGP 65110/65200 |
| ISP B - Transit | isp-b eth2 `172.16.0.13/30` | transit eth2 `172.16.0.14/30` | eBGP 65120/65200 |
| Service LAN | transit eth3 `198.51.100.1/24` | service eth1 `198.51.100.10/24` | locally connected |

Management-Netz: automatisch von Containerlab (eth0); kein Bestandteil des Routing-Konzepts.
