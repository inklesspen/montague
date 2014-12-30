import os
from montague.loadwsgi import Loader
from montague import load_app, load_server
from montague.structs import DEFAULT

here = os.path.dirname(__file__)


def test_read_config(fakeapp):
    expected = {
        'application': {
            DEFAULT: {'use': 'package:FakeApp#basic_app'},
            'egg': {'use': 'egg:FakeApp#other'},
            'filtered-app': {
                'filter-with': 'filter',
                'use': 'package:FakeApp#basic_app',
            },
        },
        'filter': {
            'filter': {
                'use': 'egg:FakeApp#caps',
                'method_to_call': 'lower',
            },
        },
        'server': {
            'server_factory': {
                'use': 'egg:FakeApp#server_factory',
                'port': 42,
            },
            'server_runner': {
                'use': 'egg:FakeApp#server_runner',
                'host': '127.0.0.1',
            },
        },
    }
    json_style_loader = Loader(os.path.join(here, 'config_files/simple_config.json'))

    assert json_style_loader.config_loader.config() == expected


def test_load_app(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    app = load_app(config_path)
    app2 = load_app(config_path, name='egg')
    assert app is fakeapp.apps.basic_app
    assert app2 is fakeapp.apps.basic_app2


def test_load_server(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    server = load_server(config_path, name='server_factory')
    actual = server(fakeapp.apps.basic_app)
    assert actual.montague_conf['local_conf']['port'] == 42
    resp = actual.get('/')
    assert b'This is basic app' == resp.body
    server = load_server(config_path, name='server_runner')
    actual = server(fakeapp.apps.basic_app2)
    assert actual.montague_conf['local_conf']['host'] == '127.0.0.1'
    resp = actual.get('/')
    assert b'This is basic app2' == resp.body


def test_load_filtered_app(fakeapp):
    config_path = os.path.join(here, 'config_files/simple_config.json')
    app = load_app(config_path, name='filtered-app')
    assert isinstance(app, fakeapp.apps.CapFilter)
    assert app.app is fakeapp.apps.basic_app
    assert app.method_to_call == 'lower'
