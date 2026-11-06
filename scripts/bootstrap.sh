#!/usr/bin/env bash
# Apply integrated FRR configuration after daemons are running.
# Safe to use on a newly deployed lab. The running FRR daemons remain active.
set -euo pipefail

LAB=industrial-routing
routers=(core edge-a edge-b isp-a isp-b transit)
for router in "${routers[@]}"; do
  container="clab-${LAB}-${router}"
  echo "Checking ${container} ..."
  ready=0
  for attempt in $(seq 1 30); do
    if docker exec "$container" vtysh -c 'show version' >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 2
  done
  if (( ready != 1 )); then
    echo "ERROR: vtysh not ready in ${container}" >&2
    exit 1
  fi
  echo "Loading /etc/frr/frr.conf on ${router}"
  docker exec "$container" vtysh -b
  case "$router" in
    core|edge-a|edge-b)
      if ! docker exec "$container" vtysh -c 'show running-config' | grep -q '^router ospf'; then
        echo "ERROR: OSPF config was not loaded on ${router}" >&2
        exit 1
      fi
      ;;
  esac
  echo "Ready: ${router}"
done

echo "FRR bootstrap finished."
