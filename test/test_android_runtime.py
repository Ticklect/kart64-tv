import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import android_runtime


class Response(io.BytesIO):
    def geturl(self):
        return 'https://release-assets.githubusercontent.com/example.apk'


class AndroidRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name)
        self.data = b'verified launcher bytes'
        spec = {'url': 'https://github.com/Ticklect/kart64-tv/releases/download/v1.0.1/test.apk',
                'size': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest()}
        self.manifest = {'variants': {abi: dict(spec) for abi in ('arm64-v8a', 'armeabi-v7a', 'x86_64')}}

    def prepare(self, abis='arm64-v8a,armeabi-v7a'):
        return android_runtime.prepare_android_runtime(abis, self.cache, manifest=self.manifest)

    def test_selects_first_supported_os_abi_not_hardware_guess(self):
        for abis, expected in [('arm64-v8a,armeabi-v7a', 'arm64-v8a'),
                               ('armeabi-v7a', 'armeabi-v7a'),
                               (' x86, x86_64,arm64-v8a ', 'x86_64')]:
            self.assertEqual(android_runtime.select_android_runtime(abis, self.manifest)[0], expected)
        for abis in ('', 'x86', 'unknown'):
            with self.assertRaises(ValueError):
                android_runtime.select_android_runtime(abis, self.manifest)

    def test_download_is_verified_and_reused_offline(self):
        with patch('android_runtime.urllib.request.urlopen', return_value=Response(self.data)):
            target = self.prepare()
        self.assertEqual(target.read_bytes(), self.data)
        with patch('android_runtime.urllib.request.urlopen', side_effect=AssertionError('network unavailable')):
            self.assertEqual(self.prepare(), target)

    def test_tampered_cache_is_replaced_only_with_verified_bytes(self):
        with patch('android_runtime.urllib.request.urlopen', return_value=Response(self.data)):
            target = self.prepare()
        target.write_bytes(b'corrupt cache')
        with patch('android_runtime.urllib.request.urlopen', return_value=Response(b'wrong')):
            with self.assertRaises(ValueError):
                self.prepare()
        self.assertEqual(target.read_bytes(), b'corrupt cache')
        with patch('android_runtime.urllib.request.urlopen', return_value=Response(self.data)):
            self.prepare()
        self.assertEqual(target.read_bytes(), self.data)

    def test_bad_downloads_never_leave_an_installable_apk(self):
        for content in (b'', self.data[:-1], b'x' * len(self.data), self.data + b'extra'):
            with self.subTest(content=content):
                with patch('android_runtime.urllib.request.urlopen', return_value=Response(content)):
                    with self.assertRaises(ValueError):
                        self.prepare()
                self.assertEqual(list(self.cache.iterdir()), [])

    def test_interrupted_download_cleans_temporary_file(self):
        response = Response(self.data)
        response.read = lambda size: (_ for _ in ()).throw(OSError('connection lost'))
        with patch('android_runtime.urllib.request.urlopen', return_value=response):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_https_is_required_before_and_after_redirect(self):
        self.manifest['variants']['arm64-v8a']['url'] = 'http://example.com/test.apk'
        with patch('android_runtime.urllib.request.urlopen', side_effect=AssertionError('must not download')):
            with self.assertRaises(ValueError):
                self.prepare()
        self.manifest['variants']['arm64-v8a']['url'] = 'https://github.com/example.apk'
        response = Response(self.data)
        response.geturl = lambda: 'http://example.com/test.apk'
        with patch('android_runtime.urllib.request.urlopen', return_value=response):
            with self.assertRaises(ValueError):
                self.prepare()
        self.assertEqual(list(self.cache.iterdir()), [])
