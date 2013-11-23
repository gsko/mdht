from mdht.run import MDHT
from mdht.constants import bootstrap_addresses

rand_id = 216882130869719664159264778321560871326200781259L
dht = MDHT(rand_id)

def print_nodes(nodes):
    for node in nodes:
        print node

the_hobbit = long("D20E34D7C69C296B7CB7447532DF6AA4D2BE001C", 16)
d = dht.find_iterate(the_hobbit)
d.addCallback(print_nodes)
d.addCallback(dht.halt)

dht.run()

print "done!"
