# Routing Lab Evidence

These screenshots were captured from the actual [successful live routing GitHub Actions run on November 6, 2026](https://github.com/ModarRostom/industrial-ospf-bgp-lab/actions/runs/42273117707). The run used a simulated Containerlab topology on a GitHub-hosted Ubuntu runner.

| Image | What it documents |
|---|---|
| [01-routing-verification.png](01-routing-verification.png) | OSPF neighbor state, installed default route, BGP route, and bidirectional ICMP results |
| [02-wan-failover.png](02-wan-failover.png) | Primary and backup path selection, successful ICMP during failover, and restoration |
| [03-wan-failover-additional.png](03-wan-failover-additional.png) | Additional screenshot from the WAN failover workflow |

Only use these images as evidence of the tested CI topology. They do not establish a production SLA, guaranteed convergence time, or successful execution on another host. Sanitize screenshots before publishing if they contain secrets or private information.
