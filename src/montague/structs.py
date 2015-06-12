from __future__ import absolute_import

from itertools import tee
from six.moves import zip as izip
from characteristic import attributes, Attribute


loadable_type_entry_points = {
    'app': ['paste.app_factory'],
    'composite': ['paste.composite_factory', 'paste.composit_factory'],
    'server': ['paste.server_factory', 'paste.server_runner'],
    'filter': ['paste.filter_factory', 'paste.filter_app_factory'],
}


@attributes(['name', 'entry_point_groups', 'loadable_type',
             'config', 'global_config'], apply_immutable=True)
class LoadableConfig(object):
    @classmethod
    def app(cls, name, config, global_config):
        return cls(name=name, config=config, global_config=global_config,
                   loadable_type='app',
                   entry_point_groups=loadable_type_entry_points['app'])

    @classmethod
    def composite(cls, name, config, global_config):
        return cls(name=name, config=config, global_config={},
                   loadable_type='composite',
                   entry_point_groups=loadable_type_entry_points['composite'])

    @classmethod
    def server(cls, name, config, global_config):
        return cls(name=name, config=config, global_config={},
                   loadable_type='server',
                   entry_point_groups=loadable_type_entry_points['server'])

    @classmethod
    def filter(cls, name, config, global_config):
        return cls(name=name, config=config, global_config={},
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


@attributes(['factory', 'local_conf', 'global_conf',
             Attribute('inner', default_value=None),
             Attribute('outer', default_value=None),
             Attribute('is_app', default_value=False)])
class Loadable(object):
    """A chain of Loadables is built from the config files. An app or filter with
       filter-with will become an Loadable with another Loadable as the 'outer'
       attribute, while a filter-app with a next property will become a Loadable
       with another Loadable as an 'inner' property."""
    def normalize(self):
        # The desired end state is a chain of loadables, starting with
        # the outermost filter, each with an inner property; the final
        # loadable contains the app (or last filter) and has no inner.

        # We call this method on what we can treat as the root loadable
        # of a binary tree, perform an in-order traversal to get the chain,
        # and then reconstruct the chain as (effectively) a linked list.

        chain = []
        self._make_chain(chain)
        for node in chain:
            node.inner = None
            node.outer = None
        for parent, child in pairwise(chain):
            parent.inner = child
        return chain[0]

    def _make_chain(self, chain):
        if self.outer is not None:
            self.outer._make_chain(chain)
        chain.append(self)
        if self.inner is not None:
            self.inner._make_chain(chain)

    def get(self):
        loaded = self.factory(self.global_conf, **self.local_conf)
        if self.inner is None:
            if self.is_app:
                return loaded
            else:
                # Need to compose these filters
                composed = ComposedFilter()
                composed.add_filter(loaded)
                return composed
        val = self.inner.get()
        if isinstance(val, ComposedFilter):
            # still composing
            val.add_filter(loaded)
            return val
        else:
            return loaded(val)


def pairwise(iterable):
    # recipe from itertools
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
