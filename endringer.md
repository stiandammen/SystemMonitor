# Endringer - QThread Optimalisering

## Oversikt
Alle tunge operasjoner (WMI-kall, prosessiterasjon, diskoperasjoner) kjører nå i `DataCollector` sin QThread i stedet for UI-tråden. Dette eliminert lagging ved vindusbevegelse.

---

## 1. `data/collector.py`

### Nye signaler
```python
processes_updated = pyqtSignal(list)    # Sending topp 100 prosesser
storage_updated = pyqtSignal(list)       # Sending partisjonsliste
system_info_updated = pyqtSignal(dict)  # Sending CPU/GPU/RAM info
```

### Nye metoder
- `_collect_processes()` - Samler prosessliste i bakgrunnstråden
- `_collect_storage()` - Samler disk/partisjonsinfo i bakgrunnstråden
- `_collect_system_info()` - Samler CPU/GPU/RAM info med caching
- `_get_cpu_name()` - Henter CPU-navn via WMI
- `_get_gpu_name()` - Henter GPU-navn via GPUtil
- `_get_motherboard()` - Henter hovedkort-info via WMI
- `_get_ram_info()` - Henter RAM-størrelse og type via WMI

### Oppdatert `run()` metode
- Inkrementell innsamling med intervaller: 3s (prosesser), 5s (lagring), 10s (systeminfo)
- Alle tunge operasjoner flyttet til bakgrunnstråden

---

## 2. `views/overview_page.py`

### Fjernet QTimers (kjørte på UI-tråden)
- `_process_timer` (3000ms) - itererte alle prosesser på UI-tråden
- `_storage_timer` (5000ms) - gjorde diskoperasjoner med WMI på UI-tråden
- `_system_info_timer` (10000ms) - gjorde WMI-kall på UI-tråden

### Nye metoder
- `set_data_collector(collector)` - Kobler til DataCollector-signaler
- `_on_processes_updated(processes)` - Callback for processes_updated signal
- `_on_storage_updated(partitions)` - Callback for storage_updated signal
- `_on_system_info_updated(info)` - Callback for system_info_updated signal
- `_update_process_table(processes)` - Oppdaterer prosess-tabellen med data fra bakgrunnstråden
- `_update_storage_display(partitions)` - Viser lagringsinfo fra bakgrunnstråden

### Variabler lagt til
```python
self._processes_cache = []
self._storage_cache = []
self._system_info_cache = {}
self._system_info_cache_time = 0
self._system_info_cache_ttl = 30
```

### Fix: Fjernet duplikat linje
- Linje `pct = usage.percent` fjernet (brukte variabel som ikke eksisterte)

---

## 3. `views/cpu.py`

### Fjernet
- `_start_update_timer()` fra `__init__`
- `_update_timer` QTimer som pollet psutil hver 500ms på UI-tråden

### Nye metoder
- `set_data_collector(collector)` - Kobler til DataCollector-signaler + starter display-timer
- `_on_data_ready(data)` - Tar imot CPU-data fra DataCollector via data_ready signal
- `_update_display()` - Oppdaterer display med cached data fra bakgrunnstråden

### Oppdatert
- `_start_update_timer()` - Startes via `set_data_collector()` for å unngå UI-blokkering
- `_update_data()` → `_update_display()` - Bruker cached data istedenfor å hente direkte

### Fix: Tippfeil
- `setValue` → `set_value` for uptime

---

## 4. `__main__.py`

### Nye tilkoblinger
```python
collector.data_ready.connect(window.update_data)

# Koble OverviewPage til DataCollector
if isinstance(window._views["overview"], OverviewPage):
    window._views["overview"].set_data_collector(collector)

# Koble CPUView til DataCollector
if isinstance(window._views["cpu"], CPUView):
    window._views["cpu"].set_data_collector(collector)
```

---

## 5. `core/window.py`

### Fix: Duplikat setStyleSheet
- **Problem:** `min_btn` hadde to `setStyleSheet()`-kall der det andre overskrev det første med en ugyldig stylesheet
- **Løsning:** Slått sammen begge stylesheetene til én komplett QPushButton-stylesheet

---

## Architektur etter endringene

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Thread (Main)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ OverviewPage│  │   CPUView   │  │   Other Views       │  │
│  │             │  │             │  │                    │  │
│  │ _uptime_timer│  │_update_timer│  │                    │  │
│  │  (1 sek)   │  │  (500ms)   │  │                    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         ▲                ▲                                   │
│         │                │                                   │
│         │    signals     │                                   │
└─────────│────────────────│───────────────────────────────────┘
          │                │
┌─────────│────────────────│───────────────────────────────────┐
│         │                │                                   │
│  ┌──────┴────────────────┴──────┐                           │
│  │       DataCollector (QThread)  │                          │
│  │                                 │                          │
│  │  _collect_data() - hvert sek    │                          │
│  │  _collect_processes() - 3s int  │                          │
│  │  _collect_storage() - 5s int   │                          │
│  │  _collect_system_info() - 10s   │                          │
│  └─────────────────────────────────┘                           │
│                     Background Thread                         │
└───────────────────────────────────────────────────────────────┘
```

---

## Resultat
- UI lagging ved vindusbevegelse eliminert
- Alle tunge operasjoner kjører i bakgrunnstråden
- UI-tråden kun ansvarlig for visning
- Smooth vindusbevegelse uten blokkering
