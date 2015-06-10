from __future__ import absolute_import

from six.moves.configparser import SafeConfigParser, InterpolationError
from .interfaces import IConfigLoader, IConfigLoaderFactory
from zope.interface import directlyProvides, implementer
from characteristic import attributes
from .structs import DEFAULT, LoadableConfig
from .logging import convert_loggers, convert_handlers, convert_formatters, combine
import six
import os.path

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
        self._data = self._read()
        self._config = self._process()

    def _read(self):
        parser = SafeConfigParser()
        parser.read(self.path)
        self._globals = parser.defaults()
        data = {}
        for section in parser.sections():
            section_data = data.setdefault(section, {})
            for option in parser.options(section):
                if option in self._globals:
                    continue
                try:
                    section_data[option] = parser.get(section, option)
                except InterpolationError:
                    section_data[option] = parser.get(section, option, raw=True)
        return data

    def _process(self):
        orig = self._data
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
        config['globals'] = {
            'here': os.path.dirname(self.path),
            '__file__': self.path,
        }
        for key, value in six.iteritems(self._globals):
            config['globals'][key] = value
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

    def config(self):
        return self._config

    def app_config(self, name):
        if name in self._config['application']:
            constructor = LoadableConfig.app
            local_config = self._config['application'][name]
        elif name in self._config['composite']:
            constructor = LoadableConfig.composite
            local_config = self._config['composite'][name]
        else:
            raise KeyError
        return constructor(
            name=name, config=local_config, global_config=self._config['globals'])

    def server_config(self, name):
        if name in self._config['server']:
            constructor = LoadableConfig.server
            local_config = self._config['server'][name]
        else:
            raise KeyError
        return constructor(
            name=name, config=local_config, global_config=self._config['globals'])

    def filter_config(self, name):
        if name in self._config['filter']:
            constructor = LoadableConfig.filter
            local_config = self._config['filter'][name]
        else:
            raise KeyError
        return constructor(
            name=name, config=local_config, global_config=self._config['globals'])

    def logging_config(self, name):
        if name != DEFAULT:
            raise KeyError
        parser = SafeConfigParser()
        parser.read(self.path)
        for section_name in ('loggers', 'handlers', 'formatters'):
            if not parser.has_section(section_name):
                raise KeyError
        loggers = convert_loggers(parser)
        handlers = convert_handlers(parser)
        formatters = convert_formatters(parser)
        return combine(loggers, handlers, formatters)
