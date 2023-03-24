import abc
import os
import typing
from json import dumps
from urllib import parse

from opentelemetry.semconv.resource import ResourceAttributes

import deep.version
from deep.api.attributes import BoundedAttributes
from deep.api.types import AttributeValue
from deep import logging

LabelValue = AttributeValue
Attributes = typing.Dict[str, LabelValue]

_DEEP_SDK_VERSION = deep.version.__version__

TELEMETRY_SDK_NAME = ResourceAttributes.TELEMETRY_SDK_NAME
TELEMETRY_SDK_VERSION = ResourceAttributes.TELEMETRY_SDK_VERSION
TELEMETRY_AUTO_VERSION = ResourceAttributes.TELEMETRY_AUTO_VERSION
TELEMETRY_SDK_LANGUAGE = ResourceAttributes.TELEMETRY_SDK_LANGUAGE
PROCESS_EXECUTABLE_NAME = ResourceAttributes.PROCESS_EXECUTABLE_NAME
SERVICE_NAME = ResourceAttributes.SERVICE_NAME
SERVICE_NAMESPACE = ResourceAttributes.SERVICE_NAMESPACE
SERVICE_INSTANCE_ID = ResourceAttributes.SERVICE_INSTANCE_ID
SERVICE_VERSION = ResourceAttributes.SERVICE_VERSION

DEEP_RESOURCE_ATTRIBUTES = "DEEP_RESOURCE_ATTRIBUTES"
DEEP_SERVICE_NAME = "DEEP_SERVICE_NAME"


class Resource:
    """A Resource is an immutable representation of the entity producing telemetry as Attributes."""

    def __init__(
            self, attributes: Attributes, schema_url: typing.Optional[str] = None
    ):
        self._attributes = BoundedAttributes(attributes=attributes)
        if schema_url is None:
            schema_url = ""
        self._schema_url = schema_url

    @staticmethod
    def create(
            attributes: typing.Optional[Attributes] = None,
            schema_url: typing.Optional[str] = None,
    ) -> "Resource":
        """Creates a new `Resource` from attributes.

        Args:
            attributes: Optional zero or more key-value pairs.
            schema_url: Optional URL pointing to the schema

        Returns:
            The newly-created Resource.
        """
        if not attributes:
            attributes = {}
        resource = _DEFAULT_RESOURCE.merge(
            DeepResourceDetector().detect()
        ).merge(Resource(attributes, schema_url))
        if not resource.attributes.get(SERVICE_NAME, None):
            default_service_name = "unknown_service"
            process_executable_name = resource.attributes.get(
                PROCESS_EXECUTABLE_NAME, None
            )
            if process_executable_name:
                default_service_name += ":" + process_executable_name
            resource = resource.merge(
                Resource({SERVICE_NAME: default_service_name}, schema_url)
            )
        return resource

    @staticmethod
    def get_empty() -> "Resource":
        return _EMPTY_RESOURCE

    @property
    def attributes(self) -> BoundedAttributes:
        return self._attributes

    @property
    def schema_url(self) -> str:
        return self._schema_url

    def merge(self, other: "Resource") -> "Resource":
        """Merges this resource and an updating resource into a new `Resource`.

        If a key exists on both the old and updating resource, the value of the
        updating resource will override the old resource value.

        The updating resource's `schema_url` will be used only if the old
        `schema_url` is empty. Attempting to merge two resources with
        different, non-empty values for `schema_url` will result in an error
        and return the old resource.

        Args:
            other: The other resource to be merged.

        Returns:
            The newly-created Resource.
        """
        merged_attributes = self.attributes.copy()
        merged_attributes.update(other.attributes)

        if self.schema_url == "":
            schema_url = other.schema_url
        elif other.schema_url == "":
            schema_url = self.schema_url
        elif self.schema_url == other.schema_url:
            schema_url = other.schema_url
        else:
            logging.error(
                "Failed to merge resources: The two schemas %s and %s are incompatible",
                self.schema_url,
                other.schema_url,
            )
            return self

        return Resource(merged_attributes, schema_url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Resource):
            return False
        return (
                self._attributes == other._attributes
                and self._schema_url == other._schema_url
        )

    def __hash__(self):
        return hash(
            f"{dumps(self._attributes.copy(), sort_keys=True)}|{self._schema_url}"
        )

    def to_json(self, indent=4) -> str:
        return dumps(
            {
                "attributes": dict(self._attributes),
                "schema_url": self._schema_url,
            },
            indent=indent,
        )


_EMPTY_RESOURCE = Resource({})
_DEFAULT_RESOURCE = Resource(
    {
        TELEMETRY_SDK_LANGUAGE: "python",
        TELEMETRY_SDK_NAME: "deep",
        TELEMETRY_SDK_VERSION: _DEEP_SDK_VERSION,
    }
)


class ResourceDetector(abc.ABC):
    def __init__(self, raise_on_error=False):
        self.raise_on_error = raise_on_error

    @abc.abstractmethod
    def detect(self) -> "Resource":
        raise NotImplementedError()


class DeepResourceDetector(ResourceDetector):
    # pylint: disable=no-self-use
    def detect(self) -> "Resource":
        env_resources_items = os.environ.get(DEEP_RESOURCE_ATTRIBUTES)
        env_resource_map = {}

        if env_resources_items:
            for item in env_resources_items.split(","):
                try:
                    key, value = item.split("=", maxsplit=1)
                except ValueError as exc:
                    logging.warning(
                        "Invalid key value resource attribute pair %s: %s",
                        item,
                        exc,
                    )
                    continue
                value_url_decoded = parse.unquote(value.strip())
                env_resource_map[key.strip()] = value_url_decoded

        service_name = os.environ.get(DEEP_SERVICE_NAME)
        if service_name:
            env_resource_map[SERVICE_NAME] = service_name
        return Resource(env_resource_map)
