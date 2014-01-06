#!/usr/bin/env python2
import pickle
import sys

from twisted import web
from twisted.application import internet, service
from twisted.application.internet import UDPServer, TCPServer
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from twisted.web import xmlrpc
from twisted.internet import reactor

from mdht.protocols.krpc_iterator import KRPC_Iterator
from mdht_server import config

APPLICATION_NAME = "mdht_server"

app = service.Application(APPLICATION_NAME)
kad_proto = KRPC_Iterator()
kad_server = UDPServer(config.SERVER_PORT, kad_proto)
kad_server.setServiceParent(app)

class RPC(xmlrpc.XMLRPC):

    allowNone = True
    useDateTime = True

    def __init__(self, kad_proto):
        self.kad_proto = kad_proto

    def xmlrpc_grab_nodes(self):
        log.msg('received grab_nodes request')
        rt = self.kad_proto.routing_table
        nodes = rt.nodes_dict.values()
        log.msg('replying to grab_nodes ({0})'.format(nodes))
        return self._serialize(nodes)

    def xmlrpc_ping(self, hostname_port):
        log.msg('received ping request for ({0})'.format(hostname_port))
        hostname, port = hostname_port.split(":")
        port = int(port)
        d = reactor.resolve(hostname)
        d.addCallback(lambda ip: self.kad_proto.ping((ip, port)))
        d.addCallbacks(self._on_ping_reply, self._on_ping_err)
        d.addBoth(self._serialize)
        return d

    def xmlrpc_find_iterate(self, s_target_id, s_nodes):
        nodes = self._deserialize(s_nodes)
        target_id = self._deserialize(s_target_id)
        log.msg('received find_iterate request towards ({0}) '
            'with nodes ({1})'.format(target_id, nodes))
        d = self.kad_proto.find_iterate(target_id, nodes)
        d.addCallbacks(
            self._on_find_iterate_reply, self._on_find_iterate_err)
        d.addBoth(self._serialize)
        return d

    def _on_find_iterate_reply(self, reply):
        log.msg('received find_iterate reply ({0})'.format(str(reply)))
        return reply

    def _on_find_iterate_err(self, err):
        log.msg('find_iterate request processing caused an error ({0})'
            .format(str(reply)))
        return err 

    def xmlrpc_find_node(self, hostname_portstr, s_node_id):
        node_id = self._deserialize(s_node_id)
        log.msg('find_node(%s, %d)' % (hostname_portstr, node_id))
        hostname, port_str = hostname_portstr.split(":")
        port = int(port_str)
        d = reactor.resolve(hostname)
        d.addCallback(lambda ip:
            self.kad_proto.find_node((ip, port), node_id))
        d.addCallbacks(self._on_find_node_reply, self._on_find_node_err)
        d.addBoth(self._serialize)
        return d

    def xmlrpc_get_peers(self, hostname_portstr, s_node_id):
        node_id = self._deserialize(s_node_id)
        log.msg('get_peers(%s, %d)' % (hostname_portstr, node_id))
        hostname, port_str = hostname_portstr.split(":")
        port = int(port_str)
        d = reactor.resolve(hostname)
        d.addCallback(lambda ip:
            self.kad_proto.find_node((ip, port), node_id))
        d.addCallbacks(self._on_find_node_reply, self._on_find_node_err)
        d.addBoth(self._serialize)
        return d

    def _on_find_node_reply(self, reply):
        log.msg('find_node reply ({0})'.format(str(reply)))
        return reply

    def _on_find_node_err(self, err):
        log.err('find_node error ({0})'
            .format(str(err)))
        sys.exit(1)
        return err

    def _on_ping_err(self, err):
        log.err('ping error ({0})'.format(str(err)))
        sys.exit(1)
        return err

    def _on_ping_reply(self, reply):
        log.msg('ping reply ({0})'.format(str(reply)))
        return reply

    def _serialize(self, val):
        return pickle.dumps(val)

    def _deserialize(self, serial_val):
        return pickle.loads(serial_val)

r = RPC(kad_proto)
rpc_server = TCPServer(5000, web.server.Site(r))
rpc_server.setServiceParent(app)

application = app
