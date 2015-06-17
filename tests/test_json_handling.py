import os
from montague.loadwsgi import Loader
from montague import load_app, load_server
import montague_testapps.apps
from montague.validation import validate_montague_standard_format, validate_config_loader_methods

here = os.path.dirname(__file__)

LOGGING_CONFIG = {
    u'loggers': {
        u'sqlalchemy.engine': {u'handlers': [], u'level': u'INFO'},
        u'mimir': {u'handlers': [], u'level': u'DEBUG'}
    },
    u'version': 1,
    u'root': {
        u'handlers': [u'console'],
        u'level': u'INFO'
    },
    u'formatters': {
        u'generic': {u'format': u'%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s'}
    },
    u'handlers': {
        u'console': {
            u'formatter': u'generic',
            u'class': u'logging.StreamHandler',
            u'stream': u'ext://sys.stderr',
            u'level': u'NOTSET'
        }
    }
}


def test_read_config(working_set):
    expected = {
        "globals": {},
        'application': {
            'main': {'use': 'package:montague_testapps#basic_app'},
            'egg': {'use': 'egg:montague_testapps#other'},
            'filtered-app': {
                'filter-with': 'filter',
                'use': 'package:montague_testapps',
            },
        },
        "composite": {},
        'filter': {
            'filter': {
                'use': 'egg:montague_testapps#caps',
                'method_to_call': 'lower',
            },
        },
        'server': {
            'server_factory': {
                'use': 'egg:montague_testapps',
                'port': 42,
            },
            'server_runner': {
                'use': 'egg:montague_testapps#server_runner',
                'host': '127.0.0.1',
            },
        },
        'logging': {'main': LOGGING_CONFIG},
    }
    json_style_loader = Loader(os.path.join(here, 'config_files/simple_config.json'))

    assert json_style_loader.config_loader.config() == expected


def test_load_app(working_set):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is montague_testapps.apps.basic_app
    assert app2 is montague_testapps.apps.basic_app2


def test_load_server(working_set):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    server = load_server(config_path, name='server_factory')
    actual = server(montague_testapps.apps.basic_app)
    assert actual.montague_conf['local_conf']['port'] == 42
    resp = actual.get('/')
    assert b'This is basic app' == resp.body
    server = load_server(config_path, name='server_runner')
    actual = server(montague_testapps.apps.basic_app2)
    assert actual.montague_conf['local_conf']['host'] == '127.0.0.1'
    resp = actual.get('/')
    assert b'This is basic app2' == resp.body


def test_load_filtered_app(working_set):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    app = load_app(config_path, name='filtered-app')
    assert isinstance(app, montague_testapps.apps.CapFilter)
    assert app.app is montague_testapps.apps.basic_app
    assert app.method_to_call == 'lower'


def test_load_logging_config(working_set):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    loader = Loader(config_path)
    actual = loader.logging_config()
    assert actual == LOGGING_CONFIG


def test_validity(working_set):
    loader = Loader(os.path.join(here, 'config_files/simple_config.json'))
    config_loader = loader.config_loader
    validate_montague_standard_format(config_loader.config())
    validate_config_loader_methods(config_loader)
