# Jednoduchý kalkulátor: ozubené prevody a elektromotory
# Spustenie:  pip install matplotlib   a potom   python jednoduchy_kalkulator.py
import random
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

MED = "#B87333"      # meď
ZELENA = "#2E9C84"   # zelená meď (patina)
TMAVA_MED = "#6B3E1A"  # tmavá meď (zoradené hodnoty)
POZADIE = "#FBF3EA"

# Vzorce: názov -> (vstup, výstup, funkcia, rozsah náhodných čísel)
VZORCE = {
    "Ozubené koleso: d = m · z  (m = 2,5 mm)":
        ("z - počet zubov", "d - deliaci priemer [mm]", lambda z: 2.5 * z, (12, 80)),
    "Elektromotor: M = 9550 · P / n  (P = 7,5 kW)":
        ("n - otáčky [ot/min]", "M - krútiaci moment [N·m]", lambda n: 9550 * 7.5 / n, (500, 2950)),
}

hodnoty = []     # KROK 1: pole vstupných hodnôt
vysledky = []    # KROK 3: vypočítané hodnoty


def aktualny_vzorec():
    return VZORCE[vyber.get()]


def generuj():
    """Vytvorí pole 60 náhodných hodnôt, urobí operácie a nakreslí graf."""
    global hodnoty, vysledky
    vstup, vystup, funkcia, (od, do) = aktualny_vzorec()
    hodnoty = [random.randint(od, do) for _ in range(60)]
    vysledky = [funkcia(x) for x in hodnoty]

    # KROK 2: operácie s poľom (zoradenie, min, max, priemer)
    zoradene = sorted(hodnoty)
    priemer = sum(hodnoty) / len(hodnoty)
    text_pole.config(text=(
        f"Počet hodnôt: {len(hodnoty)}\n"
        f"Zoradené (prvých 10): {zoradene[:10]}\n"
        f"Min: {min(hodnoty)}    Max: {max(hodnoty)}    Priemer: {priemer:.1f}"
    ))
    popis_vstupu.config(text=f"Zadaj hodnotu ({vstup}):")
    text_vysledok.config(text="")
    kresli()


def vypocitaj():
    """Výpočet vzorca pre ľubovoľné číslo zadané používateľom."""
    funkcia = aktualny_vzorec()[2]
    try:
        x = float(pole_vstup.get().replace(",", "."))
        y = funkcia(x)
        text_vysledok.config(text=f"Výsledok: {y:.2f}".replace(".", ","), fg=ZELENA)
    except ValueError:
        text_vysledok.config(text="Zadaj platné číslo!", fg="red")
    except ZeroDivisionError:
        text_vysledok.config(text="Nulou sa deliť nedá!", fg="red")


def kresli():
    """KROK 4: pôvodné aj vypočítané hodnoty v jednom grafe."""
    vstup, vystup = aktualny_vzorec()[:2]
    obr.clear()
    os1 = obr.add_subplot(111)
    os2 = os1.twinx()                      # druhá os pre vypočítané hodnoty
    # pôvodné náhodné čísla = stĺpce (vždy viditeľné), vypočítané = zelená čiara
    stlpce = os1.bar(range(len(hodnoty)), hodnoty, color=MED, alpha=0.7, label=vstup)
    ciara, = os2.plot(vysledky, color=ZELENA, marker="s", markersize=4, linewidth=1.5, label=vystup)
    prvky = [stlpce, ciara]
    if ukaz_zoradene.get():                # NOVÁ FUNKCIA: zoradené náhodné čísla v grafe
        zoradena, = os1.plot(sorted(hodnoty), color=TMAVA_MED, linestyle="--", linewidth=2,
                             label=vstup + " (zoradené)")
        prvky.append(zoradena)
    os1.set_xlabel("Poradie hodnoty")
    os1.set_ylabel(vstup, color=MED)
    os2.set_ylabel(vystup, color=ZELENA)
    obr.legend(handles=prvky, loc="lower center", ncol=2)
    obr.subplots_adjust(bottom=0.3, right=0.85)
    platno.draw()


# ---------------------------- okno (GUI) ----------------------------
okno = tk.Tk()
okno.title("Kalkulátor: ozubené prevody a elektromotory")
okno.geometry("820x760")
okno.configure(bg=POZADIE, padx=15, pady=10)

vyber = ttk.Combobox(okno, values=list(VZORCE), state="readonly", width=48)
vyber.current(0)
vyber.bind("<<ComboboxSelected>>", lambda e: generuj())
vyber.pack(pady=5)

tk.Button(okno, text="Generovať nové hodnoty", bg=MED, fg="white",
          command=generuj).pack(pady=5)

ukaz_zoradene = tk.BooleanVar(value=True)                        # zaškrtávacie pole
tk.Checkbutton(okno, text="Zobraziť v grafe aj zoradené hodnoty", variable=ukaz_zoradene,
               bg=POZADIE, activebackground=POZADIE, command=kresli).pack()

text_pole = tk.Label(okno, bg=POZADIE, justify="left")           # popis (label)
text_pole.pack()

popis_vstupu = tk.Label(okno, bg=POZADIE)
popis_vstupu.pack(pady=(10, 0))
pole_vstup = tk.Entry(okno, justify="center")                    # vstupné pole
pole_vstup.insert(0, "30")
pole_vstup.pack()
tk.Button(okno, text="Vypočítať", bg=ZELENA, fg="white",
          command=vypocitaj).pack(pady=5)
text_vysledok = tk.Label(okno, bg=POZADIE, font=("Arial", 12, "bold"))
text_vysledok.pack()

obr = Figure(figsize=(7, 3.8), dpi=100)
platno = FigureCanvasTkAgg(obr, master=okno)
platno.get_tk_widget().pack(fill="both", expand=True)

generuj()
okno.mainloop()
