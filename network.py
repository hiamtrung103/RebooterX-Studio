"""Verified HTTPS using Windows chain building plus bundled public root CAs."""
from functools import lru_cache
import ssl
from urllib.parse import urlsplit

import certifi
import truststore


@lru_cache(maxsize=1)
def tls_context():
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=certifi.where())
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def certificate_error(error, url):
    reason = getattr(error, 'reason', error)
    if not isinstance(reason, ssl.SSLCertVerificationError):
        return None
    host = urlsplit(url).hostname or 'HTTPS server'
    return RuntimeError(
        f'Không xác minh được chứng chỉ HTTPS của {host}. '
        'Kiểm tra ngày/giờ Windows, cập nhật chứng chỉ Windows và nhờ quản trị '
        'phòng net kiểm tra proxy/phần mềm lọc HTTPS.\n'
        f'HTTPS certificate verification failed for {host}. Check Windows date/time, '
        'certificate updates and the network HTTPS proxy.\n'
        f'Detail: {getattr(reason, "verify_message", str(reason))}')
