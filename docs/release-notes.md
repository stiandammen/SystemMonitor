# Release notes

Brukervendt endringslogg — nyeste versjon øverst. Ment til å limes inn som release-body når du tagger en ny GitHub-release.

---

## v2.2.0 — 2026-07-09

### Nytt

- **Modul-oversikt (ny startskjerm).** Et alternativ til det klassiske sidepanelet: en sentrert, responsiv rutenett-visning med glassaktige bokser for hver modul (Dashboard, Processor, Graphics, Memory, Network, Storage, Settings), generell Windows-versjon i toppen og statusfelt nederst. Av som standard — slås på under **Settings → Appearance → Home screen**. Sidepanelet får et "Home"-punkt automatisk når dette er aktivert, slik at du kan navigere tilbake dit.
- Full norsk oversettelse av den nye modul-oversikten.

### Feilrettinger

- **Kritisk:** `data/collector.py` manglet `Optional`-importen som ble brukt i en typehint — dette kunne krasje programmet allerede ved oppstart, siden denne filen lastes tidlig. Rettet.
- `widgets/disk_monitor.py` (eldre, ikke aktivt koblet inn i noen visning i dag) manglet `QRectF`- og skalerings-importen (`S`) den brukte — ville krasjet hvis/når den noen gang tas i bruk igjen. Rettet.
- Versjonstallet i appen (`__version__`) hadde stått fast på `2.0.0` lenge etter at git-taggen `v2.1.0` allerede fantes for samme commit — dette kunne fått den innebygde oppdateringssjekkeren til å tro det alltid finnes en nyere versjon, selv rett etter installasjon. Rettet ved å bumpe til `2.2.0`.
- Versjonsteksten i Innstillinger → About viste en hardkodet `"v2.0.0"` uansett faktisk versjon. Vises nå dynamisk fra `__version__`.
- `setup_installer.py` sin egen `VERSION`-konstant (brukt i Windows-avinstalleringsregisteret) var også fastlåst på `2.0.0`. Bumpet.
- `SystemMonitor.spec` inneholdt en **uløst Git-merge-konflikt** (bokstavelige `<<<<<<<`/`=======`/`>>>>>>>`-markører) pluss et duplikat `icon=`-argument i `EXE(...)`-kallet — begge deler er garanterte `SyntaxError`, som gjorde at `pyinstaller SystemMonitor.spec` (brukt av GitHub Actions-release-workflowen) ikke kunne kjøre i det hele tatt. Konflikten er løst (beholdt den dynamiske sti-baserte varianten som samsvarer med `build_exe.py`), og duplikatet er fjernet.

### Kjent, uløst blokkering for automatisk release

`.github/workflows/release.yml` refererer til en `installer.wxs`-fil for å bygge MSI-installasjonsprogrammet med WiX Toolset — **denne filen finnes ikke i prosjektet**. Selv med spec-filen fikset vil et forsøk på å trigge en release via git-tag feile på WiX-steget inntil en `installer.wxs` er lagt til. Dette er ikke løst i denne runden — det krever egne produktbeslutninger (installasjonskatalog, snarveier, oppgraderings-GUID) og bør tas som egen oppgave.

---

## v2.1.0 / v2.0.0

Ingen egen endringslogg finnes fra før denne filen ble opprettet. `v2.1.0`-taggen i git peker for øvrig på samme commit som `v2.0.0` uten faktiske kodeendringer mellom dem.
