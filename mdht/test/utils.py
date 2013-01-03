"""
Various classes/functions commonly used in testing this package
"""
class Clock(object):
    """
    A drop in replacement for the time.time function

    >>> import time
    >>> time.time = Clock()
    >>> time.time()
    0
    >>> time.time.set(5)
    >>> time.time()
    5
    >>> 

    """
    def __init__(self):
        self._time = 0

    def __call__(self):
        return self.time()

    def time(self):
        return self._time

    def set(self, time):
        self._time = time


class Counter(object):
    """
    Replaces a method with a running counter of how many times it was called

    >>> import time
    >>> time.time = Counter()
    >>> time.time.count
    0
    >>> time.time()
    >>> time.time.count
    1
    >>> time.time.reset()
    >>> time.time.count
    0

    The original method will also be called if it is supplied in the constructor

    """
    def __init__(self, orig_func=None):
        self.count = 0
        self.orig_func = orig_func

    def __call__(self, *args, **kwargs):
        self.count += 1
        if self.orig_func is not None:
            return self.orig_func(*args, **kwargs)

    def reset(self):
        self.count = 0

class HollowTransport(object):
    def __init__(self):
        self.packet = None
        self.address = None

    def write(self, packet, address):
        """
        Remember what packet and address was passed into write and do nothing
        """
        self.packet = packet
        self.address = address

    def _reset(self):
        """
        Resets the HollowTransport so that it appears as if no packet was sent
        """
        self.packet = None
        self.address = None

    def _packet_was_sent(self):
        """
        Check whether a packet has been sent

        In either case, reset the HollowTransport to appear as if
        no packets have been sent

        """
        sent = self.packet != None and self.address != None
        self._reset()
        return sent



class HollowDelayedCall(object):
    def __init__(self):
        self._active = True

    def active(self):
        return self._active

    def cancel(self):
        self._active = False

class HollowReactor(object):
    def callLater(self, timeout, function, *args, **kwargs):
        return HollowDelayedCall()

    def listenUDP(self, port, protocol):
        pass

