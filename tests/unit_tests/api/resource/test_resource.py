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

import unittest
import uuid
from logging import ERROR, WARNING
from os import environ
from unittest.mock import Mock, patch

from deep import version, logging
from deep.api.attributes import BoundedAttributes
# noinspection PyProtectedMember
from deep.api.resource import Resource, TELEMETRY_SDK_NAME, TELEMETRY_SDK_LANGUAGE, TELEMETRY_SDK_VERSION, \
    SERVICE_NAME, DEEP_SERVICE_NAME, DEEP_RESOURCE_ATTRIBUTES, ResourceDetector, _DEFAULT_RESOURCE, \
    get_aggregated_resources, _DEEP_SDK_VERSION, _EMPTY_RESOURCE, PROCESS_EXECUTABLE_NAME
from deep.config import ConfigService


class TestResources(unittest.TestCase):
    def setUp(self) -> None:
        logging.init(ConfigService({}))
        environ[DEEP_RESOURCE_ATTRIBUTES] = ""

    def tearDown(self) -> None:
        environ.pop(DEEP_RESOURCE_ATTRIBUTES)

    def test_create(self):
        attributes = {
            "service": "ui",
            "version": 1,
            "has_bugs": True,
            "cost": 112.12,
        }

        expected_attributes = {
            "service": "ui",
            "version": 1,
            "has_bugs": True,
            "cost": 112.12,
            TELEMETRY_SDK_NAME: "deep",
            TELEMETRY_SDK_LANGUAGE: "python",
            TELEMETRY_SDK_VERSION: version.__version__,
            SERVICE_NAME: "unknown_service:python",
        }

        resource = Resource.create(attributes)
        self.assertIsInstance(resource, Resource)
        self.assertEqual(resource.attributes, BoundedAttributes(attributes=expected_attributes))
        self.assertEqual(resource.schema_url, "")

        schema_url = "https://opentelemetry.io/schemas/1.3.0"

        resource = Resource.create(attributes, schema_url)
        self.assertIsInstance(resource, Resource)
        self.assertEqual(resource.attributes, expected_attributes)
        self.assertEqual(resource.schema_url, schema_url)

        environ[DEEP_RESOURCE_ATTRIBUTES] = "key=value"
        resource = Resource.create(attributes)
        self.assertIsInstance(resource, Resource)
        expected_with_envar = expected_attributes.copy()
        expected_with_envar["key"] = "value"
        self.assertEqual(resource.attributes, expected_with_envar)
        environ[DEEP_RESOURCE_ATTRIBUTES] = ""

        resource = Resource.get_empty()
        self.assertEqual(resource, _EMPTY_RESOURCE)

        resource = Resource.create(None)
        self.assertEqual(
            resource,
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ),
        )
        self.assertEqual(resource.schema_url, "")

        resource = Resource.create(None, None)
        self.assertEqual(
            resource,
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ),
        )
        self.assertEqual(resource.schema_url, "")

        resource = Resource.create({})
        self.assertEqual(
            resource,
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ),
        )
        self.assertEqual(resource.schema_url, "")

        resource = Resource.create({}, None)
        self.assertEqual(
            resource,
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ),
        )
        self.assertEqual(resource.schema_url, "")

    def test_resource_merge(self):
        left = Resource({"service": "ui"})
        right = Resource({"host": "service-host"})
        self.assertEqual(
            left.merge(right),
            Resource({"service": "ui", "host": "service-host"}),
        )
        schema_urls = (
            "https://opentelemetry.io/schemas/1.2.0",
            "https://opentelemetry.io/schemas/1.3.0",
        )

        left = Resource.create({}, None)
        right = Resource.create({}, None)
        self.assertEqual(left.merge(right).schema_url, "")

        left = Resource.create({}, None)
        right = Resource.create({}, schema_urls[0])
        self.assertEqual(left.merge(right).schema_url, schema_urls[0])

        left = Resource.create({}, schema_urls[0])
        right = Resource.create({}, None)
        self.assertEqual(left.merge(right).schema_url, schema_urls[0])

        left = Resource.create({}, schema_urls[0])
        right = Resource.create({}, schema_urls[0])
        self.assertEqual(left.merge(right).schema_url, schema_urls[0])

        left = Resource.create({}, schema_urls[0])
        right = Resource.create({}, schema_urls[1])
        with self.assertLogs(level=ERROR, logger=logging.logging.getLogger("deep")) as log_entry:
            self.assertEqual(left.merge(right), left)
            self.assertIn(schema_urls[0], log_entry.output[0])
            self.assertIn(schema_urls[1], log_entry.output[0])

    def test_resource_merge_empty_string(self):
        """Verify Resource#merge behavior with the empty string.

        Attributes from the source Resource take precedence, except the empty string.

        """
        left = Resource({"service": "ui", "host": ""})
        right = Resource({"host": "service-host", "service": "not-ui"})
        self.assertEqual(
            left.merge(right),
            Resource({"service": "not-ui", "host": "service-host"}),
        )

    def test_immutability(self):
        attributes = {
            "service": "ui",
            "version": 1,
            "has_bugs": True,
            "cost": 112.12,
        }

        default_attributes = {
            TELEMETRY_SDK_NAME: "deep",
            TELEMETRY_SDK_LANGUAGE: "python",
            TELEMETRY_SDK_VERSION: _DEEP_SDK_VERSION,
            SERVICE_NAME: "unknown_service:python",
        }

        attributes_copy = attributes.copy()
        attributes_copy.update(default_attributes)

        resource = Resource.create(attributes)
        self.assertEqual(resource.attributes, attributes_copy)

        with self.assertRaises(TypeError):
            resource.attributes["has_bugs"] = False
        self.assertEqual(resource.attributes, attributes_copy)

        attributes["cost"] = 999.91
        self.assertEqual(resource.attributes, attributes_copy)

        with self.assertRaises(AttributeError):
            # noinspection PyPropertyAccess
            resource.schema_url = "bug"

        self.assertEqual(resource.schema_url, "")

    def test_service_name_using_process_name(self):
        resource = Resource.create({PROCESS_EXECUTABLE_NAME: "test"})
        self.assertEqual(
            resource.attributes.get(SERVICE_NAME),
            "unknown_service:test",
        )

    def test_invalid_resource_attribute_values(self):
        with self.assertLogs(level=WARNING, logger=logging.logging.getLogger("deep")):
            resource = Resource(
                {
                    SERVICE_NAME: "test",
                    "non-primitive-data-type": {},
                    "invalid-byte-type-attribute": (
                        b"\xd8\xe1\xb7\xeb\xa8\xe5 \xd2\xb7\xe1"
                    ),
                    "": "empty-key-value",
                    None: "null-key-value",
                    "another-non-primitive": uuid.uuid4(),
                }
            )
        self.assertEqual(
            resource.attributes,
            {
                SERVICE_NAME: "test",
            },
        )
        self.assertEqual(len(resource.attributes), 1)

    def test_aggregated_resources_no_detectors(self):
        aggregated_resources = get_aggregated_resources([])
        self.assertEqual(
            aggregated_resources,
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ),
        )

    def test_aggregated_resources_with_default_destroying_static_resource(
            self,
    ):
        static_resource = Resource({"static_key": "static_value"})

        self.assertEqual(
            get_aggregated_resources([], initial_resource=static_resource),
            static_resource,
        )

        resource_detector = Mock(spec=ResourceDetector)
        resource_detector.detect.return_value = Resource(
            {"static_key": "try_to_overwrite_existing_value", "key": "value"}
        )
        self.assertEqual(
            get_aggregated_resources(
                [resource_detector], initial_resource=static_resource
            ),
            Resource(
                {
                    "static_key": "try_to_overwrite_existing_value",
                    "key": "value",
                }
            ),
        )

    def test_aggregated_resources_multiple_detectors(self):
        resource_detector1 = Mock(spec=ResourceDetector)
        resource_detector1.detect.return_value = Resource({"key1": "value1"})
        resource_detector2 = Mock(spec=ResourceDetector)
        resource_detector2.detect.return_value = Resource(
            {"key2": "value2", "key3": "value3"}
        )
        resource_detector3 = Mock(spec=ResourceDetector)
        resource_detector3.detect.return_value = Resource(
            {
                "key2": "try_to_overwrite_existing_value",
                "key3": "try_to_overwrite_existing_value",
                "key4": "value4",
            }
        )

        self.assertEqual(
            get_aggregated_resources(
                [resource_detector1, resource_detector2, resource_detector3]
            ),
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ).merge(
                Resource(
                    {
                        "key1": "value1",
                        "key2": "try_to_overwrite_existing_value",
                        "key3": "try_to_overwrite_existing_value",
                        "key4": "value4",
                    }
                )
            ),
        )

    def test_aggregated_resources_different_schema_urls(self):
        resource_detector1 = Mock(spec=ResourceDetector)
        resource_detector1.detect.return_value = Resource(
            {"key1": "value1"}, ""
        )
        resource_detector2 = Mock(spec=ResourceDetector)
        resource_detector2.detect.return_value = Resource(
            {"key2": "value2", "key3": "value3"}, "url1"
        )
        resource_detector3 = Mock(spec=ResourceDetector)
        resource_detector3.detect.return_value = Resource(
            {
                "key2": "try_to_overwrite_existing_value",
                "key3": "try_to_overwrite_existing_value",
                "key4": "value4",
            },
            "url2",
        )
        resource_detector4 = Mock(spec=ResourceDetector)
        resource_detector4.detect.return_value = Resource(
            {
                "key2": "try_to_overwrite_existing_value",
                "key3": "try_to_overwrite_existing_value",
                "key4": "value4",
            },
            "url1",
        )
        self.assertEqual(
            get_aggregated_resources([resource_detector1, resource_detector2]),
            _DEFAULT_RESOURCE.merge(
                Resource({SERVICE_NAME: "unknown_service:python"}, "")
            ).merge(
                Resource(
                    {"key1": "value1", "key2": "value2", "key3": "value3"},
                    "url1",
                )
            ),
        )
        with self.assertLogs(level=ERROR, logger=logging.logging.getLogger("deep")) as log_entry:
            self.assertEqual(
                get_aggregated_resources(
                    [resource_detector2, resource_detector3]
                ),
                _DEFAULT_RESOURCE.merge(
                    Resource({SERVICE_NAME: "unknown_service:python"}, "")
                ).merge(
                    Resource({"key2": "value2", "key3": "value3"}, "url1")
                ),
            )
            self.assertIn("url1", log_entry.output[0])
            self.assertIn("url2", log_entry.output[0])
        with self.assertLogs(level=ERROR, logger=logging.logging.getLogger("deep")):
            self.assertEqual(
                get_aggregated_resources(
                    [
                        resource_detector2,
                        resource_detector3,
                        resource_detector4,
                        resource_detector1,
                    ]
                ),
                _DEFAULT_RESOURCE.merge(
                    Resource({SERVICE_NAME: "unknown_service:python"}, "")
                ).merge(
                    Resource(
                        {
                            "key1": "value1",
                            "key2": "try_to_overwrite_existing_value",
                            "key3": "try_to_overwrite_existing_value",
                            "key4": "value4",
                        },
                        "url1",
                    )
                ),
            )
            self.assertIn("url1", log_entry.output[0])
            self.assertIn("url2", log_entry.output[0])

    def test_resource_detector_ignore_error(self):
        resource_detector = Mock(spec=ResourceDetector)
        resource_detector.detect.side_effect = Exception()
        resource_detector.raise_on_error = False
        with self.assertLogs(level=WARNING, logger=logging.logging.getLogger("deep")):
            self.assertEqual(
                get_aggregated_resources([resource_detector]),
                _DEFAULT_RESOURCE.merge(
                    Resource({SERVICE_NAME: "unknown_service:python"}, "")
                ),
            )

    def test_resource_detector_raise_error(self):
        resource_detector = Mock(spec=ResourceDetector)
        resource_detector.detect.side_effect = Exception()
        resource_detector.raise_on_error = True
        self.assertRaises(
            Exception, get_aggregated_resources, [resource_detector]
        )

    @patch.dict(
        environ,
        {"DEEP_RESOURCE_ATTRIBUTES": "key1=env_value1,key2=env_value2"},
    )
    def test_env_priority(self):
        resource_env = Resource.create()
        self.assertEqual(resource_env.attributes["key1"], "env_value1")
        self.assertEqual(resource_env.attributes["key2"], "env_value2")

        resource_env_override = Resource.create(
            {"key1": "value1", "key2": "value2"}
        )
        self.assertEqual(resource_env_override.attributes["key1"], "value1")
        self.assertEqual(resource_env_override.attributes["key2"], "value2")

    @patch.dict(
        environ,
        {
            DEEP_SERVICE_NAME: "test-srv-name",
            DEEP_RESOURCE_ATTRIBUTES: "service.name=svc-name-from-resource",
        },
    )
    def test_service_name_env(self):
        resource = Resource.create()
        self.assertEqual(resource.attributes["service.name"], "test-srv-name")

        resource = Resource.create({"service.name": "from-code"})
        self.assertEqual(resource.attributes["service.name"], "from-code")
