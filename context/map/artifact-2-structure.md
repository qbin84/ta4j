# Struktura zależności ta4j: cykle, warstwy i podgraf kontraktów `core`

Analiza statyczna bajtkodu przez jdeps, wykonana 2026-10-30. To uzupełnienie mapy aktywności z [`artifact-1-territory.md`](artifact-1-territory.md): tam jest „co się zmienia”, tu „od czego to zależy”.

## Metodyka

- **Wejście:** kod produkcyjny `ta4j-core` i `ta4j-examples` z `target/classes`, bez testów. Przed analizą sprawdzono, że klasy są aktualne: wszystkie odpowiadają istniejącym źródłom, a 18 pozornie osieroconych klas w examples to dodatkowe klasy zdefiniowane w innych plikach (atrybut `SourceFile`).
- **Narzędzia:** jdeps z JDK 25.0.4.1 (`-verbose:class -filter:none`) oraz `javap -c -p -v`.
- **Węzły:** klasy zagnieżdżone i pomocnicze zwinięto do plików źródłowych. Wyszło **899 plików i 6425 zależności między nimi**.
- **Runtime kontra same typy.** jdeps tego nie rozróżnia, więc podział zrobiono na podstawie bajtkodu:
  - **runtime (5468, 85%):** dziedziczenie, `new`, wywołanie metody, dostęp do pola, rzutowanie i `instanceof`, literał `Foo.class`, `catch`, referencja metody w lambdzie;
  - **same typy:** wszystko, co jdeps zgłasza ponad to, czyli sygnatury, generyki, adnotacje i `throws`. Takich krawędzi nie traktujemy jako problemu architektonicznego.
- **Aktywne obszary:** 9 obszarów Javy z top 10 mapy terytorium (`scripts` pominięto, bo to nie Java).
- **Najmniejsza pętla:** najkrótszy cykl złożony wyłącznie z krawędzi runtime wewnątrz silnie spójnej składowej (SCC).

### Wybór narzędzia (skrót)

| Narzędzie | Zastosowanie |
|---|---|
| **jdeps** (JDK) | Graf pakietów i klas bez instalacji. Użyty w tej sesji. |
| jQAssistant | Bajtkod i git w Neo4j, zapytania łączące strukturę z historią |
| ArchUnit | Utrwalenie reguł jako testy JUnit (brak cykli, kierunek warstw) |
| `mvn dependency:tree` / `dependency:analyze` | Zależności bibliotek (nie kodu) |

jdeps nie liczy metryk, nie wykrywa cykli i nie ma filtrów `--focus`, `--include-only` ani `--collapse` (to flagi dependency-cruisera z ekosystemu JS). Te kroki wykonują skrypty z `context/map/scripts/`.

## 1. Cykle zależności w aktywnych obszarach

### Najważniejsze obserwacje

1. **Realne pętle między plikami są krótkie.** Każdy cykl runtime w aktywnych obszarach sprowadza się do pętli 2 plików. Największa grupa (45 plików: `core`, `rules`, `indicators`, `serialization`) to kilkanaście pętli 2–3 plików wokół interfejsów bazowych.
2. **Na poziomie pakietów jest jeden splot runtime z 37 pakietów.** Obejmuje pakiety 8 z 9 aktywnych obszarów. Poza nim są tylko pakiet główny `analysis.elliott`, `statistics.event` i moduł examples.
3. **Cykle wyłącznie z typów są dwa i są marginalne:** pliki `BarBuilder` ↔ `BarSeries` oraz pakiety `core` ↔ `named`. Praktycznie każdy cykl jest więc architektoniczny.
4. **Splot trzymają pojedyncze krawędzie „w górę”:**

   | Krawędź | Liczba krawędzi wstecznych | Przyczyna |
   |---|---|---|
   | `core` → `backtest` | 1 | `AnalysisCriterion.chooseBest(BarSeriesManager)` |
   | `analysis` → `criteria` | 2 | `Returns` → `ReturnRepresentation` |
   | `criteria` → `drawdown` | 1 | `CalmarRatioCriterion` → `Drawdown` |
   | `walkforward` → `backtest` | 1 | `WalkForwardEngine` → `ProgressCompletion` |

   Symulacja: bez odwołań pakietu głównego `core` do niższych pakietów splot maleje z 37 do 28 pakietów, a `backtest` i `walkforward` stają się osobną parą.
5. **Najaktywniejszy obszar, `analysis/elliott`, jest w większości czysty.** Do splotu należy tylko podpakiet `swing`. Lipcowe przeniesienie detektorów (`a954132ee`) zmieniło lokalizację plików, ale zależności w obie strony zostały.

### Cykle według obszarów

| Obszar | Najmniejsza pętla runtime | Dowód | Znaczenie przy zmianie | Związek z mapą |
|---|---|---|---|---|
| `core`: bar ↔ seria | **`BaseBar` ↔ `BaseBarSeries`**. Przez `bars.TimeBarBuilderFactory` → `TimeBarBuilder` rozrasta się do 4 plików (cała grupa: 8). | `BaseBar → BaseBarSeries`: rzutuje, woła. `BaseBarSeries → BaseBar`: `instanceof`, rzutuje, woła. `BaseBarSeries → TimeBarBuilderFactory`: `new` (`BaseBarSeries.java:238`). | Kontraktu mutacji nie da się zmienić ani przetestować po jednej stronie. | PR #1618, otwarte #1642/#1643, CF-727. Obszar z 25% poprawek. |
| `core`: interfejsy ↔ implementacje | **`Rule` ↔ `AndRule`/`OrRule`/`NotRule`/`XorRule`**, **`Rule` ↔ `RuleSerialization`**, **`Indicator` ↔ `IndicatorSerialization`**, **`Strategy` ↔ `StrategySerialization`**, **`Trade` ↔ `ExecutionSide`**, **`Trade` ↔ `RecordedTradeCostModel`**. Tylko typy: **`BarBuilder` ↔ `BarSeries`**. | `Rule → AndRule`: `new` (domyślne `and()`). `Rule → RuleSerialization`: woła (`Rule.java:56`). | Zmiana sygnatury `Rule` czy `Indicator` pociąga `rules`, `serialization` i `indicators`. Nie da się ich wydzielić do osobnego modułu API bez przecięcia pętli. | Wspólny mianownik `IndicatorSerialization` (20 obszarów). |
| `core` ↔ `backtest` | **`StrategyWalkForwardExecutor` ↔ `BarSeriesManager`**. Między pakietami: `AnalysisCriterion` → `BarSeriesManager` → `reports` → `criteria` → `AnalysisCriterion` (grupa 21 plików). | `AnalysisCriterion.java:460`: domyślna `chooseBest(BarSeriesManager, …)`. Pakiety: 49 krawędzi w jedną stronę, 1 w drugą. | Metoda wygody uzależnia kontrakt kryterium od silnika backtestu. | Trójka `core` + `analysis` + `backtest` (11), para `core` + `backtest` (20). |
| `analysis` (główny) | Wewnątrz pakietu: **`CashFlow` ↔ `AnalysisPositionSupport`** (lokalna). Między pakietami: `analysis` ↔ `criteria` (20/2). | `Returns → criteria.ReturnRepresentation`, `ReturnRepresentationPolicy`. | Oba pakiety zachowują się jak jeden moduł. | Wyjaśnia parę `analysis` + `criteria` (31 commitów na istniejących plikach) po usunięciu `EquityCurveCache`. |
| `criteria` | **`ActiveReturnVersusEnterAndHoldCriterion` ↔ `ActiveReturnCriterion`**. Pakiety: ↔ `pnl` (19/6), ↔ `helpers` (8/1), ↔ `drawdown` (7/1). | `CalmarRatioCriterion → Drawdown` i `SqnCriterion → StandardDeviationCriterion`: jedyne krawędzie wsteczne. | Podpakiety nie są warstwami: baza zależy od dzieci. | `analysis` + `criteria/drawdown` mają 77% wspólnych zmian. |
| `indicators` (główny) | Hub pakietów: ↔ `helpers` (39/94), `averages` (24/44), `statistics` (30/6), `zigzag` (11/3). Pliki: **`CorrentropyKalmanResidualIndicator` ↔ `CorrentropyKalmanFilterIndicator`**, `CachedIndicator` → `Indicator` → `IndicatorSerialization` → `CachedIndicator`. | Podpakiety dziedziczą po `CachedIndicator`, a złożone wskaźniki w pakiecie głównym używają podpakietów. | Zmiana silnika cache nie ma granicy. Nawet bez `core` splot ma 28 pakietów. | Powracające błędy cache po wydaniu (#1638, #1646, #1676, #1704). `indicators` + `averages`: 54%. |
| `analysis/elliott` | Pakiet główny poza splotem, lokalnie **`StudyRunner` ↔ `DetectorRobustnessMatrix`**. Podpakiet `swing` ↔ `indicators` (10/10) i ↔ `indicators.elliott` (7/9). | `FractalSwingDetector → RecentFractalSwingHigh/LowIndicator`, `ElliottSwing`, `ElliottDegree`. `ElliottWaveAnalysisRunner → CompositeSwingDetector`. | `swing` jest odrębny tylko z nazwy. | Obszar nr 1 i rosnący. `zigzag` zmienia się z nim w 44% przypadków. |
| `indicators/forecast` | **`MonteCarloReturnProjectionIndicator` ↔ `analysis.montecarlo.ShockPathMonteCarloMethod`**. Lokalnie dwie pary w `forecast` i `projection`. | `ShockPathMonteCarloMethod` używa zagnieżdżonych enumów `ShockModel` i `VolatilityUpdateMode` oraz `MonteCarloKernel`. | API Monte Carlo nie może zmieniać się niezależnie od wskaźnika. | CF-289. `MonteCarloShockPathPlanner` usunięty 6 X, a pętla została. |
| `indicators/statistics` | Lokalnie **`DynamicTimeWarpingSupport` ↔ `DynamicTimeWarpingDistanceIndicator`** i **`EventSynchronizationResult` ↔ `EventSynchronizationIndicator`**. | Udział w splocie odziedziczony po hubie `indicators`. | Niskie ryzyko. | Stabilny, 0 poprawek po wydaniu. |
| `examples/elliottwave` | Brak cykli z rdzeniem. Lokalnie **`ElliottWaveBtcMacroCycleDemo` ↔ `ElliottWaveMacroCycleDemo`**. | Wzajemne wywołania dem. | Drobne. | Obszar wygasający. |

## 2. Granice warstw

### Model warstw

Repo deklaruje jawnie tylko jedną granicę. `ta4j-core/src/main/java/org/ta4j/core/indicators/AGENTS.md` mówi, że w przestrzeni `indicators` mają być tylko wskaźniki. Detektory, konfiguracje, wyniki, runnery i fasady mają leżeć w `analysis`, `strategy` albo `backtest`. Pozostałe warstwy wyprowadzono z `package-info.java`:

| Warstwa | Pakiety |
|---|---|
| L0 fundament | `num`, `utils` |
| L1 model domeny | `core`, `bars`, `aggregator` |
| L2 obliczenia sygnałów | `indicators`, `analysis.elliott.swing`, `analysis.montecarlo`, `analysis.event`, `acceleration` |
| L3 decyzje i wyniki | `rules`, `analysis`, `analysis.cost`, `analysis.frequency` |
| L4 ocena | `criteria` |
| L5 orkiestracja | `backtest`, `walkforward`, `reports`, `portfolio`, `strategy` |
| L6 badania | `analysis.elliott`, `research` |
| L7 przykłady | moduł `ta4j-examples` |
| Kodek i rejestr (poprzecznie) | `serialization`, `named` |

**Złamanie granicy** to krawędź runtime z niższej warstwy do wyższej. Z naruszeń wyłączono:
- 25 krawędzi samych typów,
- rejestry i konfigurację zapisaną jako kod: `ReturnRepresentationPolicy` (globalny domyślny `static volatile`), pakiet `named` i jedną konfigurację walk-forward.

### Najważniejsze obserwacje

1. **Najczęściej zmieniane pliki korzystają z warstw przewidywalnie.** `CashFlow`, `CachedIndicator`, `BaseBarSeries`, `BarSeriesManager` i pakiet główny `analysis/elliott` nie mają krawędzi runtime w górę. Warstwa badań (L6) jest czysta. `criteria` i `analysis` nie sięgają do orkiestracji.
2. **Większość z 77 krawędzi w górę wynika z projektu, ale typy leżą w nieoczywistych pakietach.** Trzy rodziny dają około 2/3 naruszeń:
   - wspólny enum opcji `criteria.ReturnRepresentation` (17 plików),
   - ogólne abstrakcje w pakiecie głównym `analysis` (`AnalysisRunner`, `SeriesSelector`, `WeightedValue`, `SampleSummary`),
   - domyślne modele kosztów `analysis.cost.*` tworzone przez domenę transakcji.
3. **Prawdziwe zaskoczenia to nieliczne wywołania logiki w górę z kontraktów `core`:**
   - `Rule` tworzy `AndRule`, `OrRule`, `NotRule` i `XorRule`,
   - `BaseStrategy` woła `RuleCopies`,
   - `AnalysisCriterion` woła `BarSeriesManager`,
   - `Indicator`, `Rule` i `Strategy` wołają swoje serializatory.

   Do tego 4 wskaźniki budują reguły: `MACDVIndicator`, `VolatilityNormalizedMACDIndicator`, `NumericIndicator`, `ConvergenceDivergenceIndicator`.
4. **Jedyny plik z top 10 mapy, który łamie zadeklarowaną granicę, to `ElliottWaveAnalysisRunner` (52 commity).** To `*Runner` w przestrzeni `indicators`, który dodatkowo implementuje `analysis.AnalysisRunner`. Łącznie takich typów jest 14 i żaden nie jest udokumentowanym wyjątkiem.
5. **Często zmieniane miejsca z importem, który może zaskoczyć:**
   - `Returns` (35 commitów) → `criteria`,
   - wskaźniki prognoz (`EwmaReturnForecastStateIndicator` 31, `MonteCarloPriceForecastIndicator` 21, `MonteCarloReturnProjectionIndicator` 19) → `criteria`,
   - `BaseTradingRecord` (17) → `analysis.cost`.

### Wyniki według granic

| Sprawdzana granica | Wynik | Kluczowy dowód | Co sprawdzić dalej |
|---|---|---|---|
| Zadeklarowana: w `indicators` tylko wskaźniki | **Złamana: 14 typów** | Fasady (`Aroon`, `BollingerBand`, `DonchianChannel`, `KeltnerChannel`, `ElliottWave`, `WyckoffCycle`), runnery (`ElliottWaveAnalysisRunner`, `WyckoffCycleAnalysisRunner`), 5 typów `*Result`, `WyckoffEventDetector` | Formalne wyjątki w `AGENTS.md` albo przeniesienie do `analysis.elliott` z `@Deprecated` |
| L1 kontrakty → L3 reguły | **Złamana (logika):** 5 krawędzi | `Rule → AndRule/…`: `new`. `BaseStrategy → RuleCopies` | Fabryka w `rules` zamiast metod domyślnych |
| L1 kontrakt → L5 orkiestracja | **Złamana:** 1 krawędź | `AnalysisCriterion.java:460` `chooseBest(BarSeriesManager, …)` | Przenieść do `backtest` (odcina `backtest`+`walkforward` od splotu) |
| L1 domena transakcji → L3 koszty | **Formalnie złamana (11 krawędzi), w praktyce zła lokalizacja** | `BaseTrade`, `BaseTradingRecord` → `new ZeroCostModel`. `instanceof RecordedTradeCostModel` | Przenieść `CostModel` i spółkę bliżej domeny |
| L1 `AnalysisCriterion` → L3 typy okna | **Zgodne z projektem** (rekordy i enumy konfiguracji) | `AnalysisWindow$BarRange/…`, `AnalysisContext`, `OpenPositionHandling` | Niskie ryzyko |
| L2 wskaźniki → L3 reguły | **Złamana (logika):** 4 pliki | `NumericIndicator.java:292-341`, `ConvergenceDivergenceIndicator.java:252+` | Metody płynne do fabryki w `rules` |
| L2/L3 → L4 `ReturnRepresentation` | **Z projektu, w złej warstwie:** 17 plików | Prognozy, `ChopIndicator`, `LogReturnIndicator`, `Returns` | Przenieść enum do `analysis` albo `num`. Sprawdzić wywołania `setDefaultRepresentation` |
| L2 → pakiet główny `analysis` (prymitywy) | **Artefakt pakietu mieszanego:** ok. 15 krawędzi | `ElliottWaveAnalysisRunner → AnalysisRunner`, `ConfidenceProfile → WeightedValue` | Wydzielić prymitywy (np. `analysis.common`) |
| L2 Elliott walk-forward → L5 `walkforward` | **Złamana:** 2 pliki | `ElliottWavePredictionProvider` implementuje `PredictionProvider` | Przenieść do `analysis.elliott` |
| L6 badania: nic niżej od nich nie zależy | **Respektowana** | 0 krawędzi z L0–L5 | Utrwalić regułą ArchUnit |
| L3/L4 → L5 orkiestracja | **Respektowana** | 0 krawędzi runtime | Utrwalić regułą ArchUnit |
| Kodek wołany z niższych warstw | **Z projektu:** 22 krawędzie | `toJson()` w kontraktach, własne deskryptory w rodzinie VWAP i `AbstractTrendLineIndicator` | Lista kontrolna przy zmianach `serialization` |
| L0 `utils` jako fundament | **Złamana nazewniczo:** 1 plik | `BarSeriesUtils → BaseBarSeries`, agregatory | Przenieść do `bars` albo `aggregator` |
| L7 przykłady → biblioteka | **Respektowana** | Tylko publiczne API. W `ta4j-core` nie ma pakietów `internal`. | Rozważyć pakiet `internal`, bez niego granicy API nie da się sprawdzić narzędziem |

## 3. Podgraf: kontrakty `core`

**Plik:** [`graphs/core-contracts-upward.svg`](graphs/core-contracts-upward.svg) (plik źródłowy: `graphs/core-contracts-upward.dot`).

**Pytanie, na które odpowiada:** kogo dotyka zmiana kontraktów `org.ta4j.core` i które krawędzie wracają z niego w górę, tworząc pętle?

**Zakres:**
- **include-only:** 8 pakietów (`core`, `bars`, `rules.**`, `analysis`, `analysis.cost`, `criteria.**`, `backtest`, `serialization`),
- **collapse:** `rules.**` i `criteria.**` jako pojedyncze węzły,
- **focus:** tylko krawędzie z `core` albo do `core`, runtime, bez rejestrów,
- **w węzłach:** warstwa, commity z 12 miesięcy (tylko kod produkcyjny, dlatego `core` ma 143, a nie 187 jak w mapie) oraz fan-in i fan-out.

**Odczyt:**
- **Zasięg zmiany (krawędzie do `core`):** `criteria` 178 plików, `rules` 145, `backtest` 49, `bars` 36, `analysis` 32, `serialization` 15, `analysis.cost` 8.
- **Pętle tworzone przez logikę (czerwone):**
  - `core → backtest`: 1 krawędź `AnalysisCriterion → BarSeriesManager`, naprzeciw 49 w przeciwną stronę,
  - `core → rules`: 5 krawędzi naprzeciw 145.

  To najtańsze punkty do przecięcia.
- **Pętle z projektu albo przez złą lokalizację (pomarańczowe):**
  - `core → analysis.cost`: 14 krawędzi, więcej niż w kierunku odwrotnym (8), więc koszty zachowują się jak część domeny,
  - `core → serialization`: 5 krawędzi,
  - `core → analysis`: 3 krawędzie.

## Kluczowe wnioski

1. **Ryzyko architektoniczne skupia się w kontraktach `core`.** Interfejsy bazowe (`Rule`, `Indicator`, `Strategy`, `AnalysisCriterion`) znają swoje implementacje, serializację i silnik backtestu. Wyjaśnia to, dlaczego `core` ma najwyższy odsetek poprawek i najdroższą kaskadę zmian.
2. **Hub `CachedIndicator`** nie ma granicy pakietowej wobec rodzin wskaźników. To strukturalne tło powracających błędów cache.
3. **Pętla `BaseBar` ↔ `BaseBarSeries`** to dokładnie miejsce otwartych zgłoszeń #1642 i #1643.
4. **Część sprzężeń z historii gita ma konkretną przyczynę w kodzie.** Na przykład `analysis` ↔ `criteria` wynika z enuma `ReturnRepresentation` w złej warstwie, a nie z usuniętego `EquityCurveCache`.
5. **Najaktywniejszy obszar (`analysis/elliott`)** stoi czysto na szczycie warstw. Problemem jest tylko podpakiet `swing` i typy Elliotta w przestrzeni `indicators`.
6. **Najtańsze cięcia** to pojedyncze krawędzie wsteczne: `chooseBest`, przeniesienie `ReturnRepresentation`, Calmar → `Drawdown`, Sqn → `StandardDeviationCriterion`, `WalkForwardEngine → ProgressCompletion`.

## Odtworzenie

Uruchamiać z katalogu głównego repo, po `mvn -pl ta4j-core,ta4j-examples -am compile`.

```sh
# cykle: SCC, najmniejsze pętle, sploty pakietów
python3 context/map/scripts/jdeps_cycles.py /tmp/jd
# granice warstw (model L0–L7 zdefiniowany na górze skryptu)
python3 context/map/scripts/jdeps_layers.py /tmp/jd
# podgraf kontraktów core (kept.pkl z hot.py, patrz scripts/README.md)
python3 context/map/scripts/hot.py /tmp/kept.pkl
python3 context/map/scripts/jdeps_focus_graph.py /tmp/kept.pkl context/map/graphs/core-contracts-upward.dot
dot -Tsvg context/map/graphs/core-contracts-upward.dot -o context/map/graphs/core-contracts-upward.svg
```

Bez natywnego Graphviza można renderować przez wersję WASM (ten sam silnik `dot`):

```sh
mkdir -p /tmp/gv && (cd /tmp/gv && npm init -y && npm install --ignore-scripts @hpcc-js/wasm-graphviz@1.29.2)
node context/map/scripts/render_svg.mjs /tmp/gv context/map/graphs/core-contracts-upward.dot context/map/graphs/core-contracts-upward.svg
```

Analizy jednorazowe, wykonane w sesji bez osobnego skryptu w repo:
- cykle wyłącznie z typów na poziomie pakietów,
- symulacja „bez krawędzi w dół z `core`” (37 → 28 pakietów).

Obie korzystają z funkcji w `jdeps_cycles.py`.
