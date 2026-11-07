# Case Study: FRRouting Configuration Not Applied During Lab Startup

**Project:** Industrial Routing Lab — OSPF + BGP  
**Environment:** Containerlab 0.82.0, FRRouting 10.7.1, Docker; local observations on Windows 10 with Containerlab-WSL, followed by automated integration tests on GitHub-hosted Ubuntu  
**Incident category:** Routing control-plane initialization and test automation  
**Status:** Resolved for the documented bootstrap-and-verify workflow; successful OSPF/BGP/ICMP/failover run recorded in CI on November 6, 2026

## Executive summary

The lab initially deployed all eight containers, but the core router returned `% OSPF is not enabled in vrf default`. Investigation showed that the `ospfd` process was running and the expected FRRouting configuration existed on disk, while the **running configuration contained no OSPF configuration**. Loading the configuration with `vtysh -b` activated OSPF on the core, but no neighbors appeared until the peer routers were configured as well.

A subsequent automated run showed that invoking `vtysh -b` too early during Containerlab's node `exec` phase could fail with `Exiting: failed to connect to any daemons.` The project therefore introduced `scripts/bootstrap.sh`, which waits for FRRouting's CLI to become available, loads `/etc/frr/frr.conf` on all six routers, and checks that the OSPF router configuration is present on the core and edge routers.

The remaining failures were in **test assertions rather than missing routes**: `show ip route <prefix>` returns a detailed route entry in this FRRouting version, whereas the original tests expected a compact routing-table line. After correcting the assertions, the live CI checks passed, including a WAN failover and restoration test.

## 1. Symptoms and impact

The first troubleshooting observations were taken from the local Windows/WSL lab:

```text
$ docker exec clab-industrial-routing-core vtysh -c "show ip ospf neighbor"
% OSPF is not enabled in vrf default
```

The core's running configuration showed only basic FRR settings:

```text
frr version 10.7.1_git
frr defaults traditional
hostname core
domainname localdomain
service integrated-vtysh-config
!
end
```

Yet the OSPF daemon itself was enabled and running:

```text
$ docker exec clab-industrial-routing-core sh -c "grep '^ospfd=' /etc/frr/daemons; pgrep -a ospfd"
ospfd=yes
71 /usr/lib/frr/ospfd
```

**Impact:** Container health (`running`) was initially misleading as a measure of network readiness. OSPF adjacency and route propagation could not be assumed from a successful deployment alone.

## 2. Diagnosis

We separated three questions instead of assuming they had the same answer:

| Check | Observation | Interpretation |
|---|---|---|
| Is the container running? | Yes | Container creation succeeded, but this is not proof of protocol readiness |
| Is `ospfd` running? | Yes | The routing daemon started |
| Is the intended configuration active? | No | The OSPF configuration was not yet applied to the running daemons |
| Is the configuration present on disk? | Yes | The saved `/etc/frr/frr.conf` contained interfaces and `router ospf` |
| Does manual configuration loading help? | Yes | `vtysh -b` applied the core configuration; peer configuration was still necessary for adjacency |

Useful diagnostic commands:

```bash
docker exec clab-industrial-routing-core vtysh -c 'show running-config'
docker exec clab-industrial-routing-core cat /etc/frr/frr.conf
docker exec clab-industrial-routing-core sh -c "grep '^ospfd=' /etc/frr/daemons; pgrep -a ospfd"
docker exec clab-industrial-routing-core vtysh -c 'show ip ospf neighbor'
```

An explicit one-time load on the core:

```bash
docker exec clab-industrial-routing-core vtysh -b
```

This made OSPF available but **did not immediately establish neighbors**, because the adjacent edge routers also needed their configuration to be loaded.

### Startup timing evidence

Containerlab attempted `vtysh -b` as a node `exec` command during deployment. A [failed integration run](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42269571427) logged:

```text
Failed to execute command command="vtysh -b" node=edge-b rc=1
Exiting: failed to connect to any daemons.
```

This directly demonstrates an initialization-order/race problem for that early invocation. It does **not** establish that startup timing was the only possible cause of the original Windows/WSL observation.

## 3. Corrective action: explicit FRR bootstrap

The validated solution is [`scripts/bootstrap.sh`](../scripts/bootstrap.sh):

1. Iterate over all six FRRouting containers: `core`, `edge-a`, `edge-b`, `isp-a`, `isp-b`, and `transit`.
2. Poll `vtysh -c 'show version'` until the CLI is available, with a bounded number of attempts.
3. Apply the integrated configuration by running `vtysh -b` **after** CLI readiness.
4. Check that `router ospf` appears in `show running-config` on core and both edge routers.
5. Stop with a nonzero exit code if a required step fails.

The supported startup sequence is:

```bash
sudo containerlab deploy -t topology.clab.yml
bash scripts/bootstrap.sh
bash scripts/verify.sh
bash scripts/failover.sh
```

The `make deploy` target also deploys and invokes the bootstrap script. The [live GitHub Actions workflow](../.github/workflows/live-routing.yml) runs the bootstrap explicitly before checking routing behavior.

**Residual limitation:** Early `vtysh -b` commands defined in the topology can still produce transient startup errors if daemons are not ready. The separate readiness-checked bootstrap is the verified path; the startup race is not presented as eliminated from those early commands.

## 4. Secondary issue: false negatives in route verification

Two integration tests initially timed out despite routes being installed.

**OSPF default route:** The initial assertion tried to find an `O`/`E1` compact route marker in this command:

```bash
vtysh -c 'show ip route 0.0.0.0/0'
```

But FRRouting returned a **detailed** entry with `Known via "ospf"`, metric 15, and next hop `10.0.0.2`. The test failed even though the OSPF default route existed. A [failed CI run](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42269571427) captured the initial false negative, and later diagnostic logs confirmed the installed route.

**BGP plant prefix:** A similar assertion expected the compact `B` route code from:

```bash
vtysh -c 'show ip route 10.70.10.0/24'
```

The detailed form instead identifies the route as `Known via "bgp"`. A [subsequent CI run](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42272278414) passed OSPF checks but timed out on this BGP assertion.

The [corrected verification script](../scripts/verify.sh) checks `Known via "ospf"` and `Known via "bgp"` for detailed route queries. The [failover script](../scripts/failover.sh) deliberately uses the compact `show ip route` table to identify the selected interface (`eth1` or `eth2`).

**Engineering lesson:** A monitoring or test script must match the exact command's output format. A failed text match is not automatically proof of a routing outage.

## 5. Re-test and evidence

The [successful live CI run on November 6, 2026](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707) completed all required steps: deployment, FRR bootstrap, routing verification, failover, restoration, and cleanup.

Actual output from the successful run included:

```text
PASS OSPF neighbors (core)
PASS OSPF default route (core)
PASS BGP plant prefix (transit)
PASS ICMP plant -> service
PASS ICMP service -> plant
PASS core selected eth1
PASS core selected eth2
3 packets transmitted, 3 packets received, 0% packet loss
Restored edge-a:eth3.
PASS core selected eth1
```

Supporting material:

- [Live CI execution and console log](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707)
- [Routing verification screenshot](evidence/01-routing-verification.png)
- [WAN failover screenshot](evidence/02-wan-failover.png)
- [Test log and validation scope](test-log.md)
- [General troubleshooting guide](troubleshooting.md)

The successful live run was performed on **GitHub-hosted Ubuntu**, not as a complete verified failover run on the Windows/WSL host. No guaranteed convergence-time measurement, production SLA, or real industrial hardware test is claimed.

## 6. Lessons and prevention

- Check **daemon state**, **saved configuration**, and **running configuration** separately.
- Treat container deployment as an infrastructure step, not a routing acceptance test.
- Use readiness gates before applying daemon-dependent startup configuration.
- Validate routing at multiple layers: OSPF adjacency, RIB entries, BGP reachability, end-to-end ICMP, and controlled failover.
- Differentiate **control-plane faults** from **test-harness false negatives** using detailed CLI diagnostics.
- Preserve CI logs, reproducible commands, and evidence links, including earlier failures and subsequent fixes.

This case study records an actual troubleshooting sequence and a reproducible correction rather than a hypothetical production incident.
