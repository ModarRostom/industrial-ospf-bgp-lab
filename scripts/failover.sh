#!/usr/bin/env bash
# Simulates failure of edge-a's ISP link; restores it even on CTRL+C.
set -euo pipefail
LAB=industrial-routing
EDGE="clab-${LAB}-edge-a"
CORE="clab-${LAB}-core"
PLANT="clab-${LAB}-plant"
restored=0

restore() {
  if (( restored == 0 )); then
    docker exec "$EDGE" ip link set dev eth3 up || true
    restored=1
    echo 'Restored edge-a:eth3.'
  fi
}
trap restore EXIT INT TERM

route() { docker exec "$CORE" vtysh -c 'show ip route 0.0.0.0/0'; }
wait_for_path() {
  local expected="$1" attempt
  for attempt in $(seq 1 36); do
    if route | grep -q ", ${expected},"; then
      echo "PASS core selected ${expected}"
      return 0
    fi
    sleep 5
  done
  echo "FAIL no default route via ${expected} after 180s" >&2
  route >&2
  return 1
}

printf '\n[1] Baseline default route\n'
wait_for_path eth1
route
printf '\n[2] Disable edge-a <-> isp-a link (edge-a:eth3)\n'
docker exec "$EDGE" ip link set dev eth3 down
printf '\n[3] Wait for routing convergence via edge-b\n'
wait_for_path eth2
route
printf '\n[4] Verify plant can still reach external service\n'
docker exec "$PLANT" ping -c 3 -W 2 198.51.100.10
printf '\n[5] Restore link, wait for preferred path\n'
restore
wait_for_path eth1
route
printf '\nDone. Record actual observations in docs/test-log.md.\n'
