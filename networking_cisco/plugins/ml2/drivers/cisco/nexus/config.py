# Copyright (c) 2013 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg


ml2_cisco_opts = [
    cfg.StrOpt('vlan_name_prefix', default='q-',
               help=_("VLAN Name prefix")),
    cfg.BoolOpt('svi_round_robin', default=False,
                help=_("Distribute SVI interfaces over all switches")),
    cfg.StrOpt('managed_physical_network',
               help=_("The physical network managed by the switches.")),
    cfg.StrOpt('provider_vlan_name_prefix', default='p-',
        help=_("VLAN Name prefix for provider vlans")),
    cfg.BoolOpt('persistent_switch_config', default=False,
                help=_("To make Nexus configuration persistent")),
    cfg.IntOpt('switch_heartbeat_time', default=0,
        help=_("Periodic time to check switch connection. (0=disabled)")),
    cfg.IntOpt('switch_replay_count', default=3,
        help=_("Number of times to attempt config replay with switch.")),
    cfg.BoolOpt('provider_vlan_auto_create', default=True,
        help=_('Provider VLANs are automatically created as needed '
               'on the Nexus switch')),
    cfg.BoolOpt('provider_vlan_auto_trunk', default=True,
        help=_('Provider VLANs are automatically trunked as needed '
               'on the ports of the Nexus switch')),
    cfg.BoolOpt('vxlan_global_config', default=False,
        help=_('Create and delete Nexus switch VXLAN global settings; '
               'feature nv overlay, feature vn-segment-vlan-based, '
               'interface nve + source-interface loopback')),
    cfg.BoolOpt('host_key_checks', default=False,
                help=_("Enable strict host key checks when "
                       "connecting to Nexus switches")),
]


cfg.CONF.register_opts(ml2_cisco_opts, "ml2_cisco")

#
# Format for ml2_conf_cisco.ini 'ml2_mech_cisco_nexus' is:
# {('<device ipaddr>', '<keyword>'): '<value>', ...}
#
# Example:
# {('1.1.1.1', 'username'): 'admin',
#  ('1.1.1.1', 'password'): 'mySecretPassword',
#  ('1.1.1.1', 'compute1'): '1/1', ...}
#


class ML2MechCiscoConfig(object):
    """ML2 Mechanism Driver Cisco Configuration class."""
    nexus_dict = {}

    def __init__(self):
        self._create_ml2_mech_device_cisco_dictionary()

    def _create_ml2_mech_device_cisco_dictionary(self):
        """Create the ML2 device cisco dictionary.

        Read data from the ml2_conf_cisco.ini device supported sections.
        """
        multi_parser = cfg.MultiConfigParser()
        read_ok = multi_parser.read(cfg.CONF.config_file)

        if len(read_ok) != len(cfg.CONF.config_file):
            raise cfg.Error(_("Some config files were not parsed properly"))

        for parsed_file in multi_parser.parsed:
            for parsed_item in parsed_file.keys():
                dev_id, sep, dev_ip = parsed_item.partition(':')
                if dev_id.lower() == 'ml2_mech_cisco_nexus':
                    for dev_key, value in parsed_file[parsed_item].items():
                        self.nexus_dict[dev_ip, dev_key] = value[0]
