#!/usr/bin/env python3

import netfilterqueue
from netfilterqueue import NetfilterQueue
import asyncio
import functools
import logging
import sys

class NFQueue3(object):
    def __init__(self, queue, cb, *cb_args, **cb_kwargs):
        self.logger = logging.getLogger('NFQueue3#{}'.format(queue))
        self.logger.info('Bind queue #{}'.format(queue))
        self._loop = asyncio.get_event_loop()
        self.queue = queue
        # Use packet counter
        self.counter = 0
        # Create NetfilterQueue object
        self._nfqueue = netfilterqueue.NetfilterQueue()
        # Bind to queue and register callbacks
        self.cb = cb
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs
        self._nfqueue.bind(self.queue, self._nfcallback)
        # Register queue with asyncio
        self._nfqueue_fd = self._nfqueue.get_fd()
        # Create callback function to execute actual nfcallback
        cb2 = functools.partial(self._nfqueue.run, block=False)
        self._loop.add_reader(self._nfqueue_fd, cb2)

    def _nfcallback(self, pkt):
        self.counter += 1
        if self.cb is None:
            data = pkt.get_payload()
            self.logger.debug('Received ({} bytes): {}'.format(len(data), data))
            pkt.accept()
            return

        cb, args, kwargs = self.cb, self.cb_args, self.cb_kwargs
        cb(pkt, *args, **kwargs)

    def set_callback(self, cb, *cb_args, **cb_kwargs):
        self.logger.info('Set callback to {}'.format(cb))
        self.cb = cb
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs

    def terminate(self):
        self.logger.info('Unbind queue #{}: received {} pkts'.format(self.queue, self.counter))
        self._loop.remove_reader(self._nfqueue_fd)
        self._nfqueue.unbind()

if __name__ == '__main__':
    # Configure logging
    log = logging.getLogger('')
    format = logging.Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(format)
    log.addHandler(ch)
    log.setLevel(logging.INFO)
    # Instantiate loop
    loop = asyncio.get_event_loop()
    # Create NFQueue3 objects
    queues = []
    for n in sys.argv[1:]:
        queues.append(NFQueue3(int(n), None))
    try:
        loop.run_forever()
    except:
        pass
    for q in queues:
        q.terminate()
    loop.close()
