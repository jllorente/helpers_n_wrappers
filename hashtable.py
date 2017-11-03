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
##                            h a s h t a b l e                         ##
##########################################################################

# This module defines a basic HashTable

class HashTable:
    """ Hash table that uses any hashable object for keys and any object for value """

    def __init__(self, buckets=1024):
        """
        Create a table with number of buckets.
        Arrays are implemented with lists.
        Data structures are mutable lists to allow node update.
        """
        self.buckets = buckets
        self._keys = []
        self._size = 0
        self.data = [[] for _ in range(0, buckets)]

    def _hash(self, key, size):
        return hash(key) % size

    def _lookup_by_key(self, key):
        # Calculate index based on key hash
        index = self._hash(key, self.buckets)
        # Get hash table row of entries
        ht_row = self.data[index]
        item = None
        for _item in ht_row:
            if _item[0] == key:
                item = _item
                break
        return (ht_row, item)

    def add(self, key, node, overwrite=True):
        """ Add object with hashable key into the hash table.
        If key exists, it may raise a KeyError. """
        ht_row, item = self._lookup_by_key(key)
        if item is not None and overwrite is False:
            raise KeyError('Key already exists key="{}" item="{}"'.format(key, node))
        elif item is not None:
            # Update node in hash table
            item[1] = node
        else:
            # Add node to hash table
            ht_row.append([key, node])
            self._size += 1
            self._keys.append(key)
        return self

    def get(self, key):
        """ Get an object with key from the hash table.
        If not found, it will raise a KeyError. """
        ht_row, item = self._lookup_by_key(key)
        if item is None:
            raise KeyError('Key not found "{}"'.format(key))
        return item[1]

    def remove(self, key):
        """ Remove and return an object with key from the hash table.
        If not found, it will raise a KeyError. """
        ht_row, item = self._lookup_by_key(key)
        if item is None:
            raise KeyError('Key not found "{}"'.format(key))

        ht_row.remove(item)
        self._keys.remove(key)
        self._size -= 1
        return item[1]

    def dump(self, verbose=False):
        s = ''
        for index, ht_row in enumerate(self.data):
            if verbose or len(ht_row):
                s += '[{}]\n'.format(index)
            for subindex, item in enumerate(ht_row):
                s += '\t[{}] {}\n'.format(subindex, item)
        return s

    # Implement Python's dictionary interface
    def keys(self):
        return self._keys

    def __setitem__(self, key, value):
        self.add(key, value, overwrite=True)

    def __getitem__(self, key):
        return self.get(key)

    def __delitem__(self, key):
        return self.remove(key)

    def __len__(self):
        return self._size

    def __repr__(self):
        return '{{ {} }}'.format(', '.join(['{}:{}'.format(k, self.get(k)) for k in self._keys]))


if __name__ == "__main__":
    # Create hash table
    ht = HashTable(2)
    # Add several items
    ht.add('one', 1)
    ht.add('two', 2).add('three', 3)
    ht['four'] = 4
    # Replace an item
    ht['three'] = 'threeeee!'
    print('{} items / {}'.format(len(ht), ht))
    print(ht.dump(verbose=True))
    # Remove an item
    del ht['three']
    ht.remove('two')

    try:
        ht.add('one', 'oneeee', overwrite=False)
    except Exception as e:
        print('{}'.format(e))

    print('{} items / {}'.format(len(ht), ht))
    print(ht.dump(verbose=False))

    """
    buckets = 1024*64
    ht = HashTable(buckets)
    %timeit [ht.add(str(i), i) for i in range(0,4096)]
    %timeit [ht.add(str(i), i) for i in range(0,8192)]
    %timeit [ht.add(str(i), i) for i in range(0,16384)]
    """
