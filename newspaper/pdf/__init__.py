from ._version import __version__
from .merger import PdfFileMerger
from .pagerange import PageRange, parse_filename_page_ranges
from .pdf import PdfFileReader, PdfFileWriter

__all__ = ["pdf", "PdfFileMerger"]
