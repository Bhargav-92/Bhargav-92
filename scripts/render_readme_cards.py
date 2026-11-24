"""Generate animated profile SVGs from GitHub's public contribution calendar."""
import argparse
from collections import defaultdict
from datetime import date
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = "Bhargav-92"
BLUE = "#174bbb"
NAVY = "#15284c"
MUTED = "#496184"
LEVELS = ["#e2eafb", "#a4bdf5", "#6f98f0", "#376bd7", BLUE]


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.target = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.cells[attrs["id"]] = (attrs["data-date"], int(attrs["data-level"]))
        if tag == "tool-tip":
            self.target = attrs.get("for")

    def handle_data(self, data):
        if self.target:
            match = re.match(r"(No|[\d,]+) contributions? on ", data.strip())
            if match:
                value = match[1]
                self.counts[self.target] = 0 if value == "No" else int(value.replace(",", ""))

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.target = None

    def days(self):
        if len(self.cells) < 350 or self.cells.keys() - self.counts.keys():
            raise ValueError("GitHub returned an incomplete contribution calendar")
        return {
            day: {"count": self.counts[key], "level": level}
            for key, (day, level) in sorted(self.cells.items(), key=lambda item: item[1][0])
        }


def refresh(source):
    parser = Calendar()
    if source:
        parser.feed(source.read_text(encoding="utf-8"))
    else:
        request = Request(
            f"https://github.com/users/{USER}/contributions",
            headers={"User-Agent": "github-profile-cards", "Accept-Language": "en"},
        )
        with urlopen(request, timeout=30) as response:
            parser.feed(response.read().decode("utf-8"))
    return parser.days()


def rect(x, y, w, h, color, radius=4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{color}"/>'


def label(x, y, value, size=16, color=NAVY, font="sans-serif", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" '
        f'font-size="{size}" text-anchor="{anchor}">{escape(str(value))}</text>'
    )


def motion(body, delay=0, effect="rise"):
    return f'<g class="{effect}" style="animation-delay:{delay}ms">{body}</g>'


def card(filename, title, width, height, body, background="#f3f7ff"):
    styles = "" if os.getenv("STATIC") == "1" else """
<style>
.rise { animation: rise 680ms cubic-bezier(.2,.8,.2,1) both }
.pop { animation: pop 470ms ease-out both }
.grow { transform-box:fill-box; transform-origin:bottom; animation:grow 740ms ease-out both }
@keyframes rise { from { opacity:0; transform:translateY(10px) } }
@keyframes pop { from { opacity:0 } }
@keyframes grow { from { opacity:.25; transform:scaleY(.06) } }
@media (prefers-reduced-motion: reduce) { .rise,.pop,.grow { animation:none !important } }
</style>"""
    frame = (
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="17" '
        f'fill="{background}" stroke="#b7c9ee"/>'
    )
    (ROOT / "cards" / filename).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title>'
        f'{styles}{frame}{body}</svg>\n',
        encoding="utf-8",
    )


def hero():
    body = label(34, 43, "PORTFOLIO  /  @BHARGAV-92", 14, BLUE, "monospace")
    body += motion(label(31, 119, "Bhargav Thakar", 65, NAVY, "Georgia"), 70)
    body += motion(label(35, 157, "Frontend web developer based in India", 21, BLUE), 220)
    body += motion(label(35, 193, "I build web apps.", 17, MUTED), 330)
    for row in range(7):
        pixels = "".join(
            rect(637 + col * 16, 55 + row * 16, 12, 12, LEVELS[(col + row) % 5], 2)
            for col in range(7)
            if row in (0, 6) or col in (0, 6) or col == row or col + row == 6
        )
        body += motion(pixels, 250 + row * 65, "pop")
    card("hero.svg", "Bhargav Thakar, frontend web developer based in India", 800, 222, body)


def activity(data):
    days = [(date.fromisoformat(key), value) for key, value in sorted(data.items())]
    first = days[0][0]
    total = sum(value["count"] for _, value in days)
    active = sum(value["count"] > 0 for _, value in days)
    busy_day, busy = max(days, key=lambda pair: pair[1]["count"])
    current_run = longest = 0
    months = defaultdict(int)
    graph = label(28, 42, "Contribution calendar", 29, NAVY, "Georgia")
    graph += label(772, 40, f"{total:,} contributions", 16, BLUE, anchor="end")
    for day, value in days:
        sunday_index = (day.weekday() + 1) % 7
        week = ((day - first).days + (first.weekday() + 1) % 7) // 7
        square = rect(30 + week * 14, 65 + sunday_index * 14, 11, 11, LEVELS[value["level"]], 2)
        graph += motion(square, 310 + week * 12, "pop")
        current_run = current_run + 1 if value["count"] else 0
        longest = max(longest, current_run)
        months[day.replace(day=1)] += value["count"]
    graph += label(30, 185, f"{first:%d %b %Y}  –  {days[-1][0]:%d %b %Y}", 13, MUTED)
    for index, color in enumerate(LEVELS):
        graph += rect(704 + index * 14, 173, 11, 11, color, 2)
    card("calendar.svg", f"Contribution calendar, {total:,} contributions", 800, 204, graph)

    peak = max(months.values())
    stats = (
        f"{active} active days   ·   {longest}-day longest streak   ·   "
        f"{busy['count']} on {busy_day:%d %b %Y}"
        if total else "0 active days   ·   0-day longest streak   ·   No busiest day"
    )
    chart = label(28, 42, "Monthly activity", 29, NAVY, "Georgia")
    chart += label(30, 71, stats, 16, MUTED)
    chart += rect(30, 212, 740, 1, "#b7c9ee")
    for index, (month, count) in enumerate(months.items()):
        width = 740 / len(months)
        x = round(30 + width * (index + 0.5))
        height = round(count * 105 / max(peak, 1))
        if height:
            bar = rect(x - 13, 212 - height, 26, height, BLUE if count == peak else "#769bee")
            chart += motion(bar, 620 + index * 50, "grow")
        chart += label(x, 205 - height, count, 12, NAVY, anchor="middle")
        chart += label(x, 235, month.strftime("%b %y"), 10, MUTED, anchor="middle")
    card("monthly.svg", f"Monthly activity. {stats}", 800, 255, chart)


def links():
    tiles = [
        ("build", "Build", "Browse my repositories", "#e7efff", BLUE),
        ("write", "Write", "Find me on DEV", "#fff0e9", "#9c3926"),
        ("connect", "Connect", "Find me on LinkedIn", "#e6f4ee", "#165a47"),
    ]
    for index, (slug, title, description, bg, accent) in enumerate(tiles):
        body = label(17, 36, title, 32, accent, "Georgia")
        body += label(17, 64, description, 15, NAVY)
        body += label(228, 39, "↗", 23, accent, anchor="end")
        card(f"{slug}.svg", description, 245, 86, motion(body, 850 + index * 100), bg)

    for index, (repo, description, stack) in enumerate([
        ("Pharma-Buddy", "Pharmacy website", "JAVASCRIPT"),
        ("Amplify", "Music player for the web", "HTML / CSS / JS"),
        ("Podcast-App", "Podcast player for iPhone and iPad", "SWIFTUI"),
    ]):
        body = label(26, 44, repo, 27, NAVY, "Georgia")
        body += label(27, 73, description, 16, MUTED)
        body += label(769, 43, stack, 14, BLUE, "monospace", "end")
        card(f"{repo}.svg", f"{repo}, {description}", 800, 96, motion(body, 1140 + index * 100))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    inputs = cli.add_mutually_exclusive_group()
    inputs.add_argument("--refresh", action="store_true")
    inputs.add_argument("--calendar-html", type=Path)
    args = cli.parse_args()
    data_file = ROOT / "data" / "contributions.json"
    if args.refresh or args.calendar_html:
        data = refresh(args.calendar_html)
        data_file.parent.mkdir(exist_ok=True)
        data_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        data = json.loads(data_file.read_text(encoding="utf-8"))
    (ROOT / "cards").mkdir(exist_ok=True)
    hero()
    activity(data)
    links()


if __name__ == "__main__":
    main()
