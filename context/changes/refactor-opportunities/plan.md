# Refactor opportunities (K2, K4 zawężony, strażnicy) Implementation Plan

## Overview

Spłata dwóch długów z rankingu `research.md`, poprzedzona strażnikami, które zamieniają dwa niejawne kontrakty w testy.

- **Strażnicy.**
  - Krawędzie importów „w górę” z plików `org.ta4j.core/*.java`.
  - Format JSON wszystkich typów Rule, Indicator i AnalysisCriterion.
- **K2.** Naprawa i deprecjacja `AnalysisCriterion.chooseBest`.
- **K4 (zawężony).** Usunięcie kopii strategii przy każdym sygnale w `PositionSizer.Context` i ujednolicenie `VoteRule.getRules()` z pozostałymi kompozytami.

Ogłoszony kontrakt kopii (CF-208/CF-236) i bajty JSON pozostają bez zmian.

## Current State Analysis

- **K2.** `chooseBest` (`ta4j-core/src/main/java/org/ta4j/core/AnalysisCriterion.java:460-487`) ma trzy problemy:
  - liczy pierwszą strategię przez `manager.run(bestStrategy)` (`:474`), a pozostałe przez `manager.run(currentStrategy, tradeType)` (`:478`). To niedokończona poprawka #668;
  - na pustej liście rzuca nieudokumentowany `NoSuchElementException` z `getFirst()` (`:473`);
  - jest jedynym powodem importu `backtest.BarSeriesManager` w `core` (`:20`; research V11).

  Konsumenci: 0 produkcyjnych, 2 wywołania testowe (`ta4j-core/src/test/java/org/ta4j/core/criteria/AbstractAnalysisCriterionTest.java:50,58`).
- **K4.** `PositionSizer.Context` kopiuje strategię dwa razy:
  - w kanonicznym konstruktorze (`ta4j-core/src/main/java/org/ta4j/core/backtest/PositionSizer.java:262`), który `BarSeriesManager` wywołuje przy każdym sygnale na ścieżce z sizerem (`BarSeriesManager.java:622→698→680→709`);
  - w akcesorze `strategy()` (`:272`).

  Uzasadnienie `@SuppressFBWarnings` (`:246-248`) twierdzi, że kontekst „borrows the run's … strategy”, co przeczy kodowi. `VoteRule.getRules()` (`rules/VoteRule.java:98`) zwraca `List.copyOf(rules)` ze współdzielonymi instancjami, podczas gdy 15 pozostałych getterów reguł kopiuje przez `RuleCopies.copy` (research V6).
- **Kontrakt kopii jest przypięty testami.** `assertNotSame` jest m.in. w `BarSeriesManagerTest.java:291-292` (`context.strategy()` jest kopią i każde wywołanie daje nową), `BacktestRuntimeReportTest.java:149-150`, `BacktestExecutorTest.java:124`, `BaseStrategyTest`, `TriggeredRuleTest`, `And/OrWithThresholdRuleTest`, `LossTriggeredCooldownRuleTest` i `ChainRuleTest` (commit `5dbdca639`, CF-236).
- **Strażników brak.**
  - W CI nie ma testu krawędzi pakietów ani zgodności API (research, Architecture Insights).
  - Nie ma testu, który przechodzi po wszystkich typach (research V24). Round-trip support jest używany w 51 testach reguł i 98 testach wskaźników (V23).

## Desired End State

1. `mvn -pl ta4j-core test` zawiera test, który failuje, gdy którykolwiek top-level plik `org.ta4j.core/*.java` doda import podpakietu `org.ta4j.core.*` spoza zapisanej listy dozwolonych krawędzi.
2. `mvn -pl ta4j-core test` zawiera test, który dla każdego konkretnego publicznego typu Rule, Indicator i AnalysisCriterion z `main` wykonuje round-trip `describe → fromDescriptor → describe` z równymi deskryptorami albo znajduje go na jawnej liście wyjątków z powodem. Każde kryterium musi leżeć w pakiecie z `CRITERIA_PACKAGES`.
3. `chooseBest(manager, SELL, strategies)` ocenia wszystkie strategie tym samym `tradeType`. Pusta lista daje `IllegalArgumentException` z komunikatem. Oba przeciążenia mają `@Deprecated(since = "0.27.1", forRemoval = true)` ze wskazaniem `BacktestExecutor#executeAndKeepTopK` i frazą „scheduled for removal in 0.29.0”.
4. Konstruktor `PositionSizer.Context` nie kopiuje strategii. Akcesor `strategy()` nadal zwraca nową kopię przy każdym wywołaniu, więc istniejące `assertNotSame` przechodzą bez zmian. `VoteRule.getRules()` zwraca listę kopii reguł.
5. `scripts/run-full-build-quiet.sh` przechodzi. `CHANGELOG.md` → `Unreleased` ma wpisy w Fixed i Changed.

### Key Discoveries:

- Wzorzec testu-polityki czytającego źródła: `ta4j-core/src/test/java/org/ta4j/core/walkforward/WalkForwardPublicSincePolicyTest.java`. Używa `Path.of("src", "main", "java", …)` względem katalogu modułu i właściwości `review.worktree`.
- Konwencja deprecjacji: `@Deprecated(since = "…", forRemoval = true)` i Javadoc `@deprecated use {@link …}` (`indicators/IndicatorUtils.java:89-93`). `ta4j-examples/.../doc/RemovalReadyDeprecationScanner.java:81-86` czyta „scheduled for removal in X.Y.Z” oraz „use {@link …}”.
- Kompilator ma tylko `showDeprecation` (`pom.xml:397`), bez `-Werror`.
- API round-trip:
  - `RuleSerialization.describe(Rule)` `:87` i `fromDescriptor(BarSeries, ComponentDescriptor)` `:242`;
  - `IndicatorSerialization.describe` `:115` i `fromDescriptor(BarSeries, …)` `:228`;
  - `AnalysisCriterionSerialization.describe` `:68` i `fromDescriptor(ComponentDescriptor)` `:100`;
  - `ComponentDescriptor.equals` `:147`.
- Auto-instancjonowanie: konstruktor wyłącznie z prostymi parametrami ma około 227 z 296 plików wskaźników z publicznym konstruktorem, 36 z 66 reguł i 29 z 42 kryteriów. Do tego kryteria z niejawnym konstruktorem bezargumentowym.
- `StrategySnapshots.copy` robi też `requireNonNull(strategy, "strategy")` (`backtest/StrategySnapshots.java:22`). Konstruktor `Context` musi zachować tę walidację po usunięciu kopii.
- `CHANGELOG.md` → `Unreleased` ma sekcje `Added/Changed/Breaking/Fixed` (`CHANGELOG.md:1-30`). Wpis jest obowiązkowy dla zmian API i zachowania (`PULL_REQUESTS.md:9`).

## What We're NOT Doing

- Odwracanie kontraktu kopii („borrowed”) w getterach `BaseStrategy`, kompozytów reguł, `BacktestRuntimeReport` i `StrategyWalkForwardExecutionResult`. Kontrakt CF-208 zostaje.
- Usuwanie podwójnej kopii w `BacktestRuntimeReport` (`:109,115`) i `StrategyWalkForwardExecutionResult` (`:77,98`). To nie jest gorąca ścieżka.
- Naprawa utraty podtypu (`NamedStrategy`) w `StrategySnapshots.copy`.
- Usunięcie `chooseBest` i importu `backtest`. Nastąpi po terminie skanera (0.29.0) w osobnej zmianie.
- Delegacja `chooseBest` do `executeAndKeepTopK`. Semantyka NaN i remisów zostaje taka jak dziś.
- Ujednolicanie maszynerii serializacji (K5 właściwy), wersjonowanie formatu kanonicznego, pliki golden JSON.
- Naprawa defektów round-trip wykrytych przez strażnika. Trafiają na listę wyjątków z kategorią `KNOWN_ROUND_TRIP_DEFECT` i do raportu z fazy.
- K1, K3, K6, K7, K8 i K9 (odrzucone w research).
- ArchUnit i inne nowe zależności.

## Implementation Approach

Najpierw strażnicy (faza 1, zero zmian produkcyjnych), żeby kolejne fazy zmieniały kod pod istniejącą osłoną. Potem K2 (faza 2) w trybie test-first: test SELL failuje przed naprawą. Na końcu K4 (faza 3), które zmienia tylko wnętrze `Context` i jeden getter, przy niezmienionych istniejących asercjach kopii. Każda faza jest osobnym, odwracalnym commitem z własnym wpisem w CHANGELOG (faza 1 nie wymaga wpisu).

## Critical Implementation Details

- **Kolejność.** Strażnik importów z fazy 1 ma `core/AnalysisCriterion.java → backtest` na liście dozwolonej z adnotacją „do usunięcia razem z `chooseBest` (0.29.0)”. Faza 2 tego wpisu nie usuwa, bo import zostaje do czasu usunięcia metody.
- **SpotBugs.** Po usunięciu kopii w konstruktorze `Context` przechowuje strategię przekazaną z zewnątrz. Jeśli `verify` zgłosi `EI_EXPOSE_REP2` dla `strategy`, trzeba rozszerzyć istniejącą adnotację `@SuppressFBWarnings` o tę regułę z uzasadnieniem zgodnym z nowym kształtem, zamiast przywracać kopię.
- **Strażnik round-trip musi być deterministyczny.** Stała, ręcznie zbudowana seria (`ta4j-core/src/test/java/org/ta4j/core/mocks/MockBarSeriesBuilder.java`) i stałe wartości domyślne parametrów. Bez losowości i bez zależności od kolejności skanu: wyniki trzeba sortować po nazwie klasy przed raportem.

## Phase 1: Strażnicy kontraktów

### Overview

Dwa nowe testy-polityki w `ta4j-core`, bez zmian w kodzie produkcyjnym. Przypinają dzisiejszy stan, więc przechodzą od razu, a failują przy regresji.

### Changes Required:

#### 1. Strażnik krawędzi importów w górę

**File**: `ta4j-core/src/test/java/org/ta4j/core/ContractUpwardImportsPolicyTest.java` (nowy)

**Intent**: Zablokować wzrost importów z top-level plików `org.ta4j.core` do podpakietów (krawędzie, które według mapy spinają splot pakietów), zanim jakakolwiek zmiana zacznie je usuwać.

**Contract**:
- Test czyta źródła `src/main/java/org/ta4j/core/*.java` (bez podkatalogów) wzorem `WalkForwardPublicSincePolicyTest` (ścieżka względna do modułu i `review.worktree`). Wyciąga deklaracje `import` / `import static` z prefiksem `org.ta4j.core.<podpakiet>`. Mapuje je do pary (plik, podpakiet), gdzie podpakiet to pełna ścieżka bez klasy, np. `analysis.cost`.
- `num` jest pomijany jako warstwa niższa.
- Lista dozwolona to stała mapa plik → zbiór podpakietów, odtworzona ze stanu na `e26a1be15`. Dla 6 plików kontraktów musi zawierać dokładnie:
  - `Rule` → `rules`, `named`, `serialization`;
  - `Strategy` → `named`, `serialization`;
  - `Indicator` → `named`, `serialization`;
  - `AnalysisCriterion` → `analysis`, `analysis.cost`, `backtest`, `named`, `serialization`;
  - `BaseStrategy` → `rules`;
  - `TradingRecord` → `analysis.cost`.

  Pozostałe top-level pliki dostają wpisy zgodne ze stanem bieżącym.
- Failuje na każdej parze spoza listy, z komunikatem plik → podpakiet. Failuje też na wpisie z listy, którego już nie ma w kodzie (lista nie może być nieaktualna).
- Wpis `AnalysisCriterion → backtest` ma komentarz o planowanym usunięciu z `chooseBest`.

#### 2. Strażnik round-trip serializacji

**File**: `ta4j-core/src/test/java/org/ta4j/core/serialization/SerializationRoundTripCoverageTest.java` (nowy) oraz plik z listą wyjątków w tym samym pakiecie testowym (stała w klasie albo zasób `src/test/resources/.../serialization-roundtrip-exclusions.*`, do wyboru wykonawcy według wzorców repo)

**Intent**: Zamienić niejawny kontrakt formatu JSON (nazwy pól i parametrów konstruktorów) w test pokrywający wszystkie typy, żeby rename pola albo nowy typ bez wsparcia serializacji failował w bramce PR.

**Contract**:
- **Skanowanie.** Enumeracja klas z drzewa `src/main/java/org/ta4j/core/{rules,indicators,criteria}/**` (ten sam mechanizm ścieżki co wyżej) → `Class.forName`. Brane są typy publiczne, nieabstrakcyjne, niebędące interfejsem, przypisywalne do `Rule`, `Indicator` albo `AnalysisCriterion`, łącznie z publicznymi zagnieżdżonymi klasami statycznymi.
- **Instancjonowanie.** Pierwszy publiczny konstruktor (kolejność deterministyczna: najmniej parametrów, potem sygnatura tekstowa), którego parametry należą do zbioru prostych: `BarSeries`, `Indicator` (jako `ClosePriceIndicator` na stałej serii), `int`/`long` (wartość 3), `double` (0.5), `Num` (`numOf(2)` z fabryki serii), `boolean` (true), `String` („x”).
- **Round-trip.**
  - Rule/Indicator: `describe` → `fromDescriptor(series, d)` → `describe`.
  - Criterion: `describe` → `fromDescriptor(d)` → `describe`.
  - Asercja: `ComponentDescriptor` przed i po są równe (`equals`).
- **Lista wyjątków.** Mapa pełna nazwa klasy → kategoria i krótki powód. Kategorie:
  - `NO_SIMPLE_CONSTRUCTOR`,
  - `CONSTRUCTOR_REJECTS_DEFAULTS`,
  - `NOT_SERIALIZABLE_BY_DESIGN`,
  - `KNOWN_ROUND_TRIP_DEFECT`.

  Typ spoza listy, którego nie da się utworzyć albo który nie przechodzi round-tripu, failuje test. Wpis z listy, który przechodzi, też failuje test (lista nieaktualna).
- **Pakiety kryteriów.** Dla każdego konkretnego kryterium, także z listy wyjątków, pakiet klasy należy do `AnalysisCriterionSerialization.CRITERIA_PACKAGES`. Pole jest odczytywane refleksyjnie w teście, bo jest `private static final`, `:37-40`. Kod produkcyjny bez zmian.
- **Raport.** Test wypisuje (log albo komunikat asercji) liczby: przetestowane, przechodzące, wyjątki per kategoria. Liczby trafiają do raportu fazy.

### Success Criteria:

#### Automated Verification:

- Oba nowe testy przechodzą: `mvn -pl ta4j-core test -Dtest=ContractUpwardImportsPolicyTest,SerializationRoundTripCoverageTest`
- Strażnik importów wykrywa regresję: tymczasowe dodanie importu `org.ta4j.core.backtest.*` do `Rule.java` powoduje fail testu (sprawdzone lokalnie i cofnięte, bez commita)
- Strażnik round-trip wykrywa regresję: tymczasowa zmiana nazwy parametru konstruktora w jednej regule z auto-round-tripem (np. `rules/OverIndicatorRule`) powoduje fail testu (sprawdzone lokalnie i cofnięte, bez commita)
- Pełna bramka przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual Verification:

- Przegląd listy wyjątków: każdy wpis `KNOWN_ROUND_TRIP_DEFECT` ma powód, a ich lista jest wypisana w raporcie z fazy jako kandydaci do osobnych poprawek
- Raport liczb z testu round-trip (przetestowane, przechodzące, wyjątki per kategoria) zgadza się z rzędem wielkości z planu (około 75% typów auto-testowanych)

**Implementation Note**: Po fazie i przejściu weryfikacji automatycznej zatrzymaj się na ręczne potwierdzenie listy wyjątków przed fazą 2.

---

## Phase 2: K2 – naprawa i deprecjacja `chooseBest`

### Overview

Test-first: test SELL i test pustej listy failują przed zmianą. Potem naprawa, walidacja, deprecjacja obu przeciążeń i wpisy w CHANGELOG.

### Changes Required:

#### 1. Testy zachowania `chooseBest`

**File**: `ta4j-core/src/test/java/org/ta4j/core/criteria/AbstractAnalysisCriterionTest.java`

**Intent**: Przypiąć poprawne zachowanie przed naprawą. Test SELL pokazuje, że dziś pierwsza strategia jest liczona innym kierunkiem niż reszta.

**Contract**: Nowe przypadki:
- (a) `tradeType = SELL` i co najmniej 2 strategie z domyślnym BUY, dobrane tak, że dziś wygrywa pierwsza wyłącznie dzięki asymetrii `:474/:478`, a po naprawie wygrywa właściwa;
- (b) pusta lista → `IllegalArgumentException` z komunikatem wskazującym `strategies`;
- (c) remis: przy równych wartościach wygrywa wcześniejsza strategia (utrwalenie obecnej semantyki `betterThan`).

Istniejące wywołania (`:50,58`) zostają. Metody testowe wołające zdeprecjonowane API mają `@SuppressWarnings("removal")`.

#### 2. Naprawa i deprecjacja

**File**: `ta4j-core/src/main/java/org/ta4j/core/AnalysisCriterion.java`

**Intent**: Ocena wszystkich kandydatów tym samym `tradeType`, jawna walidacja pustej listy i oznaczenie metody do usunięcia ze wskazaniem istniejącego zamiennika w `backtest`.

**Contract**:
- `:474` liczy pierwszą strategię przez `manager.run(bestStrategy, tradeType)`.
- Przed `getFirst()` jest walidacja: pusta lista → `IllegalArgumentException("strategies must not be empty")` (dokładne brzmienie do wyboru, byle wskazywało `strategies`), z `@throws` w Javadoc.
- Oba przeciążenia (`:460`, `:472`) dostają `@Deprecated(since = "0.27.1", forRemoval = true)` oraz Javadoc `@deprecated` z frazami „scheduled for removal in 0.29.0” i „use {@link org.ta4j.core.backtest.BacktestExecutor#executeAndKeepTopK}” (pełna nazwa w linku, bez nowego importu).
- Javadoc 2-argumentowego przeciążenia mówi, że wymusza BUY.
- Semantyka remisów i NaN bez zmian.

#### 3. CHANGELOG

**File**: `CHANGELOG.md` (sekcja `## Unreleased`)

**Intent**: Udokumentować zmianę wyniku dla SELL i deprecjację zgodnie z `PULL_REQUESTS.md:9`.

**Contract**:
- `### Fixed`: `chooseBest` ocenia pierwszą strategię z przekazanym `tradeType`; wynik może się zmienić dla SELL i dla strategii z `startingType ≠ tradeType`.
- `### Fixed`: pusta lista daje `IllegalArgumentException` zamiast `NoSuchElementException`.
- `### Changed`: deprecjacja obu przeciążeń ze wskazaniem `BacktestExecutor#executeAndKeepTopK` i informacją, że ranking tam rozstrzyga NaN i remisy inaczej.

### Success Criteria:

#### Automated Verification:

- Nowe testy (a) i (b) failują przed zmianą w `AnalysisCriterion.java` i przechodzą po niej: `mvn -pl ta4j-core test -Dtest=AbstractAnalysisCriterionTest`
- Wszystkie testy kryteriów przechodzą: `mvn -pl ta4j-core test -Dtest='*CriterionTest'`
- Strażnik importów z fazy 1 przechodzi bez zmiany listy: `mvn -pl ta4j-core test -Dtest=ContractUpwardImportsPolicyTest`
- Pełna bramka przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual Verification:

- Javadoc obu przeciążeń zawiera frazy rozpoznawane przez `RemovalReadyDeprecationScanner` („scheduled for removal in 0.29.0”, „use {@link …}”)
- Wpisy CHANGELOG są w `Unreleased` w sekcjach Fixed i Changed i opisują zmianę wyniku dla SELL

**Implementation Note**: Po fazie i przejściu weryfikacji automatycznej zatrzymaj się na ręczne potwierdzenie przed fazą 3.

---

## Phase 3: K4 – kopia strategii tylko przy dostępie, spójny `VoteRule`

### Overview

Usunięcie pełnej kopii strategii przy każdym sygnale na ścieżce z sizerem, przy zachowaniu kontraktu „akcesor zwraca kopię”. Do tego ujednolicenie jedynego gettera reguł, który nie kopiuje.

### Changes Required:

#### 1. `PositionSizer.Context` bez kopii w konstruktorze

**File**: `ta4j-core/src/main/java/org/ta4j/core/backtest/PositionSizer.java`

**Intent**: Kontekst powstaje przy każdym sygnale. Kopia w konstruktorze to pełny round-trip serializacji obu reguł, nawet gdy sizer w ogóle nie sięga po strategię. Kopia zostaje wyłącznie w akcesorze `strategy()`.

**Contract**:
- Konstruktor kanoniczny (`:260-268`) zamiast `strategy = StrategySnapshots.copy(strategy)` waliduje tylko `Objects.requireNonNull(strategy, "strategy")`.
- Akcesor `strategy()` (`:271-273`) bez zmian: nowa kopia przy każdym wywołaniu.
- Uzasadnienie `@SuppressFBWarnings` (`:246-248`) mówi zgodnie z kodem, że kontekst pożycza serię, rekord i modele kosztów, a strategię przechowuje przez referencję i udostępnia wyłącznie jako kopię.
- Konsekwencja widoczna dla użytkowników: `Context.equals/hashCode` traktuje teraz dwa konteksty zbudowane z tej samej instancji strategii jako równe (wcześniej nigdy).

#### 2. Testy `Context`

**File**: `ta4j-core/src/test/java/org/ta4j/core/backtest/PositionSizerContextTest.java` (nowy; dedykowanego testu `PositionSizer` dziś nie ma)

**Intent**: Przypiąć nowy kształt: akcesor dalej kopiuje, konstruktor nie.

**Contract**:
- Asercje `BarSeriesManagerTest.java:291-292` przechodzą bez modyfikacji.
- Nowy test: dwa `Context` zbudowane z tej samej strategii i tych samych argumentów są równe.
- Nowy test: `strategy()` zwraca strategię o tej samej nazwie i regułach dających te same sygnały co oryginał.
- `null` strategia → `NullPointerException` z komunikatem `strategy`.

#### 3. `VoteRule.getRules()` zwraca kopie

**File**: `ta4j-core/src/main/java/org/ta4j/core/rules/VoteRule.java`, test `ta4j-core/src/test/java/org/ta4j/core/rules/VoteRuleTest.java`

**Intent**: Ujednolicić `VoteRule` z 15 pozostałymi getterami reguł (`RuleCopies.copy`), zgodnie z kontraktem CF-208.

**Contract**:
- `getRules()` (`:98`) zwraca niemodyfikowalną listę, w której każdy element to `RuleCopies.copy(rule)`, w tej samej kolejności. Pole `rules` bez zmian.
- Test: każdy element zwróconej listy jest `assertNotSame` wobec reguły przekazanej w konstruktorze, a dwa wywołania `getRules()` dają różne instancje elementów (wzór: `AndWithThresholdRuleTest`).
- Test: kopie dają te same wyniki `isSatisfied` co oryginały.

#### 4. CHANGELOG

**File**: `CHANGELOG.md` (sekcja `## Unreleased` → `### Changed`)

**Intent**: Udokumentować dwie zmiany zachowania publicznego API.

**Contract**: Dwa wpisy:
- `PositionSizer.Context` nie kopiuje strategii przy tworzeniu, tylko przy dostępie przez `strategy()` (szybsze backtesty z sizerem; `equals` kontekstów z tą samą strategią);
- `VoteRule.getRules()` zwraca kopie reguł jak pozostałe kompozyty.

### Success Criteria:

#### Automated Verification:

- Testy kopii przechodzą bez zmian istniejących asercji: `mvn -pl ta4j-core test -Dtest=BarSeriesManagerTest,BacktestRuntimeReportTest,BacktestExecutorTest,VoteRuleTest`
- Nowe testy `Context` i `VoteRule` przechodzą: `mvn -pl ta4j-core test -Dtest=PositionSizerContextTest,VoteRuleTest`
- Strażnicy z fazy 1 przechodzą: `mvn -pl ta4j-core test -Dtest=ContractUpwardImportsPolicyTest,SerializationRoundTripCoverageTest`
- Pełna bramka (z SpotBugs) przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual Verification:

- Uzasadnienie `@SuppressFBWarnings` w `PositionSizer.Context` opisuje faktyczny kształt (strategia przez referencję, akcesor kopiuje)
- `git diff` istniejących testów kopii (`BarSeriesManagerTest`, `BacktestRuntimeReportTest`, `BacktestExecutorTest`, `BaseStrategyTest`, testy kompozytów) jest pusty

**Implementation Note**: Po fazie i przejściu weryfikacji automatycznej zatrzymaj się na ręczne potwierdzenie.

---

## Testing Strategy

### Unit Tests:

- Faza 1: strażnik importów (pozytywny na dziś, wykrycie dodanego importu, wykrycie nieaktualnego wpisu); strażnik round-trip (wszystkie typy, lista wyjątków bez nieaktualnych wpisów, pakiety kryteriów).
- Faza 2: `chooseBest` dla SELL z asymetrią, pusta lista, remis.
- Faza 3: `Context` (kopia w akcesorze, równość, `null`), `VoteRule.getRules` (kopie, kolejność, równoważność sygnałów).

### Integration Tests:

- Istniejące `BarSeriesManagerTest` (ścieżka z sizerem `:280-305`) i `BacktestExecutorTest` (sizer `:357,480,886,955`) pokrywają przepływ backtestu z `Context` bez zmian.

### Manual Testing Steps:

1. Po fazie 1 przejrzeć listę wyjątków i wypisać wpisy `KNOWN_ROUND_TRIP_DEFECT`.
2. Po fazie 2 sprawdzić Javadoc deprecjacji pod kątem fraz skanera.
3. Po fazie 3 potwierdzić pusty diff istniejących testów kopii.

## Performance Considerations

Faza 3 usuwa jeden pełny round-trip serializacji obu reguł strategii na każdy sygnał na ścieżce z `PositionSizer`. Pomiar nie jest kryterium akceptacji, bo benchmarki działają tylko w cronie (`test-tag-benchmark.yml`).

## Migration Notes

- Użytkownicy `chooseBest` z `SELL` albo ze strategiami o `startingType ≠ tradeType` mogą dostać inną „najlepszą” strategię (wpis Fixed).
- Usunięcie `chooseBest` jest planowane na 0.29.0. Termin wykryje `RemovalReadyDeprecationScanner` w `prepare-release.yml`.

## References

- Research: `context/changes/refactor-opportunities/research.md` (ranking, weryfikacja V1–V33)
- Analiza źródłowa: `context/changes/strategy-definition-and-evaluation-analysis/research.md`
- Wzorzec testu-polityki: `ta4j-core/src/test/java/org/ta4j/core/walkforward/WalkForwardPublicSincePolicyTest.java`
- Wzorzec deprecjacji: `ta4j-core/src/main/java/org/ta4j/core/indicators/IndicatorUtils.java:89-93`
- Kontrakt kopii: commit `5dbdca639` (CF-236), `BarSeriesManagerTest.java:291-292`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Strażnicy kontraktów

#### Automated

- [ ] 1.1 Oba nowe testy przechodzą: `mvn -pl ta4j-core test -Dtest=ContractUpwardImportsPolicyTest,SerializationRoundTripCoverageTest`
- [ ] 1.2 Strażnik importów wykrywa regresję (tymczasowy import backtest w Rule.java, cofnięty)
- [ ] 1.3 Strażnik round-trip wykrywa regresję (tymczasowy rename parametru konstruktora, cofnięty)
- [ ] 1.4 Pełna bramka przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual

- [ ] 1.5 Przegląd listy wyjątków i wpisów KNOWN_ROUND_TRIP_DEFECT w raporcie z fazy
- [ ] 1.6 Raport liczb z testu round-trip zgadza się z rzędem wielkości z planu

### Phase 2: K2 – naprawa i deprecjacja chooseBest

#### Automated

- [ ] 2.1 Nowe testy (a) i (b) failują przed zmianą i przechodzą po niej: `mvn -pl ta4j-core test -Dtest=AbstractAnalysisCriterionTest`
- [ ] 2.2 Wszystkie testy kryteriów przechodzą: `mvn -pl ta4j-core test -Dtest='*CriterionTest'`
- [ ] 2.3 Strażnik importów przechodzi bez zmiany listy
- [ ] 2.4 Pełna bramka przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual

- [ ] 2.5 Javadoc deprecjacji zawiera frazy rozpoznawane przez RemovalReadyDeprecationScanner
- [ ] 2.6 Wpisy CHANGELOG w Unreleased (Fixed, Changed) opisują zmianę wyniku dla SELL

### Phase 3: K4 – kopia strategii tylko przy dostępie, spójny VoteRule

#### Automated

- [ ] 3.1 Testy kopii przechodzą bez zmian istniejących asercji: `mvn -pl ta4j-core test -Dtest=BarSeriesManagerTest,BacktestRuntimeReportTest,BacktestExecutorTest,VoteRuleTest`
- [ ] 3.2 Nowe testy Context i VoteRule przechodzą: `mvn -pl ta4j-core test -Dtest=PositionSizerContextTest,VoteRuleTest`
- [ ] 3.3 Strażnicy z fazy 1 przechodzą
- [ ] 3.4 Pełna bramka (z SpotBugs) przechodzi: `scripts/run-full-build-quiet.sh`

#### Manual

- [ ] 3.5 Uzasadnienie @SuppressFBWarnings w PositionSizer.Context opisuje faktyczny kształt
- [ ] 3.6 git diff istniejących testów kopii jest pusty
