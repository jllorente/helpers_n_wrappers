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

# This module contains assorted helper functions that do not fit any specific module

import random, string
def random_string(length):
    """Generate alphanumeric random string of specific length"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for x in range(length))

def center_text(baseline, text):
    """Return a string with the centered text over a baseline"""
    gap = len(baseline) - (len(text) + 2)
    a1 = int(gap / 2)
    a2 = gap - a1
    return '{} {} {}'.format(baseline[:a1], text, baseline[-a2:])

def repr_iterable(iterable, token='\n'):
    """Return a token separated string of joined iterables without index"""
    return '\n'.join('{}'.format(elem) for index, elem in enumerate(iterable))

def repr_iterable_index(iterable, token='\n'):
    """Return a token separated string of joined iterables with index"""
    return '\n'.join('#{}. {}'.format(index, elem) for index, elem in enumerate(iterable))

def repr_iterable_kw(iterable, token='\n'):
    """Return a token separated string of joined iterables keywords without index"""
    return '\n'.join('[{}] {}'.format(key, value) for (key, value) in iterable.items())

def repr_iterable_kw_index(iterable, token='\n'):
    """Return a token separated string of joined iterables keywords with index"""
    return '\n'.join('#{}. [{}] {}'.format(index, key, value) for index, (key, value) in enumerate(iterable.items()))

def hexdump(x):
    """Print a packet dump-like representation of data (str or bytes).
       Ported from scapy."""
    # Define functions
    chb  = lambda x: x if type(x) is str else chr(x)
    orb  = lambda x: ord(x) if type(x) is str else x
    sane = lambda x: ''.join('.' if (orb(i) < 32) or (orb(i) >= 127) else chb(i) for i in x)
    #Do operations
    if type(x) is not str and type(x) is not bytes:
      try:
        x=bytes(x)
      except:
        x = str(x)
    l = len(x)
    i = 0
    while i < l:
        print('%04x  ' % i,end = ' ')
        for j in range(16):
            if i+j < l:
                print('%02X' % orb(x[i+j]), end = ' ')
            else:
                print('  ', end = ' ')
            if j%16 == 7:
                print('', end = ' ')
        print(' ', end = ' ')
        print(sane(x[i:i+16]))
        i += 16

import sys,traceback
def trace():
    """Print exception information and stack trace entries from traceback"""
    print('Exception in user code:')
    print('-' * 60)
    traceback.print_exc(file=sys.stdout)
    print('-' * 60)

def set_attributes(obj, override=False, **kwargs):
    """Set attributes in object from a dictionary"""
    for k,v in kwargs.items():
        if hasattr(obj, k) and not override:
            continue
        setattr(obj, k, v)

def set_default_attributes(obj, args, value=None):
    """Create and initialize to value a number of attributes
       defined in the iterable args"""
    for arg in args:
        if hasattr(obj, arg):
            continue
        setattr(obj, arg, value)

import uuid
def gen_uuid(version=1, *args):
    if version == 1:
        id = uuid.uuid1()
    elif version == 3:
        id = uuid.uuid3(*args)
    elif version == 4:
        id = uuid.uuid4()
    elif version == 5:
        id = uuid.uuid5(*args)
    else:
        raise Exception('UUID version {} not supported'.format(version))
    return id
