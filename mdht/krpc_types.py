"""
@author Greg Skoczek

Module containing classes that encapsulate
KRPC Queries, Responses, and Errors

"""
class _KRPC(object):
    """
    A KRPC message always has a transaction ID

    _transaction_id: the transaction ID of this message

    """
    def __init__(self):
        self._transaction_id = None

    def __repr__(self):
        raise NotImplemented()

    def _build_repr(self, attributes):
        """
        Return a representation of the given attributes

        The reprsentation follows the form of
        `attribute1=value attribute2=value ... attributeN=value`

        """
        result = ""
        for attribute in attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value is not None:
                result += "%s=%s " % (attribute, str(attribute_value))
        return result.rstrip(" ")

    def _get_attrs(self):
        # Used in __eq__ and must be
        # implemented by subclasses
        raise NotImplementedError()

    def __eq__(self, other):
        attributes = self._get_attrs()
        return all(hasattr(other, attribute) and
                getattr(other, attribute) == getattr(self, attribute)
                for attribute in attributes)

    def __ne__(self, other):
        return not self.__eq__(other)

class Query(_KRPC):
    """
    A Query message has a type, querier ID, and various other details

    rpctype: one of ["ping", "find_node", "get_peers", "announce_peer"]
    _from: the node ID of the node from which this query originates
    target_id: the target ID of this query (every query except for
              ping uses the target_id field)
    token: the token used to validate an announce_peer query
           (the token originates from a previous get_peers query response)
    port: the port that the announcing peer will be listening on

    """
    def __init__(self):
        _KRPC.__init__(self)
        self.rpctype = None
        self._from = None
        self.target_id = None
        self.token = None
        self.port = None

    def build_response(self, nodes=None, token=None, peers=None):
        """
        Builds a response using information found in the Query

        @returns a Response

        """
        r = Response()
        # Fill in necessary details we already have
        r._transaction_id = self._transaction_id
        r.rpctype = self.rpctype
        # Fill in user provided values
        r.nodes = nodes
        r.token = token
        r.peers = peers 
        return r

    def build_error(self, code=201, message="Generic Error"):
        """
        Builds an error using information found in this Query

        @returns an Error

        """
        e = Error()
        e._transaction_id = self._transaction_id
        e.code = code
        e.message = message
        return e

    def __repr__(self):
        printable_attributes = self._get_attrs()
        return "<Query: %s>" % self._build_repr(printable_attributes)

    # TODO check if there is a way to
    # programmaticaly get this list (dir() + function filtering)
    def _get_attrs(self):
        return ('_transaction_id', 'rpctype', 
                '_from', 'target_id', 'token', 'port')

   
class Response(_KRPC):
    """
    A Response contains the requested data of the originating query

    nodes: a list of nodes closest to the original query's target ID
    token: returned from a valid get_peers query, used to verify
           that an announcing peer previously issued a get_peers request
    values: a list of peers that are associated with the target ID
            as specified in the originating query
    _from: the node that received the original query

    """
    def __init__(self):
        _KRPC.__init__(self)
        self._from = None
        self.nodes = None
        self.token = None
        self.peers = None
        self.rpctype = None

    def __repr__(self):
        printable_attributes = self._get_attrs()
        return "<Response: %s>" % self._build_repr(printable_attributes)

    # TODO see if we can replace these with a function (in Query too)
    def _get_attrs(self):
        return ('_transaction_id', '_from',
                    'nodes', 'token', 'peers', 'rpctype')

class Error(_KRPC):
    """
    An Error signifies that a query failed (for a variety of reasons)

    code: the error code of this error
    message: the message associated with this error

    """
    def __init__(self):
        _KRPC.__init__(self)
        self.code = None
        self.message = None
    
    def __repr__(self):
        printable_attributes = ['_transaction_id', 'rpctype', 'code']
        message_string = "message='%s'" % self.message
        return "<Error: %s %s>" % (
                self._build_repr(printable_attributes),
                message_string
                )

    def _get_attrs(self):
        return ('_transaction_id', 'code', 'message')
