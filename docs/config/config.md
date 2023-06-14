# Deep Python Client config values

A list of the possible config values for the deep python agent. They can be set via code, or as environment variables.

Note: When setting as environment variable prefix the key with 'DEEP_'. e.g. DEEP_SERVICE_URL

| Key                   | Default    | Description                                                                                                                          |
|-----------------------|------------|--------------------------------------------------------------------------------------------------------------------------------------|
| SERVICE_URL           | deep:43315 | The url (hostname:port) of the deep service to connect to.                                                                           |
| SERVICE_SECURE        | True       | Can be set to False if the service doesn't support secure connections.                                                               |
| LOGGING_CONF          | None       | Can be used to override the python logging config used by the agent.                                                                 |
| POLL_TIMER            | 10         | The time (in seconds) of the interval between polls.                                                                                 |
| SERVICE_AUTH_PROVIDER | None       | The auth provider to use, each provider can have their own config, see available [auth providers](../auth/providers.md) for details. |
| IN_APP_INCLUDE        | None       | A string of comma (,) seperated values that indicate a package is part of the app.                                                   |
| IN_APP_EXCLUDE        | None       | A string of comma (,) seperated values that indicate a package is not part of the app.                                               |


