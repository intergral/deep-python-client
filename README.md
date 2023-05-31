[![Tests](https://github.com/intergral/deep-python-client/actions/workflows/on_push.yaml/badge.svg)](https://github.com/intergral/deep-python-client/actions/workflows/on_push.yaml)
[![PyPI](https://img.shields.io/pypi/v/deep-agent)](https://pypi.org/project/deep-agent/)

# DEEP Python Client

DEEP is an open source dynamic insight engine based on the Grafana stack. The idea is to allow dynamic collection of
Traces, Metrics, Logs and Snapshots via the Grafana UI.

## Usage

To use DEEP simple import the package and start the agent at the earliest point in the code.

```bash
pip install deep-agent
```

```python
import deep

deep.start()
```

## Examples

There are a couple of examples [available here](./examples/README.md).

## Documentation

For further documentation on the usage of deep-agent view the [docs](https://intergral.github.io/deep-python-client/).


## Licensing

For licensing info please see [LICENSING.md](./LICENSING.md)