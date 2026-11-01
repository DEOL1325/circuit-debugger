"""Prepare the inspected BME v5 archive, without changing its class/keypoint meaning.

This is deliberately specific to the 27 reviewed images, not a generic splitter.
Related resistor views and the red/black wire layout remain in the same split.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image, ImageDraw

NAMES = ['breadboard', 'resistor', 'wire']
GROUPS = {
    '20240829_12': ('train', 'resistor_layout_A'),
    '20240829_14': ('val', 'resistor_layout_B'),
    '20240829_16': ('test', 'resistor_layout_C'),
    '20240912_15': ('train', 'wire_layout_red_and_black'),
}


def prepare(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(Counter)
    image_counts = Counter()
    corrections = []
    manifest = []
    members = {}
    seen = set()
    with ZipFile(source) as archive:
        names = sorted(n for n in archive.namelist() if n.startswith('train/images/') and n.endswith('.jpg'))
        assert len(names) == 27, 'Expected the inspected 27-image v5 export.'
        assert 'kpt_shape: [8, 3]' in archive.read('data.yaml').decode()
        for name in names:
            filename = Path(name).name
            group_key = filename[:11]
            assert group_key in GROUPS, f'Unexpected source image: {filename}'
            split, group = GROUPS[group_key]
            content = archive.read(name)
            digest = hashlib.sha256(content).hexdigest()
            assert digest not in seen, 'Exact duplicate image found.'
            seen.add(digest)
            im = Image.open(io.BytesIO(content))
            width, height = im.size
            label_name = name.replace('/images/', '/labels/').rsplit('.', 1)[0]+'.txt'
            converted = []
            for row_number, line in enumerate(archive.read(label_name).decode().splitlines(), 1):
                values = list(map(float, line.split()))
                assert len(values) == 29 and all(math.isfinite(v) for v in values)
                cls = int(values[0])
                assert values[0] == cls and cls in range(3)
                cx, cy, w, h = values[1:5]
                assert 0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1
                pts = [values[i:i+3] for i in range(5, 29, 3)]
                for x, y, v in pts:
                    assert 0 <= x <= 1 and 0 <= y <= 1 and v in (0, 1, 2)
                visible = [(x, y) for x, y, v in pts if v]
                old = [cx-w/2, cy-h/2, cx+w/2, cy+h/2]
                outside = any(not (old[0] <= x <= old[2] and old[1] <= y <= old[3]) for x, y in visible)
                # Only expand boxes; preserve keypoint positions/visibility/order exactly.
                # A 3px margin keeps tiny endpoint-only boxes from becoming line targets.
                if outside or w*width < 6 or h*height < 6:
                    x0 = max(0, min([old[0]]+[x-3/width for x, y in visible]))
                    y0 = max(0, min([old[1]]+[y-3/height for x, y in visible]))
                    x1 = min(1, max([old[2]]+[x+3/width for x, y in visible]))
                    y1 = min(1, max([old[3]]+[y+3/height for x, y in visible]))
                    values[1:5] = [(x0+x1)/2, (y0+y1)/2, x1-x0, y1-y0]
                    corrections.append({'image':filename,'row':row_number,'class':NAMES[cls],
                                        'original_box':old,'expanded_box':[x0,y0,x1,y1]})
                counts[split][NAMES[cls]] += 1
                converted.append(' '.join(format(v, '.12g') for v in values))
            members[f'images/{split}/{filename}'] = content
            members[f'labels/{split}/{Path(filename).stem}.txt'] = ('\n'.join(converted)+'\n').encode()
            image_counts[split] += 1
            manifest.append({'file':filename,'split':split,'group':group,'sha256':digest})
        for doc in ['README.dataset.txt', 'README.roboflow.txt', 'data.yaml']:
            members['provenance/original-'+doc] = archive.read(doc)

    assert dict(image_counts) == {'train':21,'val':3,'test':3}
    config = 'path: /content/circuit_pilot\ntrain: images/train\nval: images/val\ntest: images/test\nnames: [breadboard, resistor, wire]\nkpt_shape: [8, 3]\n'
    members['data.yaml'] = config.encode()
    report = {
        'source': 'BME Electronics, Circuit Detection v5, Roboflow Universe',
        'source_url': 'https://universe.roboflow.com/bme-electronics/circuit-detection-eoirn/dataset/5',
        'license': 'CC BY 4.0', 'license_url':'https://creativecommons.org/licenses/by/4.0/',
        'images':dict(image_counts), 'objects':{k:dict(v) for k,v in counts.items()},
        'classes':NAMES, 'kpt_shape':[8,3], 'boxes_expanded':len(corrections),
        'limits':[
            'No LEDs, LED polarity, hole-number ground truth, or circuit fault labels.',
            'Only 27 images of a few layouts, photographed on similar hardware.',
            'Grouping based on filenames and visual review; not verified with the creator.',
            'Red and black wire images show a related layout and are kept together in training.',
            'Validation/test contain no wire objects; their metrics do not evaluate wire recognition.',
            'Some wire keypoints mark free ends outside the board, not insertion holes.',
            'Expanded boxes include labeled points but may still omit curved wire bodies.',
            'Pilot experiment only; more independent labeled builds needed for robust evaluation.',
        ],
    }
    members['audit.json'] = json.dumps(report, indent=2).encode()
    members['box_corrections.json'] = json.dumps(corrections, indent=2).encode()
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=['file','split','group','sha256'])
    writer.writeheader(); writer.writerows(manifest)
    members['split_manifest.csv'] = csv_buffer.getvalue().encode()
    members['ATTRIBUTION.txt'] = (
        'Circuit Detection v5 by BME Electronics, via Roboflow Universe.\n'
        'https://universe.roboflow.com/bme-electronics/circuit-detection-eoirn/dataset/5\n'
        'Licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n'
        'Adapted 20 September 2026: grouped split, directory arrangement, and box expansion.\n'
        'Original images and keypoint meanings preserved. See audit.json and box_corrections.json.\n'
    ).encode()
    archive_path = destination/'breadboard-pilot-ready.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as output:
        for name, content in members.items():
            output.writestr(name, content)
    # Verify the packaged data independently, including correspondence and split support.
    with ZipFile(archive_path) as packaged:
        assert packaged.testzip() is None
        for split, expected in image_counts.items():
            assert len([n for n in packaged.namelist() if n.startswith(f'images/{split}/')]) == expected
        for entry in manifest:
            assert hashlib.sha256(packaged.read(f"images/{entry['split']}/{entry['file']}")).hexdigest() == entry['sha256']
        for name in packaged.namelist():
            if name.startswith('labels/'):
                for line in packaged.read(name).decode().splitlines():
                    v = list(map(float,line.split()))
                    assert len(v) == 29
                    for x,y,vis in [v[i:i+3] for i in range(5,29,3)]:
                        if vis:
                            assert v[1]-v[3]/2-1e-9 <= x <= v[1]+v[3]/2+1e-9
                            assert v[2]-v[4]/2-1e-9 <= y <= v[2]+v[4]/2+1e-9
    (destination/'dataset-audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(archive_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)
