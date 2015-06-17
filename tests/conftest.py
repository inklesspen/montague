import pytest
import pkg_resources
import mock
import montague.testjson


@pytest.yield_fixture(scope='function')
def working_set():
    # This is kind of a lot of work to go to just to get a dummy entry point.
    # Also plenty of pkg_resources methods use the global working set with no
    # way to override it.
    # Better APIs for this would be very nice.
    mock_ws = pkg_resources.WorkingSet()
    dist = pkg_resources.get_distribution('montague')
    mock_ep = pkg_resources.EntryPoint('json', 'montague.testjson', ['JSONConfigLoader'], dist=dist)
    mock_dist = pkg_resources.Distribution(project_name='montague_testjson', version='1.0')
    # There's some weird bug on Windows where if montague isn't installed
    # in develop mode, having mock_dist use dist's location won't work.
    mock_dist.location = montague.testjson.__file__
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
