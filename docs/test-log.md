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

GitHub Actions runs static checks via [static-checks.yml](../.github/workflows/static-checks.yml) and executes a live routing lab via [live-routing.yml](../.github/workflows/live-routing.yml). **Check the latest run results before reporting success.** CI observations apply to GitHub's ephemeral Linux runner, not automatically to the local Windows 10 host.

Earlier live CI output confirmed two OSPF core adjacencies in `Full` state, eBGP peerings carrying prefixes, and an installed OSPF default route via Edge A. Some runs still failed due to verification-script behavior; passing end-to-end connectivity and WAN failover must be demonstrated separately.

## Validation checklist

| Test | Expected | Evidence |
|---|---|---|
| Static configuration and Bash syntax | Pass | GitHub Actions result |
| Core OSPF neighbors | Edge A and Edge B in Full state | Observed in earlier CI diagnostics |
| Core default route | OSPF route via Edge A | Observed in earlier CI diagnostics |
| eBGP peers and prefix exchange | Sessions established and intended prefixes present | Observed in earlier CI diagnostics |
| Transit production prefix | `10.70.10.0/24` installed | Observed in earlier CI diagnostics |
| ICMP Plant → Service | Reachable | Pending final verification |
| ICMP Service → Plant | Reachable | Pending final verification |
| Edge A WAN failure | Core selects Edge B | Pending final verification |
| WAN restoration | Core reselects Edge A | Pending final verification |

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
