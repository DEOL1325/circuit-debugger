# Dataset and evaluation

## Online photos can help, but are not labels

Use photographs with explicit reuse permission or an appropriate dataset license. Save the source URL, author, license, date, and any required attribution for every image. Do not treat an image-search result as permission. A tutorial saying a circuit works is not sufficient ground truth for every visible connection.

Inspected on 20 September 2026: BME Electronics v5, https://universe.roboflow.com/bme-electronics/circuit-detection-eoirn/dataset/5 . The user-provided ZIP contains 27 images, breadboard/resistor/wire classes, eight keypoint slots, and CC BY 4.0 metadata. It has no LEDs and is not compatible with the original two-keypoint LED notebook. A separate pilot notebook and prepared archive are in `output/colab-pilot/`; read `START_HERE.md` and the audit before using them. Mechanical box corrections and grouped splits are documented. Its tiny held-out sets have no wires, so they cannot measure wire performance.

Technical reference for training format: https://docs.ultralytics.com/datasets/pose/ .

Prefer clear top-down photographs with visible row labels, both wire endpoints, LED legs, and resistor legs. Circuit schematics, rendered diagrams, and photographs are different visual domains. Synthetic images can supplement training, but evaluate on held-out physical photographs.

## Labels for the initial detector

Classes must use these IDs:

| ID | Class | Keypoint 1 | Keypoint 2 |
| --- | --- | --- | --- |
| 0 | resistor | Insertion point 1 | Insertion point 2 |
| 1 | led | Anode insertion point | Cathode insertion point |
| 2 | wire | Insertion point 1 | Insertion point 2 |

Mark the actual breadboard insertion points, not the component body's ends. For resistors and wires, use a consistent left-to-right endpoint ordering (top-to-bottom when tied); their electrical polarity is irrelevant. LED ordering is semantic and must never be guessed. Record invisible keypoints with visibility 0; uncertain LED polarity should be excluded or marked unknown in the provenance notes until independently established.

Every label line uses normalized coordinates:

```text
class_id box_center_x box_center_y box_width box_height x1 y1 visibility1 x2 y2 visibility2
```

Visibility: 0 absent/unlabeled, 1 labeled but occluded, 2 visible. Bounding boxes must include both terminal insertion points. Label all supported parts in an image, including faulty builds. The detector locates parts and terminals; the topology checker determines faults.

ZIP layout expected by the notebook:

```text
images/train/*.jpg
images/val/*.jpg
images/test/*.jpg
labels/train/*.txt
labels/val/*.txt
labels/test/*.txt
```

JPEG, PNG, and WebP are supported. Image and label stems must match. Keep filenames unique within each split. The notebook supplies the class mapping itself.

## Collection plan

Start with a small, carefully checked pilot (for example 50-100 usable images) to test the pipeline; this is not a promise of adequate training data. Increase the set based on held-out errors. Include different component colors, camera distances, lighting, and correct/incorrect builds. Keep fault ground truth in a separate manifest: hole labels, component types, LED polarity, expected connections, and deliberately introduced fault.

Split by physical build and source/tutorial, not by random image. Near-duplicate crops and multiple frames of the same build must stay in the same split. Keep an independent physical-photo test set. If no physical circuits can be obtained, report the narrower online-image evaluation and do not claim real-world robustness.

Recommended provenance manifest columns:

```text
image_id,source_url,author,license,attribution,build_group,split,polarity_verified,ground_truth_notes
```

## Metrics to report separately

1. Component detection: precision, recall, and box mAP.
2. Terminal localization: pixel error and error relative to breadboard hole spacing. Generic pose mAP alone does not show correct hole assignment.
3. Connection reconstruction: percentage of terminals assigned to the correct electrical strip, plus abstention rate for ambiguous cases.
4. Fault diagnosis: per-fault precision/recall, confusion matrix, false passes, and results on correctly wired circuits.
5. Full workflow: time per photo, number of user corrections, and outcome on held-out physical builds.

Do not include manually corrected predictions in an 'automatic accuracy' number. Report assisted and automatic performance separately. Compare against a simple geometry/rule baseline, and retain a fixed test set untouched by tuning.
