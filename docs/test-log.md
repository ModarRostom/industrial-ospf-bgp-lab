# Testprotokoll

> Dieses Protokoll wird **erst nach eigener Durchführung** ausgefüllt. Keine Ergebnisse aus der Konfiguration ableiten und als gemessen ausgeben.

| Feld | Wert |
|---|---|
| Datum / Umgebung | noch nicht ausgefüllt |
| Docker / Containerlab Version | noch nicht ermittelt |
| FRRouting Image | `quay.io/frrouting/frr:containerlab-10.7.1` (konfiguriert) |
| Ergebnis `make lint` | offen |
| Ergebnis `make verify` | offen |
| Ergebnis `make failover` | offen |

## Sollzustand

| Test | Erwartung | Ist / Beleg |
|---|---|---|
| Core OSPF Neighbor | Edge A und B = Full | offen |
| Core Default Route | OSPF E1 via Edge A | offen |
| BGP Sessions | Peerings Established | offen |
| Transit Plant-Prefix | `10.70.10.0/24` via ISP A | offen |
| ICMP | Plant -> Service erreichbar | offen |
| Edge-A-WAN-Ausfall | Core schwenkt via Edge B | offen |
| Nach Wiederherstellung | Core nutzt wieder Edge A | offen |

## Belegbefehle

```bash
make verify
make failover
# Optional: Live-Ausgaben in einer Datei sichern
mkdir -p evidence
bash scripts/verify.sh | tee evidence/verify.txt
bash scripts/failover.sh | tee evidence/failover.txt
```

## Beobachtungen / Korrekturen

- [ ] Fehler/Unterschiede festhalten und korrigieren.
- [ ] Screenshots oder CLI-Ausgaben vor dem Veröffentlichen auf sensible Daten prüfen.
- [ ] Ergebnisse erst nach einem vollständig reproduzierten Lauf als bestanden markieren.
