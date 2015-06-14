from __future__ import absolute_import

import collections
import types


def validate_montague_standard_format(config):
    for key in ('globals', 'application', 'composite', 'filter', 'server', 'logging'):
        assert key in config
        assert isinstance(config[key], collections.Mapping)


def validate_config_loader_methods(config_loader):
    assert hasattr(config_loader, 'config')
    assert isinstance(config_loader.config, types.MethodType)
    specific_methods_required = False
    try:
        result = config_loader.config()
        validate_montague_standard_format(result)
    except NotImplementedError:
        # config loaders can fail to implement config() as long as they implement the other methods
        specific_methods_required = True

    for method in ('app_config', 'filter_config', 'server_config', 'logging_config'):
        if specific_methods_required:
            # If you don't implement .config(), you have to implement these
            assert hasattr(config_loader, method)
            assert isinstance(getattr(config_loader, method), types.MethodType)

        # We don't know the names of actual apps/filters/etc to load, but we do know
        # the loader shouldn't raise NotImplementedError if it has actually implemented them,
        # so we can try that.
        try:
            getattr(config_loader, method)('__bogus__')
        except NotImplementedError:
            if specific_methods_required:
                raise
        except Exception:
            # any other exception is fine here, because we don't know exactly what happens
            # with a bogus name. usually KeyError, but maybe something else would be raised
            pass
