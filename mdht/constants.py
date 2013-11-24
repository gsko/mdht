# k as used in Kademlia
k = 8

# The size of the identification number used for resources and
# nodes in the Kademlia network (bits)
id_size = 160

# Time after which an RPC will timeout and fail (seconds)
rpctimeout = 30

# Time after which a high level query (as used in the SimpleNodeProtocol)
# should timeout (seconds)
query_timeout = 60           # 1 minute

# Quarantine timeout: time after which a node is removed from the quarantine
# (seconds)
quarantine_timeout = 180    # 3 minutes

# Peer timeout
# Time after which a peer that has been announced for a torrent will be
# removed from the torrent dictionary (unless reset by being reannounced)
# (seconds)
peer_timeout = 43200        # 12 hours

# Time after which a node is considered stale (seconds)
node_timeout = 900         # 15 minutes

# Time between each call to the NICE routing table update algorithm (seconds)
NICEinterval = 6

# This interval determines how often the DHT's state data will be
# saved into a file on disk (seconds)
DUMPinterval = 180          # 3 minutes

# Size of the token (bits)
tokensize = 32

# Time in seconds after which an offered token (in response to get_peers)
# will be terminated
token_timeout = 600         # 10 minutes

# Transaction ID size (bits)
transaction_id_size = 32

# Failcount threshold: The number of KRPCs a node can fail before being
# being remove from the routing table (int)
failcount_threshold = 3

# Closeness threshold: The notion that determines whether we are close
# enough to a node to announce_peer() for example
# Number of common prefix bits (number in range 0 to 160)
#closeness_threshold = 130

# Bootstrap node
bootstrap_addresses = [("127.0.0.1", 2323),
                   ("67.18.187.143", 1337),
                   ("dht.transmissionbt.com", 6881),
                   ("router.utorrent.com", 6881)]


# Global outgoing bandwidth limit (bytes / second)
global_bandwidth_rate = 20 * 1024   # 20 kilobytes

# Outgoing bandwidth limit per host (bytes / second)
host_bandwidth_rate = 5 * 1024      # 5 kilobytes


# The default port on which DHTBot will run
dht_port = 1800

###
### Internal use
###

# Time for which the secret used for token
# generation is changed (this should be greater than or
# equal to the token_timeout
#
# Note: For proper functionality, token_timeout should
# be a multiple of _secret_timeout
_secret_timeout = 5 * 60    # 5 minutes
