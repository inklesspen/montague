from montague.compat.config import ConfigMiddleware
import pytest
from webtest import TestApp as WebtestApp


class Bug(Exception):
    pass


def app_with_exception(environ, start_response):
    def cont():
        yield b"something"
        raise Bug
    start_response(b'200 OK', [(b'Content-type', b'text/html')])
    return cont()


def test_error():
    wrapped = ConfigMiddleware(app_with_exception, {'test': 1})
    test_app = WebtestApp(wrapped)
    with pytest.raises(Bug):
        test_app.get('/')
