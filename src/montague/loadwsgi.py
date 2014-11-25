from __future__ import absolute_import

import os.path
import pkg_resources
from .ini import IniConfigLoader


scheme_app_types = {
    'application': 'app',
    'app': 'app',
    'composite': 'composite',
    'composit': 'composite',
}

app_type_entry_points = {
    'app': ['montague.app_factory', 'paste.app_factory'],
    'composite': ['paste.composite_factory', 'paste.composit_factory'],
}


def load_app_from_app_config(app_config):
    scheme, resource = app_config['use'].split(':')
    pkg, name = resource.split('#')
    entry_point_map = pkg_resources.get_entry_map(pkg)
    factory = None
    for group in app_type_entry_points['app']:
        if group in entry_point_map:
            group_map = entry_point_map[group]
            if name in group_map:
                factory = group_map[name].load()
                break
    if factory is None:
        raise Exception('TODO')
    return factory({}, **app_config)


def _get_suffix(path):
    basename = os.path.basename(path)
    return ".".join(basename.split(".")[1:])


def read_config(config_path):
    suffix = _get_suffix(config_path)
    entry_point_name = "montague.config_loader"
    eps = tuple(pkg_resources.iter_entry_points(entry_point_name, suffix))
    if len(eps) == 0:
        # TODO log warning
        loader_cls = IniConfigLoader
    else:
        loader_cls = eps[0].load()
    return loader_cls(config_path)


def load_app(config_path, name="main"):
    config_loader = read_config(config_path)
    try:
        app_config = config_loader.app_config(name=name)
    except NotImplementedError:
        config = config_loader.config()
        schemes = ['application', 'app', 'composite', 'composit']
        app_configs = []
        for scheme in schemes:
            key = ':'.join([scheme, name])
            if key in config:
                app_configs.append(dict(
                    name=name, type=scheme_app_types[scheme],
                    config=config[key]))
        if len(app_configs) == 0:
            raise Exception('TODO')
        app_config = app_configs[0]['config']
    return load_app_from_app_config(app_config)


def load_wsgi(config_path, name="main"):
    pass


def load_filter(config_path, name="main"):
    pass


def app_config(config_path, name="main"):
    pass
