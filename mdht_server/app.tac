#!/usr/bin/env python2
import pickle
import sys

from twisted import web
from twisted.application import internet, service
from twisted.application.internet import UDPServer, TCPServer
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.python import log
from twisted.web import xmlrpc

from mdht.protocols.krpc_simple import KRPC_Simple
from mdht_server import config

APPLICATION_NAME = "mdht_server"

app = service.Application(APPLICATION_NAME)
kad_proto = KRPC_Simple()
kad_server = UDPServer(config.SERVER_PORT, kad_proto)
kad_server.setServiceParent(app)

class SearchListener(object):
    def __init__(self, live_search, deferred):
        self.live_search = live_search
        self.deferred = deferred

    def __call__(self):
        log.msg('live_search({0}) is complete!'
            .format(live_search.target_id))
        self.deferred.callback(live_search.get_results())

# TODO
# basic persistence (sqlite)

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
        d.addCallback(self._on_reply, "ping")
        d.addErrback(self._on_err, "ping")
        d.addBoth(self._serialize)
        return d

    def xmlrpc_find_node(self, hostname_portstr, s_node_id):
        node_id = self._deserialize(s_node_id)
        log.msg('find_node(%s, %d)' % (hostname_portstr, node_id))
        hostname, port_str = hostname_portstr.split(":")
        port = int(port_str)
        d = reactor.resolve(hostname)
        d.addCallback(lambda ip:
            self.kad_proto.find_node((ip, port), node_id))
        d.addCallback(self._on_reply, "find_node")
        d.addErrback(self._on_err, "find_node")
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
        d.addCallback(self._on_reply, "get_peers")
        d.addErrback(self._on_err, "get_peers")
        d.addBoth(self._serialize)
        return d

    def xmlrpc_get(self, s_target_id):
        target_id = self._deserialize(s_target_id)
        log.msg('get({0})'.format(target_id))
        live_search = self.kad_proto.get(target_id)
        d = Deferred()
        d.addCallback(self._on_reply, "get")
        d.addErrback(self._on_err, "get")
        d.addBoth(self._serialize)
        live_search.register_listener(SearchListener(live_search, d))
        assert not live_search.is_complete
        # TODO -- bug: some problem with deserialization on an instance
        # rather than a str
        return d

    def _on_reply(self, reply, func_str):
        log.msg('{0} reply ({1})'.format(func_str, str(reply)))
        return reply

    def _on_err(self, err, func_str):
        log.err('{0} error ({1})'.format(func_str, str(err)))
        sys.exit(1)
        return err

    def _serialize(self, val):
        return pickle.dumps(val)

    def _deserialize(self, serial_val):
        return pickle.loads(serial_val)

r = RPC(kad_proto)
rpc_server = TCPServer(5000, web.server.Site(r))
rpc_server.setServiceParent(app)

application = app
