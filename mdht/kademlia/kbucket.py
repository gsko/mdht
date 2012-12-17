"""
@author Greg Skoczek

Implementation of a KBucket that is modeled after the
kademlia reference paper and the BitTorrent DHT BEP
@see mdht/references

"""
from twisted.python import log

from mdht import constants

class KBucketError(Exception):
    """
    Exception raised for any inputs that would lead to
    unspecified behavior in the KBucket

    func: a string with the violating function
    msg:  the output warning/error message
    value: the function arguments (including optional arguments)
           that caused the error (in tuple form)

    """
    def __init__(self, func, msg, value):
        self.func = func
        self.msg = msg
        self.value = value
    def __str__(self):
        return "KBucketError: Error '%s' in function '%s'" % (
                self.func, self.msg)


class KBucket(object):
    """
    Defines a KBucket.

    Each KBucket has a minimum and maximum range for node IDs
    that it will accept. These KBuckets will accept [range_min, range_max).
    For example, a KBucket with range_min = 2, range_max = 4, will
    accept nodes with IDs of 2 and 3 (a node ID of 4 will NOT be accepted)

    Each KBucket also has a maxsize, which determines the maximum
    number of nodes that this KBucket will hold

    """
    def __init__(self, range_min, range_max, maxsize=constants.k):
        self._nodes = set()
        if range_min >= range_max:
            raise KBucketError("__init__",
                              "range_min is greater than or" +
                              "equal to range_max",
                              (range_min, range_max, maxsize))
        self.range_min = range_min
        self.range_max = range_max
        self.maxsize = maxsize

    def offer_node(self, node):
        """
        Offers the given node to the KBucket for storing.

        A KBucket will take a node if and only if its ID
        falls into the KBucket's range and either there is atleast
        one free slot, or this node is better than an existing
        node found in the KBucket

        Note: if `node' is already in this KBucket, True will be returned

        @throws BucketError when the given node's ID does not
        fall into the range of this KBucket

        @returns boolean that tells whether this KBucket accepted
        the node or not

        """
        if not self.key_in_range(node.node_id):
            raise KBucketError("offer_node",
                               "The given node has an ID that does" +
                               " not fall into the range of this KBucket",
                               (node,))
        if node in self._nodes:
            return True

        if self.full():
            worst_node = self._get_worst_node()
            if node.better_than(worst_node):
                self.remove_node(worst_node)
            else:
                return False

        self._nodes.add(node)
        return True

    def splittable(self):
        """Tells whether this KBucket covers enough range to split"""
        new_width = (self.range_max - self.range_min) / 2
        return new_width > 2

    def split(self):
        """
        Distribute this KBucket's nodes into new two KBuckets

        Two new KBuckets are created. The nodes of this KBucket are
        then distributed accordingly. Each newly created KBucket
        is of the same maxsize and covers half of the range
        of the existing KBucket. This KBucket's maxsize
        is set to 0

        @returns tuple of the new KBuckets (lbucket, rbucket), where
        lbucket covers the left half of the existing range and
        rbucket covers the right half of the existing range

        @throws KBucketError when this KBucket is not wide enough to split
        (ie it does not cover enough range to split)

        @see splittable

        """
        if not self.splittable():
            raise KBucketError("split",
                    "This KBucket is not wide enough to split", ())

        # Make two new KBuckets of equal size,
        # each covering half the range of the current KBucket
        new_width = (self.range_max - self.range_min) / 2
        lbucket = KBucket(range_min=self.range_min,
                          range_max=(self.range_min + new_width),
                          maxsize=self.maxsize)
        rbucket = KBucket(range_min=(self.range_min + new_width),
                          range_max=self.range_max,
                          maxsize=self.maxsize)

        self._distribute_nodes(lbucket, rbucket)
        self.maxsize = 0
        return (lbucket, rbucket)

    def key_in_range(self, key):
        """
        Tells whether the given key fits

        The key fits into the range of the KBucket when it
        satistifes: range_min <= key < range_max

        """
        return self.range_min <= key < self.range_max

    def remove_node(self, node):
        """
        Removes the given node from the KBucket

        Nothing happens if the node
        is not found in the KBucket

        @returns boolean describing whether the given
        node was found in the KBucket during the removal

        """
        if node in self._nodes:
            self._nodes.remove(node)
            return True
        return False

    def get_nodes(self):
        """
        Returns an iterable containing the nodes in this KBucket
        
        """
        return set(self._nodes)

    def full(self):
        return len(self._nodes) == self.maxsize

    def get_stalest_node(self):
        """
        Returns the node that has been refreshed the longest time ago
        
        If this KBucket is empty, None is returned
        
        """
        if self.empty():
            return None
        return min(self._nodes, key = lambda node: node.last_updated)

    def empty(self):
        """Tells whether this kbucket is empty"""
        return len(self._nodes) == 0

    def _get_worst_node(self):
        """
        Returns the worst node found in our kbucket
        
        The quality of a node is determined by
        the `better_than' function
        @see mdht.contact.Node.better_than

        """
        worst_node = self._nodes.pop()
        self._nodes.add(worst_node)
        for node in self._nodes:
            if worst_node.better_than(node):
                worst_node = node
        return worst_node

    def _distribute_nodes(self, lbucket, rbucket):
        while len(self._nodes) > 0:
            node = self._nodes.pop()
            if lbucket.key_in_range(node.node_id) and not lbucket.full():
                lbucket.offer_node(node)
            elif rbucket.key_in_range(node.node_id) and not rbucket.full():
                rbucket.offer_node(node)
            else:
                log.msg("While splitting a KBucket, we threw away a node")
