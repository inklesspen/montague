from montague.compat.config import ConfigMiddleware
import pytest
from webtest import TestApp as WebtestApp
import six


class Bug(Exception):
    pass


def app_with_exception(environ, start_response):
    def cont():
        yield "something"
        raise Bug
    start_response('200 OK', [('Content-type', 'text/html')])
    return cont()


@pytest.mark.skipif(six.PY3, reason="ConfigMiddleware requires Paste, which is py2-only")
def test_error():
    wrapped = ConfigMiddleware(app_with_exception, {'test': 1})
    test_app = WebtestApp(wrapped)
    with pytest.raises(Bug):
        test_app.get('/')
