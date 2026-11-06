# Industrial Routing Lab: OSPF + BGP

Reproduzierbares Routing-Lab für ein simuliertes Produktionsnetz mit zwei unabhängigen WAN-Pfaden. Neben funktionierenden Routing-Nachbarschaften stehen hier kontrollierte Routenankündigungen, nachvollziehbare Pfadwahl und ein reproduzierbarer Uplink-Ausfall im Mittelpunkt.

![Lab-Topologie](docs/topology.png)

**Setup:** Containerlab, FRRouting 10.7.1, Alpine Linux. Die FRR-Konfigurationen liegen pro Router unter `configs/` und werden beim Deployment geladen.

## Was ist im Lab enthalten?

- OSPF Area 0 zwischen Core, Edge A und Edge B
- Zwei eBGP-Uplinks und simuliertes Transit-AS (kein echter Internetzugang)
- Explizite Prefix-Listen und konditionale Default-Ankündigung durch die ISPs
- OSPF-E1-Default aus einem gelernten BGP-Default, ohne `always`
- Geplante Pfadwahl über OSPF-Cost und BGP Local Preference
- Ausfalltest: Edge-A-Uplink deaktivieren, alternativen Pfad prüfen, wiederherstellen

## Voraussetzungen

- Linux-Host oder Linux-VM mit Docker und Containerlab (mit `frr`-Kind, z. B. Containerlab 0.80+)
- Root-/sudo-Rechte für das Deployment und Zugriffsrechte auf Docker für die Skripte
- Mindestens einige GB freier RAM empfohlen (je nach Host); Internetzugang zum ersten Image-Pull
- Optional: Python 3 + PyYAML für statische Tests, Graphviz zum Neuzeichnen der Grafik

Containerlab-Befehle werden auf dem Linux-Host ausgeführt. **Getestete Deployment-Umgebung:** Windows 10 (Build 19045.6466) mit Containerlab-WSL 0.82.0 und Docker 27.5.1. Acht Container wurden am 06.11.2026 als `running` angezeigt. Die Routing-Funktion wurde dabei noch nicht bestätigt.

## Schnellstart

```bash
# Aus dem Repository-Verzeichnis
sudo containerlab deploy -t topology.clab.yml

# Routing und Konnektivität prüfen
bash scripts/verify.sh

# Den primären WAN-Link kurz deaktivieren und wiederherstellen
bash scripts/failover.sh

# Lab entfernen
sudo containerlab destroy -t topology.clab.yml --cleanup
```

Die Skripte erwarten Zugriff auf `docker` ohne `sudo`. Wenn dein Docker-Setup das nicht erlaubt, die Skripte mit den nötigen Rechten starten. **Nicht im Produktivnetz ausführen.**

## Manuell nachsehen

```bash
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf neighbor'
docker exec clab-industrial-routing-core vtysh -c 'show ip route 0.0.0.0/0'
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp ipv4 unicast summary'
docker exec clab-industrial-routing-transit vtysh -c 'show bgp ipv4 unicast 10.70.10.0/24'
docker exec clab-industrial-routing-plant ping -c 3 198.51.100.10
```

## Struktur

```text
.
├── topology.clab.yml       # Nodes, Links und Endgeräte
├── configs/                # FRR-Konfiguration aller sechs Router
├── scripts/                # Smoke-Test und WAN-Failover
├── tests/                  # Statische Konsistenz-Checks
├── docs/
│   ├── topology.png        # Netzplan
│   ├── addressing.md       # Interfaces, IPs und ASNs
│   ├── design.md           # Routing-Entscheidungen / Grenzen
│   └── test-log.md         # Vorlage für eigene Messergebnisse
└── .github/workflows/      # Statische Tests in GitHub Actions
```

## Warum diese Route Policies?

Hier wird bewusst **nicht** pauschal OSPF nach BGP redistribuiert: Die Edge-Router exportieren nur `10.70.10.0/24`. Von den Providern lassen sie ausschließlich `0.0.0.0/0` herein. Das begrenzt unbeabsichtigte Ankündigungen. Die internen Router kennen den externen Zielbereich nur über die Default Route, nicht über das ganze BGP-Routing.

Die genaue Adressierung und die Designgrenzen stehen in [Adressplan](docs/addressing.md) und [Design-Notizen](docs/design.md). Bei Problemen hilft [Troubleshooting](docs/troubleshooting.md).

## Teststatus

**Deployment bestätigt (06.11.2026):** Unter Windows 10 / Containerlab-WSL wurden die sechs FRRouting-Router und zwei Alpine-Endgeräte erfolgreich gestartet (8/8 Container `running`). **Die OSPF-/BGP-Nachbarschaften, End-to-End-Konnektivität und der WAN-Failover sind noch nicht durch veröffentlichte Testergebnisse belegt.**\n\nStatische Konfigurations- und Syntaxprüfungen laufen über [GitHub Actions](.github/workflows/static-checks.yml) bei Pushes und Pull Requests; diese ersetzen keine echten Routing-Tests. Der aktuelle Teststand und die nachzuholenden Messungen stehen in [test-log.md](docs/test-log.md).

## Verwendete Dokumentation

- [Containerlab: FRRouting kind](https://containerlab.dev/manual/kinds/frr/)
- [FRRouting: OSPF](https://docs.frrouting.org/en/stable-10.7/ospfd.html)
- [FRRouting: BGP](https://docs.frrouting.org/en/stable-10.7/bgp.html)

*Nur für Lern- und Demonstrationszwecke in einer isolierten Laborumgebung.*
