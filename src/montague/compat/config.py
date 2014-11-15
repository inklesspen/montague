# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""Paste Configuration Middleware and Objects"""
import re

__all__ = ['ConfigMiddleware', 'PrefixMiddleware']


class ConfigMiddleware(object):

    """
    A WSGI middleware that adds a ``montague.config`` key to the request
    environment.
    """

    def __init__(self, application, config):
        """
        This delegates all requests to `application`, adding a *copy*
        of the configuration `config`.
        """
        self.application = application
        self.config = config

    def __call__(self, environ, start_response):
        popped_config = None
        if 'montague.config' in environ:
            popped_config = environ['montague.config']
        environ['montague.config'] = self.config.copy()
        app_iter = None
        try:
            app_iter = self.application(environ, start_response)
        finally:
            if app_iter is None:
                # An error occurred...
                if popped_config is not None:
                    environ['montague.config'] = popped_config
        if type(app_iter) in (list, tuple):
            # Because it is a concrete iterator (not a generator) we
            # know the configuration for this request is no longer
            # needed:
            if popped_config is not None:
                environ['montague.config'] = popped_config
        return app_iter


def make_config_filter(app, global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    return ConfigMiddleware(app, conf)

make_config_middleware = ConfigMiddleware.__doc__


class PrefixMiddleware(object):
    """Translate a given prefix into a SCRIPT_NAME for the filtered
    application.

    PrefixMiddleware provides a way to manually override the root prefix
    (SCRIPT_NAME) of your application for certain, rare situations.

    When running an application under a prefix (such as '/james') in
    FastCGI/apache, the SCRIPT_NAME environment variable is automatically
    set to to the appropriate value: '/james'. Pylons' URL generating
    functions, such as url_for, always take the SCRIPT_NAME value into account.

    One situation where PrefixMiddleware is required is when an application
    is accessed via a reverse proxy with a prefix. The application is accessed
    through the reverse proxy via the the URL prefix '/james', whereas the
    reverse proxy forwards those requests to the application at the prefix '/'.

    The reverse proxy, being an entirely separate web server, has no way of
    specifying the SCRIPT_NAME variable; it must be manually set by a
    PrefixMiddleware instance. Without setting SCRIPT_NAME, url_for will
    generate URLs such as: '/purchase_orders/1', when it should be
    generating: '/james/purchase_orders/1'.

    To filter your application through a PrefixMiddleware instance, add the
    following to the '[app:main]' section of your .ini file:

    .. code-block:: ini

        filter-with = proxy-prefix

        [filter:proxy-prefix]
        use = egg:PasteDeploy#prefix
        prefix = /james

    The name ``proxy-prefix`` simply acts as an identifier of the filter
    section; feel free to rename it.

    Also, unless disabled, the ``X-Forwarded-Server`` header will be
    translated to the ``Host`` header, for cases when that header is
    lost in the proxying.  Also ``X-Forwarded-Host``,
    ``X-Forwarded-Scheme``, and ``X-Forwarded-Proto`` are translated.

    If ``force_port`` is set, SERVER_PORT and HTTP_HOST will be
    rewritten with the given port.  You can use a number, string (like
    '80') or the empty string (whatever is the default port for the
    scheme).  This is useful in situations where there is port
    forwarding going on, and the server believes itself to be on a
    different port than what the outside world sees.

    You can also use ``scheme`` to explicitly set the scheme (like
    ``scheme = https``).
    """
    def __init__(self, app, global_conf=None, prefix='/',
                 translate_forwarded_server=True,
                 force_port=None, scheme=None):
        self.app = app
        self.prefix = prefix.rstrip('/')
        self.translate_forwarded_server = translate_forwarded_server
        self.regprefix = re.compile("^%s(.*)$" % self.prefix)
        self.force_port = force_port
        self.scheme = scheme

    def __call__(self, environ, start_response):
        url = environ['PATH_INFO']
        url = re.sub(self.regprefix, r'\1', url)
        if not url:
            url = '/'
        environ['PATH_INFO'] = url
        environ['SCRIPT_NAME'] = self.prefix
        if self.translate_forwarded_server:
            if 'HTTP_X_FORWARDED_SERVER' in environ:
                environ['SERVER_NAME'] = environ['HTTP_HOST'] = \
                    environ.pop('HTTP_X_FORWARDED_SERVER').split(',')[0]
            if 'HTTP_X_FORWARDED_HOST' in environ:
                environ['HTTP_HOST'] = environ.pop('HTTP_X_FORWARDED_HOST').split(',')[0]
            if 'HTTP_X_FORWARDED_FOR' in environ:
                environ['REMOTE_ADDR'] = \
                    environ.pop('HTTP_X_FORWARDED_FOR').split(',')[0]
            if 'HTTP_X_FORWARDED_SCHEME' in environ:
                environ['wsgi.url_scheme'] = environ.pop('HTTP_X_FORWARDED_SCHEME')
            elif 'HTTP_X_FORWARDED_PROTO' in environ:
                environ['wsgi.url_scheme'] = environ.pop('HTTP_X_FORWARDED_PROTO')
        if self.force_port is not None:
            host = environ.get('HTTP_HOST', '').split(':', 1)[0]
            if self.force_port:
                host = '%s:%s' % (host, self.force_port)
                environ['SERVER_PORT'] = str(self.force_port)
            else:
                if environ['wsgi.url_scheme'] == 'http':
                    port = '80'
                else:
                    port = '443'
                environ['SERVER_PORT'] = port
            environ['HTTP_HOST'] = host
        if self.scheme is not None:
            environ['wsgi.url_scheme'] = self.scheme
        return self.app(environ, start_response)


def make_prefix_middleware(
        app, global_conf, prefix='/',
        translate_forwarded_server=True,
        force_port=None, scheme=None):
    from paste.deploy.converters import asbool
    translate_forwarded_server = asbool(translate_forwarded_server)
    return PrefixMiddleware(
        app, prefix=prefix,
        translate_forwarded_server=translate_forwarded_server,
        force_port=force_port, scheme=scheme)

make_prefix_middleware.__doc__ = PrefixMiddleware.__doc__
