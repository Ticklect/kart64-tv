"""Synthetic textures only: no Nintendo pixels or fonts in these fixtures."""
import base64, re, struct, tempfile, unittest, zipfile, zlib
from pathlib import Path
from game_theme import build_game_theme, decode_texture


def texture(kind, w, h, payload):
    header = bytearray(80)
    header[4:8] = b'XETO'
    struct.pack_into('<4I', header, 64, kind, w, h, len(payload))
    return bytes(header) + payload


def theme_archive(path):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('textures/texture_tkmk00/background_blue_sky', texture(2, 320, 240, b'\xf8\x01' * 76800))
        z.writestr('textures/other_textures/logo_mario_kart_64', texture(1, 256, 128, b'\xff' * 131072))
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            # An invented bar, not a game glyph.
            z.writestr('textures/texture_data_2/font_letter_' + letter, texture(5, 26, 16, b'\x00' * 13 + b'\xff' * 13 * 14 + b'\x00' * 13))


class ThemeTests(unittest.TestCase):
    def test_rgba16_uses_n64_big_endian_and_one_bit_alpha(self):
        w,h,pixels = decode_texture(texture(2, 2, 1, b'\xf8\x01\x07\xc0'))
        self.assertEqual((w,h), (2,1))
        self.assertEqual(pixels, bytes([255,0,0,255, 0,255,0,0]))

    def test_i4_expands_high_nibble_first_as_an_alpha_mask(self):
        self.assertEqual(decode_texture(texture(5,2,1,b'\xf8'))[2], bytes([255,255,255,255,255,255,255,136]))

    def test_rejects_bad_headers_lengths_formats_and_dimensions(self):
        for bad in [b'x', texture(99,2,1,b'aa'), texture(2,20000,20000,b'aa'), texture(2,2,2,b'aa'), b'\x01'+texture(2,1,1,b'aa')[1:]]:
            with self.subTest(size=len(bad)):
                with self.assertRaises(ValueError): decode_texture(bad)

    def test_missing_or_incompatible_assets_keep_the_plain_theme(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'custom.o2r'
            with zipfile.ZipFile(p,'w') as z: z.writestr('other','custom')
            self.assertIsNone(build_game_theme(p))
            with zipfile.ZipFile(p,'w') as z: z.writestr('textures/texture_tkmk00/background_blue_sky',b'incompatible')
            self.assertIsNone(build_game_theme(p))

    def test_generated_theme_is_self_contained_and_uses_only_allowlisted_assets(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'game.o2r';theme_archive(p)
            with zipfile.ZipFile(p,'a') as z: z.writestr('private-secret.txt','NEVER INCLUDE THIS')
            css=build_game_theme(p)
            self.assertIn('--mk-theme-version:1', css)
            self.assertIn('--mk-logo:', css)
            self.assertIn('[data-char="A"]', css)
            self.assertNotIn('NEVER INCLUDE THIS',css)
            self.assertNotIn('http',css)
            images=re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)',css)
            self.assertEqual(len(images),3)
            for payload in images: self.assertTrue(base64.b64decode(payload).startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertLess(len(css),512000)

    def test_all_private_install_formats_receive_the_derived_theme(self):
        from installer_core import make_package
        from webos_core import prepare_webos_stage, FILES
        from android_core import create_content_tar
        import tarfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);game=p/'game.o2r';theme_archive(game);stage=p/'runtime';stage.mkdir()
            for name in (*FILES,'config.xml'):
                f=stage/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'test')
            expected=build_game_theme(game).encode('utf-8')
            with zipfile.ZipFile(make_package(stage,game,p/'private.wgt')) as z:
                self.assertEqual(z.read('tv-game-theme.css'),expected)
            out=p/'webos';out.mkdir();prepare_webos_stage(stage,game,out)
            self.assertEqual((out/'tv-game-theme.css').read_bytes(),expected)
            with tarfile.open(create_content_tar(stage,game,p/'content.tar')) as t:
                self.assertEqual(t.extractfile('tv-game-theme.css').read(),expected)

    def test_android_reinstall_resets_an_old_skin_when_new_archive_has_no_assets(self):
        from android_core import create_content_tar
        from webos_core import FILES
        import tarfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);stage=p/'runtime';stage.mkdir();game=p/'custom.o2r'
            for name in FILES:
                f=stage/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'test')
            with zipfile.ZipFile(game,'w') as z:z.writestr('custom','data')
            with tarfile.open(create_content_tar(stage,game,p/'content.tar')) as t:
                reset=t.extractfile('tv-game-theme.css').read().decode('utf-8')
                self.assertIn('--mk-theme-version:0',reset)
                self.assertNotIn('data:image',reset)
