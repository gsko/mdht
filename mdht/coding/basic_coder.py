"""
@author Greg Skoczek

This module provides functions for converting in between
python long integers and bencoded integers. A bencoded
integer is one that has been encoded using the 'bencode'
standard as part of BitTorrent.

"""
import socket

from mdht import constants

class InvalidDataError(Exception):
    """
    Signifies that something was wrong with the input data

    @param message: a message describing what went wrong
    @param value: the value that triggered this error

    """
    def __init__(self, message, value):
        self.message = message
        self.value = value

    def __repr__(self):
        return ("<InvalidDataError(%s, %s)>" % (self.message, self.value))

    __str__ = __repr__


def btol(network_order_byte_string):
    """Convert the bencoded int into a python long"""
    return long(str(network_order_byte_string).encode("hex"), 16)

def ltob(long_number):
    """Convert a python long into a bencoded int"""
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
        raise InvalidDataError(
                "The network ID's value falls out of the valid range",
                network_id)
    encoded_network_id = ltob(network_id)
    return _pad_zeros(encoded_network_id, 20)

def decode_network_id(network_id_string):
    """
    Decode the network id string into a python long network id

    @raises InvalidDataError when the network id string is invalid

    """
    if len(network_id_string) != 20:
        raise InvalidDataError(
                "The network id string has an improper length",
                network_id_string)
    decoded_network_id = btol(network_id_string)
    return decoded_network_id

def decode_port(port_string):
    """
    Decodes the port string into a port integer
    
    @raises InvalidDataError when the port string is invalid
    
    """
    if len(port_string) != 2:
        raise InvalidDataError(
                "The port string is too short or too long",
                port_string)
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
        raise InvalidDataError(
                "The port number is invalid",
                port)
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
        raise InvalidDataError(
                "The address had an invalid format",
                address)

def decode_address(address_string):
    """
    Decodes the network format ipv4 address string into an address tuple
    
    @throws InvalidAddressError if the input address string is invalid
    
    """
    try:
        if len(address_string) != 6:
            raise InvalidDataError(
                    "The address string has an invalid length",
                    address_string)
        ip = socket.inet_ntoa(address_string[:4])
        port = decode_port(address_string[4:])
        return (ip, port)
    except (socket.error, TypeError):
        raise InvalidDataError(
                "The address string has an invalid format",
                address_string)
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
