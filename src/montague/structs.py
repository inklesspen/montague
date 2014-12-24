from __future__ import absolute_import

import weakref
from characteristic import attributes, Attribute


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


@attributes(['filters'], apply_with_init=False)
class ComposedFilter(object):
    def __init__(self):
        self.filters = []

    def add_filter(self, filter):
        self.filters.append(filter)

    def __call__(self, app):
        for filter in self.filters:
            app = filter(app)
        return app


@attributes(['loaded',
             Attribute('inner', default_value=None),
             Attribute('outer', default_value=None),
             Attribute('is_app', default_value=False)])
class Loadable(object):
    """A chain of Loadables is built from the config files. An app or filter with
       filter-with will become an Loadable with another Loadable as the 'outer'
       attribute, while a filter-app with a next property will become a Loadable
       with another Loadable as an 'inner' property."""
    def normalize(self):
        if self.outer is None:
            return self
        if isinstance(self.outer, weakref.ref):
            return self.outer()
        self.outer.inner = self
        outer = self.outer
        self.outer = weakref.ref(outer)
        return outer.normalize()

    def get(self):
        if self.inner is None:
            if self.is_app:
                return self.loaded
            else:
                # Need to compose these filters
                composed = ComposedFilter()
                composed.add_filter(self.loaded)
                return composed
        val = self.inner.get()
        if isinstance(val, ComposedFilter):
            # still composing
            val.add_filter(self.loaded)
            return val
        else:
            return self.loaded(val)
