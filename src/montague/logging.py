from __future__ import absolute_import

import logging
import logging.handlers
import inspect


def convert_loggers(configparser):
    names = configparser.get('loggers', 'keys')
    names = [x.strip() for x in names.split(',')]
    retval = {}
    for name in names:
        items = configparser.items('logger_{0}'.format(name), raw=True)
        section = {}
        final_name = name
        for key, value in items:
            if key == 'qualname':
                final_name = value
                continue
            if key == 'propagate':
                value = (value == '1')
            if key == 'handlers':
                value = [x.strip() for x in value.split()]
            section[key] = value
        retval[final_name] = section
    return retval


# Stolen from stdlib's logging.config
def _resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found


def adapt_args(args, name):
    try:
        callable = _resolve(name)
    except ImportError:
        raise ValueError("unable to locate {0}".format(name))
    if inspect.isclass(callable):
        callable = callable.__init__
        skipself = True
    else:
        if not hasattr(callable, '__call__'):
            raise ValueError("{0} is not callable; can't process args".format(name))
        skipself = False
    argnames = inspect.getargspec(callable).args
    if skipself:
        if argnames[0] == 'self':
            argnames = argnames[1:]
    if len(argnames) < len(args):
        raise Exception("Too many args for {0}".format(name))
    return dict(zip(argnames, args))


def convert_handlers(configparser):
    names = configparser.get('handlers', 'keys')
    names = [x.strip() for x in names.split(',')]
    retval = {}
    for name in names:
        items = configparser.items('handler_{0}'.format(name), raw=True)
        section = {}
        args = tuple()
        for key, value in items:
            if key == 'args':
                args = eval(value, vars(logging))
                continue
            if key == 'class':
                klass = value
                continue
            section[key] = value
        try:
            # check in the logging namespace first
            eval(klass, vars(logging))
        except (AttributeError, NameError):
            section['class'] = klass
        else:
            section['class'] = 'logging.{0}'.format(klass)
        section.update(adapt_args(args, section['class']))
        retval[name] = section
    return retval


def convert_formatters(configparser):
    names = configparser.get('formatters', 'keys')
    names = [x.strip() for x in names.split(',')]
    retval = {}
    for name in names:
        items = configparser.items('formatter_{0}'.format(name), raw=True)
        section = {}
        retval[name] = section
        for key, value in items:
            if key == 'class':
                if value in ('Formatter', 'logging.Formatter'):
                    # default!
                    continue
                else:
                    key = '()'
            section[key] = value

    return retval


def combine(loggers, handlers, formatters):
    retval = {'version': 1}
    for k, v in loggers.items():
        if k == 'root':
            retval['root'] = v
        else:
            retval.setdefault('loggers', {})[k] = v
    retval['handlers'] = handlers
    retval['formatters'] = formatters
    return retval
