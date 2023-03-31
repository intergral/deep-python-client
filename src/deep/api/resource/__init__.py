# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import os
import typing
from json import dumps
from urllib import parse

import deep.version
from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.api.types import AttributeValue

LabelValue = AttributeValue
Attributes = typing.Dict[str, LabelValue]

_DEEP_SDK_VERSION = deep.version.__version__

TELEMETRY_SDK_NAME = "telemetry.sdk.name"
"""
The name of the telemetry SDK as defined above.
"""

TELEMETRY_SDK_VERSION = "telemetry.sdk.version"
"""
The version string of the telemetry SDK.
"""

TELEMETRY_AUTO_VERSION = "telemetry.auto.version"
"""
The version string of the auto instrumentation agent, if used.
"""

TELEMETRY_SDK_LANGUAGE = "telemetry.sdk.language"
"""
The language of the telemetry SDK.
"""

PROCESS_EXECUTABLE_NAME = "process.executable.name"
"""
The name of the process executable. On Linux based systems, can be set to the `Name` in `proc/[pid]/status`. On Windows, can be set to the base name of `GetProcessImageFileNameW`.
"""

SERVICE_NAME = "service.name"
"""
Logical name of the service.
Note: MUST be the same for all instances of horizontally scaled services. If the value was not specified, SDKs MUST fallback to `unknown_service:` concatenated with [`process.executable.name`](process.md#process), e.g. `unknown_service:bash`. If `process.executable.name` is not available, the value MUST be set to `unknown_service`.
"""

SERVICE_NAMESPACE = "service.namespace"
"""
A namespace for `service.name`.
Note: A string value having a meaning that helps to distinguish a group of services, for example the team name that owns a group of services. `service.name` is expected to be unique within the same namespace. If `service.namespace` is not specified in the Resource then `service.name` is expected to be unique for all services that have no explicit namespace defined (so the empty/unspecified namespace is simply one more valid namespace). Zero-length namespace string is assumed equal to unspecified namespace.
"""

SERVICE_INSTANCE_ID = "service.instance.id"
"""
The string ID of the service instance.
Note: MUST be unique for each instance of the same `service.namespace,service.name` pair (in other words `service.namespace,service.name,service.instance.id` triplet MUST be globally unique). The ID helps to distinguish instances of the same service that exist at the same time (e.g. instances of a horizontally scaled service). It is preferable for the ID to be persistent and stay the same for the lifetime of the service instance, however it is acceptable that the ID is ephemeral and changes during important lifetime events for the service (e.g. service restarts). If the service has no inherent unique ID that can be used as the value of this attribute it is recommended to generate a random Version 1 or Version 4 RFC 4122 UUID (services aiming for reproducible UUIDs may also use Version 5, see RFC 4122 for more recommendations).
"""

SERVICE_VERSION = "service.version"
"""
The version string of the service API or implementation.
"""

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
