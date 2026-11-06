# SlideReady PPTX analysis integration

This package contains a React page and a Flask API adapted from your uploaded `PPTanalyzer.py`. It keeps the analyzer's rule-based checks and report fields, but changes it from “look for a file in data/raw” to “analyze the uploaded file passed to a function.”

## Files
- `frontend/SlidePrep.jsx` — upload, Analyse, Reset, loading/error state, and results on the same page.
- `frontend/SlidePrep.css` — responsive page styling.
- `frontend/.env.example` — API base URL example.
- `backend/app.py` — Flask upload API at `POST /api/analyze-ppt`.
- `backend/PPTanalyzer.py` — analyzer adapted to accept a file path and return a report.
- `backend/requirements.txt` — Python packages.

## 1. Backend setup (Windows PowerShell)
Open PowerShell in the `backend` folder (the folder containing `app.py`):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this for the current terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Keep this terminal running. The API runs at `http://127.0.0.1:5000`. Check `http://127.0.0.1:5000/api/health` in your browser; it should return a small JSON status response.

## 2. Add the page to your existing React/Vite frontend
Copy `SlidePrep.jsx` and `SlidePrep.css` into the frontend source folder, usually `src/`.

If your app uses React Router, add a route such as:

```jsx
import SlidePrep from "./SlidePrep"; // adjust the path if the file is in src/pages

// Inside <Routes>:
<Route path="/slide-prep" element={<SlidePrep />} />
```

If you do not use React Router, render `<SlidePrep />` where you want the page to appear.

Create a `.env` file in the **Vite frontend root**, beside `package.json` (not inside `src`), containing:

```env
VITE_API_URL=http://127.0.0.1:5000
```

Restart Vite after creating or changing `.env`:

```powershell
npm install
npm run dev
```

Open the local URL Vite prints, then navigate to `/slide-prep` if you added that route. Keep both the Flask and Vite terminals running.

## 3. How it works
1. Choose a `.pptx` file (only `.pptx` is accepted; maximum 30 MB).
2. Click **Analyse**. The page posts the file as multipart form data to Flask and displays **Analyzing…** while waiting.
3. Flask runs the analyzer and returns JSON; the page renders summary metrics, overall findings, slide-by-slide findings/suggestions, extracted text, and repeated four-word phrases.
4. **Reset** clears the selected file, messages, and report.

The backend also writes `pptanalysis.json` and `pptanalysis.txt` into `backend/output/ppt_analysed/`.

## Troubleshooting
- **Failed to fetch / connection refused:** confirm `python app.py` is running and `.env` has `http://127.0.0.1:5000`; restart Vite after editing `.env`.
- **Module not found:** activate the backend `.venv` and run `pip install -r requirements.txt` from `backend`.
- **No route/page found:** make sure the `SlidePrep` import and route are added to your existing React app.
- **Wrong file type:** save/export the presentation as `.pptx`; legacy `.ppt` files are not supported.

This analyzer performs rule-based structural checks, not visual AI analysis or factual verification.
