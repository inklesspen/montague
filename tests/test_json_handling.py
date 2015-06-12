import os
import pytest
import pkg_resources
import mock
from montague.loadwsgi import Loader
from montague import load_app, load_server
from montague.structs import DEFAULT
import montague_testapps

here = os.path.dirname(__file__)


@pytest.yield_fixture(scope='function')
def working_set():
    # This is kind of a lot of work to go to just to get a dummy entry point.
    # Also plenty of pkg_resources methods use the global working set with no
    # way to override it.
    # Better APIs for this would be very nice.
    mock_ws = pkg_resources.WorkingSet()
    dist = pkg_resources.get_distribution('montague')
    mock_ep = pkg_resources.EntryPoint('json', 'montague.testjson', ['JSONConfigLoader'], dist=dist)
    mock_dist = pkg_resources.Distribution(project_name='montague_testjson')
    mock_dist.location = dist.location
    mock_dist._ep_map = {
        'montague.config_loader': {
            'json': mock_ep
        }
    }
    mock_ws.add(mock_dist)
    patcher = mock.patch.multiple(pkg_resources,
                                  working_set=mock_ws,
                                  iter_entry_points=mock_ws.iter_entry_points,
                                  require=mock_ws.require)
    patcher.start()
    yield
    patcher.stop()


def test_read_config(working_set):
    expected = {
        'application': {
            DEFAULT: {'use': 'package:montague_testapps#basic_app'},
            'egg': {'use': 'egg:montague_testapps#other'},
            'filtered-app': {
                'filter-with': 'filter',
                'use': 'package:montague_testapps#basic_app',
            },
        },
        'filter': {
            'filter': {
                'use': 'egg:montague_testapps#caps',
                'method_to_call': 'lower',
            },
        },
        'server': {
            'server_factory': {
                'use': 'egg:montague_testapps#server_factory',
                'port': 42,
            },
            'server_runner': {
                'use': 'egg:montague_testapps#server_runner',
                'host': '127.0.0.1',
            },
        },
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
