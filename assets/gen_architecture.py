#!/usr/bin/env python3
"""Generate hypebot-rs architecture diagram — clean grid layout, orthogonal arrows."""

from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1280, 860
FONT_DIR = "/home/ubuntu/.claude/skills/canvas-design/canvas-fonts"

# === Colors ===
BG_DEEP   = (5, 8, 18)
BG_MID    = (9, 14, 28)
CYAN      = (14, 165, 233)
GREEN     = (34, 197, 94)
VIOLET    = (139, 92, 246)
AMBER     = (245, 158, 11)
RED       = (239, 68, 68)
SKY       = (56, 189, 248)
WHITE     = (248, 250, 252)
SLATE     = (148, 163, 184)

def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * max(0, min(1, t))) for a, b in zip(c1, c2))


class Box:
    """A positioned component box for precise arrow anchoring."""
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def cx(self): return self.x + self.w // 2
    @property
    def cy(self): return self.y + self.h // 2
    @property
    def top(self): return self.y
    @property
    def bot(self): return self.y + self.h
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    def top_at(self, frac): return (self.x + int(self.w * frac), self.y)
    def bot_at(self, frac): return (self.x + int(self.w * frac), self.y + self.h)
    def left_at(self, frac): return (self.x, self.y + int(self.h * frac))
    def right_at(self, frac): return (self.x + self.w, self.y + int(self.h * frac))


def create_architecture():
    img = Image.new('RGB', (W, H), BG_DEEP)
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(H):
        bg = lerp(BG_DEEP, (10, 16, 32), y / H)
        draw.line([(0, y), (W, y)], fill=bg)

    # Dot grid
    for gx in range(0, W, 20):
        for gy in range(0, H, 20):
            draw.point((gx, gy), fill=lerp(BG_DEEP, SLATE, 0.04))

    # Scan lines
    for y in range(0, H, 3):
        draw.line([(0, y), (W, y)], fill=lerp(BG_DEEP, WHITE, 0.006))

    # === Fonts ===
    font_title    = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Bold.ttf", 30)
    font_sub      = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Regular.ttf", 14)
    font_comp     = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Bold.ttf", 17)
    font_desc     = ImageFont.truetype(f"{FONT_DIR}/InstrumentSans-Regular.ttf", 12)
    font_label    = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Regular.ttf", 10)
    font_layer    = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Bold.ttf", 11)
    font_filter   = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Regular.ttf", 11)
    font_fnum     = ImageFont.truetype(f"{FONT_DIR}/GeistMono-Bold.ttf", 11)

    # === Title ===
    draw.text((60, 30), "hypebot-rs", font=font_title, fill=WHITE)
    draw.text((60, 64), "architecture overview", font=font_sub, fill=lerp(BG_MID, CYAN, 0.55))
    draw.line([(60, 86), (320, 86)], fill=lerp(BG_MID, CYAN, 0.18), width=1)

    # =========================================================================
    # LAYOUT — strict grid with generous vertical gaps
    # =========================================================================
    LEFT_MARGIN = 120
    COL_GAP = 30
    BOX_W = 250
    BOX_H = 74
    ROW_GAP = 60          # vertical space between rows (for arrows)
    LAYER_LABEL_X = 26

    row_y = [120, 120 + BOX_H + ROW_GAP,
             120 + 2 * (BOX_H + ROW_GAP),
             120 + 3 * (BOX_H + ROW_GAP)]

    # Column x positions (3 columns in main area)
    col_x = [LEFT_MARGIN,
             LEFT_MARGIN + BOX_W + COL_GAP,
             LEFT_MARGIN + 2 * (BOX_W + COL_GAP)]

    # =========================================================================
    # DRAW COMPONENT HELPER
    # =========================================================================
    def draw_box(bx, by, bw, bh, name, line1, line2, color):
        """Draw a component box, return Box for anchoring."""
        # Fill
        for row in range(bh):
            t = row / bh
            c = lerp(lerp(BG_DEEP, color, 0.07), lerp(BG_DEEP, color, 0.025), t)
            draw.line([(bx, by + row), (bx + bw, by + row)], fill=c)

        # Border
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10,
                               outline=lerp(BG_MID, color, 0.50), width=2)

        # Top edge glow
        for i in range(4):
            a = 0.12 - i * 0.03
            draw.line([(bx + 6, by + 2 + i), (bx + bw - 6, by + 2 + i)],
                      fill=lerp(BG_MID, color, a))

        # Status dot
        dx, dy = bx + 16, by + 18
        for r in range(7, 0, -1):
            a = 0.08 + (1 - r / 7) * 0.55
            draw.ellipse([dx - r, dy - r, dx + r, dy + r], fill=lerp(BG_MID, color, a))

        # Text
        draw.text((bx + 30, by + 11), name, font=font_comp, fill=WHITE)
        draw.text((bx + 16, by + 36), line1, font=font_desc, fill=lerp(BG_MID, color, 0.60))
        draw.text((bx + 16, by + 52), line2, font=font_desc, fill=lerp(BG_MID, color, 0.40))

        return Box(bx, by, bw, bh)

    # =========================================================================
    # ARROW HELPERS — orthogonal only (vertical + horizontal segments)
    # =========================================================================
    def arrowhead(x, y, direction, color):
        """Draw a small triangle. direction: 'down','up','right','left'."""
        s = 6
        hc = lerp(BG_MID, color, 0.60)
        if direction == 'down':
            draw.polygon([(x, y), (x - s, y - s), (x + s, y - s)], fill=hc)
        elif direction == 'up':
            draw.polygon([(x, y), (x - s, y + s), (x + s, y + s)], fill=hc)
        elif direction == 'right':
            draw.polygon([(x, y), (x - s, y - s), (x - s, y + s)], fill=hc)
        elif direction == 'left':
            draw.polygon([(x, y), (x + s, y - s), (x + s, y + s)], fill=hc)

    def vline(x, y1, y2, color, dashed=False, w=2):
        c = lerp(BG_MID, color, 0.35)
        if dashed:
            step = 10
            y = min(y1, y2)
            end = max(y1, y2)
            while y < end:
                draw.line([(x, y), (x, min(y + 6, end))], fill=c, width=w)
                y += step
        else:
            draw.line([(x, y1), (x, y2)], fill=c, width=w)

    def hline(y, x1, x2, color, dashed=False, w=2):
        c = lerp(BG_MID, color, 0.35)
        if dashed:
            step = 10
            x = min(x1, x2)
            end = max(x1, x2)
            while x < end:
                draw.line([(x, y), (min(x + 6, end), y)], fill=c, width=w)
                x += step
        else:
            draw.line([(x1, y), (x2, y)], fill=c, width=w)

    def arrow_down(x, y1, y2, color, dashed=False):
        """Vertical arrow pointing down."""
        vline(x, y1, y2, color, dashed)
        arrowhead(x, y2, 'down', color)

    def arrow_right(y, x1, x2, color, dashed=False):
        """Horizontal arrow pointing right."""
        hline(y, x1, x2, color, dashed)
        arrowhead(x2, y, 'right', color)

    def arrow_L_down(x1, y1, x2, y2, color, dashed=False):
        """L-shaped: go down from (x1,y1), then horizontal to x2, then down to y2."""
        mid_y = y1 + (y2 - y1) // 2
        vline(x1, y1, mid_y, color, dashed)
        hline(mid_y, x1, x2, color, dashed)
        vline(x2, mid_y, y2, color, dashed)
        arrowhead(x2, y2, 'down', color)

    def arrow_elbow_down(x1, y1, mid_y, x2, y2, color, dashed=False):
        """Explicit elbow: down from y1 to mid_y, horizontal to x2, down to y2."""
        vline(x1, y1, mid_y, color, dashed)
        hline(mid_y, x1, x2, color, dashed)
        vline(x2, mid_y, y2, color, dashed)
        arrowhead(x2, y2, 'down', color)

    # =========================================================================
    # LAYER LABELS
    # =========================================================================
    layer_info = [
        (row_y[0] + BOX_H // 2, "TRANSPORT", CYAN),
        (row_y[1] + BOX_H // 2, "PROCESSING", SKY),
        (row_y[2] + BOX_H // 2, "EXECUTION", GREEN),
        (row_y[3] + BOX_H // 2, "INFRA", AMBER),
    ]
    for ly, label, color in layer_info:
        draw.text((LAYER_LABEL_X, ly - 6), label, font=font_layer,
                  fill=lerp(BG_MID, color, 0.35))
        draw.line([(LAYER_LABEL_X - 6, ly - 8), (LAYER_LABEL_X - 6, ly + 6)],
                  fill=lerp(BG_MID, color, 0.45), width=2)

    # === Horizontal separator lines between layers ===
    for i in range(1, 4):
        sep_y = row_y[i] - ROW_GAP // 2
        draw.line([(LEFT_MARGIN - 20, sep_y), (col_x[2] + BOX_W + 20, sep_y)],
                  fill=lerp(BG_DEEP, SLATE, 0.04), width=1)

    # =========================================================================
    # ROW 0: TRANSPORT
    # =========================================================================
    ws = draw_box(col_x[0], row_y[0], BOX_W, BOX_H,
                  "HlWsClient", "websocket lifecycle manager",
                  "subscribe · heartbeat · reconnect", CYAN)

    rest = draw_box(col_x[1], row_y[0], BOX_W, BOX_H,
                    "REST Client", "HTTP order interface",
                    "placement · cancel · query", CYAN)

    # =========================================================================
    # ROW 1: PROCESSING
    # =========================================================================
    feed = draw_box(col_x[0], row_y[1], BOX_W, BOX_H,
                    "MarketFeed", "typed event pipeline",
                    "candles · trades · orderbook", SKY)

    runner = draw_box(col_x[1], row_y[1], BOX_W, BOX_H,
                      "SymbolRunner", "per-symbol lifecycle group",
                      "warmup · feed · strategy · watchdog", SKY)

    strategy = draw_box(col_x[2], row_y[1], BOX_W, BOX_H,
                        "Strategy", "signal generation layer",
                        "breakout-retest · filters · gates", VIOLET)

    # =========================================================================
    # ROW 2: EXECUTION
    # =========================================================================
    executor = draw_box(col_x[0], row_y[2], BOX_W, BOX_H,
                        "OrderExecutor", "serialized exchange calls",
                        "nonce safety · race-condition guard", GREEN)

    pos_mgr = draw_box(col_x[1], row_y[2], BOX_W, BOX_H,
                       "PositionMgr", "order state tracking",
                       "open · filled · canceled · failed", GREEN)

    # =========================================================================
    # ROW 3: INFRASTRUCTURE
    # =========================================================================
    state = draw_box(col_x[0], row_y[3], BOX_W, BOX_H,
                     "State", "persistent local context",
                     "survive restarts · restore setup", AMBER)

    watchdog = draw_box(col_x[1], row_y[3], BOX_W, BOX_H,
                        "Watchdog", "runtime health monitor",
                        "stale feed · HTTP errors · recovery", RED)

    notif = draw_box(col_x[2], row_y[3], BOX_W, BOX_H,
                     "Notifications", "Discord + DryRun pipeline",
                     "trade alerts · status · safe testing", SKY)

    # =========================================================================
    # ARROWS  (all orthogonal — clean and readable)
    # =========================================================================

    # --- Transport → Processing ---
    # HlWsClient ↓ MarketFeed (straight down, center-aligned)
    arrow_down(ws.cx, ws.bot, feed.top, CYAN)

    # REST ↓ SymbolRunner (straight down)
    arrow_down(rest.cx, rest.bot, runner.top, CYAN)

    # --- Processing: horizontal flow ---
    # MarketFeed → SymbolRunner
    arrow_right(feed.cy, feed.right, runner.left, SKY)

    # SymbolRunner → Strategy
    arrow_right(runner.cy, runner.right, strategy.left, VIOLET)

    # --- Processing → Execution ---
    # SymbolRunner ↓ OrderExecutor  (elbow: down, left, down)
    mid1 = runner.bot + (ROW_GAP // 2)
    arrow_elbow_down(runner.bot_at(0.3)[0], runner.bot, mid1,
                     executor.cx, executor.top, GREEN)

    # SymbolRunner ↓ PositionMgr (straight down)
    arrow_down(runner.bot_at(0.7)[0], runner.bot, pos_mgr.top, GREEN)

    # --- Strategy signal feedback → Execution (dashed) ---
    # Strategy down to mid, left to PositionMgr
    sig_mid_y = strategy.bot + (ROW_GAP // 2) + 8
    vline(strategy.cx, strategy.bot, sig_mid_y, VIOLET, dashed=True)
    hline(sig_mid_y, strategy.cx, pos_mgr.right_at(0.5)[0], VIOLET, dashed=True)
    vline(pos_mgr.right_at(0.5)[0], sig_mid_y, pos_mgr.top, VIOLET, dashed=True)
    arrowhead(pos_mgr.right_at(0.5)[0], pos_mgr.top, 'down', VIOLET)

    # --- Execution → Transport feedback (OrderExecutor → REST, dashed up) ---
    fb_x = executor.top_at(0.7)[0]
    fb_mid_y = executor.top - (ROW_GAP // 2)
    vline(fb_x, executor.top, fb_mid_y, CYAN, dashed=True)
    hline(fb_mid_y, fb_x, rest.bot_at(0.3)[0], CYAN, dashed=True)
    vline(rest.bot_at(0.3)[0], fb_mid_y, rest.bot, CYAN, dashed=True)
    arrowhead(rest.bot_at(0.3)[0], rest.bot, 'up', CYAN)

    # --- Execution → Infrastructure ---
    # OrderExecutor ↓ State
    arrow_down(executor.cx, executor.bot, state.top, AMBER)

    # PositionMgr ↓ Watchdog (elbow)
    arrow_elbow_down(pos_mgr.bot_at(0.3)[0], pos_mgr.bot,
                     pos_mgr.bot + ROW_GAP // 2,
                     watchdog.cx, watchdog.top, RED)

    # PositionMgr ↓ Notifications
    arrow_elbow_down(pos_mgr.bot_at(0.7)[0], pos_mgr.bot,
                     pos_mgr.bot + ROW_GAP // 2 + 10,
                     notif.cx, notif.top, SKY)

    # =========================================================================
    # RIGHT PANEL — Strategy Filters
    # =========================================================================
    panel_x = col_x[2] + BOX_W + 40
    panel_y = row_y[0]
    panel_w = 210
    panel_h = row_y[2] + BOX_H - row_y[0]

    # Panel bg
    for row in range(panel_h):
        c = lerp((7, 11, 22), (11, 15, 28), row / panel_h)
        draw.line([(panel_x, panel_y + row), (panel_x + panel_w, panel_y + row)], fill=c)

    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                           radius=8, outline=lerp(BG_MID, VIOLET, 0.25), width=1)

    # Title
    draw.text((panel_x + 14, panel_y + 12), "STRATEGY FILTERS",
              font=font_layer, fill=VIOLET)
    draw.line([(panel_x + 14, panel_y + 30), (panel_x + panel_w - 14, panel_y + 30)],
              fill=lerp(BG_MID, VIOLET, 0.12), width=1)

    filters = [
        ("01", "Structure break"),
        ("02", "Retest confirmation"),
        ("03", "ADX trend gate"),
        ("04", "ATR buffer & stop"),
        ("05", "BB width filter"),
        ("06", "Volume ratio"),
        ("07", "Time & cooldown"),
        ("08", "Signal compose"),
    ]

    item_h = (panel_h - 60) // len(filters)

    for i, (num, label) in enumerate(filters):
        fy = panel_y + 44 + i * item_h

        # Number badge
        draw.text((panel_x + 14, fy), num, font=font_fnum, fill=lerp(BG_MID, VIOLET, 0.55))

        # Connector dot
        dot_x = panel_x + 38
        draw.ellipse([dot_x - 3, fy + 4, dot_x + 3, fy + 10], fill=lerp(BG_MID, VIOLET, 0.40))

        # Label
        draw.text((panel_x + 48, fy), label, font=font_filter,
                  fill=lerp(BG_MID, WHITE, 0.55))

    # Vertical pipeline line
    pipe_x = panel_x + 38
    draw.line([(pipe_x, panel_y + 52), (pipe_x, panel_y + 44 + (len(filters) - 1) * item_h + 8)],
              fill=lerp(BG_MID, VIOLET, 0.14), width=1)

    # Arrow from Strategy box to panel
    arrow_right(strategy.cy, strategy.right, panel_x, VIOLET, dashed=True)

    # =========================================================================
    # BOTTOM LEGEND
    # =========================================================================
    bar_y = H - 40
    draw.line([(40, bar_y), (W - 40, bar_y)], fill=lerp(BG_MID, SLATE, 0.07), width=1)
    draw.text((60, bar_y + 10), "hypebot-rs · architecture v0.1",
              font=font_label, fill=lerp(BG_MID, SLATE, 0.28))

    legend = [
        ("data flow", CYAN),
        ("signal path", VIOLET),
        ("execution", GREEN),
        ("feedback (dashed)", SLATE),
    ]
    lx = W - 60
    for label, color in reversed(legend):
        bbox = draw.textbbox((0, 0), label, font=font_label)
        tw = bbox[2] - bbox[0]
        lx -= tw + 26
        draw.ellipse([lx, bar_y + 14, lx + 7, bar_y + 21],
                     fill=lerp(BG_MID, color, 0.6))
        draw.text((lx + 12, bar_y + 10), label, font=font_label,
                  fill=lerp(BG_MID, color, 0.45))

    # Corner marks
    mc = lerp(BG_MID, SLATE, 0.08)
    for cx, cy in [(24, 24), (W - 24, 24), (24, H - 24), (W - 24, H - 24)]:
        draw.line([(cx - 5, cy), (cx + 5, cy)], fill=mc, width=1)
        draw.line([(cx, cy - 5), (cx, cy + 5)], fill=mc, width=1)

    draw.rectangle([14, 14, W - 15, H - 15], outline=lerp(BG_MID, SLATE, 0.035), width=1)

    return img


if __name__ == "__main__":
    img = create_architecture()
    img.save("/home/ubuntu/hypebot-rs-showcase/assets/architecture.png", quality=95)
    print("Architecture diagram saved.")
