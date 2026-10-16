class ApplicationError(Exception):
    pass


class NeighborNotFound(ApplicationError):
    pass


class ChatModelNotConfigured(ApplicationError):
    pass


class ChatModelTimeout(ApplicationError):
    pass


class ChatModelFailed(ApplicationError):
    pass
