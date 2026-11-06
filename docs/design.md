# Network Design Decisions

## Problem statement

A small simulated industrial production network (`10.70.10.0/24`) must reach an external service (`198.51.100.10`). Two WAN connections provide redundancy. Failure of the preferred uplink should not leave the service permanently unreachable.

## Separation of routing domains

- **OSPF Area 0** interconnects the core and both edge routers. The production LAN is advertised as a passive OSPF interface, so no OSPF Hello packets are sent to the client.
- **eBGP** connects Edge A to ISP A and Edge B to ISP B. Each ISP connects to a simulated transit AS.
- Edge routers accept **only `0.0.0.0/0`** from the ISP. With a learned default route, `default-information originate` advertises an OSPF E1 default internally. The configuration deliberately omits `always`: an edge router should stop advertising a usable exit when its upstream default route disappears.
- ISP routers originate a default route only if the external service prefix has been learned from the transit AS (`default-originate route-map HAS-SERVICE`). This avoids treating a failed upstream service as a viable exit in the lab.
- The enterprise AS advertises **only `10.70.10.0/24`** to its upstream neighbors. Broad `redistribute ospf` is intentionally avoided.
- The transit AS prefers the return path through ISP A using BGP local preference `200`, rather than ISP B with `150`. This preference applies within the simulated transit AS.

## Path selection

**Normal state:** The core's OSPF link cost to Edge A is `10`; the cost to Edge B is `30`. Both edge routers originate the same OSPF external type-1 default metric. The core is expected to prefer Edge A. Return traffic is evaluated separately using BGP local preference in the transit AS.

**Failure state:** Bringing down `edge-a:eth3` interrupts Edge A's eBGP session. After the BGP default is withdrawn, Edge A should stop originating the OSPF default; the core should then select Edge B. After the link is restored and routing converges, Edge A should become preferred again.

**Convergence:** BGP and OSPF do not converge instantly. The verification scripts wait for changes in control-plane state; no guaranteed failover time is claimed.

## Scope

This lab covers IPv4, OSPF, eBGP, prefix filtering, and redundancy. It does **not** include a production firewall, Kubernetes, or BFD. Those topics would require separate designs and independent tests. Both Linux clients use a default route to their local router.

## Limitations

- No real PLCs, industrial controllers, OT operations, or physical industrial hardware.
- No live Internet service or production-ready security controls.
- No validated latency, throughput, or high-availability service-level guarantee.
- Prefix filtering limits route advertisements, but is not a substitute for a full ISP-edge or Zero Trust security architecture.
