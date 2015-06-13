Writing your own config loader
==============================

Do you want to store your WSGI app config in Redis? In a
`TOML <https://github.com/toml-lang/toml>`__ file? In
`ZooKeeper <http://zookeeper.apache.org/>`__? You can do that.

You will need to decide two things:

1. A filename extension for your configuration format: for actual files,
   that's easy. A JSON loader should work with ``foo.json`` files.
   However, if you are loading your configuration from a service, you
   still need to pick a filename extension; Montague uses that to
   dispatch to config loaders. Perhaps you will store the Redis
   connection info in ``myfile.redis``, or perhaps the file doesn't even
   exist and you extract the connection info from the path name.
2. Whether you need to support individual ``app_config``,
   ``server_config``, etc methods: the default INI loader supports these
   because the PasteDeploy INI format allows individual app configs to
   override global variables for that specific app.

Config loaders must provide the methods listed in the :class:`montague.interfaces.IConfigLoader`
interface; it's recommended, though not required, that they actually
implement the interface using :mod:`zope.interface`.

Montague Standard Format
------------------------

The actual layout of your configuration information will obviously vary
from format to format. Because of this, Montague has a standard layout
you should use when implementing the :meth:`montague.interfaces.IConfigLoader.config()` method. You should
return a dict that looks like this: ::

    {
        "globals": {},
        "application": {},
        "composite": {},
        "filter": {},
        "server": {},
        "logging": {},
    }

Of course, the dict can contain other keys as well, but those are the
ones Montague cares about.
