from __future__ import absolute_import

import json
from montague.structs import LoadableConfig


class JSONConfigLoader(object):
    """This is a sample config loader. It uses a structural
       convention that makes more sense for JSON; the root object
       contains 'application' and 'server' keys, which each contain keys
       for the respective items. It has basically no error handling
       and is kind of inefficient."""

    def __init__(self, path):
        self.path = path

    @property
    def _config(self):
        return json.load(open(self.path))

    def config(self):
        return self._config

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

    def logging_config(self, name):
        # montague should be able to load it from the .config() property.
        raise NotImplementedError
