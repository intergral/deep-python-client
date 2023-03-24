import abc
import base64
from importlib import import_module

from deep.config import ConfigService


class UnknownAuthProvider(Exception):
    pass


class AuthProvider(abc.ABC):

    def __init__(self, config) -> None:
        self._config = config

    @staticmethod
    def get_provider(config: ConfigService):
        provider = config.SERVICE_AUTH_PROVIDER
        if provider is None or provider == "":
            return None

        module, cls = provider.rsplit(".", 1)
        provider_class = getattr(import_module(module), cls)
        if provider_class is None:
            raise UnknownAuthProvider("Cannot find auth provider with name: %s" % provider)

        return provider_class(config)

    @abc.abstractmethod
    def provide(self):
        raise NotImplementedError()


class BasicAuthProvider(AuthProvider):
    def provide(self):
        username = self._config.SERVICE_USERNAME
        password = self._config.SERVICE_PASSWORD
        if username is not None and password is not None:
            encode = base64.b64encode(
                (username + ':' + password).encode("utf-8"))
            return [('authorization', 'Basic%20' + encode.decode('utf-8'))]
        return []
