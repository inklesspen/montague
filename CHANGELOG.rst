
Changelog
=========

unreleased
-----------------------------------------

* Remove the PasteDeploy FakeApp package in favor of ``montague_testapps``.
* Enable a ``looponfail`` tox environment.
* Fix some eval-related bugs in the logging ini conversion.
* Reincorporate the test JSON config loader, active only during tests.
* Remove the ``DEFAULT`` sentinal value; we'll use 'main' as the default loadable name, just like grandpa used to do. This is a breaking change.

0.1.5 (2015-05-12)
-----------------------------------------

* The legacy PasteDeploy support was spun off into a separate package (``montague_pastedeploy``), enabling simplicity.

0.1.0 (2014-11-12)
-----------------------------------------

* First release on PyPI, corresponding to PasteDeploy 1.5.2.
* Backwards incompatibility: ConfigMiddleware stores the config under ``montague.config`` in the environment instead of ``paste.config`` and no longer offers a threadlocal ``CONFIG`` importable. (This removes the dependency on Paste.)
