# First Colab experiment

1. Open Colab and upload `01_breadboard_pilot.ipynb` as a NEW notebook.
2. Select a T4 GPU runtime.
3. Run the cells in order. At the upload prompt, choose `breadboard-pilot-ready.zip`.
4. After training, run the download cell to save `breadboard_pilot_best.pt` immediately.
5. Run the evaluation cell, save `breadboard_pilot_results.json`, and inspect the predicted images.
6. Return those two output files to the project chat for inspection and integration planning.

Do not use `train_terminal_detector.ipynb` for this ZIP. That original notebook expects resistor/LED/wire classes and two keypoints. This pilot preserves the downloaded dataset's breadboard/resistor/wire classes and eight keypoint slots.

## What was inspected and prepared

- 27 images; 902 annotations (27 boards, 372 resistors, 503 wires).
- Grouped split: 21 training, 3 validation, 3 test images.
- Repeated views of related layouts kept together. Grouping is based on visual review and filename sessions, not creator-certified physical build IDs.
- 574 bounding boxes expanded to include labeled keypoints or give thin boxes a margin. Keypoint meanings/visibility and original images are unchanged. This is a mechanical repair, not newly verified box ground truth.
- Original source/configuration and CC BY 4.0 attribution retained in the ZIP.
- Per-image split manifest and per-box correction log included.

## Limits

No LEDs or labeled electrical faults exist in this export. All wire photographs belong to a related-layout group kept together in training, so validation/test contain no wire objects. Report their metrics only as a tiny breadboard/resistor pilot. Independent wire and LED data are still needed. The photos use a larger breadboard than the frontend's 30-row demonstration; automatic hole mapping is not yet implemented.

The notebook was checked locally for valid JSON/Python, and its upload, configuration, and label-validation cells were executed locally using a stand-in for Colab file upload. GPU training and online model download have NOT been executed here. The Ultralytics version matches the user's successful Colab setup (8.4.156).
