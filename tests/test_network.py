from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
import threading
import unittest
import urllib.error
from unittest.mock import patch

import certifi
import core
import network


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'verified-local-https')

    def log_message(self, *_args):
        pass


class HttpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / 'fixtures' / 'tls'
        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(cls.fixture/'server.pem', cls.fixture/'server-key.pem')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.socket = server_context.wrap_socket(cls.server.socket, server_side=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'https://localhost:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def test_public_roots_bundled_and_verification_enabled(self):
        self.assertGreater(Path(certifi.where()).stat().st_size, 100000)
        context = network.tls_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
        self.assertIs(context, network.tls_context())

    def test_added_ca_builds_valid_chain_without_changing_windows_store(self):
        context = network.tls_context.__wrapped__()
        context.load_verify_locations(cafile=str(self.fixture/'ca.pem'))
        with patch('core.tls_context', return_value=context):
            self.assertEqual(core.Repository().request(self.url), b'verified-local-https')

    def test_unknown_ca_fails_closed_without_repeated_retries(self):
        with patch('core.time.sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError, 'chứng chỉ HTTPS'):
                core.Repository().request(self.url)
            sleep.assert_not_called()

    def test_trusted_ca_does_not_allow_wrong_hostname(self):
        context = network.tls_context.__wrapped__()
        context.load_verify_locations(cafile=str(self.fixture/'ca.pem'))
        with patch('core.tls_context', return_value=context):
            with self.assertRaisesRegex(RuntimeError, 'certificate verification failed'):
                core.Repository().request(self.url.replace('localhost', '127.0.0.1'))

    def test_temporary_connection_failure_retries_and_enforces_size_limit(self):
        with patch('core.urllib.request.urlopen', side_effect=urllib.error.URLError('offline')) as request, patch('core.time.sleep'):
            with self.assertRaises(urllib.error.URLError):
                core.Repository().request('https://example.test/')
            self.assertEqual(request.call_count, 3)
        context = network.tls_context.__wrapped__()
        context.load_verify_locations(cafile=str(self.fixture/'ca.pem'))
        with patch('core.tls_context', return_value=context):
            with self.assertRaisesRegex(ValueError, 'size limit'):
                core.Repository().request(self.url, limit=4)

    def test_http_download_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'require HTTPS'):
            core.Repository().request('http://example.test/')
