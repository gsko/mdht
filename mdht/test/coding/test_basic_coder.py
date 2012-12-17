from twisted.trial import unittest

# Functions being tested
from mdht.coding.basic_coder import (ltob, btol, encode_address,
        decode_address, encode_port, decode_port, encode_network_id, 
        decode_network_id, InvalidDataError)

class LongNumberCodingTestCase(unittest.TestCase):
    def test_ltob_and_btol(self):
        bijection = lambda num: btol(ltob(num))
        self.assertEqual(0, bijection(0))
        self.assertEqual(512, bijection(512))
        self.assertEqual(1024, bijection(1024))
        self.assertEqual(9120890186313616, bijection(9120890186313616))
        self.assertEqual(2**150, bijection(2**150))
        self.assertEqual(2**133, bijection(2**133))

class AddressCodingTestCase(unittest.TestCase):
    def test_encode_and_decode_address_validAddresses(self):
        valid_addresses = [("127.0.0.1", 80), ("4.2.2.1", 53),
                     ("8.8.8.8", 52), ("12.12.42.42", 1385),
                     ("0.0.0.0", 0), ("255.255.255.255", 65535)]
        for address in valid_addresses:
            self.assertEquals(address,
                              decode_address(encode_address(address)))

    def test_encode_address_invalidAddresses(self):
        invalid_addresses = [("127.0.0.1", 1000000000000), # port too big
                             ("not an address", 50),
                             ("one element")]
        for address in invalid_addresses:
            self.assertRaises(InvalidDataError, encode_address, address)

    def test_encode_address_EdgeAddresses(self):
        zero_address = ("0.0.0.0", 0)
        full_address = ("255.255.255.255", 65535)
        port_three_address = ("0.0.0.0", 3)
        self.assertEquals("\x00\x00\x00\x00\x00\x00",
                            encode_address(zero_address))
        self.assertEquals("\xff\xff\xff\xff\xff\xff",
                            encode_address(full_address))
        self.assertEquals("\x00\x00\x00\x00\x00\x03",
                            encode_address(port_three_address))

    def test_decode_address_invalidAddresses(self):
        invalid_addresses = ["1",           # too short
                             "5555" * 80,   # too long
                             12521]         # not a string
        for address in invalid_addresses:
            self.assertRaises(InvalidDataError,
                              decode_address,
                              address)

    def test_encode_port_validPorts(self):
        expected_encodings = {0 : "\x00\x00", 255 : "\x00\xff",
                                65535 : "\xff\xff"}
        for port, expected_port_string in expected_encodings.iteritems():
            self.assertEquals(expected_port_string, encode_port(port))

    def test_encode_port_invalidPorts(self):
        self.assertRaises(InvalidDataError, encode_port, -1)
        self.assertRaises(InvalidDataError, encode_port, 65536)

    def test_decode_port_validPorts(self):
        expected_ports = {"\x00\x00" : 0, "\x00\xff" : 255,
                            "\xff\xff" : 65535}
        for encoded_port, expected_decoding in expected_ports.iteritems():
            self.assertEquals(expected_decoding, decode_port(encoded_port))

    def test_decode_port_invalidPorts(self):
        self.assertRaises(InvalidDataError, decode_port, "")
        self.assertRaises(InvalidDataError, decode_port, "\xff\xff\xff")

class NetworkIDCodingTestCase(unittest.TestCase):
    def test_encode_network_id_validIDs(self):
        self.assertEquals("\x00" * 20, encode_network_id(0))
        self.assertEquals("\xff" * 20, encode_network_id(2**160 - 1))

    def test_encode_network_id_invalidIDs(self):
        self.assertRaises(InvalidDataError, encode_network_id, -1)
        self.assertRaises(InvalidDataError, encode_network_id, 2**160)

    def test_decode_network_id_validIDs(self):
        self.assertEquals(0, decode_network_id("\x00" * 20))
        self.assertEquals(2**160 - 1, decode_network_id("\xff" * 20))

    def test_decode_network_id_invalidIDs(self):
        # Too short of a string
        self.assertRaises(InvalidDataError, decode_network_id, "\x00")
        # Too long of a string
        self.assertRaises(InvalidDataError, decode_network_id, "\xff" * 21)
