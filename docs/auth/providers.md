# Auth Providers
There are different ways to authenticate the request to the deep services.

## Basic Auth Provider

This is a simple Basic auth provider that will attach the 'authorization' header to outbound requests.

To use this set 'SERVICE_AUTH_PROVIDER' to 'deep.api.auth.AuthProvider'. Then provider the username and password via the config.

| Key              | Default | Description                               |
|------------------|---------|-------------------------------------------|
| SERVICE_USERNAME | None    | The user name to use when attaching auth. |
| SERVICE_PASSWORD | None    | The password to use when attaching auth.  |
