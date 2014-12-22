from __future__ import absolute_import

from .compat.loadwsgi import ConfigLoader as CompatConfigLoader
from six.moves.configparser import InterpolationMissingOptionError
from .interfaces import IConfigLoader, IConfigLoaderFactory
from zope.interface import directlyProvides, implementer
from characteristic import attributes
import copy
import six


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
        if self._data is None:
            self._read_from_file()
        auto_gen_count = 0
        additional = {}
        workdata = copy.deepcopy(self._data)
        for value in six.itervalues(workdata):
            if 'filter-with' in value:
                # Need to make this into a section if it isn't already
                if ':' in value['filter-with']:
                    auto_gen_count += 1
                    auto_gen_name = 'filter-{0}'.format(auto_gen_count)
                    additional['filter:{0}'.format(auto_gen_name)] = {
                        'use': value['filter-with']
                    }
                    value['filter-with'] = auto_gen_name
        workdata.update(additional)
        return workdata

    def app_config(self, name):
        raise NotImplementedError

    def server_config(self, name):
        raise NotImplementedError

    def filter_config(self, name):
        raise NotImplementedError
