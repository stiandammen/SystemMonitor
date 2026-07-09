"""Norwegian (bokmål) translations.

Flat mapping of English source strings (as written in the UI code) to their
Norwegian translation. Strings missing from this table simply fall back to
the English source text — see ``LanguageManager.tr``.
"""

TRANSLATIONS_NO = {
    # ── Sidebar navigation ──────────────────────────────────────────────
    "Dashboard": "Oversikt",
    "Processor": "Prosessor",
    "Graphics": "Grafikk",
    "Network": "Nettverk",
    "Memory": "Minne",
    "Storage": "Lagring",
    "Logs": "Logger",
    "Settings": "Innstillinger",
    "Operational": "I drift",

    # ── Module launcher (alternate home screen) ──────────────────────────
    "Home": "Hjem",
    "Select a module": "Velg en modul",
    "Click a module to open detailed monitoring": "Klikk på en modul for å åpne detaljert overvåkning",
    "Operating system": "Operativsystem",
    "Version": "Versjon",
    "All systems operational": "Alle systemer operative",
    "Live system overview": "Live systemoversikt",
    "CPU load and temperature": "CPU-belastning og temperatur",
    "GPU load and VRAM": "GPU-belastning og VRAM",
    "RAM usage and swap": "RAM-bruk og swap",
    "Download and upload speed": "Ned- og opplastingshastighet",
    "Disk space and I/O": "Diskplass og I/O",
    "Theme, alerts and units": "Tema, varsler og enheter",

    # ── Settings — home screen option ────────────────────────────────────
    "Home screen": "Startskjerm",
    "Choose between the classic sidebar or a centered grid of module tiles as your start screen":
        "Velg mellom det klassiske sidepanelet eller et sentrert rutenett av modul-bokser som startskjerm",
    "Sidebar navigation (Default)": "Sidepanel-navigasjon (standard)",
    "Module launcher": "Modul-oversikt",

    # ── Alert message templates (formatted with {value}/{threshold}) ────
    "CPU usage is {value:.1f}% (threshold: {threshold:.1f}%)":
        "CPU-bruk er {value:.1f} % (terskel: {threshold:.1f} %)",
    "CRITICAL: CPU usage is {value:.1f}%!":
        "KRITISK: CPU-bruk er {value:.1f} %!",
    "Memory usage is {value:.1f}% (threshold: {threshold:.1f}%)":
        "Minnebruk er {value:.1f} % (terskel: {threshold:.1f} %)",
    "CRITICAL: Memory usage is {value:.1f}%!":
        "KRITISK: Minnebruk er {value:.1f} %!",
    "Disk usage is {value:.1f}% (threshold: {threshold:.1f}%)":
        "Diskbruk er {value:.1f} % (terskel: {threshold:.1f} %)",
    "GPU temperature is {value:.1f}°C (threshold: {threshold:.1f}°C)":
        "GPU-temperatur er {value:.1f} °C (terskel: {threshold:.1f} °C)",
    "CPU temperature is {value:.1f}°C (threshold: {threshold:.1f}°C)":
        "CPU-temperatur er {value:.1f} °C (terskel: {threshold:.1f} °C)",

    # ── Tray menu / splash ───────────────────────────────────────────────
    "Show System Monitor": "Vis System Monitor",
    "Quit": "Avslutt",
    "Loading monitoring engine…": "Laster overvåkingsmotor…",
    "System threshold exceeded": "Systemterskel overskredet",

    # ── Settings — header & information ──────────────────────────────────
    "Application preferences": "Programinnstillinger",
    "Information": "Informasjon",
    "About System Monitor": "Om System Monitor",
    "Application Info": "Programinformasjon",
    "View version number, build details and project links": "Se versjonsnummer, byggdetaljer og lenker til prosjektet",
    "Documentation & Help": "Dokumentasjon og hjelp",
    "Technical Documentation": "Teknisk dokumentasjon",
    "Learn what the different metrics (IRQ, P-cores, etc.) actually mean": "Lær hva de ulike målingene (IRQ, P-kjerner, osv.) faktisk betyr",
    "Version {0}": "Versjon {0}",
    "Advanced system diagnostics and hardware telemetry in real-time.":
        "Avansert systemdiagnostikk og maskinvaretelemetri i sanntid.",
    "Close": "Lukk",
    "P-Cores & E-Cores": "P-kjerner og E-kjerner",
    "Hybrid Intel CPUs (12th gen+) use Performance cores for heavy tasks "
    "and Efficiency cores for background work to save power.":
        "Hybride Intel-CPU-er (12. gen.+) bruker ytelseskjerner (P-kjerner) til tunge "
        "oppgaver og effektivitetskjerner (E-kjerner) til bakgrunnsarbeid for å spare strøm.",
    "Context Switches": "Kontekstbytter",
    "How often the CPU switches between different tasks. High numbers are normal, "
    "but extreme spikes can indicate heavy multitasking or driver issues.":
        "Hvor ofte CPU-en bytter mellom ulike oppgaver. Høye tall er normalt, "
        "men ekstreme topper kan tyde på tung multitasking eller drivproblemer.",
    "Interrupts (IRQ)": "Avbrudd (IRQ)",
    "Signals from hardware to the CPU. High interrupt rates can mean "
    "malfunctioning hardware or high network/disk load.":
        "Signaler fra maskinvare til CPU-en. Høy avbruddsfrekvens kan bety "
        "feil på maskinvare eller høy nettverks-/disklast.",
    "VRAM": "VRAM",
    "Dedicated memory on your Graphics Card. If this fills up, "
    "graphics-heavy apps will slow down significantly.":
        "Dedikert minne på skjermkortet. Hvis dette fylles opp, "
        "vil grafikktunge programmer bli betydelig tregere.",
    "Page File / Swap": "Sidefil / Swap",
    "A portion of your storage used as 'extra' RAM when physical memory is full. "
    "Using this is much slower than real RAM.":
        "En del av lagringsplassen som brukes som «ekstra» RAM når fysisk minne er fullt. "
        "Dette er mye tregere enn ekte RAM.",

    # ── Settings — General ────────────────────────────────────────────────
    "General": "Generelt",
    "Language": "Språk",
    "Display language used throughout the application": "Visningsspråk som brukes i hele programmet",
    "Show system tray icon": "Vis ikon i systemstatusfeltet",
    "Display the application icon in the Windows system tray": "Vis programikonet i systemstatusfeltet i Windows",
    "Start application minimized": "Start programmet minimert",
    "Launch directly to tray without showing the main window": "Start direkte til systemstatusfeltet uten å vise hovedvinduet",
    "Run on Startup": "Kjør ved oppstart",
    "Launch System Monitor automatically when you sign in to Windows": "Start System Monitor automatisk når du logger på Windows",
    "Enable animations": "Aktiver animasjoner",
    "Smooth transitions and animated charts throughout the interface": "Jevne overganger og animerte grafer i hele grensesnittet",
    "Check for updates on startup": "Se etter oppdateringer ved oppstart",
    "Automatically check for new versions when the application starts": "Se automatisk etter nye versjoner når programmet starter",
    "Check now": "Sjekk nå",
    "Check for updates": "Se etter oppdateringer",
    "Manually query for the latest available release": "Sjekk manuelt etter siste tilgjengelige utgivelse",
    "Update Check": "Oppdateringssjekk",
    "You are running the latest version.\n\nVersion: {0}\nNo updates available.":
        "Du kjører den nyeste versjonen.\n\nVersjon: {0}\nIngen oppdateringer tilgjengelig.",

    # ── Settings — Tab visibility ────────────────────────────────────────
    "Tab Visibility": "Fanesynlighet",
    "Show {0} tab": "Vis fanen {0}",
    "Display the {0} tab in the sidebar — hide it for a cleaner interface "
    "if you don't use it (e.g. no dedicated GPU)":
        "Vis fanen {0} i sidemenyen — skjul den for et renere grensesnitt "
        "hvis du ikke bruker den (f.eks. uten dedikert skjermkort)",

    # ── Settings — Performance ───────────────────────────────────────────
    "Performance": "Ytelse",
    "Fast (250ms)": "Rask (250 ms)",
    "Normal (500ms)": "Normal (500 ms)",
    "Low (2000ms)": "Lav (2000 ms)",
    "Update speed": "Oppdateringshastighet",
    "How often metrics are refreshed — faster gives real-time detail, "
    "slower saves CPU and power":
        "Hvor ofte målingene oppdateres — raskere gir sanntidsdetaljer, "
        "tregere sparer CPU og strøm",
    "5 minutes": "5 minutter",
    "15 minutes": "15 minutter",
    "1 hour": "1 time",
    "History length": "Historikklengde",
    "How much time the live graphs keep visible before scrolling off":
        "Hvor lang tid de levende grafene holder dataene synlige før de ruller av",

    # ── Settings — Appearance ────────────────────────────────────────────
    "Appearance": "Utseende",
    "Cyber Cyan (Default)": "Cyber Cyan (Standard)",
    "Premium Dark": "Premium mørk",
    "Cyberpunk": "Cyberpunk",
    "Heimdal": "Heimdal",
    "Theme": "Tema",
    "Overall visual appearance of the application": "Programmets overordnede visuelle utseende",
    "100% (Default)": "100 % (Standard)",
    "UI Scale": "Grensesnittskala",
    "Adjust the overall interface size to match your display": "Juster den generelle grensesnittstørrelsen til skjermen din",

    # ── Settings — Units & display ───────────────────────────────────────
    "Units & Display": "Enheter og visning",
    "Celsius (°C)": "Celsius (°C)",
    "Fahrenheit (°F)": "Fahrenheit (°F)",
    "Temperature unit": "Temperaturenhet",
    "Unit used to display CPU, GPU and storage temperature readings": "Enhet som brukes til å vise temperaturmålinger for CPU, GPU og lagring",
    "Mbps (Megabits — ISP standard)": "Mbps (Megabit — ISP-standard)",
    "MB/s (Megabytes — file transfer)": "MB/s (Megabyte — filoverføring)",
    "Network speed unit": "Enhet for nettverkshastighet",
    "Unit used to display network download and upload speeds": "Enhet som brukes til å vise nedlastings- og opplastingshastigheter",
    "0 decimals (e.g. 42)": "0 desimaler (f.eks. 42)",
    "1 decimal (e.g. 42.3)": "1 desimal (f.eks. 42,3)",
    "2 decimals (e.g. 42.34)": "2 desimaler (f.eks. 42,34)",
    "Decimal precision": "Desimalpresisjon",
    "Number of decimal places shown for temperature and network speed readouts":
        "Antall desimaler som vises for temperatur- og nettverkshastighetsavlesninger",

    # ── Settings — Alerts ────────────────────────────────────────────────
    "Alerts & Notifications": "Varsler og meldinger",
    "Enable system alerts": "Aktiver systemvarsler",
    "Receive notifications when system metrics exceed configured thresholds":
        "Motta varsler når systemmålinger overstiger konfigurerte terskler",
    "CPU alert threshold": "Terskel for CPU-varsel",
    "Send an alert when CPU usage exceeds this percentage": "Send et varsel når CPU-bruken overstiger denne prosentandelen",
    "RAM usage threshold": "Terskel for RAM-bruk",
    "Send an alert when memory usage exceeds this percentage": "Send et varsel når minnebruken overstiger denne prosentandelen",
    "Disk space threshold": "Terskel for diskplass",
    "Send an alert when a partition's used space exceeds this percentage": "Send et varsel når brukt plass på en partisjon overstiger denne prosentandelen",
    "CPU temperature threshold": "Terskel for CPU-temperatur",
    "Send an alert when CPU temperature exceeds this value (°C)": "Send et varsel når CPU-temperaturen overstiger denne verdien (°C)",
    "GPU temperature threshold": "Terskel for GPU-temperatur",
    "Send an alert when GPU temperature exceeds this value (°C)": "Send et varsel når GPU-temperaturen overstiger denne verdien (°C)",
    "System Notifications (Windows popups)": "Systemvarsler (Windows-popup)",
    "In-app Visuals": "Visuelle varsler i appen",
    "Notification method": "Varslingsmetode",
    "Show alerts as Windows system tray popups, or as banners inside the app":
        "Vis varsler som popup-vinduer i Windows-systemstatusfeltet, eller som bannere inne i appen",

    # ── Settings — Data & export ─────────────────────────────────────────
    "Data & Export": "Data og eksport",
    "CSV": "CSV",
    "JSON": "JSON",
    "Plain text": "Ren tekst",
    "Export format": "Eksportformat",
    "File format used when exporting monitoring snapshots": "Filformat som brukes når overvåkingsøyeblikksbilder eksporteres",
    "Browse…": "Bla gjennom …",
    "Export destination": "Eksportmål",
    "Folder where exported monitoring data files are saved": "Mappe der eksporterte overvåkingsdatafiler lagres",
    "Current path": "Gjeldende bane",
    "Export now": "Eksporter nå",
    "Export snapshot": "Eksporter øyeblikksbilde",
    "Save a snapshot of current system metrics to the export folder": "Lagre et øyeblikksbilde av nåværende systemmålinger til eksportmappen",
    "Select Export Directory": "Velg eksportmappe",
    "No Data": "Ingen data",
    "No monitoring data available yet.\nPlease wait a moment and try again.":
        "Ingen overvåkingsdata tilgjengelig ennå.\nVent litt og prøv igjen.",
    "Export Successful": "Eksport vellykket",
    "Export Failed": "Eksport mislyktes",

    # ── Settings — Prometheus exporter ───────────────────────────────────
    "Prometheus Exporter": "Prometheus-eksportør",
    "Enable metrics endpoint": "Aktiver målepunkt-endepunkt",
    "Expose live metrics at /metrics in Prometheus text format so external "
    "tools (Prometheus, Grafana agent, curl) can scrape this machine":
        "Eksponer sanntidsmålinger på /metrics i Prometheus-tekstformat slik at "
        "eksterne verktøy (Prometheus, Grafana-agent, curl) kan hente data fra denne maskinen",
    "Port": "Port",
    "TCP port the metrics server listens on": "TCP-port som målepunktserveren lytter på",
    "Scrape URL": "Hente-URL",
    "Point your Prometheus server (or curl) at this address while enabled":
        "Pek Prometheus-serveren din (eller curl) mot denne adressen mens dette er aktivert",

    # ── Settings — Maintenance ───────────────────────────────────────────
    "Maintenance": "Vedlikehold",
    "Reset all settings to default": "Tilbakestill alle innstillinger til standard",
    "Reset settings": "Tilbakestill innstillinger",
    "Restore all preferences to factory defaults — this cannot be undone":
        "Gjenopprett alle innstillinger til fabrikkstandard — dette kan ikke angres",
    "Reset Settings": "Tilbakestill innstillinger",
    "Reset all settings to their default values?\n\nThis cannot be undone.":
        "Tilbakestille alle innstillinger til standardverdiene?\n\nDette kan ikke angres.",
    # ── CPU view ─────────────────────────────────────────────────────────
    "CPU Monitor": "CPU-overvåking",
    "Per-Core Usage": "Bruk per kjerne",
    "CPU Information": "CPU-informasjon",
    "CPU": "CPU",
    "Architecture": "Arkitektur",
    "Uptime": "Oppetid",
    "Base Clock": "Grunnklokke",
    "Physical Cores": "Fysiske kjerner",
    "Logical Processors": "Logiske prosessorer",
    "Cache": "Buffer",
    "Current Usage": "Nåværende bruk",
    "Interrupts/sec": "Avbrudd/sek",
    "Unknown": "Ukjent",
    "Fan Speeds (RPM)": "Viftehastighet (RPM)",
    "No fan sensors exposed by this system. Most consumer PCs only "
    "report fan RPM through vendor tools like HWiNFO.":
        "Ingen viftesensorer eksponeres av dette systemet. De fleste forbruker-PC-er "
        "rapporterer kun viftehastighet gjennom leverandørverktøy som HWiNFO.",
    "Voltage Rails": "Spenningsskinner",
    "No voltage sensors exposed by this system's firmware/WMI interface.":
        "Ingen spenningssensorer eksponeres av dette systemets fastvare-/WMI-grensesnitt.",

    # ── GPU view ─────────────────────────────────────────────────────────
    "GPU Monitor": "GPU-overvåking",
    "No GPU found.\nCheck that NVIDIA/AMD/Intel drivers are installed.":
        "Ingen GPU funnet.\nKontroller at NVIDIA-/AMD-/Intel-drivere er installert.",
    "iGPU": "iGPU",
    "Mobile": "Mobil",
    "Load": "Belastning",
    "Temp": "Temp",
    "Power": "Strøm",
    "Fan": "Vifte",
    "CLOCK SPEEDS": "KLOKKEFREKVENSER",
    "Core (GPU):": "Kjerne (GPU):",
    "Core Max:": "Kjerne maks:",
    "Memory:": "Minne:",
    "Memory Max:": "Minne maks:",
    "TEMPERATURE": "TEMPERATUR",
    "Edge (GPU):": "Kant (GPU):",
    "Hotspot:": "Hotspot:",
    "STATUS": "STATUS",
    "GPU Usage:": "GPU-bruk:",
    "Memory Usage:": "Minnebruk:",
    "Fan:": "Vifte:",
    "Power:": "Strøm:",
    "GFX Voltage:": "GFX-spenning:",
    "VIDEO MEMORY": "VIDEOMINNE",
    "Used:": "Brukt:",
    "Total:": "Totalt:",
    "Free:": "Ledig:",
    "SYSTEM INFORMATION": "SYSTEMINFORMASJON",
    "PCIe:": "PCIe:",
    "Driver:": "Driver:",
    "Type:": "Type:",
    "Vendor:": "Leverandør:",
    "Performance over time": "Ytelse over tid",
    "Integrated (iGPU)": "Integrert (iGPU)",
    "Mobile (dGPU)": "Mobil (dGPU)",
    "Desktop (dGPU)": "Stasjonær (dGPU)",
    "DRIVER & SYSTEM INFORMATION": "DRIVER OG SYSTEMINFORMASJON",
    "Driver Version:": "Driverversjon:",
    "Driver Date:": "Driverdato:",
    "HARDWARE": "MASKINVARE",
    "Architecture:": "Arkitektur:",
    "VRAM:": "VRAM:",
    "Memory Type:": "Minnetype:",
    "DirectX:": "DirectX:",
    "Vulkan:": "Vulkan:",
    "Supported": "Støttet",

    # ── Memory view ──────────────────────────────────────────────────────
    "LIVE": "LIVE",
    "Memory Monitor": "Minneovervåking",
    "Used": "Brukt",
    "Available": "Tilgjengelig",
    "Cached": "Bufret",
    "Free": "Ledig",
    "Memory Distribution": "Minnefordeling",
    "Memory Usage Over Time": "Minnebruk over tid",
    "System Status": "Systemstatus",
    "Healthy": "Sunn",
    "Total Memory": "Totalt minne",
    "Memory Type": "Minnetype",
    "Critical": "Kritisk",
    "Warning": "Advarsel",
    "60s ago": "60 sek. siden",
    "now": "nå",
    "Usage %": "Bruk %",
    "Memory: {0:.1f} MB ({1:.1f}%)": "Minne: {0:.1f} MB ({1:.1f} %)",
    "Kill {0}": "Drep {0}",
    "PID: {0}  |  {1}": "PID: {0}  |  {1}",

    # ── Network view ─────────────────────────────────────────────────────
    "Refresh:": "Oppdater:",
    "Download": "Nedlasting",
    "Upload": "Opplasting",
    "Connections": "Tilkoblinger",
    "Interfaces Up": "Aktive grensesnitt",
    "Network Traffic": "Nettverkstrafikk",
    "Active Connections": "Aktive tilkoblinger",
    "Protocol Distribution": "Protokollfordeling",
    "Network Interfaces": "Nettverksgrensesnitt",
    "Network Topology": "Nettverkstopologi",
    "Health": "Helse",
    "Good": "God",
    "Uptime": "Oppetid",
    "Total Sent": "Totalt sendt",
    "Total Recv": "Totalt mottatt",
    "TCP + UDP": "TCP + UDP",
    "Other": "Annet",
    "of {0} interfaces": "av {0} grensesnitt",
    "Local IP": "Lokal IP",
    "Port": "Port",
    "Remote IP": "Ekstern IP",
    "Proto": "Protokoll",
    "State": "Status",
    "Up": "Oppe",
    "Down": "Nede",

    # ── Overview / Dashboard page ────────────────────────────────────────
    "Dashboard": "Oversikt",
    "System performance overview": "Oversikt over systemytelse",
    "OS": "OS",
    "Battery": "Batteri",
    "CPU Load": "CPU-belastning",
    "GPU Load": "GPU-belastning",
    "Disk Activity": "Diskaktivitet",
    "Temperature": "Temperatur",
    "Loading...": "Laster...",
    "GPU load": "GPU-belastning",
    "{0:.1f}% utilization": "{0:.1f} % bruk",
    "{0:.0f}% of {1:.0f} GB": "{0:.0f} % av {1:.0f} GB",
    "Down / Up {0}": "Ned / Opp {0}",
    "R/W MB/s": "L/S MB/s",
    "GPU temp": "GPU-temp",
    "System temp": "Systemtemp",
    "CPU Usage": "CPU-bruk",
    "Memory Usage": "Minnebruk",
    "System Information": "Systeminformasjon",
    "Processor": "Prosessor",
    "Graphics": "Grafikk",
    "Operating System": "Operativsystem",
    "Not detected": "Ikke oppdaget",
    "Storage Drives": "Lagringsdisker",
    "{0:.1f} GB used": "{0:.1f} GB brukt",
    "{0:.1f} GB free": "{0:.1f} GB ledig",
    "used": "brukt",
    "No drives detected": "Ingen disker funnet",

    # ── Storage view ─────────────────────────────────────────────────────
    "Storage Monitor": "Lagringsovervåking",
    "disks": "disker",
    "Total Capacity": "Total kapasitet",
    "Read Speed": "Lesehastighet",
    "Write Speed": "Skrivehastighet",
    "PHYSICAL DISKS": "FYSISKE DISKER",
    "TOTAL PERFORMANCE": "TOTAL YTELSE",
    "Disk Latency": "Disklatens",
    "Disk Operations": "Diskoperasjoner",
    "Disk Bandwidth": "Diskbåndbredde",
    "Disk Load": "Diskbelastning",
    "Read": "Les",
    "Write": "Skriv",
    "Waiting for data...": "Venter på data...",
    "Unknown Disk": "Ukjent disk",

    "Settings Reset": "Innstillinger tilbakestilt",
    "All settings have been reset to defaults.\n"
    "Some changes may require a restart to take effect.":
        "Alle innstillinger er tilbakestilt til standard.\n"
        "Enkelte endringer krever omstart for å tre i kraft.",

    # ── Log viewer ───────────────────────────────────────────────────────
    "Log Viewer": "Loggvisning",
    "Inspect application log files in real time": "Se gjennom programmets loggfiler i sanntid",
    "Category": "Kategori",
    "Level": "Nivå",
    "All": "Alle",
    "Search log...": "Søk i logg...",
    "Auto-refresh": "Automatisk oppdatering",
    "Refresh": "Oppdater",
    "Open Folder": "Åpne mappe",
    "Clear View": "Tøm visning",
    "No log files found.": "Ingen loggfiler funnet.",
    "No matching log entries.": "Ingen samsvarende loggoppføringer.",
    "Showing last {0} lines of {1}": "Viser siste {0} linjer av {1}",
    "Could not read log file: {0}": "Kunne ikke lese loggfil: {0}",

    # ── About Dialog Additions ───────────────────────────────────────────
    "Key Features:": "Nøkkelfunksjoner:",
    "Processor (CPU)": "Prosessor (CPU)",
    "Advanced real-time analysis of core load (P/E cores), clocks, temperatures, and IRQs.":
        "Avansert sanntidsanalyse av kjernebelastning (P/E-kjerner), frekvenser, temperaturer og IRQ.",
    "Graphics (GPU)": "Grafikk (GPU)",
    "Telemetry for GPU utilization, VRAM allocation, temperatures, and power draw.":
        "Telemetri for GPU-utnyttelse, VRAM-allokering, temperaturer og strømforbruk.",
    "System Memory (RAM)": "Arbeidsminne (RAM)",
    "Precise tracking of physical RAM and pagefile, memory speed, and top processes.":
        "Presis overvåking av fysisk RAM, sidefil, minnehastighet og topp-prosesser.",
    "Storage (Disk)": "Lagring (Disk)",
    "Real-time I/O throughput, partition space usage, and SMART health monitoring.":
        "Sanntids I/O-hastigheter, partisjonsbruk og SMART-helseovervåking.",
    "Network": "Nettverk",
    "Bandwidth tracking (download/upload), active connections, and network topology.":
        "Båndbreddeanalyse (nedlasting/opplasting), aktive tilkoblinger og topologi.",
    "Smart Alerts": "Terskelvarsler",
    "Threshold alarms for hardware events via system notifications or in-app toasts.":
        "Terskelvarsler for maskinvarehendelser via systemvarsler eller in-app-toasts.",
    "Telemetry Export": "Dataeksport og API",
    "JSON/CSV snapshot export and built-in Prometheus metrics server (/metrics).":
        "Eksport av JSON/CSV og innebygd Prometheus-endepunkt (/metrics).",
}

