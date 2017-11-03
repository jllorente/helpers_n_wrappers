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

##########################################################################
##                             c o n t a i n e r 3                      ##
##########################################################################

# This module defines a generic Container class and ContainerNode unit

import logging

LOGLEVELCONTAINER = logging.INFO
LOGLEVELNODE = logging.INFO


class Container(object):

    def __init__(self, name='Container', loglevel=LOGLEVELCONTAINER, datatype='set'):
        """
        Initialize the Container.
        Added datatype parameter to select from list or set.
            Use set for higher performance
            Use list for preserving insertion order
        """
        self._version = 0.7
        self._logger = logging.getLogger(name)
        self._logger.setLevel(loglevel)
        self._name = name
        self._dict = {}             # Indexes lookup keys to nodes
        self._dict_id2keys = {}     # Indexes node ids to registered keys

        if datatype == 'list':
            self._nodes = []         # Stores a list of indexed nodes
            self._gen_datatype = lambda: []
            self._add_datatype = lambda x,data: x.append(data)
            self._remove_datatype = lambda x,data: x.remove(data)
        elif datatype == 'set':
            self._nodes = set()      # Stores a set of indexed nodes
            self._gen_datatype = lambda: set()
            self._add_datatype = lambda x,data: x.add(data)
            self._remove_datatype = lambda x,data: x.remove(data)
        else:
            raise Exception('Datatype "{}" not supported!'.format(datatype))

    def _add_lookupkeys(self, node, keys):
        for key, isunique in keys:
            # The key is not unique - create a storage of items for key
            if not isunique:
                if key not in self._dict:
                    self._dict[key] = self._gen_datatype()
                self._add_datatype(self._dict[key], node)
            # Check the unique key is not already in use
            elif key in self._dict:
                raise KeyError('Failed to add: key {} already exists for node {}'.format(key, self._dict[key]))
            # Add the unique key to the dictionary
            else:
                self._dict[key] = node

    def _remove_lookupkeys(self, node, keys):
        for key, isunique in keys:
            # The key is not unique - remove from stored items for key
            if not isunique:
                self._logger.debug('Removed shared key {} of node {}'.format(key, node))
                self._remove_datatype(self._dict[key], node)
                # The storage has no more items, remove it
                if len(self._dict[key]) == 0:
                    del self._dict[key]
            # Check the unique key is already in use
            elif key not in self._dict:
                raise KeyError('Failed to remove: key {} does not exists for node {}'.format(key, node))
            # Add the unique key to the dictionary
            else:
                self._logger.debug('Removed unique key {} of node {}'.format(key, node))
                del self._dict[key]

    def add(self, node):
        """
        Add a ContainerNode to the Container.

        @param node: The node
        """
        if node in self._nodes:
            raise Exception('Failed to add: node already exists {}'.format(node))

        # Register node lookup keys
        keys = node.lookupkeys()
        self._add_lookupkeys(node, keys)
        # Map node id to lookup keys
        self._dict_id2keys[id(node)] = keys
        # Add node to the storage
        self._add_datatype(self._nodes, node)
        self._logger.debug('Added node {}'.format(node))

    def get(self, key, update=False):
        """
        Obtain a node with the given key.

        @param key: The values of the node.
        @param update: If activated, update the node.
        @return: The node node or KeyError if not found
        """
        node = self._dict[key]
        if update and isinstance(node, ContainerNode):
            node.update()
        return node

    def getall(self):
        """
        Returns a shallow copy of the internal storage
        """
        return list(self._nodes)

    def has(self, key, check_expire=True):
        """
        Check if there is a node with the given key

        @param key: The values of the node.
        @param check_expire: If activated, check for expired node.
        @return: True if there is a node.
        """
        try:
            node = self._dict[key]
            if not isinstance(node, ContainerNode):
                return True
            if check_expire and node.hasexpired():
                self.remove(node)
                return False
            return True
        except KeyError:
            return False

    def lookup(self, key, update=True, check_expire=True):
        """
        Look up a node with the given key.

        @param key: The values of the node.
        @param update: If activated, update the node.
        @param check_expire: If activated, check for expired node.
        @return: The node node.
        """
        try:
            node = self._dict[key]
            if not isinstance(node, ContainerNode):
                return node
            if check_expire and node.hasexpired():
                self.remove(node)
            if update:
                node.update()
            return node
        except KeyError:
            return None

    def remove(self, node, callback=True):
        """
        Remove an node from the Storage node.

        @param node: The node
        """
        # Remove node lookup keys
        keys = node.lookupkeys()
        self._remove_lookupkeys(node, keys)
        # Remove map node id to lookup keys
        del self._dict_id2keys[id(node)]
        # Remove node from the storage
        self._remove_datatype(self._nodes, node)
        self._logger.debug('Removed node {}'.format(node))
        # Evaluate callback to ContainerNode item
        if callback:
            self._logger.debug('Delete callback for node {}'.format(node))
            node.delete()

    def removeall(self, callback=True):
        # Iterate all nodes in the storage and remove them
        for node in self.getall():
            self.remove(node, callback)
        # Sanity clear
        self._dict_id2keys.clear()
        self._dict.clear()
        self._nodes.clear()

    def updatekeys(self, node):
        # Get lookup keys
        old_keys = self._dict_id2keys[id(node)]
        new_keys = node.lookupkeys()
        # Remove previous keys
        self._remove_lookupkeys(node, old_keys)
        # Remove map node id to lookup keys
        del self._dict_id2keys[id(node)]
        # Register node lookup keys
        self._add_lookupkeys(node, new_keys)
        # Map node id to lookup keys
        self._dict_id2keys[id(node)] = new_keys
        self._logger.debug('Updated keys for node {}'.format(node))

    def __len__(self):
        """ Returns the length of the internal list node """
        return len(self._nodes)

    def __repr__(self):
        return '{} ({} items)'.format(self._name, len(self))

    def dump(self):
        return '\n'.join(['#{} {}'.format(i+1, node.dump()) for i, node in enumerate(self._nodes)])


class ContainerNode(object):

    def __init__(self, name='ContainerNode', loglevel=LOGLEVELNODE):
        """ Initialize the ContainerNode """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(loglevel)
        self._name = name

    def lookupkeys(self):
        """ Return the lookup keys of the node """
        key = self._name
        isunique = True
        return ((key, isunique),)

    def hasexpired(self):
        """ Return True if the TTL of the node has expired """
        return False

    def update(self):
        """
        Perform additional actions when the node is being updated.
        """
        pass

    def delete(self):
        """
        Perform additional actions when the node is being deleted.
        """
        pass

    def dump(self):
        """
        Return a string representation of the node.
        """
        return ''

    def __repr__(self):
        return self._name


if __name__ == "__main__":
    ct = Container()
    cn1 = ContainerNode('cn1')
    ct.add(cn1)
    cn2 = ContainerNode('cn2')
    ct.add(cn2)
    ct.removeall()
    print(ct)
