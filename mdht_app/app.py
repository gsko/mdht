from twisted.application import internet, service
from twisted.internet.protocol import Factory, Protocol
from twisted.python import log

from mdht.protocols.krpc_iterator import KRPC_Iterator
from mdht_app import config

protocol = KRPC_Iterator()
application = service.Application(config.APPLICATION_NAME)
mdht_service = internet.UDPServer(config.SERVER_PORT, protocol)
mdht_service.setServiceParent(application)

log.msg('%s running on localhost:%d', config.SERVER_PORT)
