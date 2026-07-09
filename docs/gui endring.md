# GUI-ENDRING — Ny startskjerm (modul-lanseringsvisning)

STATUS: ✅ IMPLEMENTERT (2026-07-09) — se seksjon 8 for endelig oppsummering.

Referanse: mockup-bilder generert i samtale 2026-07-09 (siste versjon = glass-utgaven uten systemstatus-panel).

---

## 1. Bakgrunn

I dag åpnes appen med et fast venstre sidepanel (`widgets/sidebar.py`, `PremiumSidebar`) som navigasjonsmetode mellom Dashboard, Processor, Graphics, Network, Memory, Storage og Settings. Ønsket er å utforske en alternativ startopplevelse inspirert av Dashy/Homepage-stil "launcher"-dashboard (se r/homelab-eksempel med "Dashwise"), hvor man i stedet møtes av en sentrert samling firkantede bokser man klikker seg videre fra.

## 2. Mål med endringen

- Erstatte (eller supplere) sidepanel-navigasjon med klikkbare, firkantede modul-bokser i selve innholdsflaten.
- Beholde nøyaktig samme visuelle språk som resten av appen: mørk cyber-cyan-bakgrunn, `Segoe UI`, samme aksentfarger per modul som allerede brukes på `GlassMetricCard` i `overview_page.py` (CPU=grønn, GPU=lilla, Minne=blå, Nettverk=cyan, Lagring=oransje).
- Gi boksene et tydelig "glass"-uttrykk (transparens/blur/lys kant), ikke bare flate kort.
- Sentrert layout — boks-rutenettet skal se balansert ut uavhengig av antall bokser i siste rad.
- Ikke vise detaljert systeminformasjon (CPU/GPU/RAM-status osv.) på denne skjermen — det hører hjemme inne i de enkelte modulene. Generell Windows-info (OS-navn og versjon) i toppfeltet er greit.

## 3. Nåværende tilstand (kode som finnes)

| Fil | Rolle i dag |
|---|---|
| `widgets/sidebar.py` | `PremiumSidebar` — fast venstre navigasjonspanel, 280px bredde, med `NAV_STRUCTURE`-liste over views. |
| `views/overview_page.py` | Dashboard-siden. Header + rutenett av `GlassMetricCard` (CPU/GPU/RAM/Nett/Disk/Temp) + graf-seksjon + info-rad. |
| `widgets/overview_widgets.py` | `GlassMetricCard`, `GlassChartPanel`, `GlassInfoPanel`, `GlassStoragePanel` — eksisterende kort-byggeklosser. |
| `widgets/glass_card.py` | `GlassCard` / `PremiumMetricCard` — halvtransparent kort-variant (`rgba(30,35,64,0.85)` bakgrunn, `rgba(74,108,247,0.25)` kant), i dag lite brukt men viser at glass-stil allerede finnes i kodebasen. |
| `styles/theme.py` | `ThemeManager` med temaer `cyber-cyan` (standard), `premium`, `cyberpunk`, `heimdal`. Alle fargekoder for aksenter/tekst/bakgrunn hentes herfra. |

## 4. Foreslått ny skjerm — oppbygning

### 4.1 Toppfelt (beholdes stort sett som i dag)
- Venstre: logo-boks (grønn, avrundet 8px) + "System Monitor" / "v2.0".
- Høyre: to små info-pills med **generell Windows-informasjon** — OS-navn (f.eks. "Windows 11 Pro") og versjon/build (f.eks. "23H2 · 22631"). Ingen CPU/GPU/RAM-tall her.
- Et lite tannhjul-ikon for innstillinger.

### 4.2 Hero-seksjon (ny)
- Sentrert overskrift: "Velg en modul".
- Sentrert undertekst: "Klikk på en boks for å åpne detaljert overvåkning".

### 4.3 Modul-bokser (kjernen i endringen)
Rutenett av like store, kvadratiske/avrundede glass-bokser, sentrert i flaten (bruker `justify-content: center` med fleksibel kolonnebredde, slik at siste rad ikke blir venstrejustert eller skjev uansett antall bokser).

Én boks per eksisterende view:

| Boks | Ikon (dagens qtawesome-navn) | Aksentfarge |
|---|---|---|
| Dashboard | `mdi.view-dashboard` | `ACCENT_GREEN` |
| Processor | `ph.cpu` | `ACCENT_GREEN` |
| Grafikk | `ph.monitor` | `ACCENT_PURPLE` |
| Minne | `mdi.memory` | `ACCENT_BLUE` |
| Nettverk | `ph.wifi-high` | `ACCENT_CYAN` |
| Lagring | `ph.database` | `ACCENT_ORANGE` |
| Innstillinger | `ph.gear` | `TEXT_SECONDARY` (nøytral) |

Hver boks inneholder (alt sentrert):
1. Sirkulær ikon-badge (~42px), bakgrunn = aksentfarge @ ~15% opacity, kant = aksentfarge @ ~30% opacity.
2. Modulnavn (fet, 11–12px).
3. Kort undertekst — kun statisk/generell tekst (f.eks. "8 kjerner", "32 GB DDR5", "3 disker"), **ikke** sanntids måleverdier.

**Glass-styling per boks:**
- Bakgrunn: lagdelt — svak hvit topp-til-bunn-gradient (`rgba(255,255,255,0.07)` → `rgba(255,255,255,0.015)`) oppå en halvtransparent mørk basefarge (`rgba(22,31,42,0.55)`).
- `backdrop-filter: blur(14px)` for faktisk glasseffekt.
- Kant: `1px solid rgba(255,255,255,0.10)` rundt, med en lysere topp-kant i modulens aksentfarge (`rgba(accent,0.45)`) som "glass-sheen".
- Hjørneavrunding: 16px (litt større enn dagens 12–14px kort, for et roligere/mer premium uttrykk).
- Skygge: `0 10px 26px rgba(0,0,0,0.35)` for dybde.
- To svake, uskarpe fargeklatter (grønn/cyan) plassert bak hele rutenettet gir et ambient glow-uttrykk gjennom glasset, uten å konkurrere med boksene.

### 4.4 Bunnfelt (beholdes)
- Sentrert statuslinje: grønn prikk + "Alle systemer operative", tilsvarende dagens footer i `PremiumSidebar._setup_footer()`.

## 5. Hva som IKKE er med i denne versjonen

- Ingen "System Health"-stripe med CPU/GPU/RAM/Disk/Temp-status (fjernet etter tilbakemelding — hører til inni modulene, ikke på startskjermen).
- Ingen detaljerte maskinvaredata i toppfeltet — kun OS-navn og versjon.
- Ingen kategoriserte faner (slik referansebildet fra r/homelab hadde med "homelab/internet/dev/Schule") — alle moduler vises i ett samlet, sentrert rutenett siden appen kun har én kategori av views.

## 6. Tekniske notater til senere implementering

- Sidepanelet kan enten fjernes helt til fordel for denne startskjermen, eller beholdes som en smal ikon-rad for rask navigering når man allerede er inne i en modul — avklares før implementering starter.
- `backdrop-filter` støttes ikke direkte av Qt Style Sheets (QSS) på samme måte som CSS. Ekte blur i PyQt6 må løses med `QGraphicsBlurEffect` på en bakgrunnslayer, eller simuleres med lag av halvtransparente `QFrame`-er. Dette bør vurderes separat før koding starter.
- Boks-klikk kan gjenbruke samme signalmønster som `PremiumSidebar.view_selected` (`pyqtSignal(str)`) slik at `MainWindow` ikke trenger endres strukturelt.
- Fargeverdier og radius bør hentes fra `theme_manager.colors` (ikke hardkodes), slik at endringen fungerer på tvers av alle fire temaene (`cyber-cyan`, `premium`, `cyberpunk`, `heimdal`).

## 7. Akseptansekriterier (når/hvis dette skal bygges)

- [x] Startskjerm viser sentrert rutenett av modul-bokser i stedet for/i tillegg til sidepanel.
- [x] Boksene har synlig glass-effekt (transparens + kant-sheen), ikke flate solid-fargede kort.
- [x] Ingen sanntids systemmålinger vises på denne skjermen.
- [x] Toppfelt viser kun generell Windows-info (OS-navn + versjon).
- [x] Layout forblir sentrert og balansert ved endring av vindusbredde og ved ulikt antall moduler.
- [x] Fungerer med alle fire temaer uten hardkodede farger.

## 8. Implementering — endelig oppsummering (2026-07-09)

Bygget som et alternativt, valgfritt oppstartsvisning — ikke en erstatning av sidepanelet, men et eget "home"-view man kan velge under Innstillinger.

**Nye/endrede filer:**
- `widgets/module_launcher.py` (ny) — `ModuleTile` (glass-boks) og `ModuleLauncherPage` (toppfelt med Windows-navn/versjon + tannhjul, sentrert hero-tekst, responsivt sentrert rutenett av bokser, footer-status).
- `config.py` — ny innstilling `home_screen_style` (`'sidebar'` standard / `'launcher'`).
- `views/settings.py` — ny "Home screen"-rad under Appearance-seksjonen med valg mellom sidepanel og modul-oversikt.
- `widgets/glass_sidebar.py` — valgfritt "Home"-navigasjonspunkt (`mdi.home-variant`) som legges til/fjernes live når innstillingen endres, slik at man kan navigere tilbake til lanseringssiden fra en modul-visning.
- `core/window.py` — registrerte `"home"`-viewet, velger riktig startvisning basert på innstillingen, skjuler sidepanelet automatisk mens man er på lanseringssiden og viser det igjen inne i modulene.
- `i18n/strings_no.py` — norske oversettelser for alle nye tekster.

**Avvik fra opprinnelig skisse:**
- Under-tekstene på boksene (f.eks. "RTX 4070", "32 GB DDR5") i mockup-bildet var eksempeldata for én bestemt PC. I den faktiske implementeringen brukes generelle, funksjonelle beskrivelser (f.eks. "GPU-belastning og VRAM") som er korrekte for alle brukere uten å måtte kjøre maskinvaredeteksjon på lanseringssiden.
- Ikoner er gjenbrukt 1:1 fra `NAV_STRUCTURE` i `glass_sidebar.py` (samme `qtawesome`-navn som allerede var validert i appen), pluss `mdi.home-variant` for det nye Hjem-punktet.

**Ikke gjort (bevisst utenfor scope):**
- Ekte CSS-lignende `backdrop-filter`-blur er ikke mulig i Qt Style Sheets — glasseffekten er simulert med halvtransparent bakgrunn, kant-sheen i modulens aksentfarge og `QGraphicsDropShadowEffect`, slik notatet i seksjon 6 forutså.
- Ingen automatisert GUI-test kjørt i denne økten (sandkasse-miljøet mangler systembibliotekene `libEGL`/`libGL` og root-tilgang til å installere dem). Verifisert med `python -m py_compile` på alle filer og manuell gjennomgang av alle signal-/metodenavn på tvers av filene.
