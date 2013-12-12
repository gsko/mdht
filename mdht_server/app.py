#!/usr/bin/env python2
from twisted.application import internet, service
from twisted.application.internet import UDPServer
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log
from twisted.scripts.twistd import run

from mdht.protocols.krpc_iterator import KRPC_Iterator
from mdht_app import config

APPLICATION_NAME = "mdht_server"

app = service.Application(APPLICATION_NAME)
kad_proto = KRPC_Iterator()
kad_server = UDPServer(config.SERVER_PORT, kad_proto)
kad_server.setServiceParent(app)

log.msg('%s running on localhost:%d', config.SERVER_PORT)
