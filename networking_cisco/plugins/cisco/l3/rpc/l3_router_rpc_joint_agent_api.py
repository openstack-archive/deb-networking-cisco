# Copyright 2014 Cisco Systems, Inc.  All rights reserved.
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
#

from oslo_log import log as logging
import oslo_messaging

from neutron.common import rpc as n_rpc

from networking_cisco.plugins.cisco.common import (
    cisco_constants as c_constants)

LOG = logging.getLogger(__name__)


class L3RouterJointAgentNotifyAPI(object):
    """API for plugin to notify Cisco cfg agent."""

    def __init__(self, l3plugin):
        self._l3plugin = l3plugin
        self.topic = c_constants.CFG_AGENT_L3_ROUTING
        target = oslo_messaging.Target(topic=self.topic, version='1.0')
        self.client = n_rpc.get_client(target)

    def _agent_notification(self, context, method, routers, operation, data):
        """Notify individual Cisco cfg agents."""
        admin_context = context if context.is_admin else context.elevated()
        for router in routers:
            if router['hosting_device'] is None:
                continue
            agents = self._l3plugin.get_cfg_agents_for_hosting_devices(
                    admin_context, [router['hosting_device']['id']],
                    admin_state_up=True, active=True, schedule=True)
            for agent in agents:
                LOG.debug('Notify %(agent_type)s at %(topic)s.%(host)s the '
                          'message %(method)s',
                          {'agent_type': agent.agent_type,
                           'topic': c_constants.CFG_AGENT_L3_ROUTING,
                           'host': agent.host,
                           'method': method})
                cctxt = self.client.prepare(server=agent.host)
                cctxt.cast(context, method, routers=[router['id']])

    def router_deleted(self, context, router):
        """Notifies agents about a deleted router."""
        self._agent_notification(context, 'router_deleted', [router],
                                 operation=None, data=None)

    def routers_updated(self, context, routers, operation=None, data=None):
        """Notifies agents about configuration changes to routers.

        This includes operations performed on the router like when a
        router interface is added or removed.
        """
        if routers:
            self._agent_notification(context, 'routers_updated', routers,
                                     operation, data)

    def hosting_devices_removed(self, context, hosting_data, deconfigure,
                                host):
        """Notify cfg agent that some hosting devices have been removed.

        This notification informs the cfg agent in <host> that the
        hosting devices in the <hosting_data> dictionary have been removed
        from the hosting device pool. The <hosting_data> dictionary also
        contains the ids of the affected logical resources for each hosting
        devices:
             {'hd_id1': {'routers': [id1, id2, ...],
                         'fw': [id1, ...],
                         ...},
              'hd_id2': {'routers': [id3, id4, ...]},
                         'fw': [id1, ...],
                         ...},
              ...}
        The <deconfigure> argument is True if any configurations for the
        logical resources should be removed from the hosting devices
        """
        if not hosting_data:
            return

        LOG.debug('Notify Cisco cfg agent at %(host)s the message '
                  'hosting_devices_removed', {'host': host})

        payload = {'hosting_data': hosting_data, 'deconfigure': deconfigure}
        cctxt = self.client.prepare(topic=c_constants.CFG_AGENT, server=host)
        cctxt.cast(context, 'hosting_devices_removed', payload=payload)
