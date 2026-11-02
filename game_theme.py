"""Prepare a private menu skin from the player's archive. No game assets ship here.

Only named texture resources are decoded; archive paths are never extracted.
Unsupported archives retain the asset-free fallback. PNG encoding uses stdlib.
"""
import base64
import struct
import zipfile
import zlib


def decode_texture(data):
    if len(data) < 80 or data[:4] != b'\0' * 4 or data[4:8] != b'XETO':
        raise ValueError('Unsupported texture resource header')
    kind, width, height, size = struct.unpack_from('<4I', data, 64)
    if not (1 <= width <= 512 and 1 <= height <= 512) or kind not in (1, 2, 5):
        raise ValueError('Unsupported texture dimensions or format')
    count = width * height
    expected = {1: count * 4, 2: count * 2, 5: (count + 1) // 2}[kind]
    if size != expected or len(data) != 80 + size:
        raise ValueError('Invalid texture payload length')
    raw = data[80:]
    if kind == 1:
        return width, height, raw
    rgba = bytearray()
    if kind == 2:
        for (value,) in struct.iter_unpack('>H', raw):
            rgba.extend(((value >> 11 & 31) * 255 // 31, (value >> 6 & 31) * 255 // 31,
                         (value >> 1 & 31) * 255 // 31, 255 if value & 1 else 0))
    else:
        for i in range(count):
            value = (raw[i // 2] >> (0 if i % 2 else 4)) & 15
            rgba.extend((255, 255, 255, value * 17))
    return width, height, bytes(rgba)


def _png(width, height, rgba):
    def chunk(name, payload):
        return struct.pack('>I', len(payload)) + name + payload + struct.pack('>I', zlib.crc32(name + payload) & 0xffffffff)
    rows = b''.join(b'\0' + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def _url(width, height, rgba):
    return 'url("data:image/png;base64,' + base64.b64encode(_png(width, height, rgba)).decode('ascii') + '")'


def build_game_theme(archive):
    """Return bounded, self-contained CSS, or None for an incompatible archive."""
    try:
        with zipfile.ZipFile(archive) as source:
            def read(name, kind, width, height):
                info = source.getinfo(name)
                if info.file_size > 80 + 512 * 512 * 4:
                    raise ValueError('Oversized menu texture')
                data = source.read(info)
                if len(data) < 80 or struct.unpack_from('<3I', data, 64) != (kind, width, height):
                    raise ValueError('Incompatible menu texture')
                return decode_texture(data)

            background = read('textures/texture_tkmk00/background_blue_sky', 2, 320, 240)
            logo = read('textures/other_textures/logo_mario_kart_64', 1, 256, 128)
            glyphs = [(letter, read('textures/texture_data_2/font_letter_' + letter, 5, 26, 16)[2])
                      for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
            optional = dict(zip('0123456789', ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')))
            for char, name in optional.items():
                try:
                    glyphs.append((char, read('textures/texture_data_2/font_number_' + name, 5, 26, 16)[2]))
                except KeyError:
                    pass
            titles = []
            for name, width, selector in (
                ('texture_game_select', 200, 'body.k64-native-theme.k64-launcher h2'),
                ('texture_game_select', 200, 'body.k64-native-theme #k64-home h1'),
                ('texture_player_select', 220, 'body.k64-native-theme #k64-tv [data-page="controllers"] h1'),
                ('texture_option', 130, 'body.k64-native-theme #k64-tv [data-page="settings"] h1'),
            ):
                try:
                    image = read('textures/texture_tkmk00/' + name, 2, width, 32)
                    titles.append(selector + '{background-image:' + _url(*image) + ';'
                                  'background-repeat:no-repeat;background-position:center;background-size:auto 100%;height:1.25em;}'
                                  + selector + ' .tv-game-text{visibility:hidden;}')
                except KeyError:
                    pass

        # Crop horizontal padding, retain original height and antialiasing.
        atlas_width = len(glyphs) * 26
        atlas = bytearray(atlas_width * 16 * 4)
        rules = []
        for index, (char, pixels) in enumerate(glyphs):
            columns = [x for x in range(26) if any(pixels[(y * 26 + x) * 4 + 3] for y in range(16))]
            left, right = (min(columns), max(columns) + 1) if columns else (0, 8)
            for y in range(16):
                start = (y * atlas_width + index * 26) * 4
                atlas[start:start + 104] = pixels[y * 104:(y + 1) * 104]
            selector = '.tv-game-text [data-char="' + char + '"]'
            rules.append(selector + '{width:' + str((right - left) / 16) + 'em;'
                         'mask-position:-' + str((index * 26 + left) / 16) + 'em 0;'
                         '-webkit-mask-position:-' + str((index * 26 + left) / 16) + 'em 0;'
                         'mask-image:var(--mk-font);-webkit-mask-image:var(--mk-font);'
                         'mask-size:' + str(atlas_width / 16) + 'em 1em;-webkit-mask-size:' + str(atlas_width / 16) + 'em 1em;'
                         'background:var(--mk-letter-color);}' + selector + ':before{content:none}')
        css = ('/* Private: derived locally from your game archive; do not publish. */\n'
               'body{--mk-theme-version:1;--mk-background:' + _url(*background) + ';--mk-logo:' + _url(*logo)
               + ';--mk-font:' + _url(atlas_width, 16, atlas) + ';}\n' + '\n'.join(rules + titles) + '\n')
        if len(css) > 512000:
            return None
        return css
    except (KeyError, ValueError, zipfile.BadZipFile, struct.error):
        return None
