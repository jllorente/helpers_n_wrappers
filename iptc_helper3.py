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

# NOTES
# - Table names are lowercase - filter, mangle, nat, raw
# - Chain names are uppercase - FORWARD, INPUT, OUTPUT, PREROUTING, POSTROUTING
# - Both chains and tables are singletons

# TODO
# - Use Table.ALL when the iptc code is fixed for iterating all tables

# REFACTOR
# flush_chain  has changed
# add_chain    has changed
# delete_chain has changed
# delete_rule  has changed
# batch_add_chains   has changed
# batch_delete_rules has changed

import iptc

MODE_BATCH = False

def flush_all(ipv6=False):
    """ Flush all tables """
    for table in ('security', 'raw', 'mangle', 'nat', 'filter'):
        flush_table(table, ipv6=ipv6)

def flush_table(table, ipv6=False):
    """ Flush a table """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    iptc_table.flush()

def flush_chain(table, chain, ipv6=False, silent=False):
    """ Flush a chain """
    try:
        iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
        iptc_chain.flush()
    except Exception as e:
        if not silent:
            raise

def zero_all(table, ipv6=False):
    """ Zero all tables """
    for table in ('security', 'raw', 'mangle', 'nat', 'filter'):
        zero_table(table, ipv6=ipv6)

def zero_table(table, ipv6=False):
    """ Zero a table """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    iptc_table.zero_entries()

def zero_chain(table, chain, ipv6=False):
    """ Zero a chain """
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_chain.zero_counters()

def has_chain(table, chain, ipv6=False):
    """ Return True if chain exists in table False otherwise """
    return _iptc_gettable(table, ipv6=ipv6).is_chain(chain)

def has_rule(table, chain, rule_d, ipv6=False):
    """ Return True if rule exists in chain False otherwise """
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
    return iptc_rule in iptc_chain.rules

def add_chain(table, chain, ipv6=False, silent=False):
    """ Return True if chain was added successfuly to a table, raise Exception otherwise """
    try:
        iptc_table = _iptc_gettable(table, ipv6=ipv6)
        iptc_table.create_chain(chain)
        return True
    except Exception as e:
        if not silent:
            raise
        return False

def add_rule(table, chain, rule_d, position=0, ipv6=False):
    """ Add a rule to a chain in a given position. 0=append, 1=first, n=nth position """
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
    if position == 0:
        # Insert rule in last position -> append
        iptc_chain.append_rule(iptc_rule)
    elif position > 0:
        # Insert rule in given position -> adjusted as iptables CLI
        iptc_chain.insert_rule(iptc_rule, position - 1)
    elif position < 0:
        # Insert rule in given position starting from bottom -> not available in iptables CLI
        nof_rules = len(iptc_chain.rules)
        iptc_chain.insert_rule(iptc_rule, position + nof_rules)

def insert_rule(table, chain, rule_d, ipv6=False):
    """ Add a rule to a chain in the 1st position """
    add_rule(table, chain, rule_d, position=1, ipv6=ipv6)

def delete_chain(table, chain, ipv6=False, flush=False, silent=False):
    """ Delete a chain """
    try:
        if flush:
            flush_chain(table, chain, ipv6=ipv6, silent=silent)
        iptc_table = _iptc_gettable(table, ipv6=ipv6)
        iptc_table.delete_chain(chain)
    except Exception as e:
        if not silent:
            raise

def delete_rule(table, chain, rule_d, ipv6=False, silent=False):
    """ Delete a rule from a chain """
    try:
        iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
        iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
        iptc_chain.delete_rule(iptc_rule)
    except Exception as e:
        if not silent:
            raise

def get_chains(table, ipv6=False):
    """ Return the existing chains of a table """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    return [iptc_chain.name for iptc_chain in iptc_table.chains]

def get_rule(table, chain, position=0, ipv6=False, silent=False):
    """ Get a rule from a chain in a given position. 0=all rules, 1=first, n=nth position """
    try:
        if position == 0:
            # Return all rules
            return dump_chain(table, chain, ipv6=ipv6)
        elif position > 0:
            # Return specific rule by position
            iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
            iptc_rule = iptc_chain.rules[position - 1]
            return _decode_iptc_rule(iptc_rule, ipv6=ipv6)
        elif position < 0:
            # Return last rule  -> not available in iptables CLI
            iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
            iptc_rule = iptc_chain.rules[position]
            return _decode_iptc_rule(iptc_rule, ipv6=ipv6)
    except Exception as e:
        if not silent:
            raise

def replace_rule(table, chain, old_rule_d, new_rule_d, ipv6=False):
    """ Replaces an existing rule of a chain """
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_old_rule = _encode_iptc_rule(old_rule_d, ipv6=ipv6)
    iptc_new_rule = _encode_iptc_rule(new_rule_d, ipv6=ipv6)
    iptc_chain.replace_rule(iptc_new_rule, iptc_chain.rules.index(iptc_old_rule))

def get_rule_statistics(table, chain, rule_d, ipv6=False):
    """ Return a tuple with the rule counters (numberOfBytes, numberOfPackets) """
    if not has_rule(table, chain, rule_d, ipv6=ipv6):
        raise AttributeError('Chain <{}@{}> has no rule <{}>'.format(chain, table, rule_d))
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
    iptc_rule_index = iptc_chain.rules.index(iptc_rule)
    return iptc_chain.rules[iptc_rule_index].get_counters()

def get_rule_position(table, chain, rule_d, ipv6=False):
    """ Return the position of a rule within a chain """
    if not has_rule(table, chain, rule_d):
        raise AttributeError('Chain <{}@{}> has no rule <{}>'.format(chain, table, rule_d))
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
    return iptc_chain.rules.index(iptc_rule)


def test_rule(rule_d, ipv6=False):
    """ Return True if the rule is a well-formed dictionary, False otherwise """
    try:
        _encode_iptc_rule(rule_d, ipv6=ipv6)
        return True
    except:
        return False

def test_match(name, value, ipv6=False):
    """ Return True if the match is valid, False otherwise """
    try:
        iptc_rule = iptc.Rule6() if ipv6 else iptc.Rule()
        _iptc_setmatch(iptc_rule, name, value)
        return True
    except:
        return False

def test_target(name, value, ipv6=False):
    """ Return True if the target is valid, False otherwise """
    try:
        iptc_rule = iptc.Rule6() if ipv6 else iptc.Rule()
        _iptc_settarget(iptc_rule, {name:value})
        return True
    except:
        return False


def repr_all(ipv6=False):
    """ Return a string representation of all tables """
    s = ''
    for table in ['security', 'raw', 'mangle', 'nat', 'filter']:
        s += repr_table(table, ipv6=ipv6)
    return s
    #return '\n'.join(repr_table(table, ipv6=ipv6) for table in ['security', 'raw', 'mangle', 'nat', 'filter'])

def repr_table(table, ipv6=False):
    """ Return a string representation of a table """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    return '\n'.join('[{}]\n{}'.format(c.name, repr_chain(table, c.name)) for c in iptc_table.chains)

def repr_chain(table, chain, ipv6=False, indent = '\t'):
    """ Return a string representation of a chain """
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    return '\n'.join('{}{}'.format(indent, _repr_rule(r, ipv6=ipv6)) for r in iptc_chain.rules)


def dump_all(ipv6=False):
    """ Return a dictionary representation of all tables """
    d = {}
    for table in ['security', 'raw', 'mangle', 'nat', 'filter']:
        d[table] = dump_table(table, ipv6=ipv6)
    return d

def dump_table(table, ipv6=False):
    """ Return a dictionary representation of a table """
    d = {}
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    for iptc_chain in iptc_table.chains:
        d[iptc_chain.name] = dump_chain(iptc_table.name, iptc_chain.name, ipv6=ipv6)
    return d

def dump_chain(table, chain, ipv6=False):
    """ Return a list with the dictionary representation of the rules of a table """
    l = []
    iptc_chain = _iptc_getchain(table, chain, ipv6=ipv6)
    for i, iptc_rule in enumerate(iptc_chain.rules):
        l.append(_decode_iptc_rule(iptc_rule, ipv6=ipv6))
    return l


def batch_begin(table = None, ipv6=False):
    """ Disable autocommit on a table """
    MODE_BATCH = True
    if table:
        tables = (table, )
    else:
        tables = ('security', 'raw', 'mangle', 'nat', 'filter')
    for table in tables:
        iptc_table = _iptc_gettable(table, ipv6=ipv6)
        iptc_table.autocommit = False

def batch_end(table = None, ipv6=False):
    """ Enable autocommit on table and commit changes """
    MODE_BATCH = False
    if table:
        tables = (table, )
    else:
        tables = ('security', 'raw', 'mangle', 'nat', 'filter')
    for table in tables:
        iptc_table = _iptc_gettable(table, ipv6=ipv6)
        iptc_table.autocommit = True

def batch_add_chains(table, chains, ipv6=False, flush=True):
    """ Add multiple chains to a table """
    iptc_table = _batch_begin_table(table, ipv6=ipv6)
    for chain in chains:
        if iptc_table.is_chain(chain):
            iptc_chain = iptc.Chain(iptc_table, chain)
        else:
            iptc_chain = iptc_table.create_chain(chain)
        if flush:
            iptc_chain.flush()
    _batch_end_table(table, ipv6=ipv6)

def batch_delete_chains(table, chains, ipv6=False):
    """ Delete multiple chains of a table """
    iptc_table = _batch_begin_table(table, ipv6=ipv6)
    for chain in chains:
        if iptc_table.is_chain(chain):
            iptc_chain = iptc.Chain(iptc_table, chain)
            iptc_chain.flush()
            iptc_table.delete_chain(chain)
    _batch_end_table(table, ipv6=ipv6)

def batch_add_rules(table, batch_rules, ipv6=False):
    """ Add multiple rules to a table with format (chain, rule_d, position) """
    iptc_table = _batch_begin_table(table, ipv6=ipv6)
    for (chain, rule_d, position) in batch_rules:
        iptc_chain = iptc.Chain(iptc_table, chain)
        iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
        if position == 0:
            # Insert rule in last position -> append
            iptc_chain.append_rule(iptc_rule)
        elif position > 0:
            # Insert rule in given position -> adjusted as iptables CLI
            iptc_chain.insert_rule(iptc_rule, position-1)
        elif position < 0:
            # Insert rule in given position starting from bottom -> not available in iptables CLI
            nof_rules = len(iptc_chain.rules)
            iptc_chain.insert_rule(iptc_rule, position + nof_rules)
    _batch_end_table(table, ipv6=ipv6)

def batch_delete_rules(table, batch_rules, ipv6=False, silent=True):
    """ Delete  multiple rules from  table with format (chain, rule_d) """
    try:
        iptc_table = _batch_begin_table(table, ipv6=ipv6)
        for (chain, rule_d) in batch_rules:
            iptc_chain = iptc.Chain(iptc_table, chain)
            iptc_rule  = _encode_iptc_rule(rule_d, ipv6=ipv6)
            iptc_chain.delete_rule(iptc_rule)
        _batch_end_table(table, ipv6=ipv6)
    except Exception as e:
        if not silent:
            raise


### INTERNAL FUNCTIONS ###
def _iptc_gettable(table, ipv6=False):
    """ Return an updated view of an iptc_table """
    iptc_table = iptc.Table6(table) if ipv6 else iptc.Table(table)
    if MODE_BATCH is False:
        iptc_table.commit()
        iptc_table.refresh()
    return iptc_table

def _iptc_getchain(table, chain, ipv6=False, silent=False):
    """ Return an iptc_chain of an updated table """
    try:
        iptc_table = _iptc_gettable(table, ipv6=ipv6)
        if not iptc_table.is_chain(chain):
            raise AttributeError('Table <{}> has no chain <{}>'.format(table, chain))
        return iptc.Chain(iptc_table, chain)
    except Exception as e:
        if not silent:
            raise

def _iptc_setattr(object, name, value):
    # Translate attribute name
    name = name.replace('-', '_')
    setattr(object, name, value)

def _iptc_setattr_d(object, value_d):
    for name, value in value_d.items():
        _iptc_setattr(object, name, value)

def _iptc_setrule(iptc_rule, name, value):
    _iptc_setattr(iptc_rule, name, value)

def _iptc_setmatch(iptc_rule, name, value):
    # Iterate list/tuple recursively
    if isinstance(value, list) or isinstance(value, tuple):
        for inner_value in value:
            _iptc_setmatch(iptc_rule, name, inner_value)
    # Assign dictionary value
    elif isinstance(value, dict):
        iptc_match = iptc_rule.create_match(name)
        _iptc_setattr_d(iptc_match, value)
    # Assign value directly
    else:
        iptc_match = iptc_rule.create_match(name)
        _iptc_setattr(iptc_match, name, value)

def _iptc_settarget(iptc_rule, value):
    # Target is dictionary - Use only 1 pair key/value
    if isinstance(value, dict):
        for k, v in value.items():
            iptc_target = iptc_rule.create_target(k)
            _iptc_setattr_d(iptc_target, v)
            return
    # Simple target
    else:
        iptc_target = iptc_rule.create_target(value)

def _encode_iptc_rule(rule_d, ipv6=False):
    # Sanity check
    assert(isinstance(rule_d, dict))
    # Basic rule attributes
    rule_attr = ('src', 'dst', 'protocol', 'in-interface', 'out-interface', 'fragment')
    iptc_rule = iptc.Rule6() if ipv6 else iptc.Rule()
    # Avoid issues with matches that require basic parameters to be configured first
    for name in rule_attr:
        if name in rule_d:
            _iptc_setrule(iptc_rule, name, rule_d[name])
    for name, value in rule_d.items():
        try:
            if name in rule_attr:
                #_iptc_setrule(iptc_rule, name, value)
                continue
            elif name == 'target':
                _iptc_settarget(iptc_rule, value)
            else:
                _iptc_setmatch(iptc_rule, name, value)
        except Exception as e:
            #print('Ignoring unsupported field <{}:{}>'.format(name, value))
            continue
    return iptc_rule

def _decode_iptc_rule(iptc_rule, ipv6=False):
    """ Return a dictionary representation of an iptc_rule """
    d = {}
    if ipv6==False and iptc_rule.src != '0.0.0.0/0.0.0.0':
        d['src'] = iptc_rule.src
    elif ipv6==True and iptc_rule.src != '::/0':
        d['src'] = iptc_rule.src
    if ipv6==False and iptc_rule.dst != '0.0.0.0/0.0.0.0':
        d['dst'] = iptc_rule.dst
    elif ipv6==True and iptc_rule.dst != '::/0':
        d['dst'] = iptc_rule.dst
    if iptc_rule.protocol != 'ip':
        d['protocol'] = iptc_rule.protocol
    if iptc_rule.in_interface is not None:
        d['in-interface'] = iptc_rule.in_interface
    if iptc_rule.out_interface is not None:
        d['out-interface'] = iptc_rule.out_interface
    if ipv6 == False and iptc_rule.fragment:
        d['fragment'] = iptc_rule.fragment
    for m in iptc_rule.matches:
        if m.name not in d:
            d[m.name] = m.get_all_parameters()
        elif isinstance(d[m.name], list):
            d[m.name].append(m.get_all_parameters())
        else:
            d[m.name] = [d[m.name], m.get_all_parameters()]
    if iptc_rule.target and iptc_rule.target.name and len(iptc_rule.target.get_all_parameters()):
        name = iptc_rule.target.name.replace('-', '_')
        d['target'] = {name:iptc_rule.target.get_all_parameters()}
    elif iptc_rule.target and iptc_rule.target.name:
        d['target'] = iptc_rule.target.name
    # Return a filtered dictionary
    return _filter_empty_field(d)

def _repr_rule(iptc_rule, ipv6=False):
    """ Return a string representation of an iptc_rule """
    s = ''
    if ipv6==False and iptc_rule.src != '0.0.0.0/0.0.0.0':
        s += 'src {} '.format(iptc_rule.src)
    elif ipv6==True and iptc_rule.src != '::/0':
        s += 'src {} '.format(iptc_rule.src)
    if ipv6==False and iptc_rule.dst != '0.0.0.0/0.0.0.0':
        s += 'dst {} '.format(iptc_rule.dst)
    elif ipv6==True and iptc_rule.dst != '::/0':
        s += 'dst {} '.format(iptc_rule.dst)
    if iptc_rule.protocol != 'ip':
        s += 'protocol {} '.format(iptc_rule.protocol)
    if iptc_rule.in_interface is not None:
        s += 'in {} '.format(iptc_rule.in_interface)
    if iptc_rule.out_interface is not None:
        s += 'out {} '.format(iptc_rule.out_interface)
    if ipv6 == False and iptc_rule.fragment:
        s += 'fragment '
    for m in iptc_rule.matches:
        s += '{} {} '.format(m.name, m.get_all_parameters())
    if iptc_rule.target and iptc_rule.target.name and len(iptc_rule.target.get_all_parameters()):
        s += '-j {} '.format(iptc_rule.target.get_all_parameters())
    elif iptc_rule.target and iptc_rule.target.name:
        s += '-j {} '.format(iptc_rule.target.name)
    return s

def _batch_begin_table(table, ipv6=False):
    """ Disable autocommit on a table """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    iptc_table.autocommit = False
    return iptc_table

def _batch_end_table(table, ipv6=False):
    """ Enable autocommit on table and commit changes """
    iptc_table = _iptc_gettable(table, ipv6=ipv6)
    iptc_table.autocommit = True
    return iptc_table

def _filter_empty_field(data_d):
    """
    Remove empty lists from dictionary values
    Before: {'target': {'CHECKSUM': {'checksum-fill': []}}}
    After:  {'target': {'CHECKSUM': {'checksum-fill': ''}}}
    Before: {'tcp': {'dport': ['22']}}}
    After:  {'tcp': {'dport': '22'}}}
    """
    for k, v in data_d.items():
        if isinstance(v, dict):
            data_d[k] = _filter_empty_field(v)
        elif isinstance(v, list) and len(v) != 0:
            v = [_filter_empty_field(_v) if isinstance(_v, dict) else _v for _v in v ]
        if isinstance(v, list) and len(v) == 1:
            data_d[k] = v.pop()
        elif isinstance(v, list) and len(v) == 0:
            data_d[k] = ''
    return data_d

### /INTERNAL FUNCTIONS ###


# How to use
if __name__== '__main__':
    import uuid
    # Generate chain name
    chain = uuid.uuid4().hex[:10]

    for ipv6 in [False, True]:
        table = 'filter'
        if not has_chain(table, chain, ipv6=ipv6):
            print('Create new chain {}.{} ipv6={}'.format(table, chain, ipv6))
            add_chain(table, chain, ipv6=ipv6)
        else:
            print('Flush existing chain {}.{} ipv6={}'.format(table, chain, ipv6))
            flush_chain(table, chain, ipv6=ipv6)

        rule_d = {'in_interface':'wan0',
                  'protocol':'tcp',
                  'tcp': {'tcp-flags': ['FIN,SYN,RST,ACK', 'SYN']},
                  'conntrack': {'ctstate': ['NEW,RELATED']},
                  'comment':{'comment':'New incoming TCP connection'},
                  'mark':[{'mark': '0x1'},{'mark': '0x2'}],
                  'target':'ACCEPT'}
        # Append new rule
        add_rule(table, chain, rule_d, position=0, ipv6=ipv6)
        # Show chain rules
        print('Display chain {}.{} ipv6={}'.format(table, chain, ipv6))
        print(dump_chain(table, chain, ipv6=ipv6))
        # Show first rule
        print('Display chain 1st rule {}.{} ipv6={}'.format(table, chain, ipv6))
        print(get_rule(table, chain, position=1, ipv6=ipv6))
        # Delete chain
        delete_chain(table, chain, ipv6=ipv6, flush=True)
        print('Display table {} ipv6={}'.format(table, ipv6))
        print(dump_table(table, ipv6=ipv6))
        # Show remaining chains of table
        print('Display table chains {} ipv6={}'.format(table, ipv6))
        print(get_chains(table))
