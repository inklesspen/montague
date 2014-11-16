import os
from montague.compat import loadapp

here = os.path.dirname(__file__)


def test_main(fakeapp):
    app = loadapp('config:sample_configs/basic_app.ini',
                  relative_to=here)
    assert app is fakeapp.apps.basic_app
    app = loadapp('config:sample_configs/basic_app.ini#main',
                  relative_to=here)
    assert app is fakeapp.apps.basic_app
    app = loadapp('config:sample_configs/basic_app.ini',
                  relative_to=here, name='main')
    assert app is fakeapp.apps.basic_app
    app = loadapp('config:sample_configs/basic_app.ini#ignored',
                  relative_to=here, name='main')
    assert app is fakeapp.apps.basic_app


def test_other(fakeapp):
    app = loadapp('config:sample_configs/basic_app.ini#other',
                  relative_to=here)
    assert app is fakeapp.apps.basic_app2


def test_composit(fakeapp):
    app = loadapp('config:sample_configs/basic_app.ini#remote_addr',
                  relative_to=here)
    assert isinstance(app, fakeapp.apps.RemoteAddrDispatch)
    assert app.map['127.0.0.1'] is fakeapp.apps.basic_app
    assert app.map['0.0.0.0'] is fakeapp.apps.basic_app2
