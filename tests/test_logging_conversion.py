import os
import pytest
from six.moves.configparser import ConfigParser
from montague.logging import convert_loggers, convert_handlers, convert_formatters, combine
import sys

here = os.path.dirname(__file__)


@pytest.fixture
def ini_cp():
    ini_dir = os.path.join(here, 'config_files')
    ini_path = os.path.join(ini_dir, 'logging.ini')
    cp = ConfigParser()
    cp.read(ini_path)
    return cp
    

def test_loggers(ini_cp):
    expected = {
        'root': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'simpleExample': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
    actual = convert_loggers(ini_cp)
    assert expected == actual


def test_handlers(ini_cp):
    # py26 names it 'strm' for unknown reasons
    stream_key_name = 'stream' if (sys.version_info[0] > 2 or sys.version_info[1] > 6) else 'strm'
    expected = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            stream_key_name: sys.stdout,
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'level': 'WARNING',
            'formatter': 'complicated',
        }
    }
    actual = convert_handlers(ini_cp)
    assert expected == actual


def test_formatters(ini_cp):
    expected = {
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'complicated': {
            'format': 'F1 %(asctime)s %(levelname)s %(message)s',
            'datefmt': '%a, %d %b %Y %H:%M:%S +0000',
            # class is omitted because it's the default
        },
        'withclass': {
            # montague doesn't have to inspect the callable for formatters
            # so this class doesn't have to exist
            '()': 'foobar.FooBarClass',
            'first': 'foo',
            'second': 'bar',
        },
    }
    actual = convert_formatters(ini_cp)
    assert expected == actual


def test_combined(ini_cp):
    loggers = convert_loggers(ini_cp)
    handlers = convert_handlers(ini_cp)
    formatters = convert_formatters(ini_cp)
    root_logger = loggers['root']
    other_loggers = dict([(k, v) for k, v in loggers.items() if k != 'root'])
    expected = {
        'version': 1,
        'root': root_logger,
        'loggers': other_loggers,
        'handlers': handlers,
        'formatters': formatters,
    }
    actual = combine(loggers, handlers, formatters)
    assert expected == actual
