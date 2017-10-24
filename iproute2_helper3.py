"""
BSD 3-Clause License

Copyright (c) 2017, Jesus Llorente Santos, Aalto University, Finland
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from socket import AF_INET, AF_INET6
from pyroute2 import IPRoute, IPSet

ipr = IPRoute()
ips = IPSet()

def ipset_list(name=None):
    return ips.list(name=name)

def ipset_flush(name=None):
    return ips.flush(name)

def ipset_create(name, stype='hash:ip', family=AF_INET, maxelem=65536, hashsize=None):
    ips.create(name, stype=stype, family=family, maxelem=maxelem, hashsize=hashsize)

def ipset_destroy(name):
    return ips.destroy(name)

def ipset_add(name, entry, family=AF_INET, etype='ip'):
    # etype = {ip, net, ip,mark ..}
    if etype == 'ip':
        entry = entry.split('/')[0]
    ips.add(name, entry, family=family, etype=etype)

def ipset_delete(name, entry, family=AF_INET, etype='ip'):
    # etype = {ip, net, ip,mark ..}
    if etype == 'ip':
        entry = entry.split('/')[0]
    ips.delete(name, entry, family=family, etype=etype)

def ipset_test(name, entry, family=AF_INET, etype='ip'):
    # etype = {ip, net, ip,mark ..}
    if etype == 'ip':
        entry = entry.split('/')[0]
    try:
        return ips.test(name, entry, family=family, etype=etype)
    except:
        return False

def ipset_exists(name):
    return [x for x in ips.list()
            if x.get_attr('IPSET_ATTR_SETNAME') == name]

def get_links():
    res = []
    links = ipr.get_links()
    for link in links:
        link_info = {}
        link_info['index'] = link['index']
        for attr in link['attrs']:
            attr_name, attr_value = attr
            if attr_name == 'IFLA_IFNAME':
                link_info['name'] = attr_value
            elif attr_name == 'IFLA_OPERSTATE':
                link_info['state'] = attr_value
            elif attr_name == 'IFLA_CARRIER':
                link_info['carrier'] = attr_value
            elif attr_name == 'IFLA_ADDRESS':
                link_info['macaddr'] = attr_value
            elif attr_name == 'IFLA_MTU':
                link_info['mtu'] = attr_value
        res.append(link_info)
    return res

def get_link(name):
    link_dict = get_links()
    for link in link_dict:
        if not 'name' in link:
            continue
        if link['name'] == name:
            return [link]
    return []


def tc_add_qdisc(nic, kind, handle, *args, **kwargs):
    assert(handle in range(1,0xFFFF))
    if 'default' in kwargs:
        assert(kwargs['default'] in range(1,0xFFFF))
    nic_id = ipr.link_lookup(ifname=nic)[0]
    ipr.tc('add', kind, nic_id, handle<<16, *args, **kwargs)

def tc_del_qdisc(nic, kind, handle):
    assert(handle in range(1,0xFFFF))
    nic_id = ipr.link_lookup(ifname=nic)[0]
    ipr.tc('del', kind, nic_id, handle<<16)

def tc_add_class_htb(nic, major, parent_minor, classid_minor, rate, ceil = None):
    assert(major in range(1,0xFFFF))
    assert(parent_minor in range(0,0xFFFF))  #parent could be a qdisc
    assert(classid_minor in range(1,0xFFFF))
    nic_id = ipr.link_lookup(ifname=nic)[0]
    classid_f = major << 16 | classid_minor
    parent_f  = major << 16 | parent_minor
    ipr.tc('add-class', 'htb', nic_id, classid_f, parent=parent_f, rate=rate, ceil=ceil)

def tc_del_class_htb(nic, major, minor):
    assert(major in range(1,0xFFFF))
    assert(minor in range(1,0xFFFF))
    nic_id = ipr.link_lookup(ifname=nic)[0]
    classid_f = major << 16 | classid_minor
    parent_f  = major << 16 | parent_minor
    ipr.tc('del-class', 'htb', nic_id, classid_f)
