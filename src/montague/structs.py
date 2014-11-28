from __future__ import absolute_import

from characteristic import attributes


@attributes(['name', 'entry_point_groups',
             'loadable_type', 'config'], apply_immutable=True)
class LoadableConfig(object):
    pass
