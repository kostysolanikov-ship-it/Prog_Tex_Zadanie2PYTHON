**# Kalkulátor: ozubené prevody a elektromotory

Jednoduchá desktopová aplikácia v jazyku **Python** s grafickým rozhraním (**Tkinter**) a vizualizáciou v knižnici **Matplotlib**. Slúži na rýchly výpočet technických vzorcov pre ozubené kolesá a elektromotory, ako aj na štatistickú analýzu a grafické zobrazenie náhodne vygenerovaných vstupných hodnôt.

## Hlavné funkcie

* **Výber technického vzorca** cez rozbaľovací zoznam (`Combobox`):
  * **Ozubené koleso:** $d = m \cdot z$ (pre modul $m = 2,5\text{ mm}$, rozsah počtu zubov $z$ od $12$ do $80$).
  * **Elektromotor:** $M = \frac{9550 \cdot P}{n}$ (pre výkon $P = 7,5\text{ kW}$, rozsah otáčok $n$ od $500$ do $2950\text{ ot/min}$).
* **Generovanie a štatistika poľa (60 náhodných hodnôt):**
  * Vytvorí 60 náhodných celých čísel z rozsahu zvoleného vzorca a vypočíta pre ne príslušné výstupné hodnoty.
  * Zobrazí počet hodnôt, prvých 10 zoradených hodnôt, minimum, maximum a aritmetický priemer.
* **Vlastný výpočet:**
  * Umožňuje zadať ľubovoľnú číselnú hodnotu (podporuje bodku aj čiarku ako oddeľovač desatinných miest) a vypočíta výsledok zaokrúhlený na dve desatinné miesta.
  * Ošetruje neplatný vstup (`ValueError`) aj delenie nulou (`ZeroDivisionError`).
* **Interaktívny graf:**
  * Používa dve nezávislé zvislé osi (`twinx`): ľavá os zobrazuje vstupné hodnoty ako stĺpcový graf, pravá os zobrazuje vypočítané hodnoty ako spojnicový graf.
  * Zaškrtávacie pole **„Zobraziť v grafe aj zoradené hodnoty“** prepína zobrazenie čiarkovanej krivky zoradených vstupných hodnôt.

## Požiadavky

* Python 3.x
* Knihovna `matplotlib` (modul `tkinter` je zvyčajne súčasťou štandardnej inštalácie Pythonu)

Inštalácia `matplotlib`:

```bash
pip install matplotlib**
