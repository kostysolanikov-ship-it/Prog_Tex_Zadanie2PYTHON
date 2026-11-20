# Jednoduchý kalkulátor: ozubené prevody a elektromotory
# Verzia 3: zvýraznené stĺpce min a max + polia s hodnotou min a max
# Spustenie:  pip install matplotlib   a potom   python zadanie3.py
import random
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

MED = "#B87333"      # meď
ZELENA = "#2E9C84"   # zelená meď (patina)
TMAVA_MED = "#6B3E1A"  # tmavá meď (zoradené hodnoty)
POZADIE = "#FBF3EA"
MIN_FARBA = "#2B6CB0"   # modrá = minimum
MAX_FARBA = "#C0392B"   # červená = maximum

# Vzorce: názov -> (vstup, výstup, funkcia, rozsah náhodných čísel)
VZORCE = {
    "Ozubené koleso: d = m · z  (m = 2,5 mm)":
        ("z - počet zubov", "d - deliaci priemer [mm]", lambda z: 2.5 * z, (12, 80)),
    "Elektromotor: M = 9550 · P / n  (P = 7,5 kW)":
        ("n - otáčky [ot/min]", "M - krútiaci moment [N·m]", lambda n: 9550 * 7.5 / n, (500, 2950)),
}

hodnoty = []     #: pole vstupných hodnôt
vysledky = []    #: pole vypočítaných hodnôt


def aktualny_vzorec():
    return VZORCE[vyber.get()]


def generuj():
    #Vytvorí pole 60 náhodných hodnôt, urobí operácie a nakreslí graf
    global hodnoty, vysledky
    vstup, vystup, funkcia, (od, do) = aktualny_vzorec()
    hodnoty = [random.randint(od, do) for _ in range(60)]
    vysledky = [funkcia(x) for x in hodnoty]

    #: operácie s poľom (zoradenie, priemer; min a max sa zobrazia v poliach nižšie)
    zoradene = sorted(hodnoty)
    priemer = sum(hodnoty) / len(hodnoty)
    text_pole.config(text=(
        f"Počet hodnôt: {len(hodnoty)}\n"
        f"Zoradené (prvých 10): {zoradene[:10]}\n"
        f"Priemer: {priemer:.1f}"
    ))
    popis_vstupu.config(text=f"Zadaj hodnotu ({vstup}):")
    text_vysledok.config(text="")
    kresli()


def zorad(zostupne):
    #NOVÁ FUNKCIA: zoradí stĺpce (False = od najmenšieho, True = od najväčšieho)
    global hodnoty, vysledky
    if not hodnoty:
        return
    funkcia = aktualny_vzorec()[2]
    hodnoty = sorted(hodnoty, reverse=zostupne)
    vysledky = [funkcia(x) for x in hodnoty]
    kresli()


def vypocitaj():
    #Výpočet vzorca pre ľubovoľné číslo zadané používateľom
    funkcia = aktualny_vzorec()[2]
    try:
        x = float(pole_vstup.get().replace(",", "."))
        y = funkcia(x)
        text_vysledok.config(text=f"Výsledok: {y:.2f}".replace(".", ","), fg=ZELENA)
    except ValueError:
        text_vysledok.config(text="Zadaj platné číslo!", fg="red")
    except ZeroDivisionError:
        text_vysledok.config(text="Nulou sa deliť nedá!", fg="red")


def aktualizuj_min_max():
    #NOVÁ FUNKCIA: napíše minimum a maximum do farebných polí v okne
    vstup, vystup, funkcia, _ = aktualny_vzorec()
    znak_vstup, znak_vystup = vstup.split()[0], vystup.split()[0]     # napr. "z" a "d"
    for pole, hodnota in ((pole_min, min(hodnoty)), (pole_max, max(hodnoty))):
        pocet = hodnoty.count(hodnota)
        text = "MIN" if pole is pole_min else "MAX"
        if pocet > 1:
            text += f"  (×{pocet})"
        vypocitane = f"{funkcia(hodnota):.2f}".replace(".", ",")
        pole.config(text=f"{text}\n{znak_vstup} = {hodnota}  →  {znak_vystup} = {vypocitane}")


def kresli():
    #: pôvodné aj vypočítané hodnoty v jednom grafe
    vstup, vystup = aktualny_vzorec()[:2]
    obr.clear()
    os1 = obr.add_subplot(111)
    os2 = os1.twinx()                      
    stlpce = os1.bar(range(len(hodnoty)), hodnoty, color=MED, alpha=0.7, label=vstup)
    ciara, = os2.plot(vysledky, color=ZELENA, marker="s", markersize=4, linewidth=1.5, label=vystup)
    mn, mx = min(hodnoty), max(hodnoty)
    for stlpec, hodnota in zip(stlpce, hodnoty):      # NOVÉ: zvýraznenie min a max stĺpcov
        if hodnota == mx or hodnota == mn:
            stlpec.set_facecolor(MAX_FARBA if hodnota == mx else MIN_FARBA)
            stlpec.set_alpha(1)
            stlpec.set_edgecolor("black")
    prvky = [Patch(facecolor=MED, alpha=0.7, label=vstup), ciara,
             Patch(facecolor=MIN_FARBA, edgecolor="black", label=f"Minimum: {mn}"),
             Patch(facecolor=MAX_FARBA, edgecolor="black", label=f"Maximum: {mx}")]
    if ukaz_zoradene.get():                # NOVÁ FUNKCIA: zoradené náhodné čísla v grafe
        zoradena, = os1.plot(sorted(hodnoty), color=TMAVA_MED, linestyle="--", linewidth=2,
                             label=vstup + " (zoradené)")
        prvky.append(zoradena)
    os1.set_xlabel("Poradie hodnoty")
    os1.set_ylabel(vstup, color=MED)
    os2.set_ylabel(vystup, color=ZELENA)
    obr.legend(handles=prvky, loc="outside lower center", ncol=3, fontsize=8)
    aktualizuj_min_max()
    platno.draw()


# ---------------------------- okno (GUI) ----------------------------
okno = tk.Tk()
okno.title("Kalkulátor: ozubené prevody a elektromotory")
okno.geometry(f"820x{min(800, okno.winfo_screenheight() - 80)}")   # prispôsobí sa malým obrazovkám
okno.configure(bg=POZADIE, padx=15, pady=10)

vyber = ttk.Combobox(okno, values=list(VZORCE), state="readonly", width=48)
vyber.current(0)
vyber.bind("<<ComboboxSelected>>", lambda e: generuj())
vyber.pack(pady=5)

tk.Button(okno, text="Generovať nové hodnoty", bg=MED, fg="white",
          command=generuj).pack(pady=5)

rad_zoradenia = tk.Frame(okno, bg=POZADIE)
rad_zoradenia.pack(pady=(0, 5))
tk.Button(rad_zoradenia, text="↑ Stĺpce od najmenšieho po najväčší", bg=TMAVA_MED, fg="white",
          command=lambda: zorad(False)).pack(side="left", padx=3)
tk.Button(rad_zoradenia, text="↓ Stĺpce od najväčšieho po najmenší", bg=TMAVA_MED, fg="white",
          command=lambda: zorad(True)).pack(side="left", padx=3)

ukaz_zoradene = tk.BooleanVar(value=True)                        # zaškrtávacie pole
tk.Checkbutton(okno, text="Zobraziť v grafe aj zoradené hodnoty", variable=ukaz_zoradene,
               bg=POZADIE, activebackground=POZADIE, command=kresli).pack()

rad_min_max = tk.Frame(okno, bg=POZADIE)                          # NOVÉ: polia min a max
rad_min_max.pack(pady=5)
pole_min = tk.Label(rad_min_max, bg=MIN_FARBA, fg="white", width=26, pady=5,
                    font=("Arial", 11, "bold"))
pole_min.pack(side="left", padx=4)
pole_max = tk.Label(rad_min_max, bg=MAX_FARBA, fg="white", width=26, pady=5,
                    font=("Arial", 11, "bold"))
pole_max.pack(side="left", padx=4)

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

obr = Figure(figsize=(7, 3.8), dpi=100, layout="constrained")  # sám zladí rozloženie
platno = FigureCanvasTkAgg(obr, master=okno)
platno.get_tk_widget().pack(fill="both", expand=True)

generuj()
okno.mainloop()