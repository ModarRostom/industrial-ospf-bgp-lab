# Test Log and Validation Evidence

This log distinguishes **observed deployment results** from **unverified routing outcomes**. A running container does not, by itself, demonstrate an established routing adjacency.

## Local deployment observation

| Field | Observed result |
|---|---|
| Date | November 6, 2026 |
| Host | Windows 10 Build 19045.6466, Containerlab-WSL |
| Containerlab | 0.82.0 |
| Docker Engine | 27.5.1 |
| FRRouting image | `quay.io/frrouting/frr:containerlab-10.7.1` |
| Linux client image | `alpine:3.20` |
| Deployment command | `sudo containerlab deploy -t topology.clab.yml` |
| Result | 8 of 8 containers reported as `running` (six FRR routers, two Linux clients) |
| Evidence | Local console output shared during debugging; a raw deployment log has not been committed |

## Automated CI observations

The live integration test **passed on November 6, 2026**, on a GitHub-hosted Ubuntu runner:

- [Successful live routing workflow (OSPF, BGP, ICMP, failover, recovery)](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707)
- [Successful static configuration and Bash syntax workflow](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117662)

The live workflow deployed eight containers, bootstrapped all six FRRouting instances, ran `scripts/verify.sh`, and ran `scripts/failover.sh`; both scripts exited successfully. The lab was destroyed after the run.

| Test | Expected behavior | Observed in successful CI run |
|---|---|---|
| Static tests | Configuration consistency and valid Bash syntax | PASS |
| Core OSPF neighbors | Edge A and Edge B in `Full` state | PASS |
| Core default route | OSPF default via Edge A (`eth1`) | PASS |
| eBGP routing | Production prefix learned at transit | PASS |
| ICMP Plant → Service | Reachable | PASS |
| ICMP Service → Plant | Reachable | PASS |
| Primary uplink failure | Core switches to Edge B (`eth2`) | PASS |
| Connectivity during failover | External service remains reachable | PASS: 3/3 replies, 0% packet loss in the post-failover ping |
| Uplink restoration | Core returns to Edge A (`eth1`) | PASS |

**Evidence excerpts from the live workflow:**

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

**Scope:** These observations were recorded on GitHub's ephemeral Linux runner and do not independently verify the latest local Windows/WSL deployment. The test demonstrates route failover under the simulated edge-to-ISP link outage; it does not establish a production SLA, measured end-to-end convergence time, or hardware redundancy.

## Reproduce checks locally

Run these commands from `~/industrial-ospf-bgp-lab`:

```bash
# Apply saved router configurations after all FRR daemons become ready.
bash scripts/bootstrap.sh

# Verify routing and connectivity without modifying the topology.
bash scripts/verify.sh

# Only after successful verification, test WAN failover and restoration.
bash scripts/failover.sh
```

To capture outputs and exit statuses:

```bash
mkdir -p evidence
set -o pipefail
bash scripts/verify.sh 2>&1 | tee evidence/verify.txt
printf 'verify_exit=%s\n' "${PIPESTATUS[0]}" | tee -a evidence/verify.txt

# Run only if verification passed.
bash scripts/failover.sh 2>&1 | tee evidence/failover.txt
printf 'failover_exit=%s\n' "${PIPESTATUS[0]}" | tee -a evidence/failover.txt
```

**Safety:** The failover script temporarily disables `edge-a:eth3` and attempts to restore it automatically. Use only in the simulated lab.

## Publication checklist

1. Review the actual neighbor states, routing tables, and connectivity results.
2. Record failures, root causes, corrections, and re-test results.
3. Publish only sanitized logs or screenshots containing no tokens, credentials, or company data.
4. Claim `PASS` only when the corresponding test has actually succeeded.
