"""Render a read-only dataset overview and keypoint audit."""
import io
import sys
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw

archive, output = sys.argv[1:]
out = Path(output)
out.mkdir(parents=True, exist_ok=True)
with ZipFile(archive) as z:
    names = sorted(n for n in z.namelist() if n.endswith('.jpg'))
    sheet = Image.new('RGB', (5*260, 6*285), 'white')
    for i, name in enumerate(names):
        im = Image.open(io.BytesIO(z.read(name))).convert('RGB')
        im.thumbnail((250,250))
        x, y = (i%5)*260, (i//5)*285
        sheet.paste(im,(x,y+25))
        ImageDraw.Draw(sheet).text((x+5,y+5),Path(name).name.split('_jpg')[0], fill='black')
    sheet.save(out/'overview.jpg')
    for index in [0, 9, 12, 15, 18, 21, 24]:
        name = names[index]
        im = Image.open(io.BytesIO(z.read(name))).convert('RGB')
        draw = ImageDraw.Draw(im)
        label = name.replace('/images/','/labels/').rsplit('.',1)[0]+'.txt'
        rows = [list(map(float,l.split())) for l in z.read(label).decode().splitlines()]
        for row in rows:
            if int(row[0]) == 0:
                continue
            color = 'yellow' if int(row[0]) == 1 else 'cyan'
            for k in range(8):
                x,y,v = row[5+3*k:8+3*k]
                if v:
                    x,y=x*im.width,y*im.height
                    draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
                    draw.text((x+4,y-6),str(k),fill=color)
        im.save(out/f'keypoints-{index}.jpg')
print(out)
