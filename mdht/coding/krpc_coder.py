"""
@author Greg Skoczek

Encode and decode functions used in processing KRPCs/packets
originating from and destined to the DHT network

@see mdht.krpc_types for the representation of KRPCs used by mdht

"""
from mdht import contact
from mdht.coding import basic_coder
from mdht.coding.bencode import bdecode, bencode, BTFailure
from mdht.krpc_types import Query, Response, Error

class InvalidKRPCError(Exception):
    """
    Catch-all abstraction error for the encoding/decoding process

    This error will catch errors in the encoding/decoding process
    so that the user of the encode/decode functions can abstract
    the error handling to just this error

    @param invalid_message: the encoded packet or krpc object that caused
        the error

    """
    def __init__(self, invalid_message, exception):
        self.invalid_message = invalid_message
        self.exception = exception

    def __repr__(self):
        return "InvalidKRPCError({0}, {1})".format(self.invalid_message, str(self.exception))
    __str__ = __repr__

def decode(packet):
    """
    Decode the raw network packet into a valid KRPC

    @return an instance of either Query, Response, or Error
    @see mdht.krpc_types
    @raises InvalidKRPCError if the given packet is invalid

   """
    #try:
    dpacket = _decode(packet)
    return dpacket
#    except (ValueError, KeyError, AttributeError, _ProtocolFormatError,
#            basic_coder.InvalidDataError, BTFailure, TypeError) as e:
#        raise InvalidKRPCError(packet, e)
#    else:
#        return dpacket

def encode(message):
    """
    Encode a valid KRPC into a raw network packet ready for transmission

    @return a bencoded representation of the input KRPC message
    @see mdht.krpc_types
    @raises InvalidKRPCError if the given krpc object is invalid

    """
    #try:
    packet = _encode(message)
    return packet
#    except (ValueError, KeyError, AttributeError, _ProtocolFormatError,
#            basic_coder.InvalidDataError, TypeError, BTFailure):
#        raise InvalidKRPCError(message)
#    else:
        #return packet

##
## Private encoding / decoding helper functions
##

class _ProtocolFormatError(Exception):
    """
    Error signifiying invalid krpc options were included in the message

    This exception is thrown when the given protocol message / object
    contains options that do not conform to the BEP5 specification

    @see mdht/references/bep0005.html

    """
    pass

def _decode(packet):
    """@see decode"""
    # Decode the bencoded dict into a python dict
    rpc_dict = bdecode(packet)

    # Decode the message into one of Query/Response/Error (as found
    # in message_types)
    msgtype = rpc_dict["y"]
    message_decoders = {'q': _query_decoder, 
                        'r': _response_decoder,
                        'e': _error_decoder}
    rpc = message_decoders[msgtype](rpc_dict)

    # Attach the transaction id
    rpc._transaction_id = basic_coder.btol(rpc_dict['t'])
    return rpc 

def _query_decoder(rpc_dict):
    """
    Decode the given KRPC dictionary into a valid Query
    
    @see decode
    @return krpc_types.Query

    """
    q = Query()
    q._from = basic_coder.decode_network_id(rpc_dict['a']['id'])
    q.rpctype = rpctype = rpc_dict['q']

    if rpctype == 'ping':
        pass
    elif rpctype == 'find_node':
        q.target_id = basic_coder.decode_network_id(rpc_dict['a']['target'])
    elif rpctype == 'get_peers':
        q.target_id = basic_coder.decode_network_id(rpc_dict['a']['info_hash'])
    elif rpctype == 'announce_peer':
        q.target_id = basic_coder.decode_network_id(rpc_dict['a']['info_hash'])
        # Try encoding the port (to ensure it is within range)
        basic_coder.encode_port(rpc_dict['a']['port'])
        q.port = rpc_dict['a']['port']
        q.token = basic_coder.btol(rpc_dict['a']['token'])
    else:
        raise _ProtocolFormatError()
    return q

def _response_decoder(rpc_dict):
    """
    Decode the given KRPC dictionary into a valid Response

    @see decode
    @return krpc_types.Response

    """
    r = Response()
    # All responses have querier IDs
    r._from = basic_coder.decode_network_id(rpc_dict['r']['id'])
    # find_node always returns a list of nodes
    # get_peers sometimes returns a list of nodes
    if 'nodes' in rpc_dict['r']:
        r.nodes = _decode_nodes(rpc_dict['r']['nodes'])
    # get_peers always returns a list of peers
    if 'values' in rpc_dict['r']:
        r.peers = _decode_addresses(rpc_dict['r']['values'])
    # get_peers returns a token
    if 'token' in rpc_dict['r']:
        r.token = basic_coder.btol(rpc_dict['r']['token'])
    return r

def _decode_addresses(address_string):
    """Decode a concatenated address string into a list of address tuples"""
    addresses = []
    # Each address string has a length of 6
    encoded_addresses = _chunkify(address_string, 6)
    for address_string in encoded_addresses:
        address = basic_coder.decode_address(address_string)
        addresses.append(address)
    return addresses 

def _decode_nodes(node_string):
    """Decode a concatenated node string into a list of nodes"""
    nodes = []
    # Each node string has a length of 26
    encoded_nodes = _chunkify(node_string, 26)
    for node_string in encoded_nodes:
        decoded_node = contact.decode_node(node_string)
        nodes.append(decoded_node)
    return nodes

def _chunkify(string, n):
    """Split the string into n sized chunks"""
    for i in xrange(0, len(string), n):
        yield string[i:i+n]

def _error_decoder(rpc_dict):
    """
    Decode the given KRC dictionary into a valid Error

    @see decode
    @return krpc_types.Error

    """
    e = Error()
    e.code, e.message = rpc_dict['e']
    if e.code not in [201, 202, 203]:
        raise _ProtocolFormatError()
    return e

def _encode(message):
    """@see encode"""
    intermediate_msg = {}
    # Encode and attach the transaction id
    intermediate_msg['t'] = (
            basic_coder.ltob(message._transaction_id))

    # Determine the type of this KRPC
    if isinstance(message, Query):
        intermediate_msg['y'] = 'q'
    elif isinstance(message, Response):
        intermediate_msg['y'] = 'r'
    elif isinstance(message, Error):
        intermediate_msg['y'] = 'e'
    else:
        raise _ProtocolFormatError()

    message_encoders = {'q': _query_encoder,
                        'r': _response_encoder,
                        'e': _error_encoder};
    # Add the additional Query/Response/Error
    # data onto the message
    addition = message_encoders[intermediate_msg['y']](message)
    intermediate_msg.update(addition)
    # Bencode the KRPC dictionary
    encoded_msg = bencode(intermediate_msg)
    return encoded_msg

def _query_encoder(query):
    """@see encode"""
    query_dict = {"q": query.rpctype,
                  "a": { "id": basic_coder.encode_network_id(query._from)}}
    # Perform specific rpc encoding
    if query.rpctype == 'ping':
        pass
    elif query.rpctype == 'find_node':
        query_dict['a']['target'] = (
                basic_coder.encode_network_id(query.target_id))
    elif query.rpctype == 'get_peers':
        query_dict['a']['info_hash'] = (
                basic_coder.encode_network_id(query.target_id))
    elif query.rpctype == 'announce_peer':
        query_dict['a']['token'] = basic_coder.ltob(query.token)
        # Try encoding the port, to see if it is within range
        basic_coder.encode_port(query.port)
        query_dict['a']['port'] = query.port
        query_dict['a']['info_hash'] = (
                basic_coder.encode_network_id(query.target_id))
    else:
        raise _ProtocolFormatError()
    return query_dict

def _response_encoder(response):
    """@see encode"""
    resp_dict = {"r": {"id": basic_coder.encode_network_id(response._from)}}
    if response.nodes is not None:
        encoded_nodes = [contact.encode_node(node) for node in response.nodes]
        resp_dict['r']['nodes'] = "".join(encoded_nodes)
    if response.peers is not None:
        encoded_peers = [basic_coder.encode_address(peer)
                            for peer in response.peers]
        resp_dict['r']['values'] = "".join(encoded_peers)
    if response.token is not None:
        resp_dict['r']['token'] = basic_coder.ltob(response.token)
    return resp_dict

def _error_encoder(error):
    """@see encode"""
    # Verify the error code is in the valid range
    if error.code not in [201, 202, 203]:
        raise _ProtocolFormatError()
    # Make sure the message is actually a string
    error.message = str(error.message)
    err_dict = {"e": [error.code, error.message]}
    return err_dict
