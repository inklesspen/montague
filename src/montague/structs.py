from __future__ import absolute_import

from characteristic import attributes


@attributes(['kind'], apply_immutable=True)
class Sigil(object):
    pass

DEFAULT = Sigil(kind='loadable_config')


loadable_type_entry_points = {
    'app': ['paste.app_factory'],
    'composite': ['paste.composite_factory', 'paste.composit_factory'],
    'server': ['paste.server_factory', 'paste.server_runner'],
    'filter': ['paste.filter_factory', 'paste.filter_app_factory'],
}


@attributes(['name', 'entry_point_groups',
             'loadable_type', 'config'], apply_immutable=True)
class LoadableConfig(object):
    @classmethod
    def app(cls, name, config):
        return cls(name=name, config=config,
                   loadable_type='app',
                   entry_point_groups=loadable_type_entry_points['app'])

    @classmethod
    def composite(cls, name, config):
        return cls(name=name, config=config,
                   loadable_type='composite',
                   entry_point_groups=loadable_type_entry_points['composite'])

    @classmethod
    def server(cls, name, config):
        return cls(name=name, config=config,
                   loadable_type='server',
                   entry_point_groups=loadable_type_entry_points['server'])

    @classmethod
    def filter(cls, name, config):
        return cls(name=name, config=config,
                   loadable_type='filter',
                   entry_point_groups=loadable_type_entry_points['filter'])
