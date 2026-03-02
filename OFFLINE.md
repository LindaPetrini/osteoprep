# Offline setup — phone access via USB cable (no internet needed)

## Step 1 — first-time Mac setup (do this before the flight, needs internet)

Open Terminal on Mac and run:

```bash
rsync -av --exclude .venv --exclude __pycache__ --exclude '*.pyc' --exclude .env --exclude 'tests/' \
  linda@100.121.250.101:/home/linda/projects/osteoprep/ ~/osteoprep-offline/
```

Then do a first run to install dependencies (takes ~1 min, needs internet):

```bash
cd ~/osteoprep-offline
./run_local.sh
# Ctrl+C once it starts — deps are now installed
```

## Step 2 — on the plane (USB cable, no internet)

### On iPhone
1. Settings → **Airplane Mode ON**
2. Settings → **Personal Hotspot → Allow Others to Join: ON**
   (hotspot works via USB without cellular — no data used)

### Connect the cable
Plug iPhone into Mac with Lightning or USB-C cable.
Accept "Trust This Computer" on iPhone if asked.

### On Mac
Open Terminal:

```bash
cd ~/osteoprep-offline
./run_local.sh
```

It will print something like:
```
Open on phone: http://172.20.10.3:8080
```

If no IP prints, find it manually:
```bash
# Run this in another terminal tab:
ipconfig getifaddr bridge100 2>/dev/null || \
  ifconfig | grep "inet 172.20" | awk '{print $2}'
```

### On iPhone
Open Safari → type the IP address printed above + `:8080`
Example: `http://172.20.10.3:8080`

Bookmark it. Done.

## What works offline
- Flashcard review (spaced repetition)
- Quiz (topic + subject-wide)
- Practice exam
- Progress tracking
- Topic explainers (already generated and cached in DB)
- Section mini-questions

## What doesn't work offline
- AI chat ("Chiedi a Claude")
- Generating new quiz questions ("Genera nuove domande")
- Explanation generation for questions not yet explained
  (shows "Spiegazione non disponibile" — doesn't crash)

## Troubleshooting
- **Phone can't reach the IP**: make sure Personal Hotspot is still ON on iPhone, cable is plugged in
- **run_local.sh fails on "No module named X"**: re-run it, pip install might have failed once
- **Port 8080 already in use**: `lsof -ti:8080 | xargs kill` then re-run
- **Python version error**: `brew install python@3.11` then re-run setup
