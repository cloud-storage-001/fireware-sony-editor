"""A simple parser for tar archives"""

import io
import tarfile
from stat import *

from . import *
from ..util import *

TarHeader = Struct('TarHeader', [
    ('...', 257),
    ('magic', Struct.STR % 8),
    ('...', 235),
])
tarHeaderMagic = [b'ustar\x0000', b'ustar  \0']


def _convertFileType(type):
    return {
        tarfile.REGTYPE: S_IFREG,
        tarfile.LNKTYPE: S_IFLNK,
        tarfile.SYMTYPE: S_IFLNK,
        tarfile.CHRTYPE: S_IFCHR,
        tarfile.BLKTYPE: S_IFBLK,
        tarfile.DIRTYPE: S_IFDIR,
        tarfile.FIFOTYPE: S_IFIFO,
    }.get(type, S_IFREG)


def isTar(file):
    """Returns true if the file provided is a tar file"""
    header = TarHeader.unpack(file)
    return header and header.magic in tarHeaderMagic


def readTar(file):
    """Unpacks a .tar file and returns a the contained files"""
    file.seek(0)
    tar = tarfile.TarFile(fileobj=file)
    for member in tar:
        yield UnixFile(
            path='/' + member.name,
            size=member.size,
            mtime=member.mtime,
            mode=_convertFileType(member.type) | member.mode,
            uid=member.uid,
            gid=member.gid,
            contents=tar.extractfile(member) if not member.issym() else io.BytesIO(member.linkname.encode('latin1')),
        )
