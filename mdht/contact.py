"""
@author Greg Skoczek

Objects used to encapsulate the identity of DHT nodes

"""
import time
import sys
import socket
from socket import inet_aton, inet_ntoa

from mdht.coding import basic_coder
from mdht import constants

def encode_node(node):
    """
    Encodes the given node into a network string

    The format of the network string is specified in the
    BitTorrent DHT extension specification

    @see DHTBot/references/README for the DHT BEP

    """
    return "%s%s" % (basic_coder.encode_network_id(node.node_id),
                     basic_coder.encode_address(node.address))

def decode_node(node_string):
    """
    Decodes a network string into a Node object

    @see encode_node for the format of this network string

    """
    node_id = basic_coder.decode_network_id(node_string[:20])
    address = basic_coder.decode_address(node_string[20:])
    return Node(node_id, address)

class Node(object):
    def __init__(self, node_id, address):
        # Verify the node_id and address are in the proper format
        basic_coder.encode_address(address)
        basic_coder.encode_network_id(node_id)
        # Network information
        self.node_id = node_id
        self.address = address
        # Statistical information
        self.last_updated = time.time()
        self.totalrtt = 0
        self.successcount = 0
        self.failcount = 0

    def distance(self, node_id):
        return node_id ^ self.node_id

    def successful_query(self, origin_time):
        """
        Register that a query has completed successfully

        This function records that a query originating at origin_time
        has been responded to with a properly formatted response. This
        time difference is used to contribute to the calculation of the RTT

        """
        self._touch(origin_time)
        self.successcount += 1

    # TODO what about timed out queries, are they "failed"
    # what about the rtt then?
    def failed_query(self, origin_time):
        """
        Register that a query has failed

        This function behaves just as successful_query(), with the
        exception that the query has failed (either it has timed out,
        or an error message was received instead of a response)
        @see successful_query

        """
        self._touch(origin_time)
        self.failcount += 1

    # TODO make another function, something like
    # "preferably_evict" so that we know whether we should
    # remove a node based on more factors than just freshness
    def fresh(self):
        """
        Tells whether this node is `fresh'

        Freshness is determined by comparing the time the last query
        response (or error) was received to constants.node_timeout
        @see mdht.constants
        @returns boolean
        
        """
        current_time = time.time()
        age = current_time - self.last_updated
        return age < constants.node_timeout

    def better_than(self, other_node):
        """
        Tells whether this node is preferable to the other_node
        """
        if self.fresh() and not other_node.fresh():
            return True

        better_rtt = self._rtt() < other_node._rtt()
        if self.fresh() and better_rtt:
            return True

        return False

    def _rtt(self):
        """
        Tell this nodes average Round Trip delay Time

        The RTT is determined by calculating the total rtt of each query
        and dividing it by the number of successful queries. In this way,
        the rtt increases significantly for each failed query

        """
        total_reply_count = self.successcount + self.failcount
        if total_reply_count == 0:
            return sys.maxint
        return self.totalrtt / total_reply_count


    def _touch(self, origin_time):
        current_time = time.time()
        self.last_updated = current_time
        self.totalrtt += current_time - origin_time

    def __eq__(self, other):
        return not self.__ne__(other)

    def __hash__(self):
        return basic_coder.btol(encode_node(self))

    def __ne__(self, other):
        return other.__hash__() ^ self.__hash__()

    def __repr__(self):
        return "%s last_updated=%d successcount=%d failcount=%d" % (
                self.__str__(), self.last_updated, self.successcount,
                self.failcount)

    def __str__(self):
        return "node: id=(%d) address=(%s)" % (
            self.node_id, address_str(self.address))

def address_str(address):
    return "ip=%s port=%d" % address

