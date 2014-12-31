from __future__ import absolute_import

from collections import OrderedDict
from .compat.loadwsgi import ConfigLoader as CompatConfigLoader
from six.moves.configparser import InterpolationMissingOptionError
from .interfaces import IConfigLoader, IConfigLoaderFactory
from zope.interface import directlyProvides, implementer
from characteristic import attributes
from .vendor import reify
from .structs import DEFAULT, LoadableConfig
import copy
import six

SCHEMEMAP = {
    'application': 'application',
    'app': 'application',
    'composite': 'composite',
    'composit': 'composite',
    'server': 'server',
    'filter': 'filter',
    'filter-app': 'filter-app',
    'pipeline': 'pipeline'
}


@attributes(['path'], apply_with_init=False, apply_immutable=True)
@implementer(IConfigLoader)
class IniConfigLoader(object):
    directlyProvides(IConfigLoaderFactory)

    def __init__(self, path):
        self.path = path

    @reify
    def _data(self):
        loader = CompatConfigLoader(self.path)
        parser = loader.parser
        self._globals = parser.defaults()
        data = {}
        for section in parser.sections():
            # Order matters for get/set overrides
            section_data = data.setdefault(section, OrderedDict())
            for option in parser.options(section):
                if option in self._globals:
                    continue
                try:
                    section_data[option] = parser.get(section, option)
                except InterpolationMissingOptionError:
                    # TODO, mark this as needing reinterpolation
                    section_data[option] = parser.get(section, option, raw=True)
        return data

    @reify
    def _config(self):
        # We're going to be mutating the contents; better make a copy
        orig = copy.deepcopy(self._data)
        config = {}
        for key in six.iterkeys(orig):
            if ':' in key:
                scheme, name = key.split(':', 1)
                kind_config = config.setdefault(SCHEMEMAP[scheme], {})
                if name == 'main':
                    name = DEFAULT
                kind_config[name] = orig[key]
            else:
                config[key] = orig[key]
        config['globals'] = copy.deepcopy(self._globals)
        apps = config.setdefault('application', {})
        filters = config.setdefault('filter', {})
        generated_filter_count = 0
        filter_apps = config.pop('filter-app', {})
        for name, filter_app in six.iteritems(filter_apps):
            use = filter_app.pop('next')
            generated_filter_count += 1
            filter_name = '_montague_filter_{0}'.format(generated_filter_count)
            apps[name] = {'use': use, 'filter-with': filter_name}
            filters[filter_name] = filter_app
        pipelines = config.pop('pipeline', {})
        for name, pipeline in six.iteritems(pipelines):
            items = pipeline['pipeline'].split()
            pipeline_app = items[-1]
            pipeline_filters = items[:-1]
            pipeline_filters.reverse()
            apps[name] = {'use': pipeline_app}
            last_item = apps[name]
            for count, use_filter in enumerate(pipeline_filters, start=1):
                filter_name = '_montague_pipeline_{0}_filter_{1}'.format(name, count)
                filters[filter_name] = {'use': use_filter}
                last_item['filter-with'] = filter_name
                last_item = filters[filter_name]
        return config

    @reify
    def defaults(self):
        return self._config['globals']

    def config(self):
        return self._config

    def _process_config(self, name, local_config, constructor):
        global_config = copy.deepcopy(self._config['globals'])
        local_config = copy.deepcopy(local_config)
        # We're gonna modify the config; make a copy of the keys.
        keys = tuple(six.iterkeys(local_config))
        for key in keys:
            if key[:4] == 'get ':
                global_key = local_config.pop(key)
                local_config[key[4:]] = global_config[global_key]
            elif key[:4] == 'set ':
                new_val = local_config.pop(key)
                global_config[key[4:]] = new_val
        return constructor(name=name, config=local_config, global_config=global_config)

    def app_config(self, name):
        if name in self._config['application']:
            constructor = LoadableConfig.app
            local_config = self._config['application'][name]
        elif name in self._config['composite']:
            constructor = LoadableConfig.composite
            local_config = self._config['composite'][name]
        else:
            raise KeyError
        return self._process_config(name, local_config, constructor)

    def server_config(self, name):
        if name in self._config['server']:
            constructor = LoadableConfig.server
            local_config = self._config['server'][name]
        else:
            raise KeyError
        return self._process_config(name, local_config, constructor)

    def filter_config(self, name):
        if name in self._config['filter']:
            constructor = LoadableConfig.filter
            local_config = self._config['filter'][name]
        else:
            raise KeyError
        return self._process_config(name, local_config, constructor)
