# Vision-Based-Desktop-Automation-with-Dynamic-Icon-Grounding
an automated script made to identify some sort of icons and interact with it accordingly

# Vision-Based Desktop Automation with Dynamic Icon Grounding


This project automates writing and saving text files in Windows Notepad by combining computer vision, GUI automation, and API data fetching.

It detects the Notepad desktop icon using OpenCV, opens it automatically, types post content line-by-line, saves each post safely, and repeats the process with strong fallback and recovery mechanisms.

## Requirements

Operating System: Windows

Python: 3.10 or newer

Display: Desktop must be visible (real UI automation)

This project uses uv so we are using a pyproject.toml

## Installation (Using uv)

```bash
pip install uv
```

```bash
uv venv
```

```bash
uv pip install .
```
Dependencies are resolved directly from pyproject.toml.


## Running the project

```bash
uv run python tjmVis.py
```
## How it works on a high level

1. **Fetch Posts**
   - Attempts an API request
   - Falls back to local data if offline

2. **Scan Desktop**
   - Takes a screenshot
   - Runs edge detection
   - Matches the Notepad icon template at multiple scales

3. **Resolve Icon**
   - Automatically selects the icon if only one match is found
   - Prompts the user to choose if multiple matches are detected

4. **Automation Loop**
   - Opens Notepad
   - Types content line by line
   - Saves the file using collision-safe naming
   - Closes Notepad
   - Repeats for all posts

5. **Fallbacks**
   - Start Menu–based launch
   - Retry logic for unstable steps
   - Failure isolation per post to prevent full-run 
