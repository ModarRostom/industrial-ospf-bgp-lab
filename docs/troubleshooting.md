# Troubleshooting

Kurze Checks, falls der Lab-Aufbau nicht wie erwartet konvergiert.

## Container starten nicht

```bash
sudo containerlab inspect -t topology.clab.yml
docker ps -a --filter name=clab-industrial-routing
```

Prüfen, ob das FRR-Image gepullt werden konnte und ob die eingesetzte Containerlab-Version das native `frr`-Kind unterstützt. Das Verwaltungsnetz liegt auf `eth0`; die im Netzplan genannten Links beginnen bei `eth1`.

## OSPF-Nachbar fehlt

```bash
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf interface'
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf neighbor'
docker exec clab-industrial-routing-edge-a ip addr show eth1
```

Interfaces, Subnetze, Area, Passive-Interface und Netztyp auf beiden Seiten vergleichen. Die Client-Seite am Core ist absichtlich passiv.

## eBGP bleibt auf Idle / Active

```bash
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp summary'
docker exec clab-industrial-routing-isp-a vtysh -c 'show bgp summary'
docker exec clab-industrial-routing-edge-a vtysh -c 'show running-config'
```

IP-Adresse des Peers und remote-as prüfen. Auch prüfen, ob die Router auf dem Link per ICMP erreichbar sind. Ein Established-Peering allein beweist noch nicht, dass die gewünschten Routen gefiltert und übertragen werden.

## BGP läuft, aber keine Default-Route am Core

```bash
docker exec clab-industrial-routing-isp-a vtysh -c 'show ip route 198.51.100.0/24'
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp ipv4 unicast 0.0.0.0/0'
docker exec clab-industrial-routing-core vtysh -c 'show ip route 0.0.0.0/0'
```

ISP A gibt den Default nur weiter, wenn die Service-Route vom Transit gelernt wurde. Edge A gibt den OSPF-Default nur weiter, wenn es selbst einen Default gelernt hat. Fehlt eine dieser Stufen, zuerst die Route an dieser Stufe überprüfen.

## Ping geht nur in eine Richtung

Prüfen, ob das Plant-Netz auf `transit` via BGP gelernt wurde. Danach auf den Clients prüfen, ob ihre Default-Route Richtung Core bzw. Transit zeigt. Bei der Fehlersuche zuerst die Routing-Tabelle, dann den tatsächlichen ICMP-Pfad kontrollieren.

```bash
docker exec clab-industrial-routing-transit vtysh -c 'show ip route 10.70.10.0/24'
docker exec clab-industrial-routing-plant ip route
docker exec clab-industrial-routing-service ip route
```

Alle Änderungen in `docs/test-log.md` dokumentieren und Konfigurationsdateien entsprechend korrigieren. Keine Live-Ausgaben vortäuschen.
