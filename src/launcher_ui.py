"""
AI Gesture Mouse — Launcher UI  (v3 — single-window page flip)

Two "pages" live inside the same Tk window:
  • Home     — hero, Start button, Controls button
  • Controls — gesture reference cards, Back button

No Toplevel is used; pages are stacked Frames, only one visible at a time.
"""

import sys
import tkinter as tk
from pathlib import Path

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ── Colour palette ─────────────────────────────────────────────────────────────
BG        = "#0A0C12"
SURFACE   = "#111420"
CARD_BG   = "#161A28"
CARD_HOV  = "#1C2235"
BORDER    = "#252D45"
ACCENT    = "#00C8FF"
ACCENT_H  = "#33D8FF"
ACCENT2   = "#7B61FF"
SUCCESS   = "#00E5A0"
WARNING   = "#FFB340"
PINK      = "#FF6B9D"
ORANGE    = "#FF6B40"
TEXT_PRI  = "#EDF0FF"
TEXT_SEC  = "#6B7799"
TEXT_MID  = "#A0AABF"

WIN_W, WIN_H = 460, 640

# ── Gesture catalogue ──────────────────────────────────────────────────────────
GESTURES = [
    ("☝️",  "Move Cursor",   ACCENT,   "Point only your index finger — cursor follows fingertip with zero accidental clicks"),
    ("✌️",  "Left Click",    SUCCESS,  "Raise 2 fingers (Index + Middle) — fires exactly ONE click at the current position"),
    ("👍",  "Right Click",   WARNING,  "Thumbs-Up — thumb raised straight up, all other fingers curled into a fist"),
    ("🖐️",  "Double Click",  ACCENT2,  "Show the BACK of your open hand (all 5 fingers extended facing camera)"),
    ("3️⃣", "Scroll",        PINK,     "Raise 3 fingers (Index + Middle + Ring) — move hand up or down to scroll smoothly"),
]



# ── Hover effect helper ────────────────────────────────────────────────────────
def _hover(w, n, h):
    w.bind("<Enter>", lambda _: w.configure(bg=h))
    w.bind("<Leave>", lambda _: w.configure(bg=n))


# ── Main launcher window ───────────────────────────────────────────────────────
class LauncherWindow:
    """
    Single Tk window with two 'pages':
      _home_frame    – shown on startup
      _controls_frame – shown when Controls is clicked
    Only one is visible at a time; switching is instant (no Toplevel).
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Gesture Mouse")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.minsize(WIN_W, WIN_H)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{WIN_W}x{WIN_H}+{(sw-WIN_W)//2}+{(sh-WIN_H)//2}")

        self._started = False

        # Container that holds both pages stacked on top of each other
        self._container = tk.Frame(self.root, bg=BG)
        self._container.pack(fill="both", expand=True)
        self._container.grid_rowconfigure(0, weight=1)
        self._container.grid_columnconfigure(0, weight=1)

        self._home_frame     = tk.Frame(self._container, bg=BG)
        self._controls_frame = tk.Frame(self._container, bg=BG)

        for frame in (self._home_frame, self._controls_frame):
            frame.grid(row=0, column=0, sticky="nsew")

        self._build_home()
        self._build_controls()
        self._show_home()

    # ── Page switching ─────────────────────────────────────────────────────────
    def _show_home(self):
        self.root.title("AI Gesture Mouse")
        self._home_frame.tkraise()

    def _show_controls(self):
        self.root.title("AI Gesture Mouse — Controls")
        self._controls_frame.tkraise()

    # ── HOME PAGE ──────────────────────────────────────────────────────────────
    def _build_home(self):
        f = self._home_frame

        # ── top glow bar ──
        tk.Frame(f, bg=ACCENT, height=3).pack(fill="x")

        # ── Hero icon ──
        hero = tk.Frame(f, bg=BG)
        hero.pack(fill="x", pady=(36, 0))

        # Draw a hand icon using canvas shapes (no emoji dependency)
        icon_canvas = tk.Canvas(hero, width=90, height=90,
                                bg=BG, bd=0, highlightthickness=0)
        icon_canvas.pack()
        self._draw_hand_icon(icon_canvas, 45, 45, ACCENT)

        # ── Title ──
        tk.Label(f, text="AI Gesture Mouse",
                 font=("Segoe UI", 22, "bold"),
                 bg=BG, fg=TEXT_PRI).pack(pady=(16, 4))

        tk.Label(f,
                 text="Touchless control powered by\nhand gesture recognition",
                 font=("Segoe UI", 10),
                 bg=BG, fg=TEXT_SEC, justify="center").pack()

        # ── Accent divider ──
        div = tk.Frame(f, bg=SURFACE, height=1)
        div.pack(fill="x", padx=50, pady=24)

        # Accent gradient overlay on divider (simulated with two thin frames)
        tk.Frame(f, bg=ACCENT, height=2).pack(fill="x", padx=80, pady=0)
        # Un-pack the plain divider and replace with the glow line
        div.pack_forget()

        # ── Feature badges (3 small cards) ──
        badges_row = tk.Frame(f, bg=BG)
        badges_row.pack(pady=(0, 0))

        badge_data = [
            ("Move",   ACCENT,   "1 finger\n(Index)"),
            ("Click",  SUCCESS,  "2 fingers\n(one-shot)"),
            ("Scroll", PINK,     "3 fingers\n(Up / Down)"),
        ]
        for title, col, sub in badge_data:
            card = tk.Frame(badges_row, bg=CARD_BG,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", padx=6, ipadx=10, ipady=6)
            tk.Label(card, text=title, font=("Segoe UI", 9, "bold"),
                     bg=CARD_BG, fg=col).pack()
            tk.Label(card, text=sub, font=("Segoe UI", 7),
                     bg=CARD_BG, fg=TEXT_SEC, justify="center").pack()

        # ── Buttons ──
        btn_wrap = tk.Frame(f, bg=BG)
        btn_wrap.pack(pady=28)

        # START button
        self.start_btn = tk.Button(
            btn_wrap,
            text="  ▶   Start",
            font=("Segoe UI", 13, "bold"),
            bg=ACCENT, fg="#000000",
            activebackground=ACCENT_H, activeforeground="#000000",
            relief="flat", cursor="hand2", bd=0,
            width=24, pady=13,
            command=self._on_start
        )
        self.start_btn.pack(pady=(0, 10))
        _hover(self.start_btn, ACCENT, ACCENT_H)

        # CONTROLS button — same blue family
        ctrl_btn = tk.Button(
            btn_wrap,
            text="  ☰  Controls",
            font=("Segoe UI", 11, "bold"),
            bg="#0E4F6A", fg=ACCENT,
            activebackground="#155F80", activeforeground=ACCENT_H,
            relief="flat", cursor="hand2", bd=0,
            width=24, pady=11,
            highlightbackground=ACCENT, highlightthickness=1,
            command=self._show_controls
        )
        ctrl_btn.pack()
        _hover(ctrl_btn, "#0E4F6A", "#155F80")

        # ── Footer ──
        tk.Label(f,
                 text="Press  Q  or  ESC  inside the camera window to stop",
                 font=("Segoe UI", 8),
                 bg=BG, fg=TEXT_SEC).pack(side="bottom", pady=14)

    # ── CONTROLS PAGE ──────────────────────────────────────────────────────────
    def _build_controls(self):
        f = self._controls_frame

        # ── top glow bar ──
        tk.Frame(f, bg=ACCENT, height=3).pack(fill="x")

        # ── Header row: back arrow + title ──
        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(18, 0))

        back_btn = tk.Button(
            hdr,
            text="←  Back",
            font=("Segoe UI", 10, "bold"),
            bg="#0E4F6A", fg=ACCENT,
            activebackground="#155F80", activeforeground=ACCENT_H,
            relief="flat", cursor="hand2", bd=0,
            padx=14, pady=6,
            highlightbackground=ACCENT, highlightthickness=1,
            command=self._show_home
        )
        back_btn.pack(side="left")
        _hover(back_btn, "#0E4F6A", "#155F80")

        tk.Label(hdr, text="Hand Gesture Controls",
                 font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=TEXT_PRI).pack(side="left", padx=16)

        tk.Label(f,
                 text="Touchless gestures recognized in real-time by your camera",
                 font=("Segoe UI", 8),
                 bg=BG, fg=TEXT_SEC).pack(anchor="w", padx=28, pady=(4, 0))

        tk.Frame(f, bg=ACCENT, height=2).pack(fill="x", padx=24, pady=(12, 6))

        # ── Scrollable card list ──
        outer = tk.Frame(f, bg=BG)
        outer.pack(fill="both", expand=True, padx=22, pady=(0, 4))

        canvas = tk.Canvas(outer, bg=BG, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        cards_frame = tk.Frame(canvas, bg=BG)
        cw = canvas.create_window((0, 0), window=cards_frame, anchor="nw")

        cards_frame.bind("<Configure>",
                         lambda e: canvas.configure(
                             scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * e.delta / 120), "units"))

        for icon_text, name, colour, desc in GESTURES:
            card = tk.Frame(cards_frame, bg=CARD_BG,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=4, padx=2, ipady=5)

            # Badge
            badge = tk.Frame(card, bg=colour, width=58, height=52)
            badge.pack(side="left", padx=(10, 0))
            badge.pack_propagate(False)
            tk.Label(badge, text=icon_text,
                     font=("Segoe UI Emoji", 19),
                     bg=colour, fg="#000000",
                     justify="center").place(relx=0.5, rely=0.5, anchor="center")

            # Text
            txt = tk.Frame(card, bg=CARD_BG)
            txt.pack(side="left", fill="x", expand=True, padx=12)

            tk.Label(txt, text=name,
                     font=("Segoe UI", 11, "bold"),
                     bg=CARD_BG, fg=colour, anchor="w").pack(anchor="w")

            tk.Label(txt, text=desc,
                     font=("Segoe UI", 8),
                     bg=CARD_BG, fg=TEXT_MID,
                     anchor="w", wraplength=310, justify="left").pack(
                anchor="w", pady=(2, 0))

        # ── Footer ──
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=22)
        tk.Label(f,
                 text="Scroll to see all gestures",
                 font=("Segoe UI", 7),
                 bg=BG, fg=TEXT_SEC).pack(pady=6)

    # ── Canvas hand icon ───────────────────────────────────────────────────────
    @staticmethod
    def _draw_hand_icon(canvas, cx, cy, colour):
        """Draw a simple open-hand silhouette using ovals and rectangles."""
        # Palm
        canvas.create_oval(cx-22, cy-5, cx+22, cy+32, fill=colour, outline="")
        # Fingers (5 rounded rects approximated as ovals)
        finger_data = [
            (cx-18, cy-38, cx-10, cy+2),   # pinky
            (cx-9,  cy-44, cx-1,  cy+2),   # ring
            (cx,    cy-46, cx+8,  cy+2),   # middle
            (cx+9,  cy-42, cx+17, cy+2),   # index
            (cx-28, cy-20, cx-16, cy+8),   # thumb (angled)
        ]
        for x1, y1, x2, y2 in finger_data:
            canvas.create_oval(x1, y1, x2, y2, fill=colour, outline="")
        # Palm overlap to fill gaps
        canvas.create_rectangle(cx-20, cy-10, cx+20, cy+30,
                                fill=colour, outline="")

    # ── Handlers ──────────────────────────────────────────────────────────────
    def _on_start(self):
        self._started = True
        self.root.quit()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def show(self):
        self.root.mainloop()
        return self._started

    def destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass
