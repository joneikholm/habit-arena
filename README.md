# Habit Arena

Log your own daily habits. Several models predict tomorrow's target (e.g.
evening mood), and you watch which model wins as your data grows.

## Install (once)

```bash
git clone https://github.com/joneikholm/habit-arena.git
cd habit-arena
python3 -m venv .venv               # Windows: python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## On your phone

The app runs on your laptop; your phone opens it over the Wi-Fi.

1. Start the server so other devices can reach it:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. Find your laptop's address: macOS `ipconfig getifaddr en0`,
   Windows `ipconfig` (the IPv4 address).
3. On the phone (same Wi-Fi), open `http://<that address>:8000`.
4. Add it to the home screen (Share → Add to Home Screen on iPhone, the ⋮ menu
   on Android): it then opens like an app.

The laptop must be on and the server running. Anyone on the same Wi-Fi can
open the page too, so use a pseudonym. On a school network that blocks
device-to-device traffic, use your phone's hotspot for the laptop instead.

## Every day

1. **Log**: tap your values during the day or in the evening. Log the
   target every day, including day 1.
2. **Results → Live**: press **Predict tomorrow** (it waits until today's
   target is logged). Tomorrow evening, when you log the target, yesterday's
   guesses are scored.

The first day has no "yesterday", so the models start from day 2. Each model
waits for its own number of days (see the leaderboard).

## Choose your own fields

On the **Log** page, press **Edit fields**: add, edit or delete fields, set each one's range,
options and per-day rule, pick the target, and press **Save**. Field types:
`number`, `scale`, `yesno`, `choice`. Read "How to log data a model can learn
from" before you decide.

Once a field has entries, its name, type and options are locked, so the old
entries keep their meaning. Its range and per-day rule can still change. A
deleted field's entries stay in `data.db`, so its name can't be reused for a
new field. Saving writes `config.yaml`, which you can also edit by hand.

## Your own models

Each file in `models/` has a block:

```python
# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----

# ---- END ----
```

Paste your code from the LNN platform there:

| model file | copy from the platform |
|---|---|
| `models/mean_baseline.py` | step 1: your `mean` |
| `models/pearson.py` | step 10: the given (grey) code at the top of the editor AND your own code |
| `models/neuron.py` | step 18: the given (grey) code at the top of the editor AND your own code |
 A model you haven't pasted into uses
a ready-made file in `reference/` if your teacher gave you one, and otherwise
says "waiting for your code". The Code column shows "your code", "reference",
"missing: ..." or "no code yet"; if your code crashes, the error is shown
there. Restart the app after pasting. The `NEEDED` line in each model file lists
the functions the model calls.

Adding a model = adding one file in `models/` with a class that extends `Model`.

## Synthetic data

Open **Results → Backtest**, choose **Synthetic**, pick a number of days
and press **Generate and run**. The fake student follows a known hidden
rule; open "The hidden rule" and check which model finds it. Try 10, 60
and 365 days. From the terminal: `python -m app.seed --days 365`.

## Privacy

Use a pseudonym. Invented or partly invented data is fine. Everything stays
in `data.db` on your machine.
