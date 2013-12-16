#!/usr/bin/env python2
import pickle

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

    def xmlrpc_ping(self, hostname_port):
        log.msg('received ping request for ({0})'.format(hostname_port))
        hostname, port = hostname_port.split(":")
        port = int(port)
        d = reactor.resolve(hostname)
        d.addCallback(lambda ip: (ip, port))
        d.addCallback(self._on_ping_reply)
        d.addBoth(self._serialize)
        return d

    def _on_ping_reply(self, ping_reply):
        log.msg('received ping reply ({0}'.format(ping_reply))
        return self._serialize(ping_reply)

    def xmlrpc_grab_nodes(self):
        log.msg('received grab_nodes request')
        rt = self.kad_proto.routing_table
        nodes = rt.nodes_dict.values()
        log.msg('replying to grab_nodes ({0})'.format(nodes))
        return self._serialize(nodes)

    def _serialize(self, val):
        return pickle.dumps(val)

r = RPC(kad_proto)
rpc_server = TCPServer(5000, web.server.Site(r))
rpc_server.setServiceParent(app)

application = app

log.msg('%s running on localhost:%d', config.SERVER_PORT)
