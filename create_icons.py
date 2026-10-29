"""Generate original application artwork; requires Pillow when rebuilding assets."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def generate():
    out=Path(__file__).resolve().parent/'assets';out.mkdir(exist_ok=True)
    image=Image.new('RGBA',(512,512));d=ImageDraw.Draw(image)
    d.rounded_rectangle((8,8,504,504),radius=100,fill='#102b51',outline='#6984a5',width=8)
    for y in range(2):
        for x in range(10):
            d.rectangle((56+x*40,58+y*32,96+x*40,90+y*32),fill='#f4ecd6' if (x+y)%2==0 else '#102b51')
    d.rounded_rectangle((86,244,155,390),radius=20,fill='#060e1b')
    d.rounded_rectangle((357,244,426,390),radius=20,fill='#060e1b')
    d.polygon([(116,321),(153,203),(208,179),(304,179),(359,203),(396,321),(350,367),(162,367)],fill='#e94c37',outline='#ffb16c',width=7)
    d.rounded_rectangle((194,196,318,262),radius=20,fill='#fff0ba')
    d.polygon([(212,284),(300,284),(325,365),(187,365)],fill='#ffdc42')
    d.line((173,329,124,329),fill='#f4ecd6',width=13);d.line((339,329,388,329),fill='#f4ecd6',width=13)
    try:font=ImageFont.truetype('arialbd.ttf',68)
    except OSError:font=ImageFont.load_default(size=68)
    d.text((256,425),'64',font=font,anchor='mm',fill='#fff0ba',stroke_width=2,stroke_fill='#06172c')
    image.save(out/'kart64.png');image.save(out/'kart64.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    for size in (80,130,256):image.resize((size,size),Image.Resampling.LANCZOS).save(out/f'kart64-{size}.png')
if __name__=='__main__':generate()
