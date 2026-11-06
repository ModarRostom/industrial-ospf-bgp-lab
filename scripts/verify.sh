#!/usr/bin/env bash
# Read-only smoke tests. Run after 'containerlab deploy'.
set -euo pipefail
LAB=industrial-routing
node() { docker exec "clab-${LAB}-$1" "${@:2}"; }
show() { node "$1" vtysh -c "$2"; }

wait_for() {
  local label="$1"; shift
  local attempt
  for attempt in $(seq 1 36); do
    if "$@" >/dev/null 2>&1; then
      echo "PASS $label"
      return 0
    fi
    sleep 5
  done
  echo "FAIL $label (timeout)" >&2
  return 1
}

has_neighbor() { [[ $(show core 'show ip ospf neighbor' | grep -c 'Full' || true) -eq 2 ]]; }
has_default() { show core 'show ip route 0.0.0.0/0' | grep -q 'Known via "ospf"'; }
has_plant_route() { show transit 'show ip route 10.70.10.0/24' | grep -q 'Known via "bgp"'; }
can_reach_service() { node plant ping -c 2 -W 2 198.51.100.10; }
can_reach_plant() { node service ping -c 2 -W 2 10.70.10.10; }

wait_for 'OSPF neighbors (core)' has_neighbor
wait_for 'OSPF default route (core)' has_default
wait_for 'BGP plant prefix (transit)' has_plant_route
wait_for 'ICMP plant -> service' can_reach_service
wait_for 'ICMP service -> plant' can_reach_plant

echo
echo '--- core: OSPF neighbors ---'
show core 'show ip ospf neighbor'
echo '--- core: installed default ---'
show core 'show ip route 0.0.0.0/0'
echo '--- edge-a: BGP summary ---'
show edge-a 'show bgp ipv4 unicast summary'
echo '--- edge-b: BGP summary ---'
show edge-b 'show bgp ipv4 unicast summary'
echo '--- transit: installed plant route ---'
show transit 'show ip route 10.70.10.0/24'
echo
echo 'Smoke test finished. Review output before adding any evidence to GitHub.'
