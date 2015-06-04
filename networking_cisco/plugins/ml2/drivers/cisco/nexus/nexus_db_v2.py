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
#

from oslo_log import log as logging
import sqlalchemy.orm.exc as sa_exc

import neutron.db.api as db
from neutron.i18n import _LW

from networking_cisco.plugins.ml2.drivers.cisco.nexus import (
    exceptions as c_exc)
from neutron.plugins.ml2.drivers.cisco.nexus import (
    nexus_models_v2)

LOG = logging.getLogger(__name__)


def get_nexusport_binding(port_id, vlan_id, switch_ip, instance_id):
    """Lists a nexusport binding."""
    LOG.debug("get_nexusport_binding() called")
    return _lookup_all_nexus_bindings(port_id=port_id,
                                      vlan_id=vlan_id,
                                      switch_ip=switch_ip,
                                      instance_id=instance_id)


def get_nexusvlan_binding(vlan_id, switch_ip):
    """Lists a vlan and switch binding."""
    LOG.debug("get_nexusvlan_binding() called")
    return _lookup_all_nexus_bindings(vlan_id=vlan_id, switch_ip=switch_ip)


def get_nexusport_switch_bindings(switch_ip):
    """Lists all Nexus port switch bindings."""
    LOG.debug("get_nexusport_switch_bindings() called")
    return _lookup_all_nexus_bindings(switch_ip=switch_ip)


def add_nexusport_binding(port_id, vlan_id, vni, switch_ip, instance_id,
                          is_provider_vlan):
    """Adds a nexusport binding."""
    LOG.debug("add_nexusport_binding() called")
    session = db.get_session()
    binding = nexus_models_v2.NexusPortBinding(port_id=port_id,
                  vlan_id=vlan_id,
                  vni=vni,
                  switch_ip=switch_ip,
                  instance_id=instance_id,
                  is_provider_vlan=is_provider_vlan)
    session.add(binding)
    session.flush()
    return binding


def remove_nexusport_binding(port_id, vlan_id, vni, switch_ip, instance_id,
                             is_provider_vlan):
    """Removes a nexusport binding."""
    LOG.debug("remove_nexusport_binding() called")
    session = db.get_session()
    binding = _lookup_all_nexus_bindings(session=session,
                                         vlan_id=vlan_id,
                                         vni=vni,
                                         switch_ip=switch_ip,
                                         port_id=port_id,
                                         instance_id=instance_id,
                                         is_provider_vlan=is_provider_vlan)
    for bind in binding:
        session.delete(bind)
    session.flush()
    return binding


def update_nexusport_binding(port_id, new_vlan_id):
    """Updates nexusport binding."""
    if not new_vlan_id:
        LOG.warning(_LW("update_nexusport_binding called with no vlan"))
        return
    LOG.debug("update_nexusport_binding called")
    session = db.get_session()
    binding = _lookup_one_nexus_binding(session=session, port_id=port_id)
    binding.vlan_id = new_vlan_id
    session.merge(binding)
    session.flush()
    return binding


def get_nexusvm_bindings(vlan_id, instance_id):
    """Lists nexusvm bindings."""
    LOG.debug("get_nexusvm_bindings() called")
    return _lookup_all_nexus_bindings(instance_id=instance_id,
                                      vlan_id=vlan_id)


def get_port_vlan_switch_binding(port_id, vlan_id, switch_ip):
    """Lists nexusvm bindings."""
    LOG.debug("get_port_vlan_switch_binding() called")
    return _lookup_all_nexus_bindings(port_id=port_id,
                                      switch_ip=switch_ip,
                                      vlan_id=vlan_id)


def get_port_switch_bindings(port_id, switch_ip):
    """List all vm/vlan bindings on a Nexus switch port."""
    LOG.debug("get_port_switch_bindings() called, "
              "port:'%(port_id)s', switch:'%(switch_ip)s'",
              {'port_id': port_id, 'switch_ip': switch_ip})
    try:
        return _lookup_all_nexus_bindings(port_id=port_id,
                                          switch_ip=switch_ip)
    except c_exc.NexusPortBindingNotFound:
        pass


def get_nexussvi_bindings():
    """Lists nexus svi bindings."""
    LOG.debug("get_nexussvi_bindings() called")
    return _lookup_all_nexus_bindings(port_id='router')


def _lookup_nexus_bindings(query_type, session=None, **bfilter):
    """Look up 'query_type' Nexus bindings matching the filter.

    :param query_type: 'all', 'one' or 'first'
    :param session: db session
    :param bfilter: filter for bindings query
    :return: bindings if query gave a result, else
             raise NexusPortBindingNotFound.
    """
    if session is None:
        session = db.get_session()
    query_method = getattr(session.query(
        nexus_models_v2.NexusPortBinding).filter_by(**bfilter), query_type)
    try:
        bindings = query_method()
        if bindings:
            return bindings
    except sa_exc.NoResultFound:
        pass
    raise c_exc.NexusPortBindingNotFound(**bfilter)


def _lookup_all_nexus_bindings(session=None, **bfilter):
    return _lookup_nexus_bindings('all', session, **bfilter)


def _lookup_one_nexus_binding(session=None, **bfilter):
    return _lookup_nexus_bindings('one', session, **bfilter)


def _lookup_first_nexus_binding(session=None, **bfilter):
    return _lookup_nexus_bindings('first', session, **bfilter)


def add_nexusnve_binding(vni, switch_ip, device_id, mcast_group):
    """Adds a nexus nve binding."""
    LOG.debug("add_nexusnve_binding() called")
    session = db.get_session()
    binding = nexus_models_v2.NexusNVEBinding(vni=vni,
                                              switch_ip=switch_ip,
                                              device_id=device_id,
                                              mcast_group=mcast_group)
    session.add(binding)
    session.flush()
    return binding


def remove_nexusnve_binding(vni, switch_ip, device_id):
    """Remove the nexus nve binding."""
    LOG.debug("remove_nexusnve_binding() called")
    session = db.get_session()
    binding = (session.query(nexus_models_v2.NexusNVEBinding).
               filter_by(vni=vni, switch_ip=switch_ip,
                         device_id=device_id).one())
    if binding:
        session.delete(binding)
        session.flush()
        return binding


def get_nve_vni_switch_bindings(vni, switch_ip):
    """Return the nexus nve binding(s) per switch."""
    LOG.debug("get_nve_vni_switch_bindings() called")
    session = db.get_session()
    try:
        return (session.query(nexus_models_v2.NexusNVEBinding).
                filter_by(vni=vni, switch_ip=switch_ip).all())
    except sa_exc.NoResultFound:
        return None


def get_nve_vni_member_bindings(vni, switch_ip, device_id):
    """Return the nexus nve binding per switch and device_id."""
    LOG.debug("get_nve_vni_member_bindings() called")
    session = db.get_session()
    try:
        return (session.query(nexus_models_v2.NexusNVEBinding).
                filter_by(vni=vni, switch_ip=switch_ip,
                          device_id=device_id).all())
    except sa_exc.NoResultFound:
        return None


def get_nve_switch_bindings(switch_ip):
    """Return all the nexus nve bindings for one switch."""
    LOG.debug("get_nve_switch_bindings() called")
    session = db.get_session()
    try:
        return (session.query(nexus_models_v2.NexusNVEBinding).
                filter_by(switch_ip=switch_ip).all())
    except sa_exc.NoResultFound:
        return None


def get_nve_vni_deviceid_bindings(vni, device_id):
    """Return all the nexus nve bindings for one vni/one device_id."""
    LOG.debug("get_nve_vni_deviceid_bindings() called")
    session = db.get_session()
    try:
        return (session.query(nexus_models_v2.NexusNVEBinding).
                filter_by(vni=vni, device_id=device_id).all())
    except sa_exc.NoResultFound:
        return None
