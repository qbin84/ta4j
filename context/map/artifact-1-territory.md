# Mapa terenu ta4j: aktywność, stabilność i sprzężenia (XI 2025 – X 2026)

Analiza historii gita z okna 2025-10-30 – 2026-10-30, wykonana 2026-10-30 na `master` (HEAD `c6d7a5f24`). Repo ma historię od 2013-12-22, więc okno 12 miesięcy jest pełne. Pierwszy commit w oknie: 2025-11-03.

## Metodyka

**Zbiór bazowy:** 2260 commitów bez merge'ów → **1826** po filtrach. Odrzucono:

| Powód | Commity |
|---|---|
| Boty (`github-actions` – podbicia wersji, `dependabot`) | 33 |
| Duplikaty po rebase (ten sam autor, temat i zestaw plików) | 81 |
| Samo formatowanie (`style:`, spotless, formatter) | 71 |
| Masowe zmiany mechaniczne: SPDX w nagłówkach licencji (939 plików), migracja na JUnit 5 (~530 plików ×2), przenosiny pakietów i modułu `ta4j-cli` | 11 |
| Commity dotykające wyłącznie szumu: `*.md` (w tym CHANGELOG), `pom.xml`, `*.xml`, `*.yml`, `*.json`, `*.csv`, `src/*/resources`, `.github/`, `config/`, `docs/`, grafiki | 238 |

- Duże commity z funkcjami zostają. Świadomie zostawiono też `d0ef59e7c` „Update Indicator Unstable Counts” (155 plików), bo to realna zmiana zachowania.
- **Zmiany nazw połączone**: ścieżki zmapowano na obecne. Najważniejsze przypadki: detektory swingów `indicators/elliott` → `analysis/elliott/swing`, event-sync → `indicators/statistics/event`, reorganizacja pakietów forecast (CF-289), `refactor(elliott): organize analysis packages`.
- **Obszar** to pakiet Javy (main i test liczone razem). „(główny)” oznacza tylko pliki bezpośrednio w pakiecie, bez podpakietów.
- **Metryka** to liczba commitów dotykających obszaru lub pliku.
- **Commit AI**: autor albo trailer `Co-authored-by` to agent (Claude, Google Jules, Copilot).

## 1. Ranking aktywności

**Udział AI:** 92 z 1826 commitów (~5%): Claude 48, Jules 28, Copilot (Autofix / SWE agent) 16. Wiele commitów ludzi wspomina review Codexa, ale bez trailera nie da się ich przypisać, więc realny udział AI jest prawdopodobnie wyższy.

### TOP 10 obszarów

| # | Obszar | Commity | AI | Funkcja produktu |
|---|---|---|---|---|
| 1 | `ta4j-core/.../analysis/elliott/**` | 237 | 3 (1%) | Statystyczna walidacja detekcji fal Elliotta: badania, runnery, bootstrap nulls, detektory swingów |
| 2 | `ta4j-core/.../indicators/` (główny) | 209 | 21 (10%) | Silnik wskaźników: `CachedIndicator`, cache i propagacja zależności, rozgrzewka |
| 3 | `ta4j-core/.../core/` (główny) | 187 | 18 (10%) | Model danych: `BaseBar`, `BaseBarSeries`, `ConcurrentBarSeries`, walidacja OHLC |
| 4 | `ta4j-core/.../indicators/statistics/**` | 178 | 1 (1%) | Wskaźniki statystyczne: EWMA, CUSUM, synchronizacja zdarzeń |
| 5 | `ta4j-examples/.../analysis/elliottwave/**` | 148 | 1 (1%) | Dema i harnessy kalibracyjne fal Elliotta (BTC, cykle makro) |
| 6 | `scripts/**` | 145 | 2 (1%) | Automatyzacja buildu i wydań, testy workflow |
| 7 | `ta4j-core/.../backtest/` | 139 | 15 (11%) | Backtesting: `BarSeriesManager`, `BacktestExecutor`, modele egzekucji, sizing |
| 8 | `ta4j-core/.../criteria/**` | 129 | 16 (12%) | Kryteria oceny strategii: zysk, drawdown, ryzyko |
| 9 | `ta4j-core/.../analysis/` (główny) | 123 | 25 (20%) | Wyniki tradingu: `CashFlow`, `CumulativePnL`, `Returns` |
| 10 | `ta4j-core/.../indicators/forecast/**` | 114 | 1 (1%) | Prognozy zwrotów: stany EWMA, projekcje Monte Carlo |

Tuż za top 10: `indicators/elliott` (111), `indicators/candles` (91), `serialization` (86).

### TOP 10 plików

| # | Plik | Commity | AI |
|---|---|---|---|
| 1 | `ta4j-core/src/main/java/org/ta4j/core/analysis/CashFlow.java` | 67 | 20 |
| 2 | `ta4j-core/src/main/java/org/ta4j/core/indicators/CachedIndicator.java` | 64 | 10 |
| 3 | `ta4j-examples/src/test/java/ta4jexamples/analysis/elliottwave/backtest/ElliottWaveBtcMacroCycleDemoTest.java` | 61 | 0 |
| 4 | `ta4j-core/src/test/java/org/ta4j/core/analysis/elliott/ElliottResearchTest.java` | 61 | 0 |
| 5 | `ta4j-core/src/test/java/org/ta4j/core/analysis/CashFlowTest.java` | 56 | 16 |
| 6 | `ta4j-core/src/main/java/org/ta4j/core/analysis/CumulativePnL.java` | 56 | 15 |
| 7 | `ta4j-core/src/test/java/org/ta4j/core/indicators/CachedIndicatorTest.java` | 55 | 8 |
| 8 | `ta4j-core/src/test/java/org/ta4j/core/indicators/elliott/ElliottWaveAnalysisRunnerTest.java` | 54 | 0 |
| 9 | `ta4j-core/src/test/java/org/ta4j/core/analysis/elliott/ElliottResearch.java` | 54 | 0 |
| 10 | `ta4j-core/src/main/java/org/ta4j/core/indicators/elliott/ElliottWaveAnalysisRunner.java` | 52 | 0 |

**AI pracuje prawie wyłącznie w fundamentach:** `analysis` ~20%, `backtest`, `criteria` i `indicators` ~10–12%. W obszarach Elliotta, forecast i statistics udział AI to ≤1%.

## 2. Zmiany w czasie

Kwartały liczone od początku okna. Tempo rosło przez cały rok: Q1 (XI–I) 104 → Q2 (II–IV) 215 → Q3 (V–VII) 415 → **Q4 (VIII–X) 1092**. Sam sierpień 2026 to 616 commitów. Trendy oceniono po udziale obszaru w kwartale, nie po liczbach bezwzględnych.

| Obszar | Q1 | Q2 | Q3 | Q4 | Trend |
|---|---|---|---|---|---|
| `analysis/elliott` | 0 (0%) | 8 (4%) | 29 (7%) | 200 (18%) | rosnący |
| `indicators` (główny) | 16 (15%) | 11 (5%) | 55 (13%) | 127 (12%) | stały |
| `core` (główny) | 17 (16%) | 15 (7%) | 34 (8%) | 121 (11%) | stały |
| `indicators/statistics` | 1 | 3 | 13 | 161 (15%) | sezonowy (VIII: 132) |
| `examples/elliottwave` | 2 | 116 (54%) | 27 | 3 | wygasający |
| `scripts` | 6 | 16 | 65 (16%) | 58 | sezonowy (V–VIII) |
| `backtest` | 9 | 3 | 25 | 102 | sezonowy (VIII–IX) |
| `criteria` | 3 | 11 | 19 | 96 | sezonowy (VIII–IX) |
| `analysis` (główny) | 5 | 12 | 5 | 101 | sezonowy (VIII–IX) |
| `indicators/forecast` | 0 | 0 | 55 | 59 | sezonowy (start VII) z ogonem |

### Kampanie za skokami

| Kiedy | Obszar | Kampania |
|---|---|---|
| III 2026 | `examples/elliottwave` (105 commitów w miesiąc) | PR #1448 multi-timeframe wave counting i kalibracja dema BTC. Potem logika przechodzi do rdzenia („Unify live BTC macro fitting in core”). |
| V–VIII 2026 | `scripts` | Hardening release workflow, AI release scheduler (migracja na OpenAI), bramki jakości, CLI z akceleracją GPU |
| VII 2026 | `indicators/forecast`, `indicators` | CF-289 (warstwa prognoz: Kalman, rough volatility, change-point) oraz CF-236 (dług „series ownership”) |
| VIII 2026 | `indicators/statistics` | CF-453 (event synchronization), CF-454 (lead-lag, DTW, event-MI), SPC (CUSUM, EWMA variance, Cpk, sizer) |
| VIII–IX 2026 | `backtest`, `criteria`, `analysis` | EquityBundle → EquityCurveCache (#1613), CF-455 (parameter search), CF-360 (audyt), zamrażanie wejść backtestu, Omega i Calmar |
| VIII i X 2026 | `analysis/elliott` | CF-525 (zamrożony protokół badań), CF-586 – CF-590 (rodziny fal korekcyjnych) |
| cały rok | `core`, `indicators` | Stałe tło. W Q4: współbieżność i mutacje serii (CF-727), CF-558 (testy filtrów), wydajność `DecimalNum` |

**Przesunięcie nacisku:** wiosną dema Elliotta → latem infrastruktura wydań i prognozy → w sierpniu i wrześniu statystyka oraz backtest → w październiku badania Elliotta w rdzeniu na tle stałej pracy nad fundamentami.

## 3. Stabilność: poprawki i reverty (top 5)

**Metoda:**
- Poprawka to commit z fix, fixes, fixed, hotfix albo bugfix w temacie.
- Każdą poprawkę przypisano do PR-a, którym weszła do mastera. „W trakcie PR” oznacza gałąź `feature/*` z poprawianą funkcją. „Po wydaniu” oznacza naprawę kodu już obecnego na masterze.
- Poprawki CI i buildu policzono osobno.
- Revert przypisano do obszaru, którego dotyczył.

| Obszar | Commity | Poprawki | Reverty | W trakcie PR | Po wydaniu | Ocena |
|---|---|---|---|---|---|---|
| `analysis/elliott` | 237 | 52 (22%) | 0 | 45 | 4 (jeden PR #1618) + 3 CI | ważny, nie psuje się |
| `indicators` (główny) | 209 | 45 (22%) | 1 | 40 | 4 osobne błędy + 2 CI | ważny, z powracającymi błędami cache |
| `core` (główny) | 187 | 47 (25%) | 0 | 31 | 12 (#1618) + 3 bezpieczeństwo + 2 drobne | psuje się w jednym miejscu: współbieżne mutacje serii |
| `indicators/statistics` | 178 | 30 (17%) | 0 | 30 | 0 | ważny, stabilny (długie review) |
| `examples/elliottwave` | 148 | 8 (5%) | 0 | 6 | 2 CI | stabilny, wygasający |

- **`indicators`**: błędy po wydaniu wracają w tym samym mechanizmie cache i rekurencji:
  - #1638: inicjalizacja Kalmana,
  - #1646 (CF-638): cache bez rewizji,
  - #1676 (zgłoszenie #1666): ciągłość wygładzania,
  - #1704 (CF-729): rejestracja zależności wskaźników złożonych.
- **`core`**: PR #1618 `bugfix/preserve-series-begin-index` (25 VIII – 29 IX) naprawiał skutki CF-236. Problem nie jest zamknięty: otwarte zgłoszenia **#1642** i **#1643** opisują nieatomowe mutacje `BaseBar` w `ConcurrentBarSeries`. CF-727 tylko dokumentuje ten kontrakt. Trzy poprawki z X 2026 to hardening deserializacji (Jules/Sentinel).
- **Reverty w całym roku: 5**, wszystkie małe lub jednorazowe:
  - w top 5 tylko jednolinijkowy `CachedBuffer` (bramka SpotBugs),
  - 2 lipcowe reverty Elliotta → `examples/strategies` (próba i błąd tego samego dnia),
  - revert CF-236 → `analysis` i `backtest`,
  - revert „Optimize PortfolioSeriesManager” (22 X) → `portfolio`. Commit współtworzony przez Jules powstał na nieaktualnej bazie i usunął ~3000 linii nowszego kodu.
- **GitHub (`ta4j/ta4j`, tylko odczyt)**:
  - 36 PR-ów zamkniętych bez merge'a. W `core` jest ich 10, głównie odrzucone lub zastąpione propozycje zewnętrzne (nimo23, BarPool, #907 pluggable cache, #1504 OnChange). W `indicators` jest 6, w tym #1581, zamknięty po 3 dniach. W `statistics` jest #1219 (wariancja próbkowa), z odnośnikiem do #1475 jako kontynuacji.
  - Jedyne otwarte zgłoszenia błędów to #1642 i #1643 (oba w `core`).

## 4. Sprzężenia (współzmiany)

Pominięto 58 szerokich commitów (więcej niż 6 obszarów albo ponad 40 plików). Procent liczony jest względem mniej aktywnego obszaru z pary. W nawiasie podano wartość liczoną tylko na plikach istniejących dziś.

| Para | Razem | % mniej aktywnego |
|---|---|---|
| `core:analysis` + `core:criteria` | 36 (31) | 40% (37%) |
| `core:indicators/elliott` + `examples:analysis/elliottwave` | 35 | 37% |
| `core:analysis/event` + `core:indicators/statistics` | 34 (33) | 76% (73%) |
| `core:indicators` + `core:indicators/averages` | 31 (30) | 54% (53%) |
| `core:(root)` + `core:analysis` | 31 (30) | 28% (30%) |
| `core:analysis` + `core:criteria/drawdown` | 27 (25) | 77% (71%) |
| `core:analysis` + `core:backtest` | 26 (25) | 23% (25%) |
| `core:backtest` + `core:criteria` | 25 | 28% (30%) |

**Najczęstsza trójka:** `core:(root)` + `core:analysis` + `core:criteria` (15 commitów). Tworzy ona klaster **seria → krzywa kapitału → kryteria i backtest**.

**Wnioski dla top 3:**

- **`analysis/elliott`** jest najbardziej samodzielny: żaden partner nie przekracza 9% jego commitów.
  - Sprzężenie z `core:(root)` (20 commitów, 12%) wynika z jednej kampanii mutacji barów we wrześniu (#1618).
  - Z `indicators` łączą go detektory swingów i `CachedIndicator`.
  - `indicators/zigzag` (44% z 18) i `examples:charting/replay` (32% z 31) zmieniają się prawie zawsze razem z nim.
  - Z `examples/elliottwave` łączy go tylko 7 commitów, bo oba obszary były aktywne w różnych okresach.
- **`core:indicators`** to hub silnika cache:
  - `averages` zmienia się razem z nim w 54% przypadków (szczyt w X 2026: race'y przy przesuwaniu głowy serii),
  - `helpers` w 44%, `zigzag` w 50%, `forecast` w 18%.
- **`core:(root)`** jest źródłem kaskady: zmiana kontraktu serii (okna, snapshoty, rewizje) wymusza zmiany w `analysis` (28%), `criteria` (24%), `criteria/drawdown` (31%) i `backtest` (16%). To najdroższa granica w repo i miejsce z największą liczbą poprawek po wydaniu.

## 5. Wspólny mianownik i aktualność plików

**`CHANGELOG.md` to wspólny mianownik całego repo.**
- Pojawia się w 458 z 1676 commitów (27%) i zmienia się razem z 74 obszarami kodu.
- Jest **edytowany ręcznie**: około 586 z 600 zmian w roku. Bot wydań tylko przenosi `## Unreleased` pod nagłówek wersji (`scripts/prepare-release.sh`).
- Wpisy wymusza reguła PR.RULE.CHANGELOG_STYLE w `PULL_REQUESTS.md`.
- Koszt to konflikty (2026-09-02 „Remove committed changelog conflict markers”) i porządkowanie wpisów („Compact … changelog entries”).

**Pozostałe pliki wspólne:**

| Plik | Typ zmian | Koszt |
|---|---|---|
| `README.md` | ręczny (~128 zmian) + bot podbija wersje Mavena. `ReadmeContentManager` generuje wykresy i fragmenty kodu, ale uruchamia się go ręcznie; nie jest podpięty pod build ani CI. | średni |
| `pom.xml` | głównie automat wydań | niski |
| `CachedIndicator` | prawdziwy hub w kodzie | wysoki merytorycznie |

**Aktualność plików:**
- Z 1430 plików w analizowanych commitach 216 (15%) już nie istnieje.
- Wszystkie 23 pliki wskazane w analizie sprzężeń istnieją w HEAD.

| Usunięty plik | Kiedy i dlaczego |
|---|---|
| `analysis/EquityCurveCache.java` (+ test) | Współtworzył klaster `analysis`↔`criteria`↔`backtest` (29 commitów). Usunięty 2026-09-26 („defer … to a follow-up”), więc może wrócić w innej formie. |
| `criteria/CriteriaEvaluation.java`, `EquityBundleAware.java` | 2026-08-25 |
| `SeriesSnapshots.java` | Istniał tylko na gałęzi #1618 |
| `MonteCarloShockPathPlanner.java` | 2026-10-06, przeprojektowanie akceleracji |
| Stara wersja LPPL (`LPPLExhaustion*`, `SpdrSector*`) | VII 2026 |
| `config/spotbugs/known-debt-filter.xml` | 2026-07-03, spłata długu w CF-236 |

Po przeliczeniu par tylko na istniejących plikach wnioski się nie zmieniają. Klaster `analysis`↔`criteria` trzyma się dziś na `CashFlow`, `CumulativePnL` i `Returns`.

## Kluczowe wnioski

1. **Dwa nurty pracy**: badania fal Elliotta (rdzeń, wskaźniki i dema, razem ~500 commitów; obecnie główny kierunek) oraz fundamenty silnika (seria, cache wskaźników, backtest, krzywa kapitału).
2. **Ryzyko** skupia się w dwóch miejscach: współbieżne mutacje serii w `core` (otwarte #1642 i #1643) oraz mechanizm cache i rekurencji w `CachedIndicator`.
3. **Najdroższa granica zmian**: kontrakt `BarSeries` pociąga za sobą zmiany w `analysis`, `criteria` i `backtest`.
4. **Wysoki odsetek poprawek** w `statistics` i `analysis/elliott` wynika z długich rund review przed merge'em, a nie z awaryjności.
5. **Koszt organizacyjny**: ręczny `CHANGELOG.md` jest punktem kolizji wszystkich równoległych PR-ów.
6. **AI**: ~5% commitów, skoncentrowane w fundamentach. Jeden incydent: commit Jules na nieaktualnej bazie wymagał revertu.

## Odtworzenie

Skrypty są w `context/map/scripts/`, a kolejność uruchamiania opisuje `context/map/scripts/README.md`:
- `hot.py`: parsowanie historii, filtry, łączenie zmian nazw,
- `agg.py`: ranking obszarów i plików,
- `time.py`: rozkład miesięczny,
- `camp.py`: wyciąganie kampanii z opisów commitów,
- `fix.py`: poprawki i reverty,
- `fixpr.py`: przypisanie poprawek do PR-ów,
- `couple.py`: pary i trójki obszarów (progi: 6 obszarów, 40 plików),
- `hub.py`: wspólne pliki,
- `exist.py`: usunięte pliki i pary liczone tylko na istniejących plikach.

Podstawowe zapytanie: `git log --no-merges --since="12 months ago" -M --numstat`. Dane z GitHuba pobrano przez `gh pr list` i `gh issue list -R ta4j/ta4j`.
