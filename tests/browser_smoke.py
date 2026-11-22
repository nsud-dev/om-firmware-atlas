"""Exercise owner and developer journeys against a built Atlas served over HTTP."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from threading import Thread

from playwright.sync_api import expect, sync_playwright


class SiteHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def owner_journey(page, base, phone):
    page.goto(base)
    finder = page.get_by_label("Find your camera")
    finder.fill("E148")
    finder.press("Enter")
    expect(page).to_have_url(base + "views/cameras/om5-ii/")

    page.get_by_role("link", name="View the showcase").click()
    expect(page).to_have_url(base + "views/showcases/om5-ii/")
    expect(page.locator("#primary-nav").get_by_text("For camera owners", exact=True)).to_have_attribute(
        "aria-current", "true")
    project = page.locator(".model-panel").filter(has=page.get_by_role("heading", name="Caduceus for OM-5", exact=True))
    expect(project.get_by_role("img")).to_have_attribute("src", re.compile(r"picture-mode-look\.png$"))
    expect(project.get_by_role("link", name="Full project details")).to_have_attribute(
        "href", re.compile(r"caduceus-om5/#for-om5-ii$"))

    # Click the actual link with pointer hit testing. Do not fetch upstream.
    guide = project.get_by_role("link", name="Install guide")
    destination = guide.evaluate("a => a.href")
    page.route(destination, lambda route: route.fulfill(content_type="text/plain", body="Install guide"))
    guide.click()
    expect(page).to_have_url(destination)
    page.go_back()

    page.keyboard.press("/")
    search = page.get_by_role("searchbox", name="Search terms")
    expect(search).to_be_focused()
    search.press_sequentially("Caduceus")
    results = page.locator(".search-results a")
    # The search index is loaded by a worker. Wait for the first real result.
    page.wait_for_function("""() => {
        if (document.querySelector('.search-results a')) return true;
        document.querySelector('#mkdocs-search-query').dispatchEvent(new KeyboardEvent('keyup'));
        return false;
    }""", polling=200)
    destination = results.first.evaluate("a => a.href")
    search.press("Enter")
    expect(page).to_have_url(destination)

    if phone:
        menu = page.locator("[data-menu-toggle]")
        menu.focus()
        page.keyboard.press("Enter")
        expect(page.locator("#primary-nav a").first).to_be_focused()
        page.keyboard.press("Escape")
        expect(menu).to_be_focused()
        expect(menu).to_have_attribute("aria-expanded", "false")


def developer_journey(page, base, phone):
    page.goto(base + "views/evidence/om5-ii-v020-alpha1-owner/")
    if phone:
        page.locator("[data-menu-toggle]").click()
    page.locator("#primary-nav").get_by_role("link", name="For developers").click()
    expect(page).to_have_url(base + "research/")
    page.locator(".explore-grid").get_by_role("link", name="Cross-body research").click()
    expect(page).to_have_url(base + "cross-body/")
    page.get_by_role("link", name="E-M5 Mark III platform").click()
    expect(page).to_have_url(base + "views/research/em5-iii/#platform")
    expect(page.get_by_role("heading", name="Claims and test evidence")).to_be_visible()
    page.goto(base + "research/")
    page.locator(".explore-grid").get_by_role("link", name="Research by camera").click()
    page.get_by_role("link", name="OM-5 Mark II", exact=True).click()
    expect(page).to_have_url(base + "views/research/om5-ii/")
    page.goto(base + "research/")
    page.get_by_role("link", name="Use the Atlas with your AI", exact=True).last.click()
    expect(page).to_have_url(base + "research-with-ai/")
    page.go_back()
    page.get_by_role("link", name="Share a finding").click()
    expect(page).to_have_url(base + "research-with-ai/#share-what-you-find")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", help="Optional path to an existing Chromium binary")
    parser.add_argument("--browser-arg", action="append", default=[])
    args = parser.parse_args()
    site = Path(__file__).resolve().parents[1] / "site"
    if not (site / "index.html").exists():
        parser.error("Build the Atlas before running the browser checks.")
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(SiteHandler, directory=site)) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.executable, args=args.browser_arg)
                for width, height in ((1440, 900), (390, 844)):
                    page = browser.new_page(viewport={"width": width, "height": height})
                    owner_journey(page, f"http://127.0.0.1:{server.server_port}/", width == 390)
                    developer_journey(page, f"http://127.0.0.1:{server.server_port}/", width == 390)
                    print(f"Owner and developer journeys passed at {width} x {height}")
                browser.close()
        finally:
            server.shutdown()
