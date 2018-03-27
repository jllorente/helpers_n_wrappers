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

from asyncio import Queue

class AsyncSocketQueue(object):
    """
    This class attempts to solve the bug found with loop.sock_recv() used via asyncio.wait_for()
    It uses a simple internal asyncio.Queue() to store the received messages of a *connected socket*
    """
    def __init__(self, sock, loop, queuesize=0, msgsize=1024):
        self._sock = sock
        self._loop = loop
        self._queue = Queue(maxsize=queuesize, loop=loop)
        # Register reader in loop
        self._sock.setblocking(False)
        self._loop.add_reader(self._sock.fileno(), AsyncSocketQueue._recv_callback, self._sock, self._queue, msgsize)

    def _recv_callback(sock, queue, msgsize):
        # Socket is read-ready
        queue.put_nowait(sock.recv(msgsize))

    async def recv(self):
        data = await self._queue.get()
        self._queue.task_done()
        return data

    async def sendall(self, data):
        await self._loop.sock_sendall(self._sock, data)

    def close(self):
        # Deregister reader in loop
        self._loop.remove_reader(self._sock.fileno())
        self._sock.close()
        del self._sock
        del self._queue
