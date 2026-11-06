# Testprotokoll / Lab Validation

Dieses Protokoll unterscheidet **beobachtete Deploy-Ergebnisse** von **noch nicht durchgeführten Routing-Tests**. Ein laufender Container beweist keine funktionsfähige Routing-Nachbarschaft.

## Bisher nachgewiesener Deployment-Stand

| Feld | Beobachtung |
|---|---|
| Datum | 06.11.2026 |
| Host | Windows 10 (Build 19045.6466), Containerlab-WSL |
| Containerlab | 0.82.0 |
| Docker Server | 27.5.1 |
| FRRouting-Image | `quay.io/frrouting/frr:containerlab-10.7.1` |
| Linux-Clients | `alpine:3.20` |
| Deployment | `sudo containerlab deploy -t topology.clab.yml` erfolgreich abgeschlossen |
| Container | 8/8 als `running` angezeigt (6 FRR-Router, 2 Linux-Hosts) |
| Nachweis | Konsolenausgabe des lokalen Deployments vom 06.11.2026; noch kein Log/Screenshot im Repository veröffentlicht |

**Offen:** OSPF-Konvergenz, BGP-Sessions, ICMP-Erreichbarkeit und WAN-Failover sind durch das Deployment allein **nicht bestätigt**.

## Routing- und Failover-Tests

| Test | Sollzustand | Ist-Zustand |
|---|---|---|
| Statische Konfigurationsprüfung (`make lint`) | Tests und Bash-Syntax erfolgreich | Noch nicht lokal dokumentiert; GitHub Actions separat prüfen |
| Core OSPF Neighbors | Edge A und B = Full | Nicht geprüft |
| Core Default Route | OSPF E1 via Edge A | Nicht geprüft |
| eBGP Sessions | Established | Nicht geprüft |
| Transit Plant-Prefix | `10.70.10.0/24` vorhanden | Nicht geprüft |
| ICMP Plant → Service | Erreichbar | Nicht geprüft |
| ICMP Service → Plant | Erreichbar | Nicht geprüft |
| Edge-A-Uplink-Ausfall | Core wählt Edge B | Nicht geprüft |
| Wiederherstellung | Core wählt erneut Edge A | Nicht geprüft |

## Reproduzierbare Befehle

Im lokalen Verzeichnis `~/industrial-ospf-bgp-lab` ausführen:

```bash
# Zuerst die unverändernden Tests
bash scripts/verify.sh

# Danach den Uplink-Ausfall und die Wiederherstellung testen
bash scripts/failover.sh
```

Für ein vollständiges Testprotokoll inklusive Exit-Code:

```bash
mkdir -p evidence
set -o pipefail
bash scripts/verify.sh 2>&1 | tee evidence/verify.txt
printf 'verify_exit=%s\n' "${PIPESTATUS[0]}" | tee -a evidence/verify.txt

# Nur nach erfolgreicher Verifikation:
bash scripts/failover.sh 2>&1 | tee evidence/failover.txt
printf 'failover_exit=%s\n' "${PIPESTATUS[0]}" | tee -a evidence/failover.txt
```

**Hinweis:** Der Failover-Test setzt temporär `edge-a:eth3` herunter und versucht, es anschließend automatisch wieder hochzufahren. Nicht in einer produktiven Umgebung ausführen.

## Für die Veröffentlichung

1. Ausgaben manuell prüfen: stimmen Nachbarschaften, Routen, Erreichbarkeit und Restore?
2. Echte Ergebnisse, Abweichungen und Troubleshooting-Schritte hier dokumentieren.
3. Nur bereinigte Testlogs/Screenshots ohne Zugangsdaten, Tokens oder Firmeninformationen hochladen.
4. Kein „Passed“ eintragen, solange der jeweilige Test nicht tatsächlich bestanden wurde.
