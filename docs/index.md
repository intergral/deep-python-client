# Deep Python Client
This is the python client for Deep, a dynamic monitor and debugging tool.

# Getting started
You will need to have a running version of the [DEEP server](#) to connect this client to.

## Install Agent
To install the python agent just add the dependency 'deep-agent' to your project.

```bash
pip install deep-agent
```

## Setup
Once installed you need to setup the agent. At the earliest part of the code you should add the following code:

```python
import deep

deep.start()
```

## Configuration
To configure the deep agent to connect to your services. You can use the following configs.

### In code
You can set config values in code to quickly try a connection.

```python
import deep

deep.start({
    'SERVICE_URL': 'localhost:43315', # the url hostname:port for the deep service
    'SERVICE_SECURE': 'False', # set to 'False' if you have not setup a secure connection for this service
})
```

### Environment
You can set the config for deep to use via environment variables. All config values can be set as environment 
variables by simply prefixing 'DEEP_' to the key. For a full list of values see [config values](./config/config.md)
