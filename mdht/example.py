from twisted.python import logging

from mdht.run import Server
from mdht.constants import bootstrap_addresses

rand_id = 216882130869719664159264778321560871326200781259L
dht = MDHT(rand_id)

dht.run()
