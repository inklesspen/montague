from __future__ import absolute_import

from zope.interface import Interface, Attribute


class IConfigLoader(Interface):
    """A config loader for a given config format.
       You do not have to implement all methods shown;
       either ini_config OR app_config, server_config, and filter_config
       must be implemented; whichever one you do not implement must still
       be present, but can simply raise NotImplementedError."""
    path = Attribute("""Location of config data. Usually will be a filesystem path,
                        but may be a URL, redis connection string, etc.""")

    def logging_configuration():
        """Provides a dict suitable for passing to logging.config.dictConfig."""

    def config():
        """Returns the entire config as a dict in whatever structure is most
           appropriate to the loader. This is intended for debugging and
           end-user convenience"""

    def ini_config():
        """Returns the entire config as a dict with INI-style keys.
           That is, an application named foo should have a key of 'application:foo'.
           montague will be responsible for isolating app/server configs."""

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
