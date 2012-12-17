"""
@author Greg Skoczek

Module encapsulating all the errors that occur
within the krpc sending/receiving process

"""
class TimeoutError(Exception):
    """
    Error denoting that a Query has timed out
    
    This exception stores no data
    
    """
    pass

class KRPCError(Exception):
    """
    Error denoting that an Error message has been received

    error: the KRPC error that has been received
    
    """
    def __init__(self, error):
        self.error = error
