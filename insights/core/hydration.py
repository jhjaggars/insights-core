import logging
import os

from insights.core import archives
from insights.core.context import (ClusterArchiveContext,
                                   ExecutionContextMeta,
                                   HostArchiveContext)

log = logging.getLogger(__name__)

if hasattr(os, "scandir"):
    def get_all_files(path):
        with os.scandir(path) as it:
            for ent in it:
                if ent.is_dir(follow_symlinks=False):
                    for pth in get_all_files(ent.path):
                        yield pth
                elif ent.is_file(follow_symlinks=False):
                    yield ent.path

else:
    def get_all_files(path):
        for f in archives.get_all_files(path):
            if os.path.isfile(f) and not os.path.islink(f):
                yield f


def identify(files):
    common_path, ctx = ExecutionContextMeta.identify(files)
    if ctx:
        return common_path, ctx

    common_path = os.path.dirname(os.path.commonprefix(files))
    if not common_path:
        raise archives.InvalidArchive("Unable to determine common path")

    return common_path, HostArchiveContext


def create_context(path, context=None):
    top = os.listdir(path)
    arc = [os.path.join(path, f) for f in top if f.endswith(archives.COMPRESSION_TYPES)]
    if arc:
        return ClusterArchiveContext(path, all_files=arc)

    all_files = list(get_all_files(path))
    if not all_files:
        raise archives.InvalidArchive("No files in archive")

    common_path, ctx = identify(all_files)
    context = context or ctx
    return context(common_path, all_files=all_files)
