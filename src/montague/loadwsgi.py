from __future__ import absolute_import

import os.path
import pkg_resources
from characteristic import attributes
from .ini import IniConfigLoader
from .vendor import reify
from .structs import LoadableConfig


scheme_loadable_types = {
    'application': 'app',
    'app': 'app',
    'composite': 'composite',
    'composit': 'composite',
}

loadable_type_entry_points = {
    'app': ['montague.app_factory', 'paste.app_factory'],
    'composite': ['paste.composite_factory', 'paste.composit_factory'],
}


@attributes(['path'], apply_with_init=False, apply_immutable=True)
class Loader(object):
    def __init__(self, path):
        self.path = path
        self.config_loader = Loader._find_config_loader(path)

    @staticmethod
    def _find_config_loader(config_path):
        suffix = _get_suffix(config_path)
        entry_point_name = "montague.config_loader"
        eps = tuple(pkg_resources.iter_entry_points(entry_point_name, suffix))
        if len(eps) == 0:
            # TODO log warning
            loader_cls = IniConfigLoader
        else:
            loader_cls = eps[0].load()
        return loader_cls(config_path)

    @reify
    def config(self):
        return self.config_loader.config()

    def app_config(self, name=None):
        try:
            return self.config_loader.app_config(name)
        except NotImplementedError:
            schemes = ['application', 'app', 'composite', 'composit']
            app_configs = []
            if name is None:
                name = "main"
            for scheme in schemes:
                key = ':'.join([scheme, name])
                loadable_type = scheme_loadable_types[scheme]
                if key in self.config:
                    groups = loadable_type_entry_points[loadable_type]
                    app_configs.append(LoadableConfig(
                        name=name,
                        entry_point_groups=groups,
                        loadable_type=loadable_type,
                        config=self.config[key]))
            if len(app_configs) == 0:
                raise Exception('TODO')
            app_config = app_configs[0]
            return app_config

    def load_app(self, name=None):
        app_config = self.app_config(name)
        scheme, resource = app_config.config['use'].split(':')
        pkg, name = resource.split('#')
        entry_point_map = pkg_resources.get_entry_map(pkg)
        factory = None
        for group in app_config.entry_point_groups:
            if group in entry_point_map:
                group_map = entry_point_map[group]
                if name in group_map:
                    factory = group_map[name].load()
                    break
        if factory is None:
            raise Exception('TODO')
        return factory({}, **app_config.config)


def _get_suffix(path):
    basename = os.path.basename(path)
    return ".".join(basename.split(".")[1:])
