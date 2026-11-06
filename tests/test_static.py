"""Static guardrails. No containers or protocol sessions are started here."""
import ipaddress
import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOPO = yaml.safe_load((ROOT / 'topology.clab.yml').read_text())
NODES = TOPO['topology']['nodes']


def config(node):
    return (ROOT / NODES[node]['startup-config']).read_text()


class LabConfigurationTests(unittest.TestCase):
    def test_router_configs_exist(self):
        routers = {'core', 'edge-a', 'edge-b', 'isp-a', 'isp-b', 'transit'}
        self.assertEqual({n for n, v in NODES.items() if v['kind'] == 'frr'}, routers)
        for router in routers:
            self.assertTrue((ROOT / NODES[router]['startup-config']).is_file())

    def test_all_link_endpoints_are_unique_and_exist(self):
        seen = set()
        for link in TOPO['topology']['links']:
            self.assertEqual(len(link['endpoints']), 2)
            for endpoint in link['endpoints']:
                node, interface = endpoint.split(':')
                self.assertIn(node, NODES)
                self.assertRegex(interface, r'^eth[1-9][0-9]*$')
                self.assertNotIn(endpoint, seen)
                seen.add(endpoint)

    def test_router_interface_addresses_match_links(self):
        interface_ips = {}
        for node, details in NODES.items():
            if details['kind'] != 'frr':
                continue
            text = config(node)
            for match in re.finditer(
                r'^interface (eth\d+)\n(.*?)(?=^!|^interface |\Z)',
                text,
                flags=re.MULTILINE | re.DOTALL,
            ):
                address = re.search(r'^ ip address (\S+)', match.group(2), re.MULTILINE)
                if address:
                    interface_ips[f'{node}:{match.group(1)}'] = ipaddress.ip_interface(address.group(1))
        # Alpine host addresses are declared in exec commands.
        for node in ('plant', 'service'):
            for cmd in NODES[node]['exec']:
                m = re.fullmatch(r'ip address add (\S+) dev (eth\d+)', cmd)
                if m:
                    interface_ips[f'{node}:{m.group(2)}'] = ipaddress.ip_interface(m.group(1))
        for link in TOPO['topology']['links']:
            endpoint_a, endpoint_b = link['endpoints']
            self.assertIn(endpoint_a, interface_ips)
            self.assertIn(endpoint_b, interface_ips)
            a, b = interface_ips[endpoint_a], interface_ips[endpoint_b]
            self.assertEqual(a.network, b.network, f'{endpoint_a} <> {endpoint_b}')
            self.assertNotEqual(a.ip, b.ip)
        self.assertEqual(len(interface_ips), len(TOPO['topology']['links']) * 2)

    def test_ebgp_peer_addresses_and_asns_match_the_link(self):
        asns = {'edge-a': 65010, 'edge-b': 65010, 'isp-a': 65110,
                'isp-b': 65120, 'transit': 65200}
        interfaces = {}
        for name in asns:
            for block in re.finditer(
                r'^interface (eth\d+)\n(.*?)(?=^!|^interface |\Z)',
                config(name), flags=re.MULTILINE | re.DOTALL,
            ):
                addr = re.search(r'^ ip address (\S+)', block.group(2), re.MULTILINE)
                if addr:
                    interfaces[f'{name}:{block.group(1)}'] = str(ipaddress.ip_interface(addr.group(1)).ip)
        checked = 0
        for link in TOPO['topology']['links']:
            left, right = link['endpoints']
            left_name, right_name = left.split(':')[0], right.split(':')[0]
            if left_name not in asns or right_name not in asns or asns[left_name] == asns[right_name]:
                continue
            self.assertIn(f'neighbor {interfaces[right]} remote-as {asns[right_name]}', config(left_name))
            self.assertIn(f'neighbor {interfaces[left]} remote-as {asns[left_name]}', config(right_name))
            checked += 1
        self.assertEqual(checked, 4)

    def test_default_origination_depends_on_transit_service(self):
        for isp in ('isp-a', 'isp-b'):
            conf = config(isp)
            self.assertIn('route-map HAS-SERVICE permit 10', conf)
            self.assertIn('match ip address prefix-list SERVICE-ONLY', conf)
            self.assertIn('default-originate route-map HAS-SERVICE', conf)

    def test_ospf_is_not_enabled_on_wan(self):
        for router in ('core', 'edge-a', 'edge-b'):
            self.assertIn('passive-interface default', config(router))
            self.assertIn('no passive-interface eth1', config(router))
        self.assertNotIn('ip ospf area', config('isp-a'))
        self.assertNotIn('ip ospf area', config('transit'))

    def test_edge_bgp_has_in_out_filters(self):
        for edge in ('edge-a', 'edge-b'):
            conf = config(edge)
            self.assertIn('ip prefix-list FROM-ISP seq 10 permit 0.0.0.0/0', conf)
            self.assertIn('ip prefix-list TO-ISP seq 10 permit 10.70.10.0/24', conf)
            self.assertIn('prefix-list FROM-ISP in', conf)
            self.assertIn('prefix-list TO-ISP out', conf)
            self.assertIn('default-information originate metric 5 metric-type 1', conf)
            self.assertNotIn('default-information originate always', conf)
            self.assertNotIn('redistribute ospf', conf)

    def test_simulated_upstreams_have_bgp_filters(self):
        for router in ('isp-a', 'isp-b', 'transit'):
            conf = config(router)
            self.assertIn('prefix-list', conf)
            self.assertIn(' in', conf)
            self.assertIn(' out', conf)
        self.assertIn('set local-preference 200', config('transit'))
        self.assertIn('set local-preference 150', config('transit'))


if __name__ == '__main__':
    unittest.main()
