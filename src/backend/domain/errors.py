"""Domain errors.

The services translate low-level failures into these few, meaningful errors,
so the API and the UI can show a clear message instead of a stack trace.
"""


class RagError(Exception):
    """Base class for all expected errors in the backend."""


class UnsupportedFileError(RagError):
    """The file extension has no registered loader."""


class DocumentLoadError(RagError):
    """A file could not be parsed or contains no extractable text."""
