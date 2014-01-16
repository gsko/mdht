"""
@author Greg Skoczek

This module provides functions for converting in between
python long integers and bencoded integers. A bencoded
integer is one that has been encoded using the 'bencode'
standard as part of BitTorrent.

"""
import socket

from twisted.python import log

from mdht import constants

class InvalidDataError(Exception):
    """
    Signifies that something was wrong with the input data

    @param message: a message describing what went wrong
    @param value: the value that triggered this error

    """
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return ("<InvalidDataError(%s)>" % self.message)

    __str__ = __repr__


def btol(network_order_byte_string):
    """Bdecode an integer"""
    return long(str(network_order_byte_string).encode("hex"), 16)

def ltob(long_number):
    """Bencode an integer"""
    numstring = hex(long_number)[2:].rstrip("L")
    if len(numstring) % 2 == 1:
        numstring = "0%s" % numstring
    return numstring.decode("hex")

def encode_network_id(network_id):
    """
    Encode the network id into the network format
    
    @raises InvalidDataError when the network id is invalid

    """
    if network_id < 0 or network_id >= 2**constants.id_size:
        # TODO print out a nice representation of the ID rather than the real id.
        # give maybe: (1.523 * 2^153)

        error_str = "The network ID:%d  is outside the valid range [0,2**160]"
        log.err(error_str)
        raise InvalidDataError(error_str % network_id)
    encoded_network_id = ltob(network_id)
    return _pad_zeros(encoded_network_id, 20)

def decode_network_id(network_id_string):
    """
    Decode the network id string into a python long network id

    @raises InvalidDataError when the network id string is invalid

    """
    if len(network_id_string) != 20:
        error_msg = 'Network id "%s" has length %d, it should be a length of 20'.format(
                network_id_string, len(network_id_string))
        raise InvalidDataError(error_msg)
    decoded_network_id = btol(network_id_string)
    return decoded_network_id

def decode_port(port_string):
    """
    Decodes the port string into a port integer
    
    @raises InvalidDataError when the port string is invalid
    
    """
    if len(port_string) != 2:
        error_msg = 'Port string "%s" has length %d, it should have length 2'.format(port_string)
        raise InvalidDataError(error_msg)
    return btol(port_string)

def encode_port(port):
    """
    Encodes the port integer into a port string in network format

    Note: this function will pad the resulting output string
    with zeros if the resulting string has a length of 1
    ie: "\xff" becomes "\x00\xff"

    @raises InvalidDataError when the port number is invalid

    """
    # A port is 2 bytes, so 2**16 - 1 is the max value
    if port < 0 or port >= 2**16:
        raise InvalidDataError("The port number is invalid")
    encoded_port = ltob(port)
    return _pad_zeros(encoded_port, 2)

def encode_address(address):
    """
    Encodes the given ipv4 address tuple into a network format string
    
    @throws InvalidAddressError if the input address is invalid
    
    """
    try:
        (ip, port) = address
        ip_string = socket.inet_aton(ip)
        # Make sure that a port's value is padded to two bytes
        # in the encoding, since each address string must
        # take up six bytes for the encoding/decoding to work
        port_string = encode_port(port)
        return "%s%s" % (ip_string, port_string)
    except (socket.error, ValueError):
        error_msg = 'Address "%s" has an invalid format' % str(address)
        log.err(error_msg)
        # TODO choose one of these ways...
        raise InvalidDataError(error_msg)

def decode_address(address_string):
    """
    Decodes the network format ipv4/udp address string into an address tuple
    
    @throws InvalidAddressError if the input address string is invalid
    
    """
    try:
        if len(address_string) != 6:
            error_str = 'Address string "%s" has length %d, it should be 6' % (
                    address_string, len(address_string))
            log.err(error_str)
            raise InvalidDataError(error_str)

        ip = socket.inet_ntoa(address_string[:4])
        port = decode_port(address_string[4:])
        return ip, port
    except (socket.error, TypeError):
        raise InvalidDataError("The address string has an invalid format")
#
# Private
#

def _pad_zeros(string, size):
    """
    Pad string to 'size' with zeros on the left  hand side
    
    ie: _pad_zeros('\xff', 2) becomes '\x00\xff'
    
    """
    num_zeros = size - len(string)
    if num_zeros > 0:
        return ("\x00" * num_zeros) + string
    else:
        return string
