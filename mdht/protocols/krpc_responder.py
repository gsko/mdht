"""
This module encapsulates a twisted protocol encapsulating the core DHT
node functionality.

"""
import time
import random
import hashlib

from collections import deque, defaultdict
from zope.interface import implements, Interface
from twisted.python import log
from twisted.python.components import proxyForInterface

from mdht import constants, contact
from mdht.coding import basic_coder
from mdht.krpc_types import Query
from mdht.protocols.krpc_sender import KRPC_Sender, IKRPC_Sender
from mdht.kademlia.routing_table import TreeRoutingTable

class IKRPC_Responder(IKRPC_Sender):
    """
    KRPC_Sender with better query handling and responses to incoming queries

    This protocol extension forms responses to incoming
    queries with compliance to the BEP 005 specification
    
    """

    def __init__(self, routing_table_class=TreeRoutingTable, node_id=None):
        """Specify a routing table and node_id to anchor this protocol"""

    def ping_Received(self, query, address):
        """
        This method is called when a ping Query has been received.

        Override this method if you want to handle incoming ping queries.
        This implementation responds with a valid ping Response.

        @param query: the ping query that has been received (this query
                      has a .rpctype of "ping")
        @address: the address from which this query originated
        @see DHTBot/references/README for the DHT specification

        """

    def find_node_Received(self, query, address):
        """
        This method is called when a find_node Query has been received.

        Override this method if you want to handle incoming find_node
        queries. This implementation responds with a valid find_node Response

        @param query: the find_node query that has been received (this
                      query has a .rpctpe of "find_node")
        @address: the address from which this query originated
        @see DHTBot/references/README for the DHT specification

        """

    def get_peers_Received(self, query, address):
        """
        This method is called when a get_peers Query has been received.

        Override this method if you want to handle incoming get_peers 
        queries. This implementation responds with a valid get_peers Response

        @param query: the get_peers query that has been received (this
                      query has a .rpctpe of "get_peers")
        @address: the address from which this query originated
        @see DHTBot/references/README for the DHT specification

        """

    def announce_peer_Received(self, query, address):
        """
        This method is called when a announce_peer Query has been received.

        Override this method if you want to handle incoming announce_peer 
        queries. This implementation responds with a valid
        announce_peer Response

        @param query: the announce_peer query that has been received (this
                      query has a .rpctpe of "announce_peer")
        @address: the address from which this query originated
        @see DHTBot/references/README for the DHT specification

        """

    def ping(self, address, timeout=None):
        """
        Send a ping query to the given address

        @param address, timeout: @see the arguments in
            mdht.protocols.krpc_sender.KRPC_Sender.sendQuery
        @returns a Deferred

        """

    def find_node(self, address, node_id, timeout=None):
        """
        Send a find_node query to the given address

        @param node_id: the id of the node we are trying to find
        @param address, timeout: @see the arguments in
            mdht.protocols.krpc_sender.KRPC_Sender.sendQuery
        @returns a Deferred

        """

    def get_peers(self, address, target_id, timeout=None):
        """
        Send a get_peers query to the given address

        @param target_id: the infohash for which we are trying to get peers
        @param address, timeout: @see the arguments in
            mdht.protocols.krpc_sender.KRPC_Sender.sendQuery
        @returns a Deferred

        """

    def announce_peer(self, address, target_id, token, port, timeout=None):
        """
        Send an announce_peer query to the given address

        @param target_id: the infohash of the content that this
            DHT node is performing a put/announce on
        @param token: the token used to validate this announce_peer
            query. This token should have been returned in a response
            to a recent get_peers query
        @param port: the port on this host on which to announce
            that there is a BitTorrent peer sharing the content
            identified by target_id
        @param address, timeout: @see the arguments in
            mdht.protocols.krpc_sender.KRPC_Sender.sendQuery
        @returns a Deferred

        """

class KRPC_Responder(KRPC_Sender):

    implements(IKRPC_Responder)

    def __init__(self,
            routing_table_class=TreeRoutingTable,
            node_id=None,
            _reactor=None):

        if node_id is None:
            node_id = random.getrandbits(160)

        # Verify the node_id is valid
        basic_coder.encode_network_id(node_id)
        KRPC_Sender.__init__(self, routing_table_class, node_id, _reactor)

        # Datastore is used for storing peers on torrents
        self._datastore = defaultdict(set)
        self._token_generator = _TokenGenerator()

    def ping_Received(self, query, address):
        # The ping response needs no additional protocol
        # data, so build_response() is empty
        response = query.build_response()
        self.sendResponse(response, address)

    def find_node_Received(self, query, address):
        target_node = self.routing_table.get_node(query.target_id)
        # If we have the target node, return it
        # otherwise return the nodes closest to the target ID
        if target_node is not None:
            nodes = [target_node]
        else:
            nodes = self.routing_table.get_closest_nodes(query.target_id)
        # Include the nodes in the response
        response = query.build_response(nodes=nodes)
        self.sendResponse(response, address)

    def get_peers_Received(self, query, address):
        nodes = None
        peers = self._datastore.get(query.target_id) or list()
        # Check if we have peers for the target infohash
        # If we don't, return the closest nodes in our routing table instead
        dont_have_peers = len(peers) == 0
        if dont_have_peers:
            peers = None
            nodes = self.routing_table.get_closest_nodes(query.target_id)
        # Generate a token that we can recalculate
        # later (upon receiving an announce_peer query
        token = self._token_generator.generate(query, address)
        # Attach the peers, nodes, and token to the response message
        response = query.build_response(nodes=nodes, peers=peers, token=token)
        self.sendResponse(response, address)

    def announce_peer_Received(self, query, address):
        token = query.token
        token_is_valid = self._token_generator.verify(query, address, token)
        if token_is_valid:
            # If the token is valid, we authenticate
            # the querying node to store itself as a peer
            # in our datastore
            node_ip, node_port = address
            peer_address = (node_ip, query.port)
            self._datastore[query.target_id].add(peer_address)
            # announce_peer responses have no additional
            # data (and serve just as a confirmation)
            response = query.build_response()
            self.sendResponse(response, address)
        else:
            log.msg("Invalid token/query/querier combination in"
                    " announce_peerReceived")

    def ping(self, address, timeout=None):
        timeout = timeout or constants.rpctimeout
        query = Query()
        query.rpctype = "ping"
        return self.sendQuery(query, address, timeout)

    def find_node(self, address, node_id, timeout=None):
        timeout = timeout or constants.rpctimeout
        query = Query()
        query.rpctype = "find_node"
        query.target_id = node_id
        return self.sendQuery(query, address, timeout)

    def get_peers(self, address, target_id, timeout=None):
        timeout = timeout or constants.rpctimeout
        query = Query()
        query.rpctype = "get_peers"
        query.target_id = target_id
        return self.sendQuery(query, address, timeout)

    def announce_peer(self, address, target_id, token, port, timeout=None):
        timeout = timeout or constants.rpctimeout
        query = Query()
        query.rpctype = "announce_peer"
        query.target_id = target_id
        query.token = token
        query.port = port
        return self.sendQuery(query, address, timeout)

class _TokenGenerator(object):
    """
    Generate unique tokens in response to get_peers requests

    This token generator does not keep track of tokens that have
    been issued. Rather, this generator deterministically hashes
    the correct token given the get_peers query and address along
    with a secret that changes every constants._secret_timeout seconds

    """
    def __init__(self, hash_constructor=hashlib.sha1):
        """Use the specified hash constructor for hashing"""
        self.hash_constructor = hash_constructor
        num_secrets = constants.token_timeout / constants._secret_timeout
        self.secrets = deque(maxlen=num_secrets)
        # Set the time to 0 so that the first generate() call
        # will force an update of the secrets
        self.last_secret_time = 0

    def generate(self, query, address):
        """
        Create a hash value for the get_peers/announce_peer query and address
        
        @param query: The query to hash
        @param address: The address of the querying node
        
        """
        # Remove timed out secrets
        self._prune_secrets()
        time_since_last_secret = time.time() - self.last_secret_time
        if (time_since_last_secret >= constants._secret_timeout or
                len(self.secrets) == 0):
            self.secrets.appendleft(self._new_secret())

        self.last_secret_time = time.time()
        return self._get_hash(query, address, self.secrets[0])

    def verify(self, query, address, token):
        """
        Verify that the token is one that we could have generated

        @return boolean indicating whether the supplied token
        is valid and should be accepted

        """
        self._prune_secrets()
        for secret in self.secrets:
            hashed_token = self._get_hash(query, address, secret)
            if hashed_token == token:
                return True
        return False

    def _get_hash(self, query, address, secret):
        """
        Create the hash code for the given query/address/secret combination
        """
        node_id = query._from
        infohash = query.target_id
        hash = self.hash_constructor()
        # The hash code relies on the querying node's ID,
        # the target infohash of the query, the address of
        # the querier, and a secret that changes every
        # constants._secret_timeout seconds
        hash.update(basic_coder.encode_network_id(node_id))
        hash.update(basic_coder.encode_network_id(infohash))
        hash.update(basic_coder.encode_address(address))
        hash.update(secret)
        # Return the hash as a number rather than a string
        numeric_hash_value = basic_coder.btol(hash.digest())
        return numeric_hash_value

    def _new_secret(self):
        """Generate a random number of size atleast that of the digest"""
        hash = self.hash_constructor()
        secret_size = hash.digest_size
        # Digest size is in bytes
        return str(random.getrandbits(secret_size * 8))

    def _prune_secrets(self):
        """Remove all secrets that are older than a token timeout"""
        time_since_last_secret = time.time() - self.last_secret_time
        num_stale_secrets = long(round(time_since_last_secret /
                                       constants.token_timeout))
        while (num_stale_secrets > 0) and (len(self.secrets) > 0):
            num_stale_secrets -= 1
            self.secrets.pop()
