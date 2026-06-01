Systemmonitor – profesjonell oversikt for IT‑personell

**Formål**
- Gi en komplett, sanntidsmonitorering av maskinvareytelse for servere, arbeidsstasjoner og utviklingsmiljøer.
- Tilrettelegge for detaljert feilsøking og ytelsesoptimalisering i avanserte IT‑driftsmiljøer.

**Arkitektur**
- **Modulær trådbasert kjerne**: Hver ressurs (CPU, minne, disk, nettverk, GPU) håndteres av en dedikert `QThread`‑subclass med eget oppdateringsintervall.
- **Signal‑drevet UI**: Data sendes via `pyqtSignal(dict)` til GUI‑komponenter, som gjør UI‑oppdatering asynkron og minimaliserer hovedtrådens belastning.
- **Caching av statisk info**: `SystemInfoCollectorThread` oppdaterer kun hvert 30 s for å redusere IO‑belastning.
- **Plattform‑spesifikke fallback‑mekanismer**: Windows‑WMI‑spørringer for disk‑/GPU‑mapping, PowerShell‑basert temperatur‑innhenting, samt Linux/macOS‑kompatible metoder.

**Kjernefunksjoner**
- **CPU‑overvåkning**
  - Prosentbruk, frekvens, temperatur (psutil + WMI/HWiNFO).
  - IRQ‑ og context‑switch‑teller.
  - 0,5 s oppdateringsintervall for høy oppdateringsfrekvens.
- **Minne‑overvåkning**
  - RAM‑prosent, brukt, tilgjengelig, total.
  - Swap‑bruk og swap‑prosent.
  - RAM‑type (DDR4/DDR5 osv.) via `data.memory.get_ram_type`.
- **Disk‑overvåkning**
  - Partisjons‑info (mountpoint, filsystem, størrelse, bruk).
  - Les‑/skrive‑hastighet per partisjon, total I/O‑rate.
  - SMART‑helse, temperatur, slitasje, feil‑logg.
  - Windows‑WMI‑basert fysisk‑disk‑til‑partisjon‑mapping.
- **Nettverks‑overvåkning**
  - Ned‑ og opplastingshastighet (bytes/s).
  - Totalt mottatt og sendt data.
  - 0,5 s intervall for rask respons på nettverksendringer.
- **GPU‑overvåkning**
  - Automatisk oppdagelse av flere GPU‑er via `GPUManager`.
  - Utnyttelse, VRAM‑bruk, total/minne‑prosent.
  - Temperatur, hotspot‑ og minne‑temp.
  - Klokkehastigheter (core, boost, minne), PCI‑generasjon/båndbredde.
  - Strømforbruk, strømgrense, vifte‑hastighet (prosent og RPM).
  - Fallback‑temperatur via WMI dersom driver‑data mangler.
- **UI‑komponenter**
  - **Live‑graf/area‑graf**: I/O‑strømmer med glød‑effekt og gradient‑fyll.
  - **Temperatur‑gauge**: Sirkel med fargekodet status (grønn/oransje/rød).
  - **SMART‑status‑widget**: Visuell indikator på disk‑helse.
  - **Disk‑kort**: Kombinerer ikon, modell, bruk‑prosent, hastigheter og SMART‑data.
  - **Stat‑fliser**: Kompakte tall for CPU‑load, minne‑bruk, nettverk, GPU‑temp.
  - **Dynamisk temastøtte**: Automatisk tilpasning til lys/mørk modus via `theme_manager`.

**Pålitelighet og kvalitet**
- Omfattende feilhåndtering og logging (kategorisert per komponent).
- Throttling av signal‑utsendelse for å unngå UI‑overbelastning.
- Fallback‑strategier for temperatur‑ og disk‑informasjon på tvers av plattformer.
- Lagrer kun nødvendig data i minnet – bruker `copy()` ved signal‑utsendelse for å unngå delte referanser.

**Målgruppe**
- Systemadministratorer som trenger fin‑granulert sanntidsdata for kapasitetsplanlegging.
- IT‑driftsteam som skal overvåke server‑ eller workstation‑ytelse.
- DevOps‑ingeniører som integrerer maskinvare‑monitorering i CI/CD‑dashboards.
- Power‑brukere som krever detaljert GPU‑ og SMART‑analyse.

**Innstillingsmuligheter (Settings‑valg)**
- **Oppdateringsintervall per samler** – juster `REFRESH_INTERVAL` for CPU, minne, disk, nettverk og GPU (fra 0,2 s til flere sekunder).
- **Temavalg** – lys, mørk eller egendefinert fargepalett via `theme_manager`.
- **Alarm‑ og terskelinnstillinger** – konfigurer varsler for høy CPU‑load, temperatur, SMART‑feil eller nettverksavbrudd; kan sendes som popup eller logg.
- **Logging‑nivå** – velg mellom `DEBUG`, `INFO`, `WARNING`, `ERROR`. Loggfilen lagres under `logs/` med rotasjonsstrategi.
- **Dataretensjon** – angir hvor lenge historiske målinger skal beholdes i minnet eller på disk (f.eks. 1‑time, 24‑timer, 7‑dager).
- **Visningspreferanser** – slå av/på spesifikke UI‑widgets (f.eks. GPU‑gauge, SMART‑kort) for å tilpasse dashboard‑layout.
- **Språk/locale** – bytt mellom norsk, engelsk og andre språk for etiketter og meldinger.
- **Eksport‑alternativer** – eksporter sanntidsdata til CSV, JSON eller Prometheus‑endpoint.
- **Autostart‑alternativ** – konfigurer programmet til å starte ved systemboot eller som en tjeneste.

**Utvidelsesmuligheter**
- Nye samlere kan legges til som subklasser av `BaseCollector` med egendefinerte `REFRESH_INTERVAL`‑verdier.
- UI‑widgets kan utvides ved å importere og kombinere eksisterende komponenter.
- Tillegg av eksterne API‑kilder (f.eks. SNMP‑ eller Prometheus‑endepunkter) er mulig via standard `terminal`‑ eller `web`‑verktøy.

Programmet kombinerer teknisk dybde, pålitelighet og fleksibilitet, og er skreddersydd for profesjonelle IT‑miljøer som krever nøyaktig, sanntidsmaskinvaremonitorering.
