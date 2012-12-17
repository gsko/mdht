"""
@author Greg Skoczek

A class containing a loose collection of attributes
associated with a transaction in the DHT network

"""
import time

class Transaction(object):
    """
    A class wrapping essential attributes of a transaction in the DHT network

    query: the query this transaction refers to
    deferred: the deferred that will be fired once a response/error is
              received corresponding to the query (or the query times out)
    timeout_call: the delayed call that is used to time this query out
                 (and remove this transaction from the transaction table)
    address: the address of the target node of this transaction
    time: the time that this transaction originated

    """
    def __init__(self):
        self.query = None
        self.deferred = None
        self.timeout_call = None
        self.address = None
        self.time = time.time()

    def __eq__(self, other):
        return not self.__ne__(other)

    def __ne__(self, other):
        return self.__hash__() ^ other.__hash__()

    def __hash__(self):
        return long(
                round(
                    float("%d%f" % (self.query.transaction_id, self.time))))

    def __str__(self):
        return "transaction: id=%d, time=%d" % (
                self.query.transaction_id, self.time)
