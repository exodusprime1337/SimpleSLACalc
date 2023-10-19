class SimpleSLACalcBaseException(Exception):
    """
    Base class for recurring exceptions
    """

    def __init__(self, message=""):
        super(SimpleSLACalcBaseException, self).__init__(message)


class ToManySLACounterItems(SimpleSLACalcBaseException):
    """
    To many SLA counter critera passed
    """


class NoSLACounterItems(SimpleSLACalcBaseException):
    """
    No SLA counter items provided
    """


class InvalidCustomDateList(SimpleSLACalcBaseException):
    """
    Either no list or a malformed list of custom exclude dates provided.
    """


class InvalidDateObject(SimpleSLACalcBaseException):
    """
    Invalid excluded date object
    """
