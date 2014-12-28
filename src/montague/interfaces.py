from __future__ import absolute_import

from zope.interface import Interface, Attribute


class IConfigLoader(Interface):
    """A config loader for a given config format.
       You do not have to implement app_config/server_config/filter_config.
       They must still be present, but can simply return NotImplementedError.
       In that case, Montague will extract the config from the config()."""
    path = Attribute("""Location of config data. Usually will be a filesystem path,
                        but may be a URL, redis connection string, etc.""")

    def logging_configuration():
        """Provides a dict suitable for passing to logging.config.dictConfig."""

    def config():
        """Returns the entire config as a dict in Montague standard format.
           Montague standard format has the following keys (all optional):
           global, application, composite, filter, server. Other than global,
           these keys should then contain name, config value pairs. Use DEFAULT
           for the default app/filter/server."""

    def app_config(name):
        """Return the config for the specified app.
           If name is montague.structs.DEFAULT, use the default name for the
           config format (such as 'main')."""

    def server_config(name):
        """Return the config for the specified server.
           If name is montague.structs.DEFAULT, use the default name for the
           config format (such as 'main')."""

    def filter_config(name):
        """Return the config for the specified filter.
           If name is montague.structs.DEFAULT, use the default name for the
           config format (such as 'main')."""


class IConfigLoaderFactory(Interface):
    """Creates ConfigLoaders"""

    def __call__(path, defaults):
        """Creates a ConfigLoader targeting the specified path."""
