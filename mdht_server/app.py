#!/usr/bin/env python2
from twisted import web
from twisted.application import internet, service
from twisted.application.internet import UDPServer, TCPServer
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from twisted.scripts.twistd import run
from twisted.web import xmlrpc

from mdht.protocols.krpc_iterator import KRPC_Iterator
from mdht_server import config

APPLICATION_NAME = "mdht_server"

app = service.Application(APPLICATION_NAME)
kad_proto = KRPC_Iterator()
kad_server = UDPServer(config.SERVER_PORT, kad_proto)
kad_server.setServiceParent(app)

class RPC(xmlrpc.XMLRPC):
    def xmlrpc_hello(self, name):
        return 'hello %s!' % name

r = RPC()
rpc_server = TCPServer(5000, web.server.Site(r))
rpc_server.setServiceParent(app)

application = app

log.msg('%s running on localhost:%d', config.SERVER_PORT)
