from __future__ import absolute_import

from .compat.loadwsgi import ConfigLoader as CompatConfigLoader
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
        defaults = parser.defaults()
        data = {}
        for section in parser.sections():
            section_data = data.setdefault(section, {})
            for option in parser.options(section):
                if option in defaults:
                    continue
                section_data[option] = parser.get(section, option)
        self._data = data

    def config(self):
        if self._data is None:
            self._read_from_file()
        return self._data

    def app_config(self, name="main"):
        raise NotImplementedError

    def server_config(self, name="main"):
        raise NotImplementedError

    def filter_config(self, name="main"):
        raise NotImplementedError
