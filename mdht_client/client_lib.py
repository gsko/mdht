import pickle
import sys

from twisted.web import xmlrpc
from twisted.internet import reactor
from twisted.python import log

def _print(x):
    print x
    return x

class RPCClient(object):
    def __init__(self, addr_str='http://localhost:5000'):
        self.proxy = xmlrpc.Proxy(addr_str)

    def start_loop(self):
        try:
            reactor.run()
        except:
            pass

    def ping(self, address_str):
        log.msg('ping({0})'.format(address_str))
        return self._call('ping', address_str)

    def find_node(self, address_str, node_id):
        log.msg('find_node({0}, {1})'.format(address_str, node_id))
        s_node_id = self._serialize(node_id)
        return self._call('find_node', address_str, s_node_id)

    def get_peers(self, address_str, node_id):
        log.msg('get_peers({0}, {1})'.format(address_str, node_id))
        s_node_id = self._serialize(node_id)
        return self._call('get_peers', address_str, s_node_id)

    def get(self, target_id):
        log.msg('get({0})'.format(target_id))
        s_target_id = self._serialize(target_id)
        return self._call('get', s_target_id)

    def grab_nodes(self):
        return self._call('grab_nodes')

    def _deserialize(self, serial_val):
        return pickle.loads(serial_val)

    def _serialize(self, val):
        return pickle.dumps(val)

    def _call(self, funcname, *args, **kwargs):
        # TODO refactor the above log.msg calls
        # into this function here
        d = self.proxy.callRemote(funcname, *args, **kwargs)
        d.addBoth(self._deserialize)
        d.addBoth(_print)
        return d
