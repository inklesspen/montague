from __future__ import absolute_import

import json
import six
from montague.interfaces import IConfigLoader, IConfigLoaderFactory
from montague.structs import LoadableConfig
from zope.interface import directlyProvides, implementer


@implementer(IConfigLoader)
class JSONConfigLoader(object):
    """This is a sample config loader. It uses a structural
       convention that makes more sense for JSON; the root object
       contains 'application' and 'server' keys, which each contain keys
       for the respective items. It has basically no error handling
       and is kind of inefficient."""
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path

    @property
    def _config(self):
        return json.load(open(self.path))

    def config(self):
        config = {}
        for section, vals in six.iteritems(self._config):
            config[section] = vals
        return config

    def app_config(self, name):
        # Obviously this will throw a KeyError if the config isn't there.
        # A real implementation would have error handling here.
        config = self._config['application'][name]
        return LoadableConfig.app(name=name, config=config, global_config={})

    def server_config(self, name):
        config = self._config['server'][name]
        return LoadableConfig.server(name=name, config=config, global_config={})

    def filter_config(self, name):
        # Not covered in tests yet.
        raise NotImplementedError
