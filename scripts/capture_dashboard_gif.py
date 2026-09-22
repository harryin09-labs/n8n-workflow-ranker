"""
Capture a GIF of the Streamlit dashboard demo:
  1. Overview metrics
  2. Leaderboards tab -> switch to Hidden Gems leaderboard
  3. Leaderboards -> Top AI Agents
  4. Workflow Explorer + complexity filter BEGINNER
  5. Hidden Gems tab
Assembles docs/dashboard_demo.gif
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

OUT = Path(r"G:\n8n-workflow-ranker\docs")
OUT.mkdir(exist_ok=True)
shots = []

# --- JS helpers -------------------------------------------------------------
JS_GET_COMBO_POS = """(labelText) => {
    const label = Array.from(document.querySelectorAll('label'))
        .find(l => l.textContent.includes(labelText));
    if (!label) return null;
    const box = label.closest('[data-testid="stSelectbox"]');
    if (!box) return null;
    const combos = box.querySelectorAll('.react-aria-ComboBox');
    for (const c of combos) {
        if (c.offsetParent !== null) {
            const r = c.getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }
    }
    return null;
}"""

JS_PICK_OPTION = """(optText) => {
    // options live in the react portal
    const roots = [document, document.querySelector('[data-testid="portal"]')];
    for (const root of roots) {
        if (!root) continue;
        const opts = root.querySelectorAll('[role="option"]');
        for (const o of opts) {
            if (o.textContent.trim() === optText && o.offsetParent !== null) {
                o.click();
                return 'picked';
            }
        }
    }
    return 'not-found';
}"""


def open_selectbox(page, label_text):
    pos = page.evaluate(JS_GET_COMBO_POS, label_text)
    if not pos:
        print("  !! no combobox for", label_text)
        return False
    page.mouse.click(pos["x"], pos["y"])
    page.wait_for_timeout(1200)
    return True


def pick_option(page, text):
    r = page.evaluate(JS_PICK_OPTION, text)
    print("  pick", r, "->", text)
    page.wait_for_timeout(1500)


def grab(page, tag, wait_ms=2000):
    page.wait_for_timeout(wait_ms / 1000)
    p = OUT / f"frame_{tag:02d}.png"
    page.screenshot(path=str(p), full_page=False)
    shots.append(str(p))
    print("shot", tag, p.name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://localhost:8505", wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(5000)

    # 1. Overview & Metrics
    grab(page, 1)

    # 2. Leaderboards -> Top Overall (already default), capture
    page.get_by_role("tab", name="🏆 Leaderboards & Rankings").click()
    grab(page, 2, 2500)

    # 3. Switch leaderboard to Hidden Gems
    if open_selectbox(page, "Select Ranking Leaderboard"):
        pick_option(page, "💎 Hidden Gems (High Quality, Low Views)")
    grab(page, 3, 3000)

    # 4. Switch to Top AI Agents
    if open_selectbox(page, "Select Ranking Leaderboard"):
        pick_option(page, "🤖 Top AI Agents")
    grab(page, 4, 3000)

    # 5. Workflow Explorer with BEGINNER filter
    page.get_by_role("tab", name="🔍 Workflow Explorer").click()
    grab(page, 5, 2000)
    if open_selectbox(page, "Complexity"):
        pick_option(page, "BEGINNER")
    grab(page, 6, 2500)

    # 7. Hidden Gems dedicated tab
    page.get_by_role("tab", name="💎 Hidden Gems").click()
    grab(page, 7, 3000)

    browser.close()

print(f"{len(shots)} frames captured")

# Assemble GIF (loop, 1.5s per frame)
frames = []
for s in shots:
    img = Image.open(s).convert("RGB")
    if img.width > 1280:
        ratio = 1280 / img.width
        img = img.resize((1280, int(img.height * ratio)), Image.LANCZOS)
    frames.append(img)

gif = OUT / "dashboard_demo.gif"
frames[0].save(gif, save_all=True, append_images=frames,
               duration=1500, loop=0, optimize=True)
print("GIF:", gif, gif.stat().st_size // 1024, "KB")
