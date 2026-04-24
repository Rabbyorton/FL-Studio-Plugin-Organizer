FL Studio’s built‑in Plugin Manager doesn’t provide vendor‑based organization out of the box, so I built a lightweight companion app to make plugin management easier. It scans your FL Studio Plugin Database and automatically reorganizes presets into vendor folders for both Effects and Generators, so you can browse your plugins in a clean, logical structure.

Usage workflow

Scan plugins in FL Studio
First, run FL Studio’s Plugin Manager and perform a full scan so your plugin database is up to date.

Run FL Studio Plugin Organizer
Open the FL Studio Plugin Organizer app, verify the Source Path points to your FL Studio Installed plugin database folder, and choose an Output Path (by default, a new Organized_FL_Plugins folder is created on your Desktop, but you can change this to any location you prefer).

Click “Organize Plugins”
The app scans your Effects and Generators (VST / VST3), reads the preset metadata, and arranges your .fst/.nfo/.png files into vendor‑named folders while showing live statistics for scanned, copied, skipped, and errored items in a modern CustomTkinter dashboard.

Review and use the organized database
Your original FL Studio Plugin Database remains untouched; the organized vendor structure is written only to the chosen output folder so you can safely review or merge it into your workflow.

Modern FL Studio Plugin Database organizer that automatically groups Effects and Generators by vendor, featuring a clean CustomTkinter UI, real‑time scan/copy/skip/error statistics, and a portable one‑file Windows executable built with PyInstaller—no Python installation required on the target machine.

---ScreenShot---
<img width="1920" height="1080" alt="Screenshot (86)" src="https://github.com/user-attachments/assets/06d8a492-3cd9-4bb7-9f0c-22f4e92ccdf8" />
