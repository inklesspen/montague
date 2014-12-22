from __future__ import absolute_import

from .compat.loadwsgi import ConfigLoader as CompatConfigLoader
from six.moves.configparser import InterpolationMissingOptionError
from .interfaces import IConfigLoader, IConfigLoaderFactory
from zope.interface import directlyProvides, implementer
from characteristic import attributes


@attributes(['path'], apply_with_init=False, apply_immutable=True)
@implementer(IConfigLoader)
class IniConfigLoader(object):
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path
        self._data = None

    def _read_from_file(self):
        loader = CompatConfigLoader(self.path)
        parser = loader.parser
        self.defaults = parser.defaults()
        data = {}
        for section in parser.sections():
            section_data = data.setdefault(section, {})
            for option in parser.options(section):
                if option in self.defaults:
                    continue
                try:
                    section_data[option] = parser.get(section, option)
                except InterpolationMissingOptionError:
                    # TODO, mark this as needing reinterpolation
                    section_data[option] = parser.get(section, option, raw=True)
        self._data = data

    def config(self):
        if self._data is None:
            self._read_from_file()
        return self._data

    def ini_config(self):
        return self.config()

    def app_config(self, name):
        raise NotImplementedError

    def server_config(self, name):
        raise NotImplementedError

    def filter_config(self, name):
        raise NotImplementedError
