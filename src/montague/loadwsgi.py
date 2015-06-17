from __future__ import absolute_import

import os.path
import pkg_resources
from characteristic import attributes
from .ini import IniConfigLoader
from .vendor import reify
from .structs import LoadableConfig, Loadable, loadable_type_entry_points
from .exceptions import ConfigNotFound


scheme_loadable_types = {
    'application': 'app',
    'composite': 'composite',
    'server': 'server',
    'filter': 'filter',
}


def lookup_object(spec):
    """
    Looks up a module or object from a some.module:func_name specification.
    To just look up a module, omit the colon and everything after it.
    """
    parts, target = spec.split(':') if ':' in spec else (spec, None)
    module = __import__(parts)

    for part in parts.split('.')[1:] + ([target] if target else []):
        module = getattr(module, part)

    return module


class CompositeHelper(object):
    def __init__(self, loader):
        self.loader = loader

    def get_app(self, name='main', global_conf=None):
        return self.loader.load_app(name)


@attributes(['path'], apply_with_init=False, apply_immutable=True)
class Loader(object):
    def __init__(self, path):
        self.path = path
        self.config_loader = Loader._find_config_loader(path)

    @staticmethod
    def _find_config_loader(config_path):
        suffix = os.path.splitext(config_path)[1]  # returns ".ext"
        suffix = suffix[1:]  # we just want "ext"
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

    def _fallback_config_loader(self, schemes, kind, name):
        _configs = []
        global_config = self.config.get('globals', {})
        for scheme in schemes:
            scheme_config = self.config.get(scheme, {})
            if name in scheme_config:
                loadable_type = scheme_loadable_types[scheme]
                constructor = getattr(LoadableConfig, loadable_type)
                _configs.append(constructor(
                    name=name,
                    config=scheme_config[name],
                    global_config=global_config))
        if len(_configs) == 0:
            not_found = "the {0} {1}".format(kind, name)
            msg = "Unable to find the config for {0}".format(not_found)
            raise ConfigNotFound(msg)
        app_config = _configs[0]
        return app_config

    def app_config(self, name=None):
        try:
            if name is None:
                name = 'main'
            return self.config_loader.app_config(name)
        except (NotImplementedError, AttributeError):
            schemes = ['application', 'composite']
            app_config = self._fallback_config_loader(schemes, 'application', name)
            return app_config

    def _adapt_entry_point_factory(self, factory, entry_point_group):
        # TODO: use decorator or something to preserve signatures
        if entry_point_group in ['paste.composite_factory', 'paste.composit_factory']:
            def adapter(global_conf, **local_conf):
                helper = CompositeHelper(self)
                return factory(helper, global_conf, **local_conf)
            return adapter
        if entry_point_group in ['paste.server_runner', 'paste.filter_app_factory']:
            def outer(global_conf, **local_conf):
                def inner(wsgi_app):
                    return factory(wsgi_app, global_conf, **local_conf)
                return inner
            return outer
        return factory

    def _load_entry_point_factory(self, resource, entry_point_groups):
        if "#" in resource:
            pkg, name = resource.split('#')
        else:
            pkg, name = resource, "main"
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
        if factory_type == 'paste.composite_factory':
            def adapter(global_conf, **local_conf):
                helper = CompositeHelper(self)
                return factory(helper, global_conf, **local_conf)
            return adapter
        return factory

    def _load_call_factory(self, resource, factory_type):
        return self._adapt_call_factory(lookup_object(resource), factory_type)

    def _load_factory(self, location, factory_types):
        scheme, resource = location.split(':', 1)
        if scheme in ('egg', 'package'):
            factory = self._load_entry_point_factory(resource, factory_types)
        elif scheme == 'call':
            factory_type = [f for f in factory_types if f.endswith('_factory')][0]
            factory = self._load_call_factory(resource, factory_type)
        elif scheme == 'config':
            raise NotImplementedError("haven't implemented config delegation yet")
        else:
            raise NotImplementedError("assuming this is the 'import some code' type")
        return factory

    def _load_app_from_config(self, app_config):
        local_conf = dict(app_config.config)
        # resolve nested uses
        use = local_conf.pop('use')
        if ':' not in use:
            loadable = self._load_app(use)
            loadable.local_conf.update(local_conf)
            loadable.global_conf.update(app_config.global_config)
        else:
            factory = self._load_factory(use, app_config.entry_point_groups)
            loadable = Loadable(factory=factory, is_app=True,
                                global_conf=app_config.global_config,
                                local_conf=local_conf)
        filter_with = loadable.local_conf.pop('filter-with', None)
        loadable = loadable.normalize()
        if filter_with is not None:
            loadable.outer = self._load_filter(name=filter_with)
        return loadable

    def _load_app(self, name):
        if name is not None and name is not 'main' and ':' in name:
            # not a config section name, let's handle this
            factory = self._load_factory(name, loadable_type_entry_points['app'])
            loadable = Loadable(
                factory=factory, global_conf={}, local_conf={})
            return loadable
        app_config = self.app_config(name)
        return self._load_app_from_config(app_config)

    def load_app(self, name=None):
        loadable = self._load_app(name)
        return loadable.normalize().get()

    def server_config(self, name=None):
        try:
            if name is None:
                name = 'main'
            return self.config_loader.server_config(name)
        except (NotImplementedError, AttributeError):
            schemes = ['server']
            server_config = self._fallback_config_loader(schemes, 'server', name)
            return server_config

    def load_server(self, name=None):
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
        return factory(server_config.global_config, **local_conf)

    def filter_config(self, name=None):
        try:
            if name is None:
                name = 'main'
            return self.config_loader.filter_config(name)
        except (NotImplementedError, AttributeError):
            schemes = ['filter']
            filter_config = self._fallback_config_loader(schemes, 'filter', name)
            return filter_config

    def _load_filter_from_config(self, filter_config):
        local_conf = dict(filter_config.config)
        # resolve nested uses
        use = local_conf.pop('use')
        if ':' not in use:
            loadable = self._load_filter(use)
            loadable.local_conf.update(local_conf)
            loadable.global_conf.update(filter_config.global_config)
        else:
            scheme, resource = filter_config.config['use'].split(':', 1)
            if scheme in ('egg', 'package'):
                factory = self._load_entry_point_factory(
                    resource, filter_config.entry_point_groups)
            elif scheme == 'call':
                factory = self._load_call_factory(resource, filter_config.loadable_type)
            else:
                raise Exception('TODO: scheme type {}'.format(scheme))
            loadable = Loadable(
                factory=factory,
                global_conf=filter_config.global_config,
                local_conf=local_conf)
        filter_with = loadable.local_conf.pop('filter-with', None)
        loadable = loadable.normalize()
        if filter_with is not None:
            loadable.outer = self._load_filter(name=filter_with)
        return loadable

    def _load_filter(self, name):
        if name is not None and name is not 'main' and ':' in name:
            # not a config section name, let's handle this
            factory = self._load_factory(name, loadable_type_entry_points['filter'])
            loadable = Loadable(
                factory=factory, global_conf={}, local_conf={})
            return loadable
        filter_config = self.filter_config(name)
        return self._load_filter_from_config(filter_config)

    def load_filter(self, name=None):
        return self._load_filter(name).normalize().get()

    def logging_config(self, name=None):
        if name is None:
            name = 'main'
        try:
            return self.config_loader.logging_config(name)
        except (NotImplementedError, AttributeError):
            return self.config['logging'][name]
