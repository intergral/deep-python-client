# DEEP Python Client

DEEP is an open source dynamic insight engine based on the Grafana stack. The idea is to allow dynamic collection of
Traces, Metrics, Logs and Snapshots via the Grafama UI.

## Usage

To use DEEP simple import the package and start the agent at the earliest point in the code.

```python
import deep

deep.start()
```

## Examples

There are a couple of examples [available here](./examples/README.md).
