from __future__ import absolute_import

import os.path
import pkg_resources
from characteristic import attributes
from .ini import IniConfigLoader
from .vendor import reify
from .structs import LoadableConfig
from .compat.util import lookup_object
from .exceptions import UnsupportedPasteDeployFeature


scheme_loadable_types = {
    'application': 'app',
    'app': 'app',
    'composite': 'composite',
    'composit': 'composite',
    'server': 'server',
}

loadable_type_entry_points = {
    'app': ['paste.app_factory'],
    'composite': ['paste.composite_factory', 'paste.composit_factory'],
    'server': ['paste.server_factory', 'paste.server_runner'],
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
                for key in self.config:
                    key_scheme, key_name = key.split(':')
                    if key_name == name:
                        raise UnsupportedPasteDeployFeature(
                            'The scheme {0} is unsupported.'.format(key_scheme))
                raise Exception('TODO')
            app_config = app_configs[0]
            return app_config

    def _adapt_entry_point_factory(self, factory, entry_point_group):
        # TODO: use decorator or something to preserve signatures
        if entry_point_group in ['paste.composite_factory', 'paste.composit_factory']:
            def adapter(global_conf, **local_conf):
                return factory(self, global_conf, **local_conf)
            return adapter
        if entry_point_group == 'paste.server_runner':
            def outer(global_conf, **local_conf):
                def inner(wsgi_app):
                    return factory(wsgi_app, global_conf, **local_conf)
                return inner
            return outer
        return factory

    def _load_entry_point_factory(self, resource, entry_point_groups):
        pkg, name = resource.split('#')
        entry_point_map = pkg_resources.get_entry_map(pkg)
        factory = None
        for group in entry_point_groups:
            if group in entry_point_map:
                group_map = entry_point_map[group]
                if name in group_map:
                    factory = group_map[name].load()
                    factory = self._adapt_entry_point_factory(factory, group)
                    break
        if factory is None:
            raise Exception('TODO')
        return factory

    def _adapt_call_factory(self, factory, factory_type):
        # PasteDeploy assumes a call-type factory will meet the specification
        # for {type}_factory. That is, server_runner is not allowed.
        if factory_type == 'composite':
            def adapter(global_conf, **local_conf):
                return factory(self, global_conf, **local_conf)
            return adapter
        return factory

    def _load_call_factory(self, resource, factory_type):
        return self._adapt_call_factory(lookup_object(resource), factory_type)

    def load_app(self, name=None, global_conf=None):
        app_config = self.app_config(name)
        scheme, resource = app_config.config['use'].split(':', 1)
        if scheme in ('egg', 'package'):
            factory = self._load_entry_point_factory(
                resource, app_config.entry_point_groups)
        elif scheme == 'call':
            factory = self._load_call_factory(resource, app_config.loadable_type)
        else:
            raise Exception('TODO: scheme type {}'.format(scheme))
        local_conf = dict(app_config.config)
        del local_conf['use']
        if global_conf is None:
            global_conf = {}
        return factory(global_conf, **local_conf)

    get_app = load_app

    def server_config(self, name=None):
        try:
            return self.config_loader.server_config(name)
        except NotImplementedError:
            # TODO: abstract this out of here and app_config...
            schemes = ['server']
            server_configs = []
            if name is None:
                name = "main"
            for scheme in schemes:
                key = ':'.join([scheme, name])
                loadable_type = scheme_loadable_types[scheme]
                if key in self.config:
                    groups = loadable_type_entry_points[loadable_type]
                    server_configs.append(LoadableConfig(
                        name=name,
                        entry_point_groups=groups,
                        loadable_type=loadable_type,
                        config=self.config[key]))
            if len(server_configs) == 0:
                for key in self.config:
                    key_scheme, key_name = key.split(':')
                    if key_name == name:
                        raise UnsupportedPasteDeployFeature(
                            'The scheme {0} is unsupported.'.format(key_scheme))
                raise Exception('TODO')
            server_config = server_configs[0]
            return server_config

    def load_server(self, name=None, global_conf=None):
        server_config = self.server_config(name)
        scheme, resource = server_config.config['use'].split(':', 1)
        if scheme in ('egg', 'package'):
            factory = self._load_entry_point_factory(
                resource, server_config.entry_point_groups)
        elif scheme == 'call':
            factory = self._load_call_factory(resource, server_config.loadable_type)
        else:
            raise Exception('TODO: scheme type {}'.format(scheme))
        local_conf = dict(server_config.config)
        del local_conf['use']
        if global_conf is None:
            global_conf = {}
        return factory(global_conf, **local_conf)


def _get_suffix(path):
    basename = os.path.basename(path)
    return ".".join(basename.split(".")[1:])
