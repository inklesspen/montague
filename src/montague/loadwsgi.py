from __future__ import absolute_import

import os.path
import pkg_resources
from characteristic import attributes
from .ini import IniConfigLoader
from .vendor import reify
from .structs import LoadableConfig, DEFAULT, Loadable
from .compat.util import lookup_object
from .exceptions import UnsupportedPasteDeployFeature, ConfigNotFound


scheme_loadable_types = {
    'application': 'app',
    'app': 'app',
    'composite': 'composite',
    'composit': 'composite',
    'server': 'server',
    'filter': 'filter',
    'filter-app': 'filter',
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
        return self.config_loader.ini_config()

    def _fallback_config_loader(self, schemes, kind, name):
        _configs = []
        true_name = name
        if name is DEFAULT:
            name = "main"
        for scheme in schemes:
            key = ':'.join([scheme, name])
            if key in self.config:
                loadable_type = scheme_loadable_types[scheme]
                constructor = getattr(LoadableConfig, loadable_type)
                _configs.append(constructor(
                    name=name,
                    config=self.config[key]))
        if len(_configs) == 0:
            for key in self.config:
                key_scheme, key_name = key.split(':')
                if key_name == name:
                    raise UnsupportedPasteDeployFeature(
                        'The scheme {0} is unsupported.'.format(key_scheme))
            if true_name is DEFAULT:
                not_found = "the default {0}".format(kind)
            else:
                not_found = "the {0} {1}".format(kind, name)
            msg = "Unable to find the config for {0}".format(not_found)
            raise ConfigNotFound(msg)
        app_config = _configs[0]
        return app_config

    def app_config(self, name=None):
        try:
            if name is None:
                name = DEFAULT
            return self.config_loader.app_config(name)
        except NotImplementedError:
            schemes = ['application', 'app', 'composite', 'composit', 'filter-app']
            app_config = self._fallback_config_loader(schemes, 'application', name)
            return app_config

    def _adapt_entry_point_factory(self, factory, entry_point_group):
        # TODO: use decorator or something to preserve signatures
        if entry_point_group in ['paste.composite_factory', 'paste.composit_factory']:
            def adapter(global_conf, **local_conf):
                return factory(self, global_conf, **local_conf)
            return adapter
        if entry_point_group in ['paste.server_runner', 'paste.filter_app_factory']:
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

    def _load_app_from_config(self, app_config, global_conf):
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
        filter_with = local_conf.pop('filter-with', None)
        app_global_conf = global_conf
        if global_conf is None:
            app_global_conf = {}
        app = factory(app_global_conf, **local_conf)
        loadable = Loadable(loaded=app, is_app=True)
        if filter_with is not None:
            loadable.outer = self._load_filter(name=filter_with, global_conf=None)
        return loadable

    def _load_app(self, name, global_conf):
        app_config = self.app_config(name)
        is_app = (app_config.loadable_type in ['app', 'composite'])
        if is_app:
            return self._load_app_from_config(app_config, global_conf)
        else:
            # filter-app is loaded as an app, but actually is a filter.
            return self._load_filter_from_config(app_config, global_conf)

    def load_app(self, name=None, global_conf=None):
        loadable = self._load_app(name, global_conf)
        return loadable.normalize().get()

    # Supports composite app pattern.
    get_app = load_app

    def server_config(self, name=None):
        try:
            if name is None:
                name = DEFAULT
            return self.config_loader.server_config(name)
        except NotImplementedError:
            schemes = ['server']
            server_config = self._fallback_config_loader(schemes, 'server', name)
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

    def filter_config(self, name=None):
        try:
            if name is None:
                name = DEFAULT
            return self.config_loader.filter_config(name)
        except NotImplementedError:
            schemes = ['filter']
            filter_config = self._fallback_config_loader(schemes, 'filter', name)
            return filter_config

    def _load_filter_from_config(self, filter_config, global_conf):
        scheme, resource = filter_config.config['use'].split(':', 1)
        if scheme in ('egg', 'package'):
            factory = self._load_entry_point_factory(
                resource, filter_config.entry_point_groups)
        elif scheme == 'call':
            factory = self._load_call_factory(resource, filter_config.loadable_type)
        else:
            raise Exception('TODO: scheme type {}'.format(scheme))
        local_conf = dict(filter_config.config)
        del local_conf['use']
        filter_with = local_conf.pop('filter-with', None)
        next = local_conf.pop('next', None)
        if global_conf is None:
            global_conf = {}
        filter = factory(global_conf, **local_conf)
        loadable = Loadable(loaded=filter)
        if filter_with is not None:
            loadable.outer = self._load_filter(name=filter_with, global_conf=None)
        if next is not None:
            loadable.inner = self._load_app(name=next, global_conf=None)
        return loadable

    def _load_filter(self, name, global_conf):
        filter_config = self.filter_config(name)
        return self._load_filter_from_config(filter_config, global_conf)

    def load_filter(self, name=None, global_conf=None):
        return self._load_filter(name, global_conf).normalize().get()


def _get_suffix(path):
    basename = os.path.basename(path)
    return ".".join(basename.split(".")[1:])
