"""Fake-asset mockups: Slack threads, JIRA tickets, calendar blocks.

Each renderer takes mockup_data (a dict) and returns a 1920x1080 PIL Image.
The renderer wraps these as ImageClip with optional subtle Ken-Burns motion.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from render.config import resolve_font

# Dark-mode palette tuned to LGTM brand
BG = (18, 18, 22)
PANEL = (28, 28, 34)
PANEL_ALT = (36, 36, 44)
BORDER = (60, 60, 68)
TEXT = (230, 230, 232)
TEXT_DIM = (140, 140, 150)
TEXT_FAINT = (95, 95, 105)
ACCENT = (232, 160, 32)
DANGER = (220, 80, 70)
SUCCESS = (90, 180, 110)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(resolve_font(path), size)


def _rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width=1):
    """Pillow has rectangle but rounded_rectangle is also available in 8.2+."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def render_slack(data: dict, font_path: str, w: int = 1920, h: int = 1080) -> Image.Image:
    """Slack thread mockup.
    data: { channel: str, messages: [ {user, time, text}, ... ] }
    """
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Sidebar (left 240px)
    draw.rectangle([0, 0, 240, h], fill=(22, 22, 28))
    workspace_font = _font(font_path, 22)
    draw.text((24, 28), "Acme Corp", font=workspace_font, fill=TEXT)
    draw.text((24, 56), "● online", font=_font(font_path, 14), fill=SUCCESS)

    # Channel list
    channels = ["# general", "# ai-pilot", "# steering-committee", "# subcommittee", "# subsubcommittee"]
    cy = 110
    for c in channels:
        is_active = c == f"# {data.get('channel', '').lstrip('#').strip()}"
        if is_active:
            draw.rectangle([0, cy - 4, 240, cy + 28], fill=(50, 50, 60))
        draw.text((24, cy), c, font=_font(font_path, 18), fill=TEXT if is_active else TEXT_DIM)
        cy += 36

    # Header
    draw.line([(240, 96), (w, 96)], fill=BORDER, width=1)
    header = f"# {data.get('channel', 'channel').lstrip('#').strip()}"
    draw.text((280, 36), header, font=_font(font_path, 32), fill=TEXT)
    draw.text((280, 76), f"{len(data.get('messages', []))} messages · 0 decisions", font=_font(font_path, 14), fill=TEXT_FAINT)

    # Messages
    y = 140
    name_font = _font(font_path, 20)
    time_font = _font(font_path, 14)
    msg_font = _font(font_path, 22)
    for msg in data.get("messages", []):
        # Avatar (rounded square, accent colored block)
        avatar_color = (60 + (hash(msg["user"]) % 100), 80, 120)
        _rounded_rect(draw, (280, y, 320, y + 40), radius=8, fill=avatar_color)
        # Initials
        initials = "".join(p[0].upper() for p in msg["user"].split(".")[:2])[:2]
        draw.text((290, y + 8), initials, font=_font(font_path, 18), fill=TEXT)

        # Name + time
        draw.text((340, y), msg["user"], font=name_font, fill=TEXT)
        # Measure name to position time after
        nbox = draw.textbbox((0, 0), msg["user"], font=name_font)
        nw = nbox[2] - nbox[0]
        draw.text((340 + nw + 12, y + 4), msg.get("time", ""), font=time_font, fill=TEXT_FAINT)

        # Message text — wrap at ~55 chars
        text = msg["text"]
        wrapped = _wrap(text, 60)
        ty = y + 32
        for line in wrapped:
            draw.text((340, ty), line, font=msg_font, fill=TEXT)
            ty += 32
        y = ty + 22
        if y > h - 120:
            break

    # Bottom input bar
    _rounded_rect(draw, (280, h - 90, w - 60, h - 30), radius=8, outline=BORDER, fill=PANEL)
    draw.text((300, h - 75), "Message #" + data.get("channel", "channel").strip("#").strip(), font=msg_font, fill=TEXT_FAINT)

    return img


def render_jira(data: dict, font_path: str, w: int = 1920, h: int = 1080) -> Image.Image:
    """JIRA ticket mockup.
    data: { key, title, status, assignee, priority, reporter, created, comments_count }
    """
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Top breadcrumb
    breadcrumb = f"Projects / Steering Committee / {data.get('key', 'TICKET-1')}"
    draw.text((80, 60), breadcrumb, font=_font(font_path, 20), fill=TEXT_DIM)

    # Title
    title_font = _font(font_path, 56)
    title = data.get("title", "Untitled")
    draw.text((80, 110), title, font=title_font, fill=TEXT)

    # Status pill
    status = data.get("status", "Open")
    status_color = ACCENT if "progress" in status.lower() else DANGER if "block" in status.lower() else (90, 130, 200)
    sx, sy = 80, 200
    sw = 280
    sh = 56
    _rounded_rect(draw, (sx, sy, sx + sw, sy + sh), radius=8, fill=status_color)
    sf = _font(font_path, 24)
    sbox = draw.textbbox((0, 0), status.upper(), font=sf)
    draw.text((sx + (sw - (sbox[2] - sbox[0])) // 2, sy + (sh - (sbox[3] - sbox[1])) // 2 - 2),
              status.upper(), font=sf, fill=BG)

    # Two-column layout: description (left, 1100w), details (right)
    desc_x = 80
    desc_y = 300
    field_font = _font(font_path, 20)
    label_font = _font(font_path, 18)

    # Description block (placeholder body text)
    draw.text((desc_x, desc_y), "Description", font=label_font, fill=TEXT_DIM)
    body_lines = data.get("description_lines", [
        "Per Q3 OKR alignment, the steering committee has",
        "directed the formation of a subcommittee to",
        "establish governance protocols for the AI pilot's",
        "governance framework. Pending charter review.",
    ])
    by = desc_y + 36
    for line in body_lines:
        draw.text((desc_x, by), line, font=_font(font_path, 24), fill=TEXT)
        by += 36

    # Details panel on right
    panel_x = 1280
    panel_y = 300
    _rounded_rect(draw, (panel_x, panel_y, panel_x + 560, panel_y + 540), radius=12, fill=PANEL, outline=BORDER, width=1)

    px = panel_x + 28
    py = panel_y + 28
    fields = [
        ("Assignee", data.get("assignee", "Unassigned")),
        ("Reporter", data.get("reporter", "—")),
        ("Priority", data.get("priority", "Medium")),
        ("Sprint", data.get("sprint", "—")),
        ("Created", data.get("created", "—")),
        ("Updated", data.get("updated", "—")),
        ("Story points", data.get("points", "—")),
    ]
    for name, val in fields:
        draw.text((px, py), name, font=label_font, fill=TEXT_DIM)
        draw.text((px, py + 24), str(val), font=field_font, fill=TEXT)
        py += 68

    # Footer: comments count
    cy = h - 120
    draw.line([(80, cy - 20), (w - 80, cy - 20)], fill=BORDER, width=1)
    comments = data.get("comments_count", 0)
    draw.text((80, cy), f"Activity · {comments} comments · 0 resolutions",
              font=_font(font_path, 22), fill=TEXT_FAINT)

    return img


def render_calendar(data: dict, font_path: str, w: int = 1920, h: int = 1080) -> Image.Image:
    """Calendar event block mockup.
    data: { date, time, title, attendees, location, organizer }
    """
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Top date
    date_str = data.get("date", "Thursday, Oct 17")
    draw.text((80, 60), date_str, font=_font(font_path, 32), fill=TEXT_DIM)

    # Big block representing the event in calendar
    block_x, block_y = 80, 160
    block_w, block_h = 1040, 740
    _rounded_rect(draw, (block_x, block_y, block_x + block_w, block_y + block_h),
                  radius=14, fill=ACCENT)
    # Vertical accent bar inside
    draw.rectangle([block_x, block_y, block_x + 12, block_y + block_h], fill=(255, 255, 255))

    # Title (large)
    title = data.get("title", "Meeting")
    title_font = _font(font_path, 56)
    wrapped = _wrap(title, 26)
    ty = block_y + 60
    for line in wrapped:
        draw.text((block_x + 60, ty), line, font=title_font, fill=BG)
        ty += 70

    # Time
    time_font = _font(font_path, 32)
    draw.text((block_x + 60, ty + 30), data.get("time", "—"), font=time_font, fill=BG)
    # Location
    if data.get("location"):
        draw.text((block_x + 60, ty + 80), "📍 " + data["location"], font=_font(font_path, 26), fill=BG)

    # Right panel: attendees + meta
    panel_x = block_x + block_w + 40
    panel_y = block_y
    panel_w = w - panel_x - 80
    _rounded_rect(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + block_h),
                  radius=14, fill=PANEL, outline=BORDER, width=1)

    px = panel_x + 32
    py = panel_y + 32
    draw.text((px, py), "Guests", font=_font(font_path, 20), fill=TEXT_DIM)
    py += 36
    attendees = data.get("attendees", 0)
    if isinstance(attendees, int):
        draw.text((px, py), f"{attendees} attending", font=_font(font_path, 36), fill=TEXT)
        py += 52
        # List a few generic names
        names = data.get("attendee_names") or [
            "Steering Committee",
            "Subcommittee Chair",
            "Compliance Lead",
            "AI Pilot PM",
            "Governance Counsel",
            "+ 6 others",
        ]
        for n in names[:6]:
            draw.text((px, py), "• " + n, font=_font(font_path, 22), fill=TEXT_DIM)
            py += 34
    else:
        draw.text((px, py), str(attendees), font=_font(font_path, 28), fill=TEXT)

    # Organizer at bottom of panel
    org = data.get("organizer", "Steering Committee")
    draw.text((px, panel_y + block_h - 80), "Organized by", font=_font(font_path, 18), fill=TEXT_DIM)
    draw.text((px, panel_y + block_h - 56), org, font=_font(font_path, 22), fill=TEXT)

    return img


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# Syntax highlighting palette
CODE_BG = (12, 14, 18)
CODE_GUTTER = (28, 30, 36)
CODE_TEXT = (220, 220, 220)
CODE_COMMENT = (110, 115, 130)
CODE_KEYWORD = (232, 160, 32)     # accent
CODE_STRING = (140, 200, 130)
CODE_NUMBER = (95, 200, 232)
CODE_FN = (240, 130, 180)


_KEYWORDS = {
    "py":  {"def","class","return","if","else","elif","for","while","import","from","as","try","except","with","in","is","not","and","or","None","True","False","lambda","yield","pass","break","continue","raise","global","nonlocal"},
    "js":  {"const","let","var","function","return","if","else","for","while","import","from","export","default","class","new","await","async","try","catch","throw","null","undefined","true","false","this","typeof"},
    "ts":  {"const","let","var","function","return","if","else","for","while","import","from","export","default","class","new","await","async","try","catch","throw","null","undefined","true","false","this","typeof","interface","type","enum","as","public","private","readonly"},
    "sh":  {"echo","if","then","else","fi","for","while","do","done","case","esac","exit","return","function","export","local"},
}

# Cheap tokenizer — splits on whitespace + punctuation, then classifies each piece
import re as _re
_TOKEN_RE = _re.compile(r'(\s+|[A-Za-z_][A-Za-z0-9_]*|"[^"]*"|\'[^\']*\'|\d+\.?\d*|//.*|#.*|[^\sA-Za-z0-9])')


def _tokenize_code(line: str, lang: str) -> list[tuple[str, tuple[int,int,int]]]:
    """Return list of (text, color) tuples. Order preserved, including whitespace."""
    keywords = _KEYWORDS.get(lang, set())
    out = []
    for m in _TOKEN_RE.findall(line):
        if not m:
            continue
        if m.startswith("//") or m.startswith("#"):
            out.append((m, CODE_COMMENT))
        elif m.startswith('"') or m.startswith("'"):
            out.append((m, CODE_STRING))
        elif m and m[0].isdigit():
            out.append((m, CODE_NUMBER))
        elif m in keywords:
            out.append((m, CODE_KEYWORD))
        elif m.isspace():
            out.append((m, CODE_TEXT))
        else:
            out.append((m, CODE_TEXT))
    return out


def render_code(data: dict, font_path: str, w: int = 1920, h: int = 1080) -> Image.Image:
    """
    Code panel mockup.
    data: { filename: str, language: "py|js|ts|sh", lines: list[str] }
    Renders a windowed code editor with line numbers, syntax-highlighted lines,
    a filename tab header, and a blinking cursor on the last line.
    """
    img = Image.new("RGB", (w, h), (8, 9, 12))
    draw = ImageDraw.Draw(img)

    filename = data.get("filename", "untitled")
    lang = data.get("language", "ts")
    lines = data.get("lines", [])

    # Outer panel inset
    inset = 80
    panel_x0, panel_y0 = inset, inset
    panel_x1, panel_y1 = w - inset, h - inset
    _rounded_rect(draw, (panel_x0, panel_y0, panel_x1, panel_y1), radius=14, fill=CODE_BG, outline=BORDER, width=2)

    # Tab header (filename tab + traffic-light circles)
    tab_h = 56
    draw.rectangle([panel_x0, panel_y0, panel_x1, panel_y0 + tab_h], fill=(22, 24, 30))
    # macOS-ish dots
    for i, color in enumerate([(220, 80, 70), (220, 180, 60), (110, 200, 110)]):
        cx = panel_x0 + 24 + i * 28
        cy = panel_y0 + tab_h // 2
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=color)
    # Filename
    name_font = _font(font_path, 22)
    fb = draw.textbbox((0, 0), filename, font=name_font)
    fw_, fh_ = fb[2] - fb[0], fb[3] - fb[1]
    draw.text((panel_x0 + (panel_x1 - panel_x0 - fw_) // 2, panel_y0 + (tab_h - fh_) // 2 - 2),
              filename, font=name_font, fill=CODE_TEXT)

    # Code area
    code_x0 = panel_x0 + 90
    gutter_w = 70
    gutter_x = panel_x0 + 8
    code_y0 = panel_y0 + tab_h + 28

    code_font_size = 36
    code_font = _font(font_path, code_font_size)
    line_h = code_font_size + 10

    # Render lines
    for i, line in enumerate(lines):
        y = code_y0 + i * line_h
        if y + line_h > panel_y1 - 16:
            break

        # Line number (right-aligned in gutter)
        ln = str(i + 1).rjust(2)
        draw.text((gutter_x + 8, y), ln, font=code_font, fill=CODE_COMMENT)

        # Tokenized line
        x = code_x0
        for tok, color in _tokenize_code(line, lang):
            draw.text((x, y), tok, font=code_font, fill=color)
            tb = draw.textbbox((0, 0), tok, font=code_font)
            x += tb[2] - tb[0]

    # Blinking cursor at end of last line (drawn as a solid block; CSS overlay
    # in Remotion will animate the blink — here we just put it always-on)
    if lines:
        last = lines[min(len(lines) - 1, (panel_y1 - 16 - code_y0) // line_h - 1)]
        last_y = code_y0 + min(len(lines), (panel_y1 - 16 - code_y0) // line_h) * line_h - line_h
        last_w = sum(
            draw.textbbox((0, 0), tok, font=code_font)[2] - draw.textbbox((0, 0), tok, font=code_font)[0]
            for tok, _ in _tokenize_code(last, lang)
        )
        cx = code_x0 + last_w + 4
        draw.rectangle([cx, last_y + 4, cx + 18, last_y + line_h - 6], fill=CODE_KEYWORD)

    return img


RENDERERS = {
    "slack": render_slack,
    "jira": render_jira,
    "calendar": render_calendar,
    "code": render_code,
}


def render_mockup(mockup_type: str, data: dict, font_path: str, resolution: tuple[int, int]) -> Image.Image:
    if mockup_type not in RENDERERS:
        raise ValueError(f"Unknown mockup_type: {mockup_type}. Known: {list(RENDERERS)}")
    return RENDERERS[mockup_type](data, font_path, w=resolution[0], h=resolution[1])
