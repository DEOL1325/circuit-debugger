# Circuit Debugger

A student project for visual breadboard inspection. React workbench, FastAPI connectivity checker, and a Google Colab training notebook.

## What works now

- Photo upload (JPEG/PNG/WebP, up to 8 MB), manually placed terminal markers, and a live breadboard connection map.
- User-confirmed hole assignments, editable jumper wires, and one resistor + one LED reference circuit.
- Connectivity checks for open connections, shorted supply terminals, bypassed components, and marked LED polarity.
- Correct, disconnected, and reversed-LED examples, plus a JSON inspection report.
- Optional model inference endpoint that returns component boxes and terminal keypoints when trained weights are installed.

**This is a working manual-confirmation prototype, not a trained automatic circuit debugger.** No model weights, claimed accuracy, or physical-circuit validation are included. Uploading a photo does not extract connections. Mark the terminals and replace all example hole numbers before checking.

## Run on your laptop

Install Python 3.11+ and Node.js 20.19+ (or a supported newer LTS). Open this folder in VS Code.

Terminal 1, from this folder:

```sh
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell alternative:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```sh
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The frontend forwards API requests to the Python server. No accounts or API keys are required.

For a single-server demo, run `npm run build` in `frontend`, then start/restart the Python server and open http://127.0.0.1:8000. Start the server after building so it detects the compiled frontend.

## Put the demo online

This repository includes a Docker deployment for Render. Create a GitHub repository containing this `circuit-debugger` folder, then in Render choose **New → Blueprint**, connect that repository, and select `render.yaml`. Render builds the frontend and backend together and gives the app one public URL. The free service may sleep when idle and take about a minute to wake. The current app is a manual-confirmation prototype; automatic photo suggestions need trained model weights, which are not included.

## First inspection

1. Choose an example at the bottom of the workbench.
2. Tick the confirmation checkbox and click **Check connections**.
3. Inspect the fault message and highlighted endpoints in the connection map.
4. Change the incorrect hole or load the correct example, confirm again, and recheck.
5. Upload a photo when available. All table values initially remain examples; replace them with observed connections. In the Photo view, select a terminal and click its location to place a marker.

## Breadboard assumptions

The prototype assumes 30 numbered rows. In each row, A-E form one conductive strip and F-J another, separated by the center gap. Rows do not connect vertically without a wire. Supply positive and negative are assigned to main-grid holes; edge power rails, split rails, other board geometries, transistors, and ICs are outside version 0.1.

LED pin 1 means **anode**, pin 2 **cathode**. The user must establish physical polarity; the system checks the labels provided. A resistor may be on either side of the LED. Equivalent wiring in different holes is accepted; comparison is electrical, not an exact visual-template match.

A pass covers only entered connectivity. It does not check resistance, supply voltage, component condition, contact quality, multiple leads occupying one hole, or whether the LED actually lights. Disconnect power before changing wiring.

## Train in Google Colab

**First experiment with the downloaded BME v5 dataset:** use `output/colab-pilot/01_breadboard_pilot.ipynb` and `output/colab-pilot/breadboard-pilot-ready.zip`. Follow that folder's `START_HERE.md`. This is a separate eight-keypoint breadboard/resistor/wire pilot, with no LED class and no held-out wire evaluation. The original notebook below is for our later custom LED dataset; do not mix the archives.

Upload `notebooks/train_terminal_detector.ipynb` to https://colab.research.google.com/ and select a GPU runtime. Read `docs/DATASET.md` before preparing the dataset ZIP. The notebook validates and trains a three-class, two-keypoint pose model; it does not generate labels automatically.

After training:

1. Download `best.pt` from the notebook and place it in a new `models` folder here.
2. In the Python environment, run `python -m pip install ultralytics`.
3. Restart the Python server. The Photo view will offer **Suggest components with AI**.

The model proposes boxes/keypoints. Hole assignment and user confirmation are still manual in this version. Automatic grid calibration, snapping, and ambiguity handling are the next integration stage; do not describe this version as end-to-end automatic.

## Verify

```sh
python -m unittest discover -s tests -v
```

API documentation: http://127.0.0.1:8000/docs.

## Project files

- `frontend/src/`: React interface and styling.
- `backend/circuit.py`: physical strip model and electrical topology checks.
- `backend/app.py`: API and optional pose-model adapter.
- `notebooks/train_terminal_detector.ipynb`: Colab training workflow.
- `docs/DATASET.md`: labels, online-image sourcing, and evaluation.
- `docs/PROJECT_PLAN.md`: staged plan through November/December.
- `tests/`: API and topology regression checks.

No public deployment has been made. This local prototype has no accounts, persistent uploads, or public-service hardening. Photos remain in browser memory in manual mode; using model inference sends the selected image to your local Python server. Refreshing clears the session, so export reports you want to keep. Fonts may load from Google Fonts; system fonts are the fallback.
