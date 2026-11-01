# Vision-Based Breadboard Circuit Fault Detection and Correction

Target: November/December 2026. Exact submission date and team size are not yet known.

## Problem statement

Students assembling breadboard circuits can struggle to identify misplaced leads and missing connections. Build an assistant that combines visual terminal recognition with electrical connectivity checks and shows localized correction suggestions.

## Architecture

React photo capture/upload and inspection UI -> FastAPI -> component/terminal pose model -> board calibration and hole assignment -> user confirmation -> connectivity graph -> fault explanations and annotated results.

Implemented in v0.1: upload, manual marking and hole assignment, graph checks, examples, report export, optional raw pose-inference adapter. Automatic board calibration and connection reconstruction are not implemented. No weights have been trained.

## Staged schedule

| Stage | Work | Exit condition |
| --- | --- | --- |
| Late September | Agree supported breadboard and LED circuit; run the workbench; investigate permitted datasets | A correct and a faulty example can be checked reliably |
| Early October | Label a pilot dataset, track provenance, split by build/source | Labels and LED polarity pass manual review |
| Mid October | Train in Colab and inspect terminal predictions | Held-out errors are understood; baseline metrics recorded |
| Late October | Add board-corner calibration and map terminal pixels to holes | Close or occluded terminals trigger confirmation instead of guessed holes |
| Early November | Integrate automatic proposals and test physical builds | End-to-end results include false passes and correction counts |
| Before submission | Freeze features; write report and presentation; rehearse | Repeatable demo, documented limits, reproducible evaluation |

If submission is in December, use the extra time for better data and testing before adding voltage-divider or transistor circuits. Those need their own topology rules, polarity conventions, and labeled cases. Do not claim support merely by adding a circuit-selection control.

## Milestone decisions

- If insertion points are too small, improve capture resolution/alignment before changing models.
- If online photos have hidden terminals, collect controlled photos or reduce the supported scope.
- If automatic snapping is unreliable, retain the assisted workflow and report its performance honestly.
- If data is insufficient, present the manual-confirmation prototype as the baseline, not as completed automatic vision.

## Submission materials still to produce

The final report, measured results, model weights, physical validation, and presentation must follow experiments. This folder contains the runnable foundation, training workflow, and plan; it is not a finished evaluated AI submission.
