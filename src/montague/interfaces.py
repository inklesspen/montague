from __future__ import absolute_import

from zope.interface import Interface, Attribute


class IConfigLoader(Interface):
    """A config loader for a given config format.
       Your implementations of app_config, server_config,
       and filter_config may simply raise NotImplementedError."""
    path = Attribute("""Location of config data. Usually will be a filesystem path,
                        but may be a URL, redis connection string, etc.""")

    def logging_configuration():
        """Provides a dict suitable for passing to logging.config.dictConfig."""

    def config():
        """Returns the entire config as a dict; montague will be
           responsible for isolating app/server configs."""

    def app_config(name="main"):
        """Return the config for the specified app."""

    def server_config(name="main"):
        """Return the config for the specified server."""

    def filter_config(name="main"):
        """Return the config for the specified filter."""


class IConfigLoaderFactory(Interface):
    """Creates ConfigLoaders"""

    def __call__(path, defaults):
        """Creates a ConfigLoader targeting the specified path."""
