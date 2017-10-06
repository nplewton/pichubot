# pichubot

## Basic Git Stuff
1. Make local folder on your computer where you want to clone the repository
2. Enter in term: "git clone https://github.com/nplewton/pichubot.git" while inside the local folder
3. "git pull" will grab the current files from the online repo (while you are in the local folder)
4. "git add examplefile.py" will add the file you wish to commit to the list of updated files
5. "git commit -m "commit message here" will commit the files you added with the message
6. "git push" will push the committed files to the online repo


# libmelee
Open API written in Python for making your own Smash Bros: Melee AI

## Setup Instructions

Linux / OSX only. (Windows coming soon)

1. Install the Dolphin version here:
https://github.com/altf4/dolphin/tree/memorywatcher-rebased
This contains an important update to allow Dolphin to be able to read projectile information from Melee. Unfortunately, you'll have to build this from source until they accept my Pull Request:
https://github.com/dolphin-emu/dolphin/pull/4407

2. Make sure you're running Melee v1.02 NTSC. Other versions will not work.

3. If you want to play interactively with or against your AI, you'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI

4. Install via pip: (or by cloning this repo for the very latest)
`pip3 install melee`

5. Run `example.py`

## NOTE:
The libmelee API should be considered to be in a state of high flux until you stop seeing this message. Expect many changes, including plenty that break compatibility. Just FYI

libmelee is inspired by, but not exactly conforming to, the OpenAI Gym API.
