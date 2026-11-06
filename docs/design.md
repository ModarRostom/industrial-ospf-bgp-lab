# Design-Entscheidungen

## Problem

Ein kleines Produktionsnetz (`10.70.10.0/24`) soll einen externen Dienst (`198.51.100.10`) erreichen. Zwei WAN-Wege stehen zur Verfügung. Der bevorzugte Zugang darf ausfallen, ohne dass die Verbindung dauerhaft verloren geht.

## Trennung der Routing-Domänen

- **OSPF Area 0** verbindet Core und beide Edge-Router. Das Produktionsnetz wird als passives OSPF-Netz angekündigt, d. h. keine OSPF-Hellos in Richtung Client.
- **eBGP** verbindet Edge A mit ISP A und Edge B mit ISP B. Jeder ISP hängt an einem simulierten Transit-AS.
- Die Edge-Router akzeptieren vom ISP **nur** `0.0.0.0/0`. Diese Route wird anschließend via `default-information originate` als OSPF E1 in das interne Netz gegeben. Das Kommando enthält absichtlich **kein `always`**. Ohne gelernte Default-Route soll kein toter WAN-Ausgang weiter beworben werden.
- Die ISP-Router schicken die Default Route nur dann, wenn die externe Service-Route vom Transit-AS bekannt ist (`default-originate route-map HAS-SERVICE`). Damit wird eine Störung **hinter** dem ISP im Lab nicht als funktionierender Ausgang beworben.
- Das Enterprise-AS kündigt nach außen **nur** `10.70.10.0/24` an. Eine ungefilterte `redistribute ospf`-Konfiguration wäre hier unnötig riskant.
- Das Transit-AS bevorzugt den Rückweg über ISP A durch `local-preference 200` gegenüber ISP B (`150`). Dies gilt ausschließlich innerhalb des simulierten Transit-AS.

## Pfadwahl

Normalfall: Core zu Edge A über OSPF cost 10, zu Edge B cost 30. Beide Default-Routen verwenden denselben OSPF-E1-External-Metric-Wert. Damit soll Edge A bevorzugt werden. Der Rückweg im Transit-AS ist separat per BGP Local Preference festgelegt.

Ausfallfall: Wenn `edge-a:eth3` ausfällt, verliert Edge A den eBGP-Default und zieht die Default-Ankündigung aus OSPF zurück. Der Core sollte anschließend Edge B verwenden. Nach Wiederherstellung sollte der bevorzugte Pfad über Edge A zurückkehren.

**Wichtig:** BGP- und OSPF-Konvergenz erfolgt nicht instantan. Die Testskripte warten auf einen Zustandswechsel, sie behaupten keine garantierte Umschaltzeit.

## Warum dieses Design und nicht mehr?

Das Lab testet bewusst IPv4, OSPF, eBGP, Prefix-Filter und Failover. Es setzt **keine** Produktiv-Firewall, kein Kubernetes und kein BFD voraus. Das wären eigene Projekte, die unabhängig getestet werden sollten. Die Linux-Clients verwenden eine einfache Default Route zum jeweils lokalen Router.

## Grenzen

- Keine echte OT-Steuerung, keine SPS und keine reale Industriehardware.
- Kein Live-Internet, kein produktionsfähiges Sicherheitsdesign.
- Keine Messung von Latenz oder garantierter Hochverfügbarkeit.
- Prefix-Filter zeigen kontrollierte Ankündigungen, ersetzen aber keine vollständige ISP- oder Zero-Trust-Sicherheitsarchitektur.
