# Troubleshooting Guide

Use these checks if the lab fails to converge or the expected route is missing.

For a documented real incident with commands, analysis, corrective actions, failed CI checks, and a successful re-test, see the [FRRouting startup and verification case study](frr-startup-troubleshooting-case-study.md).

## Containers do not start

```bash
sudo containerlab inspect -t topology.clab.yml
docker ps -a --filter name=clab-industrial-routing
```

Confirm that the FRR image was downloaded and the installed Containerlab release supports the native `frr` kind. Management connectivity uses `eth0`; data-plane links start at `eth1`.

## OSPF is not enabled / running configuration is empty

The integrated FRR file may be present in `/etc/frr/frr.conf` but not loaded into the running daemons. Check the container and apply the bootstrap procedure:

```bash
docker exec clab-industrial-routing-core cat /etc/frr/frr.conf
docker exec clab-industrial-routing-core vtysh -c 'show running-config'
bash scripts/bootstrap.sh
```

After bootstrap, the running configuration should contain `router ospf` and the configured interface IP addresses.

## Missing OSPF neighbor

```bash
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf interface'
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf neighbor'
docker exec clab-industrial-routing-edge-a ip addr show eth1
```

Compare peer interface addresses, subnets, OSPF area, passive-interface settings, and network types. The interface toward the plant client is intentionally passive.

## eBGP stays in Idle / Active

```bash
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp summary'
docker exec clab-industrial-routing-isp-a vtysh -c 'show bgp summary'
docker exec clab-industrial-routing-edge-a vtysh -c 'show running-config'
```

Check the peer IP and `remote-as` values. Verify Layer 3 reachability between both peers. An Established session alone does not prove that the intended prefixes are being exchanged.

## eBGP works, but the core has no default route

```bash
docker exec clab-industrial-routing-isp-a vtysh -c 'show ip route 198.51.100.0/24'
docker exec clab-industrial-routing-edge-a vtysh -c 'show bgp ipv4 unicast 0.0.0.0/0'
docker exec clab-industrial-routing-core vtysh -c 'show ip route 0.0.0.0/0'
```

ISP A originates a default only when the external service prefix is available from transit. Edge A originates an OSPF default only when it has learned a default itself. Inspect these dependencies in order.

**FRRouting output detail:** `show ip route 0.0.0.0/0` prints a detailed route entry (for example `Known via "ospf"`), not a compact line beginning with `O>*`. Use `show ip route` for the compact route table.

## Ping succeeds in only one direction

Verify that transit learned the production prefix through BGP. Next, inspect the default routes of both Linux clients. Compare the routing tables before diagnosing the ICMP packet path.

```bash
docker exec clab-industrial-routing-transit vtysh -c 'show ip route 10.70.10.0/24'
docker exec clab-industrial-routing-plant ip route
docker exec clab-industrial-routing-service ip route
```

Document genuine corrections and observations in `docs/test-log.md`. Never fabricate live test output.
