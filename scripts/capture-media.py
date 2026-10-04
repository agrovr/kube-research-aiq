"""Regenerate the README media: banner, console screenshots and the animated demo.

Needs Playwright for Python, ffmpeg with libwebp, the dashboard dev server on :5173 and an
offline API on :8000 started with KRAI_MOCK_LATENCY_SECONDS=0.5 and an empty job store:

    make run-api            # terminal 1
    make dashboard-dev      # terminal 2
    python scripts/capture-media.py

Set CHROMIUM to a browser executable if Playwright's bundled one isn't installed.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media"
API = "http://localhost:8000"
CONSOLE = "http://localhost:5173/"
DEMO_QUERY = ("Compare Kubernetes deployment strategies for AI research agents and recommend a "
              "production architecture.")
SEED = [
    "Evaluate how to secure and observe an LLM agent platform on Kubernetes.",
    "How should we run Postgres and Redis for an agent job queue?",
    "What is KEDA?",
]


def dive(query: str) -> None:
    body = json.dumps({"query": query, "depth": "auto", "tenant": "console"}).encode()
    request = urllib.request.Request(f"{API}/v1/research", body,
                                     {"Content-Type": "application/json"})
    urllib.request.urlopen(request).read()


def save(page: Page, name: str, **options) -> None:
    with tempfile.NamedTemporaryFile(suffix=".png") as raw:
        page.screenshot(path=raw.name, **options)
        Image.open(raw.name).convert("RGB").save(MEDIA / f"{name}.png", optimize=True)


def banner(browser) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 400}, device_scale_factor=2)
    page.goto((ROOT / "docs" / "brand" / "banner.html").as_uri())
    page.wait_for_timeout(800)
    save(page, "banner")


def demo(browser, workdir: Path) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(CONSOLE)
    page.wait_for_timeout(1500)
    frames: list[tuple[str, float]] = []

    def snap() -> None:
        path = workdir / f"f{len(frames):04d}.png"
        page.screenshot(path=path)
        frames.append((str(path), time.monotonic()))

    for _ in range(4):
        snap()
        page.wait_for_timeout(150)
    page.click("textarea")
    for i in range(0, len(DEMO_QUERY), 5):
        page.type("textarea", DEMO_QUERY[i:i + 5])
        snap()
    page.click("button.dive")
    start = time.monotonic()
    while time.monotonic() - start < 20:
        snap()
        page.wait_for_timeout(120)
        if page.locator(".sounding-status").inner_text().startswith("Surfaced"):
            break
    for _ in range(6):
        snap()
        page.wait_for_timeout(150)
    chip = page.locator(".report-section .cite").nth(4)
    chip.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    chip.click()
    for _ in range(10):
        snap()
        page.wait_for_timeout(120)

    listing = ["ffconcat version 1.0"]
    for index, (path, at) in enumerate(frames):
        last = index + 1 == len(frames)
        hold = 2.8 if last else min(max(frames[index + 1][1] - at, 0.08), 0.6)
        listing += [f"file '{path}'", f"duration {hold:.3f}"]
    listing.append(f"file '{frames[-1][0]}'")
    (workdir / "list.txt").write_text("\n".join(listing) + "\n")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
         str(workdir / "list.txt"), "-vf", "scale=1100:-1:flags=lanczos,fps=12",
         "-c:v", "libwebp_anim", "-quality", "78", "-compression_level", "6", "-loop", "0",
         str(MEDIA / "demo.webp")],
        check=True,
    )


def stills(browser) -> None:
    page = browser.new_page(viewport={"width": 1440, "height": 940}, device_scale_factor=1.5)
    page.goto(CONSOLE)
    page.wait_for_timeout(1500)
    save(page, "console")
    chip = page.locator(".report-section .cite").nth(6)
    chip.scroll_into_view_if_needed()
    chip.click()
    page.wait_for_timeout(900)
    save(page, "citations")
    page.evaluate("window.scrollTo(0, 0)")
    page.locator(".log-entry", has_text="What is KEDA").click()
    page.wait_for_timeout(800)
    save(page, "shallow")
    page.fill("textarea", "Evaluate GPU scheduling and inference serving options for self-hosted "
                          "research agents.")
    page.click("button.dive")
    page.wait_for_timeout(4300)
    save(page, "diving")

    phone = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    phone.goto(CONSOLE)
    phone.wait_for_timeout(800)
    phone.fill("textarea", "How should research workers autoscale on a Redis queue?")
    phone.click("button.dive")
    phone.wait_for_timeout(1800)
    phone.evaluate("document.querySelector('.instruments').scrollIntoView()")
    phone.wait_for_timeout(300)
    save(phone, "mobile")


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    for query in SEED:
        dive(query)
        time.sleep(8)
    with sync_playwright() as playwright, tempfile.TemporaryDirectory() as workdir:
        options = {"executable_path": os.environ["CHROMIUM"]} if "CHROMIUM" in os.environ else {}
        browser = playwright.chromium.launch(**options)
        banner(browser)
        demo(browser, Path(workdir))
        stills(browser)
        browser.close()
    print(f"Media written to {MEDIA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
