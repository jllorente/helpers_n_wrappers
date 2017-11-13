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

# This module contains network and packet realted helper functions

import socket
import struct
import sys
import traceback

# For Scapy packet parsing
try:
    from scapy.all import *
    from scapy.layers.inet import *
    from scapy.layers.inet6 import *
except ImportError:
    print('Scapy not available')

def parse_packet_scapy(data):
    ret = {}
    ip = IP(data)
    ret['src'] = ip.src
    ret['dst'] = ip.dst
    ret['ttl'] = ip.ttl
    ret['proto'] = ip.proto
    if ip.proto == 1:
        ret['type'] = ip.payload.type
        ret['code'] = ip.payload.code
    elif ip.proto == 6:
        ret['sport'] = ip.payload.sport
        ret['dport'] = ip.payload.dport
        ret['tcp_flags'] = ip.payload.flags
    elif ip.proto == 17:
        ret['sport'] = ip.payload.sport
        ret['dport'] = ip.payload.dport
    elif ip.proto == 132:
        ret['sport'] = ip.payload.sport
        ret['dport'] = ip.payload.dport
        ret['sctp_tag'] = ip.payload.tag
    return ret

def parse_packet_custom(data):
    ret = {}
    ret['src'] = socket.inet_ntoa(data[12:16])
    ret['dst'] = socket.inet_ntoa(data[16:20])
    ret['ttl'] = data[8]
    ret['proto'] = data[9]
    proto = data[9]
    ihl = (data[0] & 0x0F) * 4  #ihl comes in 32 bit words (32/8)
    if proto == 1:
        ret['icmp-type'] = data[ihl]
        ret['icmp-code'] = data[ihl+1]
    elif proto == 6:
        ret['sport'] = struct.unpack('!H', (data[ihl:ihl+2]))[0]
        ret['dport'] = struct.unpack('!H', (data[ihl+2:ihl+4]))[0]
        ret['tcp_flags'] = struct.unpack('!B', (data[ihl+13:ihl+14]))[0]
    elif proto == 17:
        ret['sport'] = struct.unpack('!H', (data[ihl:ihl+2]))[0]
        ret['dport'] = struct.unpack('!H', (data[ihl+2:ihl+4]))[0]
    elif proto == 132:
        ret['sport'] = struct.unpack('!H', (data[ihl:ihl+2]))[0]
        ret['dport'] = struct.unpack('!H', (data[ihl+2:ihl+4]))[0]
        ret['sctp_tag'] = struct.unpack('!I', (data[ihl+4:ihl+8]))[0]
    return ret

def is_ipv4(ipaddr):
    try:
        assert(socket.inet_pton(socket.AF_INET, ipaddr))
        return True
    except:
        return False

def is_ipv6(ipaddr):
    try:
        assert(socket.inet_pton(socket.AF_INET6, ipaddr))
        return True
    except:
        return False

def ipaddr_to_int(ipaddr, family = socket.AF_INET):
    if family == socket.AF_INET:
        ipaddr_b = socket.inet_pton(family, ipaddr)
        ipaddr_i = struct.unpack('!I', ipaddr_b)[0]
    elif family == socket.AF_INET6:
        ipaddr_b = socket.inet_pton(family, ipaddr)
        a, b = struct.unpack('!2Q', ipaddr_b)
        ipaddr_i = (a << 64) | b
    else:
        raise socket.error('Unsupported family "{}"'.format(family))
    return ipaddr_i

def int_to_ipaddr(ipaddr, family = socket.AF_INET):
    if family == socket.AF_INET:
        ipaddr_b = struct.pack('!I', ipaddr)
        ipaddr_s = socket.inet_ntop(family, ipaddr_b)
    elif family == socket.AF_INET6:
        a = ipaddr >> 64
        b = ipaddr & ((1 << 64) - 1)
        ipaddr_b = struct.pack('!2Q', a, b)
        ipaddr_s = socket.inet_ntop(family, ipaddr_b)
    else:
        raise socket.error('Unsupported family "{}"'.format(family))
    return ipaddr_s