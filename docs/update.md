# UPDATE LOG

Logg over endringer, forslag og dokumentasjon i SystemMonitor-prosjektet. Nyeste øverst.

---

## 2026-07-09 — Versjon 2.2.0: full statisk gjennomgang + kritiske feilrettinger

**Type:** Kode — versjonsbump og feilrettinger. Se `docs/release-notes.md` for den brukervendte versjonen.

**Bakgrunn:** Bruker ba om en ny "update-fil" med krav om at den skal være 100 % feilfri ved installasjon. Siden appen ikke kan bygges/kjøres i dette sandkasse-miljøet (mangler `libEGL`/root), ble dette løst som en full statisk gjennomgang av **hele** `src/`-treet (ikke bare filene endret i denne samtalen) med `py_compile` og `pyflakes`, etterfulgt av retting av alt som ble funnet.

**Kritiske funn og rettinger:**
- `data/collector.py` — manglende `Optional`-import. Dette er en kjernemodul som lastes ved oppstart, så dette ville krasjet **hele appen umiddelbart** ved import. Bekreftet empirisk med en isolert reproduksjon før retting.
- `widgets/disk_monitor.py` — manglende `QRectF`- og `S`-import. Bekreftet at denne filens klasser ikke er koblet inn i noen aktiv visning i dag (`views/storage.py` bruker `storage_widgets.py`/`storage_view_widgets.py` i stedet), så bugen er sovende, ikke aktiv — rettet likevel.
- `SystemMonitor.spec` — uløst Git-merge-konflikt (bokstavelige konfliktmarkører) pluss duplikat `icon=`-argument. Garantert `SyntaxError`, blokkerte hele `pyinstaller`-bygget som `.github/workflows/release.yml` er avhengig av. Løst.
- Versjonsdrift: `__version__` sto på `2.0.0` selv om git-taggen `v2.1.0` allerede peker på samme commit som HEAD. Innstillinger → About viste i tillegg en hardkodet `"v2.0.0"`-tekst uavhengig av faktisk versjon, og `setup_installer.py` hadde sin egen frikoblede `VERSION`-konstant. Alle tre synkronisert og bumpet til `2.2.0`.

**Fortsatt uløst — krever egen beslutning:** `installer.wxs` (referert av release-workflowen for WiX MSI-bygget) finnes ikke i prosjektet i det hele tatt. Selv med alt annet fikset vil en faktisk git-tag-utløst release feile på dette steget. Se release-notes.md for detaljer.

**Verifisering:** `python -m py_compile` på alle 95 `.py`-filene i `src/` + `pyflakes`-gjennomgang av hele treet, før og etter fiksene, for å bekrefte at alle reelle `undefined name`-feil er borte. Fortsatt ingen reell GUI-kjøretidstest gjort (samme miljøbegrensning som forrige økt).

---

## 2026-07-09 — Implementert: ny startskjerm (modul-lanseringsvisning)

**Type:** Kode — ny funksjonalitet, valgfri (av som standard).

**Hva ble gjort:**
- Bygget `widgets/module_launcher.py`: `ModuleTile` (glass-boks) + `ModuleLauncherPage`, en sentrert, responsiv rutenett-startskjerm med Windows OS-navn/versjon i toppen, hero-tekst, 7 modul-bokser (Dashboard, Processor, Graphics, Memory, Network, Storage, Settings) og statusfelt nederst.
- Ny innstilling `home_screen_style` (`sidebar` / `launcher`) i `config.py`, valgbar under Settings → Appearance → "Home screen".
- `widgets/glass_sidebar.py` fikk et valgfritt "Home"-navigasjonspunkt som vises live når launcher-modus er på, slik at man kan navigere tilbake dit fra en modulvisning.
- `core/window.py` kobler alt sammen: velger riktig startvisning ved oppstart, skjuler/viser sidepanelet automatisk avhengig av om man er på lanseringssiden.
- Norske oversettelser lagt til i `i18n/strings_no.py`.
- Fungerer på tvers av alle fire temaer (cyber-cyan, premium, cyberpunk, heimdal) — ingen hardkodede farger, alt hentes fra `theme_manager.colors`.

**Verifisering:** Alle berørte filer kompilerer feilfritt (`python -m py_compile`). Full GUI-kjøretidstest (instansiering av widgetene) var ikke mulig i denne økten — sandkasse-miljøet manglet systembibliotekene `libEGL`/`libGL` og det var ingen root-tilgang til å installere dem. Anbefales testet manuelt i det virkelige utviklingsmiljøet (`python -m systemmonitor` eller `run.bat`) før det anses som fullstendig verifisert.

**Status:** Implementert og slått av som standard (`home_screen_style: 'sidebar'`), slik at eksisterende oppførsel er uendret med mindre brukeren aktivt velger "Module launcher" i innstillingene.

**Åpne punkter til neste gang:**
- Manuell test i faktisk Windows-miljø (glass-effekten, ikonrendering, klikk-navigasjon, tema-bytte, vindusstørrelse-endring).
- Vurdere om under-tekstene på boksene bør hente lettvekts statisk maskinvareinfo (f.eks. faktisk kjernetall) i stedet for generiske beskrivelser.

---

## 2026-07-09 — GUI-konsept: ny startskjerm (modul-bokser)

**Type:** Dokumentasjon/design — ingen kode endret.

**Hva ble gjort:**
- Analyserte om startskjermen kan bygges om fra sidepanel-navigasjon til et sentrert rutenett av klikkbare modul-bokser, inspirert av et Dashy/Homepage-lignende homelab-dashboard.
- Kartla eksisterende byggeklosser som kan gjenbrukes: `widgets/sidebar.py`, `views/overview_page.py`, `widgets/overview_widgets.py` (`GlassMetricCard` m.fl.), `widgets/glass_card.py`, `styles/theme.py`.
- Laget to visuelle mockup-skisser (ingen implementering):
  1. Første versjon — toppfelt + "Systemstatus"-stripe (CPU/GPU/RAM/Nett/Disk/Temp) + rutenett av modul-bokser.
  2. Revidert versjon — fjernet systemstatus-stripen, la til ekte glass-effekt (blur, transparens, aksentfarget kant-sheen, ambient glow) på boksene, sentrerte hele rutenettet og forenklet toppfeltet til kun generell Windows-info (OS-navn + versjon).
- Skrev fullstendig oppgave-dokumentasjon for endringen: `docs/gui endring.md`.

**Status:** Konsept godkjent visuelt av bruker. Ikke påbegynt i kode. Venter på beslutning om sidepanelet skal fjernes helt eller beholdes i redusert form.

**Åpne spørsmål til neste gang:**
- Skal sidepanelet fjernes helt, eller leve videre som en smal ikon-rad inne i modulvisningene?
- Hvordan skal ekte "glass"/blur løses i PyQt6 (QGraphicsBlurEffect vs. lag av halvtransparente QFrame)?
- Skal denne startskjermen være en egen "hjem"-visning man kan navigere tilbake til, eller kun vises ved oppstart?
