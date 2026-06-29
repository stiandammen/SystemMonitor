# Brukerveiledning: SystemMonitor

Velkommen til brukerveiledningen for **SystemMonitor**. Dette dokumentet beskriver hvordan du installerer, kjører, konfigurerer og bruker applikasjonen for profesjonell sanntidsovervåking av maskinvare.

---

## 1. Introduksjon & Systemkrav

SystemMonitor gir IT-teknikere og superbrukere detaljert innsikt i systemytelsen. Applikasjonen overvåker CPU, minne (RAM), harddisker, nettverkstrafikk, aktive prosesser og grafikkort (GPU).

### Systemkrav:
*   **Operativsystem**: Windows 10 / 11 (anbefalt for full hardware-avlesing), Linux, eller macOS.
*   **Python-versjon**: Python 3.9 eller nyere.
*   **Nødvendige biblioteker**: PyQt6, psutil, qtawesome, GPUtil, nvidia-ml-py, wmi (kun Windows).

---

## 2. Installasjon og Oppstart

### A. Kjøre fra kildekode (Utviklingsmiljø)
Følg disse stegene for å sette opp prosjektet første gang:

1.  **Åpne terminalen** i prosjektmappen `SystemMonitor`.
2.  **Opprett et virtuelt Python-miljø (anbefalt)**:
    ```bash
    python -m venv .venv
    ```
3.  **Aktiver det virtuelle miljøet**:
    *   *Windows (PowerShell)*: `.venv\Scripts\Activate.ps1`
    *   *Windows (CMD)*: `.venv\Scripts\activate.bat`
    *   *Linux/macOS*: `source .venv/bin/activate`
4.  **Installer nødvendige avhengigheter**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Start programmet**:
    ```bash
    python __main__.py
    ```
    *Eller bruk den ferdige oppstartsfilen for Windows:* Dobbeltklikk på `run.bat`.

### B. Kompilere til en frittstående `.exe`-fil (PyInstaller)
Dersom du ønsker å distribuere programmet som en kjørbar fil uten å kreve at brukeren har Python installert:
```bash
pip install pyinstaller
pyinstaller SystemMonitor.spec
```
Den ferdige filen vil ligge i mappen `dist/SystemMonitor.exe`.

---

## 3. Daglig Bruk & Navigasjon

Applikasjonen har et moderne, mørkt grensesnitt med et sidepanel på venstre side for enkel navigering:

*   **Oversikt (Dashboard)**: Gir et raskt overblikk over de viktigste ressursene (CPU, RAM, GPU, Nettverk og Diskplass) samlet på én side med glatte, dynamiske grafer.
*   **CPU**: Detaljert graf per kjerne, temperatur, klokkefrekvenser, samt avanserte tellere som *Interrupts (IRQ)* og *Context Switches*.
*   **Minne**: Viser RAM- og Swap-forbruk, samt RAM-type (f.eks. DDR4/DDR5).
*   **Lagring**: Viser partisjoner, lese-/skrivehastigheter per disk og **SMART-helsestatus** (slitasje, temperatur og eventuelle diskfeil).
*   **Nettverk**: Sanntids ned- og opplastingshastigheter (MB/s eller Mbps), samt en tabell over aktive nettverkstilkoblinger.
*   **Logger**: Viser programmets interne logger i sanntid for feilsøking.
*   **Innstillinger**: Tilpasning av oppdateringsfrekvens, alarmer, fargetema og integrasjoner.

### 📌 Overlay-modus (Widget)
Hvis du ønsker å holde øye med ytelsen mens du arbeider i andre programmer:
1. Gå til **Innstillinger** og aktiver **Overlay Mode**, eller start programmet fra terminalen med flagget `--overlay`.
2. Hovedvinduet skjules, og et kompakt, semi-transparent widget-vindu legger seg på skjermen. Dette kan flyttes fritt og viser kun kritisk CPU-, RAM- og nettverksinfo.

---

## 4. Konfigurering og Alarmer

SystemMonitor inkluderer et intelligent alarmsystem som gir deg beskjed dersom en maskinvarekomponent nærmer seg kritiske verdier.

### Slik setter du opp alarmer:
1.  Klikk på **Innstillinger** i sidepanelet.
2.  Gå til seksjonen **Alarmer og Terskelinnstillinger**.
3.  Juster glidebryterne (*sliders*) for de ulike parameterne:
    *   **CPU og GPU temperatur** (f.eks. varsle ved 80°C).
    *   **RAM-bruk** (f.eks. varsle ved 85% fullt minne).
    *   **Diskplass** (f.eks. varsle når en partisjon har under 10% ledig plass).
4.  Velg **Varslingsmetode**:
    *   *System Notifications*: Sender standard Windows-toastvarslinger i statusfeltet.
    *   *In-App Visuals*: Viser en rød banner øverst i selve applikasjonen.

---

## 5. Avansert Oppsett

### A. Start ved Windows-oppstart (Autostart)
I **Innstillinger**, aktiver **Kjør ved oppstart (Autostart)**. SystemMonitor vil skrive en oppføring til Windows Registry under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. Ved neste omstart vil programmet åpnes automatisk (du kan også velge å starte det minimert til statusfeltet).

### B. Prometheus Metrikk-eksport (For IT-drift)
Dersom du ønsker å overvåke maskinen sentralt:
1. Gå til **Innstillinger** og aktiver **Prometheus Exporter**.
2. Angi port (standard er `9090`).
3. Du kan nå hente ut sanntidsmålinger ved å sende en HTTP-spørring til: `http://localhost:9090/metrics`. Dette endepunktet er fullt kompatibelt med Prometheus-servere for visualisering i Grafana.
