from __future__ import absolute_import


class UnsupportedPasteDeployFeature(NotImplementedError):
    """Raise this exception to signal a PasteDeploy feature unsupported by Montague."""
    pass
