#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inžiniersky kalkulátor – ozubené prevody a elektromotory
=========================================================

Zadanie (4 body) a kde ich nájdeš v kóde:

  1. Pole vstupných hodnôt (min. 50 náhodných)  ->  make_data()  / App.generate()
  2. Práca s poľom (zoradenie, min, max,
     priemer, medián, smerodajná odchýlka)      ->  App._view()  / App._update_stats()
  3. Výpočet podľa vzorca (11 vzorcov pre
     ozubené prevody a elektromotory)           ->  FORMULAS  / evaluate()
  4. Graf (pôvodné aj vypočítané hodnoty v
     jednom grafe) + GUI (Tkinter)              ->  App._draw_chart()  / trieda App

Spustenie:
    pip install matplotlib
    python kalkulator_prevody_motory.py
"""
from __future__ import annotations

import csv
import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Callable

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ======================================================================
#  FARBY – meď a všetky jej variácie (patina = zelená meď / verdigris)
# ======================================================================
BG = "#17100D"          # tmavá espresso hnedá (pozadie okna)
PANEL = "#241812"       # karty
PANEL_2 = "#2F2019"     # polia, zvýraznené plochy
BORDER = "#4A3226"      # orámovanie
TEXT = "#F4E7DA"        # krémový text
MUTED = "#B79B88"       # tlmený text
COPPER = "#B87333"      # klasická meď
COPPER_LT = "#E09A5E"   # leštená meď
COPPER_DK = "#8A4F22"   # oxidovaná meď
PATINA = "#5CC8B0"      # zelená meď (svetlá)
PATINA_MID = "#3FA58E"  # zelená meď (stredná)
PATINA_DK = "#1F6F61"   # zelená meď (tmavá)
ON_COPPER = "#1A0F08"   # text na medenom tlačidle
ERROR = "#F0846B"
CHART_BG = "#1E130E"
LIGHT_LINE = "#F6D5B0"

MIN_COUNT = 50
MAX_COUNT = 500


# ======================================================================
#  VZORCE
# ======================================================================
@dataclass(frozen=True)
class Param:
    """Konštantný parameter vzorca (napr. modul m, výkon P)."""
    key: str
    symbol: str
    label: str
    unit: str
    default: float
    minimum: float = 0.0            # hodnota musí byť STROGO väčšia ako minimum
    maximum: float | None = None    # horná hranica (vrátane), ak existuje


@dataclass(frozen=True)
class Formula:
    """Popis jedného vzorca: vstupná veličina -> výstupná veličina."""
    key: str
    group: str                       # "gears" | "motors"
    title: str
    var_symbol: str                  # vstupná veličina (pole náhodných hodnôt)
    var_name: str
    var_unit: str
    out_symbol: str                  # vypočítaná veličina
    out_name: str
    out_unit: str
    expression: str                  # vzorec na zobrazenie
    params: tuple[Param, ...]
    func: Callable[[np.ndarray, dict[str, float]], np.ndarray]
    gen: tuple[float, float, int]    # (od, do, počet desatinných miest)
    x_min: float = 0.0               # najmenšia povolená vstupná hodnota
    integer: bool = False            # vstup musí byť celé číslo (počet zubov)
    digits: int = 2                  # počet desatinných miest vo výsledku


M_ = Param("m", "m", "Modul", "mm", 2.5)
Z2 = Param("z2", "z₂", "Počet zubov kolesa", "zub.", 40)
N_ = Param("n", "n", "Otáčky hriadeľa", "ot/min", 1450)
P_ = Param("P", "P", "Výkon motora", "kW", 7.5)
NS = Param("ns", "ns", "Synchrónne otáčky", "ot/min", 3000)
U_ = Param("U", "U", "Napätie", "V", 400)
COS = Param("cosphi", "cos φ", "Účinník", "–", 0.85, 0.0, 1.0)

GROUPS = {"gears": "Ozubené prevody", "motors": "Elektromotory"}

FORMULAS: tuple[Formula, ...] = (
    # ---------------------------- OZUBENÉ PREVODY ----------------------------
    Formula("gear_d", "gears", "Deliaci priemer",
            "z", "Počet zubov", "zub.", "d", "Deliaci priemer", "mm",
            "d = m · z", (M_,), lambda z, p: p["m"] * z,
            (12, 80, 0), x_min=1, integer=True),
    Formula("gear_da", "gears", "Priemer hlavovej kružnice",
            "z", "Počet zubov", "zub.", "da", "Hlavová kružnica", "mm",
            "da = m · (z + 2)", (M_,), lambda z, p: p["m"] * (z + 2),
            (12, 80, 0), x_min=1, integer=True),
    Formula("gear_df", "gears", "Priemer pätnej kružnice",
            "z", "Počet zubov", "zub.", "df", "Pätná kružnica", "mm",
            "df = m · (z − 2,5)", (M_,), lambda z, p: p["m"] * (z - 2.5),
            (12, 80, 0), x_min=3, integer=True),
    Formula("gear_a", "gears", "Osová vzdialenosť kolies",
            "z₁", "Počet zubov pastorka", "zub.", "a", "Osová vzdialenosť", "mm",
            "a = m · (z₁ + z₂) / 2", (M_, Z2),
            lambda z, p: p["m"] * (z + p["z2"]) / 2,
            (12, 80, 0), x_min=1, integer=True),
    Formula("gear_i", "gears", "Prevodový pomer",
            "z₁", "Počet zubov pastorka", "zub.", "i", "Prevodový pomer", "–",
            "i = z₂ / z₁", (Z2,), lambda z, p: p["z2"] / z,
            (12, 80, 0), x_min=1, integer=True, digits=3),
    Formula("gear_v", "gears", "Obvodová rýchlosť kolesa",
            "z", "Počet zubov", "zub.", "v", "Obvodová rýchlosť", "m/s",
            "v = π · m · z · n / 60 000", (M_, N_),
            lambda z, p: math.pi * p["m"] * z * p["n"] / 60000,
            (12, 80, 0), x_min=1, integer=True),
    # ----------------------------- ELEKTROMOTORY -----------------------------
    Formula("motor_M", "motors", "Krútiaci moment motora",
            "n", "Otáčky", "ot/min", "M", "Krútiaci moment", "N·m",
            "M = 9550 · P / n", (P_,), lambda n, p: 9550 * p["P"] / n,
            (500, 2950, 0), x_min=1),
    Formula("motor_w", "motors", "Uhlová rýchlosť hriadeľa",
            "n", "Otáčky", "ot/min", "ω", "Uhlová rýchlosť", "rad/s",
            "ω = 2 · π · n / 60", (), lambda n, p: 2 * math.pi * n / 60,
            (500, 2950, 0), x_min=0),
    Formula("motor_s", "motors", "Sklz asynchrónneho motora",
            "n", "Otáčky", "ot/min", "s", "Sklz", "%",
            "s = (ns − n) / ns · 100", (NS,),
            lambda n, p: (p["ns"] - n) / p["ns"] * 100,
            (500, 2950, 0), x_min=0),
    Formula("motor_P1", "motors", "Elektrický príkon (3-fázový)",
            "I", "Prúd", "A", "P₁", "Elektrický príkon", "kW",
            "P₁ = √3 · U · I · cos φ / 1000", (U_, COS),
            lambda i, p: math.sqrt(3) * p["U"] * i * p["cosphi"] / 1000,
            (2, 40, 1), x_min=0),
    Formula("motor_P2", "motors", "Mechanický výkon na hriadeli",
            "M", "Krútiaci moment", "N·m", "P₂", "Výkon na hriadeli", "kW",
            "P₂ = M · 2 · π · n / 60 / 1000", (N_,),
            lambda m, p: m * 2 * math.pi * p["n"] / 60 / 1000,
            (5, 120, 1), x_min=0),
)


# ======================================================================
#  POMOCNÉ FUNKCIE (bez GUI)
# ======================================================================
def fmt(value: float, digits: int = 2) -> str:
    """Slovenský zápis čísla: 1 234,56"""
    s = f"{value:,.{digits}f}"
    return s.replace(",", "\u00a0").replace(".", ",")


def fmt_plain(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def unit_txt(unit: str, bracket: bool = False) -> str:
    """Jednotka na zobrazenie; bezrozmerné veličiny ("–") jednotku nemajú."""
    if unit in ("", "–"):
        return ""
    return f" [{unit}]" if bracket else f" {unit}"


def parse_number(text: str, label: str) -> float:
    """Prečíta číslo (povolí čiarku aj bodku). Pri chybe vyvolá ValueError."""
    cleaned = text.strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if not cleaned:
        raise ValueError(f"Pole „{label}“ je prázdne.")
    try:
        value = float(cleaned)
    except ValueError:
        raise ValueError(f"„{text.strip()}“ nie je platné číslo ({label}).") from None
    if not math.isfinite(value):
        raise ValueError(f"Hodnota v poli „{label}“ musí byť konečné číslo.")
    return value


def make_data(rng: np.random.Generator, formula: Formula, count: int) -> np.ndarray:
    """KROK 1: vygeneruje pole náhodných vstupných hodnôt."""
    low, high, decimals = formula.gen
    if decimals == 0:
        return rng.integers(int(low), int(high) + 1, size=count).astype(float)
    return np.round(rng.uniform(low, high, size=count), decimals)


def evaluate(formula: Formula, x: np.ndarray | float, params: dict[str, float]) -> np.ndarray:
    """KROK 3: výpočet vzorca nad celým poľom (aj nad jedným číslom)."""
    with np.errstate(all="ignore"):
        y = np.asarray(formula.func(np.asarray(x, dtype=float), params), dtype=float)
    if not np.all(np.isfinite(y)):
        raise ValueError("Výpočet nie je možný pre zadané parametre (delenie nulou).")
    return y


def pick_font(root: tk.Misc, candidates: list[str]) -> str:
    available = set(tkfont.families(root))
    for name in candidates:
        if name in available:
            return name
    return candidates[-1]


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def lerp_color(c1: str, c2: str, t: float) -> str:
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ======================================================================
#  APLIKÁCIA
# ======================================================================
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Inžiniersky kalkulátor – ozubené prevody a elektromotory")
        self.configure(bg=BG)
        screen_h = self.winfo_screenheight()
        self.geometry(f"1360x{min(880, screen_h - 90)}")
        self.minsize(1180, 660)

        self.f_ui = pick_font(self, ["Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue",
                                     "Ubuntu", "DejaVu Sans"])
        self.f_mono = pick_font(self, ["Consolas", "Cascadia Mono", "JetBrains Mono", "Menlo",
                                       "DejaVu Sans Mono", "Courier New"])

        self.rng = np.random.default_rng()
        self.formula: Formula = FORMULAS[0]
        self.formula_list: list[Formula] = []
        self.values = np.array([])      # pôvodné hodnoty (pole)
        self.results = np.array([])     # vypočítané hodnoty
        self.single: tuple[float, float] | None = None
        self.param_vars: dict[str, tk.StringVar] = {}
        self._recalc_job: str | None = None

        self.mode_var = tk.StringVar(value="gears")
        self.formula_var = tk.StringVar()
        self.count_var = tk.StringVar(value="60")
        self.sort_var = tk.BooleanVar(value=False)
        self.single_var = tk.StringVar()
        self.single_text = tk.StringVar()
        self.status_var = tk.StringVar()

        self._build_styles()
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.on_mode_change()

    # ------------------------------------------------------------ štýly
    def _build_styles(self) -> None:
        ui, mono = self.f_ui, self.f_mono
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL_2,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    troughcolor=PANEL, focuscolor=BG, font=(ui, 10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Card.TLabel", background=PANEL, foreground=TEXT)
        s.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=(ui, 9))
        s.configure("Section.TLabel", background=PANEL, foreground=COPPER_LT, font=(ui, 9, "bold"))
        s.configure("Formula.TLabel", background=PANEL_2, foreground=COPPER_LT, font=(mono, 16, "bold"))
        s.configure("Result.TLabel", background=PANEL, foreground=PATINA, font=(mono, 15, "bold"))
        s.configure("Error.TLabel", background=PANEL, foreground=ERROR, font=(ui, 10, "bold"))
        s.configure("Head.TLabel", background=PANEL, foreground=MUTED, font=(ui, 9, "bold"))
        s.configure("Orig.TLabel", background=PANEL, foreground=COPPER_LT, font=(mono, 10))
        s.configure("Calc.TLabel", background=PANEL, foreground=PATINA, font=(mono, 10))
        s.configure("Status.TLabel", background=PANEL, foreground=MUTED, font=(ui, 9))

        for name, bg, fg, hover in (
            ("Copper.TButton", COPPER, ON_COPPER, COPPER_LT),
            ("Patina.TButton", PATINA_DK, TEXT, PATINA_MID),
            ("Ghost.TButton", PANEL_2, TEXT, BORDER),
        ):
            s.configure(name, background=bg, foreground=fg, bordercolor=bg, lightcolor=bg,
                        darkcolor=bg, focuscolor=bg, padding=(14, 8), relief="flat",
                        font=(ui, 10, "bold"))
            s.map(name, background=[("pressed", hover), ("active", hover)],
                  bordercolor=[("pressed", hover), ("active", hover)],
                  lightcolor=[("pressed", hover), ("active", hover)],
                  darkcolor=[("pressed", hover), ("active", hover)])

        focus = [("focus", COPPER_LT)]
        s.configure("TEntry", fieldbackground=PANEL_2, foreground=TEXT, insertcolor=COPPER_LT,
                    padding=6)
        s.map("TEntry", bordercolor=focus, lightcolor=focus, darkcolor=focus)
        s.configure("TSpinbox", fieldbackground=PANEL_2, foreground=TEXT, insertcolor=COPPER_LT,
                    arrowcolor=COPPER_LT, background=PANEL_2, padding=6)
        s.map("TSpinbox", bordercolor=focus, lightcolor=focus, darkcolor=focus)
        s.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT,
                    arrowcolor=COPPER_LT, selectbackground=PANEL_2, selectforeground=TEXT,
                    padding=6)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL_2)],
              foreground=[("readonly", TEXT)], bordercolor=focus, lightcolor=focus,
              darkcolor=focus, background=[("active", BORDER)])
        self.option_add("*TCombobox*Listbox.background", PANEL_2)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", COPPER)
        self.option_add("*TCombobox*Listbox.selectForeground", ON_COPPER)
        self.option_add("*TCombobox*Listbox.font", (ui, 10))

        s.configure("TCheckbutton", background=BG, foreground=TEXT, indicatorbackground=PANEL_2,
                    indicatorcolor=PANEL_2, indicatorforeground=ON_COPPER, bordercolor=COPPER_LT,
                    font=(ui, 10))
        s.map("TCheckbutton", indicatorbackground=[("selected", COPPER_LT)],
              indicatorcolor=[("selected", COPPER_LT)],
              background=[("active", BG)], foreground=[("active", COPPER_LT)])

        s.layout("Seg.TRadiobutton", [("Radiobutton.padding", {"sticky": "nswe", "children": [
            ("Radiobutton.label", {"sticky": "nswe"})]})])
        s.configure("Seg.TRadiobutton", background=PANEL_2, foreground=MUTED, anchor="center",
                    padding=(10, 8), font=(ui, 10, "bold"))
        s.map("Seg.TRadiobutton",
              background=[("selected", COPPER), ("active", BORDER)],
              foreground=[("selected", ON_COPPER), ("active", TEXT)])

        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(22, 9),
                    borderwidth=0, bordercolor=BG, lightcolor=BG, darkcolor=BG,
                    font=(ui, 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", COPPER_DK), ("active", PANEL_2)],
              foreground=[("selected", TEXT), ("active", TEXT)],
              padding=[("selected", (22, 9))], expand=[("selected", (0, 0, 0, 0))],
              bordercolor=[("selected", BG)], lightcolor=[("selected", BG)],
              darkcolor=[("selected", BG)])

        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    rowheight=26, borderwidth=0, font=(mono, 10))
        s.map("Treeview", background=[("selected", COPPER)], foreground=[("selected", ON_COPPER)])
        s.configure("Treeview.Heading", background=COPPER_DK, foreground=TEXT, relief="flat",
                    padding=(8, 7), font=(ui, 10, "bold"))
        s.map("Treeview.Heading", background=[("active", COPPER)])
        s.configure("Vertical.TScrollbar", background=COPPER_DK, troughcolor=PANEL,
                    arrowcolor=TEXT, bordercolor=PANEL, lightcolor=COPPER_DK, darkcolor=COPPER_DK)
        s.map("Vertical.TScrollbar", background=[("active", COPPER)])

    # ----------------------------------------------------------- rozloženie
    def _card(self, parent: tk.Misc, **pack) -> tk.Frame:
        frame = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="x", **pack)
        return frame

    def _section(self, card: tk.Frame, text: str) -> None:
        ttk.Label(card, text=text, style="Section.TLabel").pack(anchor="w", padx=14, pady=(12, 6))

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # --- hlavička so symbolom ozubeného kolesa ---
        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(12, 8))
        icon = tk.Canvas(header, width=52, height=52, bg=BG, highlightthickness=0)
        icon.pack(side="left")
        self._draw_gear(icon, 26, 26)
        titles = tk.Frame(header, bg=BG)
        titles.pack(side="left", padx=14)
        tk.Label(titles, text="Inžiniersky kalkulátor", bg=BG, fg=TEXT,
                 font=(self.f_ui, 20, "bold")).pack(anchor="w")
        tk.Label(titles, text="Ozubené prevody  ·  Elektromotory  ·  analýza poľa hodnôt",
                 bg=BG, fg=COPPER_LT, font=(self.f_ui, 10)).pack(anchor="w")

        # --- medeno-patinový prechod ---
        self.strip = tk.Canvas(self, height=4, bg=BG, highlightthickness=0)
        self.strip.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.strip.bind("<Configure>", self._draw_strip)

        side = tk.Frame(self, bg=BG, width=360)
        side.grid(row=2, column=0, sticky="ns", padx=(20, 10), pady=(12, 8))
        main = tk.Frame(self, bg=BG)
        main.grid(row=2, column=1, sticky="nsew", padx=(10, 20), pady=(12, 8))

        self._build_sidebar(side)
        self._build_main(main)

        status = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        status.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").pack(
            side="left", padx=16, pady=5)
        self.status_label = status.winfo_children()[0]

    def _draw_gear(self, canvas: tk.Canvas, cx: float, cy: float) -> None:
        teeth, r_out, r_in = 10, 23, 18
        step = 2 * math.pi / teeth
        points: list[float] = []
        for i in range(teeth):
            for frac, r in ((0.0, r_in), (0.09, r_out), (0.41, r_out), (0.50, r_in), (0.75, r_in)):
                a = (i + frac) * step - math.pi / 2
                points += [cx + r * math.cos(a), cy + r * math.sin(a)]
        canvas.create_polygon(points, fill=COPPER_LT, outline=COPPER, width=1)
        canvas.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, fill=PATINA_DK, outline=PATINA, width=2)
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=BG, outline=BG)

    def _draw_strip(self, _event: tk.Event | None = None) -> None:
        w = max(self.strip.winfo_width(), 2)
        self.strip.delete("all")
        stops = [COPPER_DK, COPPER, COPPER_LT, PATINA_MID, PATINA]
        for x in range(w):
            t = x / (w - 1) * (len(stops) - 1)
            i = min(int(t), len(stops) - 2)
            self.strip.create_line(x, 0, x, 4, fill=lerp_color(stops[i], stops[i + 1], t - i))

    # --------------------------------------------------------------- panel
    def _build_sidebar(self, side: tk.Frame) -> None:
        # --- 1. oblasť a vzorec ---
        c1 = self._card(side, pady=(0, 10))
        self._section(c1, "1 · OBLASŤ A VZOREC")
        seg = tk.Frame(c1, bg=PANEL)
        seg.pack(fill="x", padx=14)
        seg.columnconfigure((0, 1), weight=1, uniform="seg")
        for col, (key, text) in enumerate(GROUPS.items()):
            ttk.Radiobutton(seg, text=text, value=key, variable=self.mode_var,
                            style="Seg.TRadiobutton", command=self.on_mode_change,
                            takefocus=False).grid(row=0, column=col, sticky="ew", padx=(0, 2) if col == 0 else (2, 0))
        self.formula_box = ttk.Combobox(c1, textvariable=self.formula_var, state="readonly",
                                        font=(self.f_ui, 10))
        self.formula_box.pack(fill="x", padx=14, pady=(10, 8))
        self.formula_box.bind("<<ComboboxSelected>>", self.on_formula_change)
        formula_wrap = tk.Frame(c1, bg=PANEL_2)
        formula_wrap.pack(fill="x", padx=14, pady=(0, 14))
        self.expr_label = ttk.Label(formula_wrap, text="", style="Formula.TLabel", anchor="center")
        self.expr_label.pack(fill="x", padx=8, pady=12)

        # --- 2. parametre a dáta ---
        c2 = self._card(side, pady=(0, 10))
        self._section(c2, "2 · PARAMETRE A DÁTA")
        self.param_frame = tk.Frame(c2, bg=PANEL)
        self.param_frame.pack(fill="x", padx=14)
        self.param_frame.columnconfigure(0, weight=1)
        count_row = tk.Frame(c2, bg=PANEL)
        count_row.pack(fill="x", padx=14, pady=(8, 0))
        count_row.columnconfigure(0, weight=1)
        ttk.Label(count_row, text=f"Počet hodnôt v poli (min. {MIN_COUNT})",
                  style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.count_spin = ttk.Spinbox(count_row, from_=MIN_COUNT, to=MAX_COUNT, increment=10,
                                      textvariable=self.count_var, width=7, justify="center")
        self.count_spin.grid(row=0, column=1, sticky="e")
        btns = tk.Frame(c2, bg=PANEL)
        btns.pack(fill="x", padx=14, pady=(12, 14))
        btns.columnconfigure((0, 1), weight=1, uniform="b")
        ttk.Button(btns, text="⟳  Nové hodnoty", style="Copper.TButton", takefocus=False,
                   command=self.generate).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(btns, text="Prepočítať", style="Ghost.TButton", takefocus=False,
                   command=lambda: self.recalculate(report=True)).grid(row=0, column=1, sticky="ew", padx=(3, 0))

        # --- 3. výpočet pre ľubovoľné číslo ---
        c3 = self._card(side)
        self._section(c3, "3 · VÝPOČET PRE ĽUBOVOĽNÉ ČÍSLO")
        self.single_label = ttk.Label(c3, text="", style="Card.TLabel")
        self.single_label.pack(anchor="w", padx=14)
        row = tk.Frame(c3, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(6, 0))
        row.columnconfigure(0, weight=1)
        self.single_entry = ttk.Entry(row, textvariable=self.single_var, font=(self.f_mono, 11))
        self.single_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.single_entry.bind("<Return>", lambda _e: self.calculate_single())
        ttk.Button(row, text="Vypočítať", style="Patina.TButton", takefocus=False,
                   command=self.calculate_single).grid(row=0, column=1)
        self.single_result = ttk.Label(c3, textvariable=self.single_text, style="Result.TLabel",
                                       wraplength=320, justify="left")
        self.single_result.pack(anchor="w", padx=14, pady=(10, 14))

    def _build_main(self, main: tk.Frame) -> None:
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        # --- štatistika poľa (KROK 2) ---
        stats = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        stats.grid(row=0, column=0, sticky="ew")
        self._stat_cells: dict[tuple[int, int], ttk.Label] = {}
        heads = ["", "Počet", "Min", "Max", "Priemer", "Medián", "Šm. odchýlka"]
        for c, text in enumerate(heads):
            ttk.Label(stats, text=text, style="Head.TLabel", anchor="e" if c else "w").grid(
                row=0, column=c, sticky="ew", padx=(14 if c == 0 else 8, 8), pady=(10, 2))
        for r, style in ((1, "Orig.TLabel"), (2, "Calc.TLabel")):
            for c in range(len(heads)):
                lab = ttk.Label(stats, text="", style=style, anchor="e" if c else "w")
                lab.grid(row=r, column=c, sticky="ew", padx=(14 if c == 0 else 8, 8),
                         pady=(0, 10 if r == 2 else 0))
                self._stat_cells[(r, c)] = lab
        stats.columnconfigure(0, weight=3)
        for c in range(1, len(heads)):
            stats.columnconfigure(c, weight=2)

        # --- lišta nástrojov ---
        bar = tk.Frame(main, bg=BG)
        bar.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        ttk.Checkbutton(bar, text="Zoradiť od najmenšej po najväčšiu", variable=self.sort_var,
                        command=self.on_sort_toggle, takefocus=False).pack(side="left")
        ttk.Button(bar, text="Exportovať CSV", style="Ghost.TButton", takefocus=False,
                   command=self.export_csv).pack(side="right")
        ttk.Button(bar, text="Uložiť graf (PNG)", style="Ghost.TButton", takefocus=False,
                   command=self.save_png).pack(side="right", padx=(0, 8))

        # --- záložky: graf / tabuľka ---
        nb = ttk.Notebook(main)
        nb.grid(row=2, column=0, sticky="nsew")
        chart_tab = tk.Frame(nb, bg=PANEL)
        table_tab = tk.Frame(nb, bg=PANEL)
        nb.add(chart_tab, text="  Graf  ")
        nb.add(table_tab, text="  Tabuľka hodnôt  ")

        self.fig = Figure(figsize=(8, 4.6), dpi=100, facecolor=PANEL, layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_tab)
        self.canvas.get_tk_widget().configure(bg=PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

        self.tree = ttk.Treeview(table_tab, columns=("i", "x", "y"), show="headings")
        scroll = ttk.Scrollbar(table_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.tag_configure("odd", background=PANEL)
        self.tree.tag_configure("even", background=PANEL_2)

    # =============================================================== LOGIKA
    def set_status(self, text: str, error: bool = False) -> None:
        self.status_var.set(text)
        self.status_label.configure(foreground=ERROR if error else MUTED)

    def on_mode_change(self) -> None:
        self.formula_list = [f for f in FORMULAS if f.group == self.mode_var.get()]
        self.formula_box.configure(values=[f.title for f in self.formula_list])
        self.formula_box.current(0)
        self.on_formula_change()

    def on_formula_change(self, _event: tk.Event | None = None) -> None:
        self.formula_box.selection_clear()
        self.formula = self.formula_list[self.formula_box.current()]
        f = self.formula
        self.expr_label.configure(text=f.expression)
        self.single = None
        self._build_params()

        self.single_label.configure(
            text=f"Zadaj hodnotu {f.var_symbol} – {f.var_name.lower()}{unit_txt(f.var_unit, True)}:")
        low, high, _ = f.gen
        self.single_var.set(str(round((low + high) / 2)))
        self.single_text.set(f"{f.out_symbol} = ?")
        self.single_result.configure(style="Result.TLabel")
        self.generate()

    def _build_params(self) -> None:
        for child in self.param_frame.winfo_children():
            child.destroy()
        self.param_vars = {}
        if not self.formula.params:
            ttk.Label(self.param_frame, text="Tento vzorec nemá žiadne ďalšie parametre.",
                      style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=2)
            return
        for r, p in enumerate(self.formula.params):
            unit = f" [{p.unit}]" if p.unit else ""
            ttk.Label(self.param_frame, text=f"{p.label} {p.symbol}{unit}",
                      style="Card.TLabel").grid(row=r, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=fmt_plain(p.default, 2).rstrip("0").rstrip(","))
            ent = ttk.Entry(self.param_frame, textvariable=var, width=9, justify="right",
                            font=(self.f_mono, 10))
            ent.grid(row=r, column=1, sticky="e", pady=3)
            ent.bind("<Return>", lambda _e: self.recalculate(report=True))
            var.trace_add("write", lambda *_: self._schedule_recalc())
            self.param_vars[p.key] = var

    def read_params(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for p in self.formula.params:
            label = f"{p.label} {p.symbol}"
            v = parse_number(self.param_vars[p.key].get(), label)
            if v <= p.minimum:
                raise ValueError(f"Parameter „{label}“ musí byť väčší ako {fmt(p.minimum, 0)}.")
            if p.maximum is not None and v > p.maximum:
                raise ValueError(f"Parameter „{label}“ nesmie byť väčší ako {fmt(p.maximum, 0)}.")
            values[p.key] = v
        return values

    def _schedule_recalc(self) -> None:
        if self._recalc_job:
            self.after_cancel(self._recalc_job)
        self._recalc_job = self.after(400, lambda: self.recalculate(report=False))

    # ---- KROK 1: generovanie poľa ----
    def generate(self) -> None:
        try:
            count = int(parse_number(self.count_var.get(), "Počet hodnôt"))
        except ValueError as exc:
            self.set_status(str(exc), error=True)
            return
        if count < MIN_COUNT or count > MAX_COUNT:
            count = min(max(count, MIN_COUNT), MAX_COUNT)
            self.count_var.set(str(count))
            self.set_status(f"Počet hodnôt musí byť v rozsahu {MIN_COUNT}–{MAX_COUNT}; upravené na {count}.",
                            error=True)
        self.values = make_data(self.rng, self.formula, count)
        if self.recalculate(report=False):
            f = self.formula
            low, high, _ = f.gen
            self.set_status(f"Vygenerovaných {count} náhodných hodnôt ({f.var_symbol}) "
                            f"v rozsahu {fmt(low, 0)}–{fmt(high, 0)}.")

    # ---- KROK 3: výpočet nad poľom ----
    def recalculate(self, report: bool = False) -> bool:
        try:
            params = self.read_params()
            self.results = evaluate(self.formula, self.values, params)
            if self.single:
                x = self.single[0]
                self.single = (x, float(evaluate(self.formula, x, params)))
                self._show_single(*self.single)
        except ValueError as exc:
            self.set_status(str(exc), error=True)
            return False
        self.refresh_all()
        if report:
            self.set_status(f"Prepočítané: {len(self.values)} hodnôt podľa vzorca {self.formula.expression}.")
        return True

    # ---- výpočet pre ľubovoľné jedno číslo ----
    def calculate_single(self) -> None:
        f = self.formula
        try:
            x = parse_number(self.single_var.get(), f.var_symbol)
            if f.integer and not float(x).is_integer():
                raise ValueError(f"{f.var_name} musí byť celé číslo.")
            if x < f.x_min:
                raise ValueError(f"Hodnota {f.var_symbol} musí byť aspoň {fmt(f.x_min, 0)}.")
            y = float(evaluate(f, x, self.read_params()))
        except ValueError as exc:
            self.single_result.configure(style="Error.TLabel")
            self.single_text.set(str(exc))
            self.set_status(str(exc), error=True)
            return
        self.single = (x, y)
        self._show_single(x, y)
        self.set_status(f"Vypočítané: {f.var_symbol} = {fmt(x, 0 if float(x).is_integer() else 3)} → "
                        f"{f.out_symbol} = {fmt(y, f.digits)}{unit_txt(f.out_unit)}")
        self._draw_chart(*self._view())

    def _show_single(self, x: float, y: float) -> None:
        f = self.formula
        self.single_result.configure(style="Result.TLabel")
        x_txt = fmt(x, 0 if float(x).is_integer() else 3)
        self.single_text.set(f"{f.out_symbol} = {fmt(y, f.digits)}{unit_txt(f.out_unit)}\n"
                             f"({f.var_symbol} = {x_txt}{unit_txt(f.var_unit)})")

    # ---- KROK 2: práca s poľom ----
    def _view(self) -> tuple[np.ndarray, np.ndarray]:
        """Zoradenie: pôvodné hodnoty vzostupne, vypočítané ostávajú k nim priradené."""
        if self.sort_var.get():
            order = np.argsort(self.values, kind="stable")
            return self.values[order], self.results[order]
        return self.values, self.results

    def on_sort_toggle(self) -> None:
        self.refresh_all()
        self.set_status("Zobrazenie: hodnoty zoradené od najmenšej po najväčšiu."
                        if self.sort_var.get() else "Zobrazenie: pôvodné (náhodné) poradie.")

    def _update_stats(self) -> None:
        f = self.formula
        names = {1: f"{f.var_symbol}  {f.var_name}" + unit_txt(f.var_unit, True),
                 2: f"{f.out_symbol}  {f.out_name}" + unit_txt(f.out_unit, True)}
        for row, arr, digits in ((1, self.values, f.gen[2]), (2, self.results, f.digits)):
            d = max(digits, 1) if row == 1 and f.gen[2] else digits
            cells = [names[row], str(len(arr)), fmt(np.min(arr), d), fmt(np.max(arr), d),
                     fmt(np.mean(arr), d + 1 if row == 1 else d), fmt(np.median(arr), d),
                     fmt(np.std(arr), d + 1)]
            for c, text in enumerate(cells):
                self._stat_cells[(row, c)].configure(text=text)

    def _update_table(self, orig: np.ndarray, calc: np.ndarray) -> None:
        f = self.formula
        self.tree.heading("i", text="#")
        self.tree.heading("x", text=f"{f.var_symbol}  {f.var_name}" + unit_txt(f.var_unit, True))
        self.tree.heading("y", text=f"{f.out_symbol}  {f.out_name}" + unit_txt(f.out_unit, True))
        self.tree.column("i", width=60, anchor="center", stretch=False)
        self.tree.column("x", width=240, anchor="e")
        self.tree.column("y", width=240, anchor="e")
        self.tree.delete(*self.tree.get_children())
        xd = f.gen[2]
        for i, (a, b) in enumerate(zip(orig, calc), start=1):
            self.tree.insert("", "end", values=(i, fmt(a, xd), fmt(b, f.digits)),
                             tags=("even" if i % 2 == 0 else "odd",))

    def refresh_all(self) -> None:
        orig, calc = self._view()
        self._update_stats()
        self._update_table(orig, calc)
        self._draw_chart(orig, calc)

    # ---- KROK 4: graf – pôvodné aj vypočítané hodnoty v jednom grafe ----
    def _draw_chart(self, orig: np.ndarray, calc: np.ndarray) -> None:
        f = self.formula
        n = len(orig)
        x = np.arange(1, n + 1)
        fig = self.fig
        fig.clear()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax1.set_facecolor(CHART_BG)

        lbl_x = f"{f.var_symbol} – {f.var_name}" + unit_txt(f.var_unit, True)
        lbl_y = f"{f.out_symbol} – {f.out_name}" + unit_txt(f.out_unit, True)

        bars = ax1.bar(x, orig, width=0.78, color=COPPER, edgecolor=COPPER_DK, linewidth=0.5,
                       alpha=0.92, label=f"Pôvodné: {lbl_x}", zorder=2)
        ms = 5 if n <= 80 else (3 if n <= 200 else 0)
        line, = ax2.plot(x, calc, color=PATINA, linewidth=2, marker="o", markersize=ms,
                         markerfacecolor=CHART_BG, markeredgecolor=PATINA, markeredgewidth=1.4,
                         label=f"Vypočítané: {lbl_y}", zorder=4)
        mean_line = ax2.axhline(float(np.mean(calc)), color=PATINA_MID, linestyle="--", linewidth=1.2,
                                label=f"Priemer {f.out_symbol} = {fmt(np.mean(calc), f.digits)}", zorder=3)
        handles = [bars, line, mean_line]

        if self.single:
            sx, sy = self.single
            sline = ax2.axhline(sy, color=LIGHT_LINE, linestyle=":", linewidth=1.8, zorder=5,
                                label=f"Zadaná hodnota: {f.var_symbol} = {fmt(sx, 0 if float(sx).is_integer() else 2)}"
                                      f" → {f.out_symbol} = {fmt(sy, f.digits)}")
            handles.append(sline)

        ax1.set_ylabel(lbl_x, color=COPPER_LT, fontsize=10, fontweight="bold")
        ax2.set_ylabel(lbl_y, color=PATINA, fontsize=10, fontweight="bold")
        ax1.set_xlabel("Poradie hodnoty v poli" + (" (zoradené vzostupne)" if self.sort_var.get() else ""),
                       color=MUTED, fontsize=10)
        ax1.set_xlim(0, n + 1)
        ax1.tick_params(axis="y", colors=COPPER_LT)
        ax2.tick_params(axis="y", colors=PATINA)
        ax1.tick_params(axis="x", colors=MUTED)
        ax1.grid(axis="y", color=BORDER, alpha=0.55, linewidth=0.7)
        ax1.set_axisbelow(True)
        for ax in (ax1, ax2):
            for spine in ax.spines.values():
                spine.set_color(BORDER)

        params = ", ".join(f"{p.symbol} = {fmt_plain(v, 3).rstrip('0').rstrip(',')}"
                           + (f" {p.unit}" if p.unit not in ("", "–") else "")
                           for p, v in self._safe_params())
        fig.suptitle(f"{f.title}:  {f.expression}", color=TEXT, fontsize=13, fontweight="bold")
        ax1.set_title(params, color=MUTED, fontsize=9)
        fig.legend(handles=handles, loc="outside lower center", ncol=2, frameon=True,
                   facecolor=PANEL_2, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
        self.canvas.draw_idle()

    def _safe_params(self) -> list[tuple[Param, float]]:
        out = []
        for p in self.formula.params:
            try:
                out.append((p, parse_number(self.param_vars[p.key].get(), p.label)))
            except (ValueError, KeyError):
                pass
        return out

    # ---- export ----
    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="hodnoty.csv",
                                            filetypes=[("CSV", "*.csv")], title="Exportovať hodnoty")
        if not path:
            return
        f = self.formula
        orig, calc = self._view()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["poradie", f"{f.var_symbol}{unit_txt(f.var_unit, True)}",
                            f"{f.out_symbol}{unit_txt(f.out_unit, True)}"])
                for i, (a, b) in enumerate(zip(orig, calc), start=1):
                    w.writerow([i, fmt_plain(a, f.gen[2]), fmt_plain(b, 4)])
        except OSError as exc:
            messagebox.showerror("Chyba pri ukladaní", str(exc))
            return
        self.set_status(f"Hodnoty exportované do súboru {path}")

    def save_png(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile="graf.png",
                                            filetypes=[("PNG", "*.png")], title="Uložiť graf")
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=200, facecolor=self.fig.get_facecolor())
        except OSError as exc:
            messagebox.showerror("Chyba pri ukladaní", str(exc))
            return
        self.set_status(f"Graf uložený do súboru {path}")


def main() -> None:
    try:  # ostrejšie písmo na Windows s vysokým DPI
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    App().mainloop()


if __name__ == "__main__":
    main()