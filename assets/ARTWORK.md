# App artwork

`kart64-master.png` is the source artwork, created with OpenAI's built-in image-generation tool. It depicts an original kart rather than extracted game artwork. The launcher banner adds typeset text to the exported image.

To regenerate the platform sizes and Android TV banner:

```sh
pip install Pillow
python create_icons.py
```

The script exports Windows ICO sizes from 16 to 256 pixels, a 512px app icon, Samsung's 256px icon, LG's 80px/130px icons and the Android/Fire TV 320x180 banner. Arial Bold is used when installed, with Pillow's default font as a fallback. The large master is excluded from Windows executable packaging.

## Generation prompt

Create one finished premium app icon for Kart64 TV, a community retro kart racing TV app. Square 1024x1024 artwork edge-to-edge, no surrounding mockup, no whitespace outside. An exceptionally art-directed original chunky red go-kart with warm ivory and golden yellow accents, oversized dark rubber wheels, compact steering wheel and seat visible, viewed three-quarter front at dynamic diagonal facing lower left, large dominant recognizable silhouette taking 78% of frame. No driver, no characters, no Nintendo logos. Refined N64-era racing nostalgia translated into clean modern 3D editorial illustration: tactile painted enamel, simple sculpted forms, restrained soft studio lighting, sharp deliberate edges, subtle grain very minimal, high contrast not clutter. Deep midnight navy full-bleed square background with a single bold warm yellow curved racing stripe sweeping behind the kart near bottom, small subtle ivory checkerboard corner detail in upper right. Kart sits grounded with soft short shadow. Small race number '64' clean cream block numerals on front red nose panel, the only text. Not a toy product photo; a distinctive polished professional application icon. Limited red/navy/yellow/ivory palette. Avoid generic glowing gradients, neon, glass, chrome, cartoon faces, mountains, scenery, excessive speed lines, tiny detail, rounded-square outer frame. Composition must be legible at 32px, centered safe area with all wheels inside 10% margin.
