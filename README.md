# Industrial Routing Lab: OSPF + BGP

[![Live routing lab validation](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/workflows/live-routing.yml/badge.svg)](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/workflows/live-routing.yml)
[![Static configuration checks](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/workflows/static-checks.yml/badge.svg)](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/workflows/static-checks.yml)

A reproducible routing lab simulating a small industrial network with two independent WAN paths. The focus is on OSPF and eBGP adjacencies, controlled route advertisements, deterministic path selection, and recovery from a primary uplink failure.

![Network topology](docs/topology.png)

**Stack:** Containerlab 0.82.0, FRRouting 10.7.1, Alpine Linux, Docker. Router configurations are stored under `configs/`.

## Architecture and objectives

- OSPF Area 0 between Core, Edge A, and Edge B
- Two independent eBGP uplinks to simulated ISPs and a transit AS (no real Internet access)
- Explicit prefix lists controlling inbound and outbound advertisements
- Conditional ISP default-route advertisement when the external service prefix is available
- OSPF external type-1 default-route origination on the edge routers only when a default route is available
- Primary and backup path selection using OSPF cost and BGP local preference
- WAN failover test: disable Edge A's ISP uplink, inspect the backup path, and restore the original link

See [network addressing](docs/addressing.md) and [design decisions](docs/design.md) for details.

For a detailed diagnosis of the FRRouting startup issue, see the [troubleshooting case study](docs/frr-startup-troubleshooting-case-study.md). It covers the initial symptoms, configuration loading, CI test corrections, and final verification.

## Prerequisites

- Linux, or Windows 10/11 with Containerlab-WSL, Docker, and Containerlab
- Permission to run Containerlab and access the Docker engine
- Enough free memory to run eight containers
- Internet access for the initial image downloads
- Optional: Python 3 + PyYAML for static tests, Graphviz to regenerate the topology diagram

**Observed environment:** Windows 10 Build 19045.6466, Containerlab-WSL 0.82.0, Docker 27.5.1. All eight containers started successfully on November 6, 2026. Container startup alone does not prove working routing.

## Quick start

```bash
# Run from the repository root
sudo containerlab deploy -t topology.clab.yml

# Load the integrated FRR configuration after the daemons become ready.
bash scripts/bootstrap.sh

# Verify OSPF/BGP and reachability before testing failures.
bash scripts/verify.sh

# Disable and restore the primary ISP uplink in this isolated lab.
bash scripts/failover.sh

# Tear down the lab when finished.
sudo containerlab destroy -t topology.clab.yml --cleanup
```

Alternatively, run `make deploy` to deploy and bootstrap, `make verify` to check connectivity, and `make failover` to test recovery.

**Important:** The scripts expect Docker access without `sudo`; adapt permissions to your environment. Run this lab only in an isolated test environment, never on production routers.

## Manual verification

```bash
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf neighbor'
docker exec clab-industrial-routing-core vtysh -c 'show ip route 0.0.0.0/0'
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp ipv4 unicast summary'
docker exec clab-industrial-routing-transit vtysh -c 'show bgp ipv4 unicast 10.70.10.0/24'
docker exec clab-industrial-routing-plant ping -c 3 198.51.100.10
```

## Repository structure

| Path | Contents |
|---|---|
| `topology.clab.yml` | Containerlab nodes, interfaces, and links |
| `configs/` | FRRouting configuration for six routers |
| `scripts/` | Configuration bootstrap, routing checks, and failover test |
| `tests/` | Static configuration checks |
| `docs/addressing.md` | IP addressing and AS numbers |
| `docs/design.md` | Routing design decisions and limitations |
| `docs/topology.png` | Network diagram |
| `docs/troubleshooting.md` | Operational troubleshooting commands |
| `docs/frr-startup-troubleshooting-case-study.md` | Diagnosed startup issue and verified resolution |
| `docs/test-log.md` | Test observations and evidence |
| `docs/evidence/` | Screenshots from the live CI validation |
| `.github/workflows/` | Static and live integration tests |

## Route-policy rationale

The edge routers do **not** redistribute the entire OSPF domain into BGP. They advertise only `10.70.10.0/24` toward the ISPs and accept only `0.0.0.0/0` from them. This avoids unintended prefix leaks and keeps the core routing table focused on internal routes and a default route.

The transit AS uses BGP local preference to favor the return path through ISP A. Outbound path selection within the plant is based on OSPF metrics. These are separate routing decisions.

## Verified results

**Automated live validation passed on November 6, 2026**, on a GitHub-hosted Ubuntu runner. The [successful live workflow run](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707) demonstrates:

- OSPF: both core adjacencies reached the `Full` state.
- OSPF: the core installed its default route via Edge A.
- BGP: the transit router installed the production prefix `10.70.10.0/24`.
- Reachability: ICMP succeeded from Plant to Service and from Service to Plant.
- WAN failover: after disabling `edge-a:eth3`, the core selected Edge B, and Plant-to-Service connectivity remained available (3/3 ping replies).
- Recovery: after restoring `edge-a:eth3`, the core selected the preferred path via Edge A again.

**Static configuration checks also passed:** [successful static workflow run](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117662).

**Local environment:** a separate deployment on Windows 10 / Containerlab-WSL reported all eight containers running. The complete live verification and failover results above were measured in GitHub Actions on Linux, **not** on the user's Windows/WSL machine. No production-grade reliability, SLA, or guaranteed convergence time is claimed.

For commands, observed results, and limitations, see the [test log](docs/test-log.md).

## Validation evidence

The screenshots were captured from the [successful Containerlab integration test on November 6, 2026](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707). They document the routing and failover results recorded by GitHub Actions.

### OSPF, BGP and end-to-end connectivity

The verification log shows two OSPF adjacencies in `Full` state, an installed default route via Edge A, BGP prefix propagation, and successful bidirectional ICMP checks.

[![OSPF and BGP routing verification evidence](docs/evidence/01-routing-verification.png)](docs/evidence/01-routing-verification.png)

[Open full-resolution routing verification screenshot](docs/evidence/01-routing-verification.png).

### WAN failover and recovery

The failover log shows the primary path via `eth1`, switching to the backup path via `eth2` after disabling Edge A's ISP interface, three successful service pings during the failover test, and restoration of `eth1`.

[![WAN failover and restoration evidence](docs/evidence/02-wan-failover.png)](docs/evidence/02-wan-failover.png)

[Open full-resolution WAN failover screenshot](docs/evidence/02-wan-failover.png). Additional evidence is available in the [evidence directory](docs/evidence/).

**Evidence scope:** These screenshots were obtained from a GitHub-hosted Ubuntu CI run. They are not proof of successful failover on a physical production network or on the local Windows/WSL system.

## References

- [Containerlab: FRRouting kind](https://containerlab.dev/manual/kinds/frr/)
- [FRRouting: OSPF](https://docs.frrouting.org/en/stable-10.7/ospfd.html)
- [FRRouting: BGP](https://docs.frrouting.org/en/stable-10.7/bgp.html)

*Educational demonstration in an isolated simulated environment. No real industrial control equipment or live Internet connectivity is used.*
