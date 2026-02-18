import requests
import pyautogui
import time
import os
import cv2
import numpy as np
import pygetwindow as gw
import tkinter as tk
from PIL import Image, ImageTk

# --- CONFIGURATION ---
API_URL = "https://jsonplaceholder.typicode.com/posts?_limit=10"
TEMPLATE_PATH = 'notepad_template.png' 
CONFIDENCE_THRESHOLD = 0.5
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
PROJECT_DIR = os.path.join(DESKTOP_PATH, "tjm-project")
ANNOTATED_DIR = os.path.join(PROJECT_DIR, "annotated")

os.makedirs(PROJECT_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)

# --- UI CLASS ---
class IconSelector:
    def __init__(self):
        self.selected_loc = None
    def ask(self, matches, screen_np):
        root = tk.Tk()
        root.title("Select Icon")
        width = len(matches) * 160 + 50
        root.geometry(f"{width}x300")
        tk.Label(root, text="Click the Notepad icon to use:", font=("Arial", 12)).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack()
        screen_rgb = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(screen_rgb)
        self.photos = []
        for i, (x, y, w, h) in enumerate(matches):
            crop = pil_img.crop((x-w//2-10, y-h//2-10, x+w//2+10, y+h//2+50))
            ph = ImageTk.PhotoImage(crop)
            self.photos.append(ph)
            btn = tk.Button(frame, image=ph, command=lambda loc=(x,y), r=root: self.select(loc, r))
            btn.grid(row=0, column=i, padx=10)
            tk.Label(frame, text=f"Option {i+1}").grid(row=1, column=i)
        root.mainloop()
        return self.selected_loc
    def select(self, loc, root):
        self.selected_loc = loc
        root.destroy()

# --- VISION ---
def get_matches_on_screen(screenshot_index=None):
    if not os.path.exists(TEMPLATE_PATH):
        print(f"[Error] Template '{TEMPLATE_PATH}' missing.")
        return [], None
    
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
    screen_edges = cv2.Canny(screen_gray, 50, 150)

    template = cv2.imread(TEMPLATE_PATH, 0)
    tH, tW = template.shape[:2]
    scales = np.linspace(0.5, 2, 10)
    found_candidates = []

    for scale in scales:
        resized_template = cv2.resize(template, (int(tW * scale), int(tH * scale)))
        resized_edges = cv2.Canny(resized_template, 50, 150)

        if resized_edges.shape[0] > screen_edges.shape[0] or resized_edges.shape[1] > screen_edges.shape[1]:
            continue

        res = cv2.matchTemplate(screen_edges, resized_edges, cv2.TM_CCOEFF_NORMED)
        locs = np.where(res >= CONFIDENCE_THRESHOLD)

        for pt in zip(*locs[::-1]):
            cur_w, cur_h = resized_edges.shape[::-1]
            cx, cy = pt[0] + cur_w//2, pt[1] + cur_h//2
            found_candidates.append((cx, cy, cur_w, cur_h))
    candidates = []
    for cand in found_candidates:
        cx, cy, w, h = cand
        if not any(abs(cx - u[0]) < 20 and abs(cy - u[1]) < 20 for u in candidates):
            candidates.append(cand)


    annotated = screen_bgr.copy()

    
    contours, _ = cv2.findContours(screen_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 20 and h > 20:  # filter out tiny noise
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 1)  # red = everything detected

    
    for (cx, cy, w, h) in candidates:
        cv2.rectangle(annotated, (cx - w//2, cy - h//2), (cx + w//2, cy + h//2), (0, 255, 0), 2)  # green = notepad match
        cv2.putText(annotated, "NOTEPAD", (cx - w//2, cy - h//2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


    if screenshot_index is not None:
        path = os.path.join(ANNOTATED_DIR, f"scan_{screenshot_index}.png")
        cv2.imwrite(path, annotated)
        print(f" -> Annotated screenshot saved: {path}")

    return candidates, screen_np

def verify_notepad_open():
    """Waits up to 5 seconds for Notepad to open, then focuses it."""
    for _ in range(5):
        time.sleep(1)
        windows = [w for w in gw.getWindowsWithTitle('Notepad') if 'Notepad' in w.title]
        if windows:
            try:
                windows[0].activate()
                time.sleep(0.5)
            except Exception as e:
                print(f" -> [Warning] Could not focus Notepad: {e}")
            return True
    return False

def open_notepad_via_startmenu():
    """Opens Notepad via the Start Menu as a fallback."""
    print(" -> [Fallback] Opening Notepad via Start Menu...")
    pyautogui.press('win')
    time.sleep(1.5)
    pyautogui.write('Notepad', interval=0.05)
    time.sleep(1.5)
    pyautogui.press('enter')
    time.sleep(2.0)
    if verify_notepad_open():
        print(" -> Notepad confirmed open and focused.")
        return True
    print(" -> [Error] Notepad did not open via Start Menu.")
    return False

def type_and_save_post(post):
    """Types post content line by line and saves with duplicate-safe naming."""
    content = f"Title: {post['title']}\n\n{post['body']}\n\n"

    
    for line in content.splitlines():
        pyautogui.write(line, interval=0.03)
        pyautogui.press('enter')
    time.sleep(0.5)

    
    base_name = f"post_{post['id']}"
    full_path = os.path.join(PROJECT_DIR, f"{base_name}.txt")
    counter = 1
    while os.path.exists(full_path):
        full_path = os.path.join(PROJECT_DIR, f"{base_name}-{counter}.txt")
        counter += 1


    pyautogui.hotkey('ctrl', 's')
    time.sleep(2.0)
    pyautogui.write(full_path)
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(1.5)

    return full_path


def main():
    print("--- 1. Setup Phase ---")


    try:
        print("Connecting to API...")
        response = requests.get(API_URL, timeout=5) 
        response.raise_for_status()
        posts = response.json()
        print(f"Fetched {len(posts)} posts from API.")
    except Exception as e:
        print(f"\n[Warning] API Unavailable ({e}).")
        print("-> Switching to OFFLINE MODE with fallback data.")
        posts = []
        for i in range(1, 11):
            posts.append({
                'id': i, 
                'title': f'Offline Backup Post {i}', 
                'body': 'This post was generated locally because the API is currently down.'
            })

    
    candidates = []
    screen_np = None
    max_setup_retries = 3

    for attempt in range(1, max_setup_retries + 1):
        print(f" -> [Setup Attempt {attempt}/{max_setup_retries}] Scanning for icon...")
        pyautogui.hotkey('win', 'm')
        time.sleep(1.5) 
        candidates, screen_np = get_matches_on_screen(screenshot_index=0)
        if candidates:
            print(" -> Icon found successfully.")
            break
        else:
            if attempt < max_setup_retries:
                print("(!) Template not found. Retrying in 2 seconds...")
                time.sleep(2.0)
            else:
                print("(!) Failed to find template after 3 attempts.")

    if not candidates:
        print("[Warning] Could not find icon on screen. Will use Start Menu for all posts.")
        target_home = None
    else:
        if len(candidates) > 1:
            selector = IconSelector()
            target_home = selector.ask(candidates, screen_np)
        else:
            target_home = candidates[0][:2]

        if not target_home:
            print("No selection made. Exiting.")
            return

    print("\n--- 2. Starting Automation Loop ---")

    for post in posts:
        post_id = post['id']
        print(f"\n[Post {post_id}] Processing...")

        
        icon_coords = None
        max_retries = 3

        if target_home is not None:
            for attempt in range(1, max_retries + 1):
                print(f" -> [Attempt {attempt}/{max_retries}] Searching for icon...")
                pyautogui.hotkey('win', 'm')
                time.sleep(1.0)
                current_candidates, _ = get_matches_on_screen(screenshot_index=post_id)

                temp_coords = None
                min_dist = 99999
                for cand in current_candidates:
                    dist = ((cand[0] - target_home[0])**2 + (cand[1] - target_home[1])**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        temp_coords = cand

                if temp_coords:
                    icon_coords = temp_coords
                    target_home = (icon_coords[0], icon_coords[1])  # update to latest position
                    print(f" -> Icon found at {target_home}.")
                    break
                else:
                    if attempt < max_retries:
                        time.sleep(2.0)

        
        if not icon_coords:
            print(f" -> [Warning] Icon not found. Trying Start Menu fallback...")
            if not open_notepad_via_startmenu():
                print(f"[Error] Start Menu fallback also failed. Skipping Post {post_id}.")
                continue
        else:
            print(f" -> Launching...")
            pyautogui.moveTo(icon_coords[0], icon_coords[1])
            pyautogui.doubleClick()

            if not verify_notepad_open():
                print("(!) Notepad failed to open. Trying Start Menu fallback...")
                if not open_notepad_via_startmenu():
                    print(f"[Error] Both launch methods failed. Skipping Post {post_id}.")
                    continue

        
        saved_path = type_and_save_post(post)
        print(f" -> Saved to: {saved_path}")

        
        print(" -> Closing...")
        pyautogui.hotkey('alt', 'f4')
        time.sleep(2.0)

        # Move away T_T
        pyautogui.moveTo(50, 50, duration=0.3)

    print("\n[Done] All posts processed.")

if __name__ == "__main__":
    main()