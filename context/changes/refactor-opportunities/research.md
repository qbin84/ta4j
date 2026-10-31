---
date: 2026-10-30T14:49:44+01:00
researcher: Tomasz Kubina
git_commit: e26a1be159bfdbb486690e1108e362036261b5c6
branch: docs/territory-map-20261030
repository: ta4j
topic: "Refactor opportunities: które problemy strefy 4 (kontrakty Rule/Strategy/Indicator/AnalysisCriterion) warto naprawić, w jakim kształcie i w jakiej kolejności"
tags: [research, refactor-opportunities, ta4j-core, rule, strategy, analysis-criterion, serialization, backtest, verified]
status: complete
last_updated: 2026-10-30
last_updated_by: Tomasz Kubina
verified_commit: e26a1be159bfdbb486690e1108e362036261b5c6
last_updated_note: "Twierdzenia strukturalne zweryfikowane ast-grep 0.51.0 z kontrolą grepem na commicie e26a1be15; korekty liczb i linii w miejscu („X (raport: Y)”), wynik w sekcji „Weryfikacja twierdzeń (ast-grep)”. Ranking i werdykty intencjonalności bez zmian."
---

# Research: Refactor opportunities w strefie kontraktów strategii

**Data**: 2026-10-30T14:49:44+01:00
**Badacz**: Tomasz Kubina (z asystą Claude, 3 równoległe sub-agenty: obecny kształt, historia i intencjonalność, wykonalność migracji)
**Commit**: e26a1be159bfdbb486690e1108e362036261b5c6
**Gałąź**: docs/territory-map-20261030
**Repozytorium**: ta4j

Ścieżki skrócone: `core/` = `ta4j-core/src/main/java/org/ta4j/core/`. Priory:
- `context/changes/strategy-definition-and-evaluation-analysis/research.md`, dalej „analiza źródłowa” (AŹ): dowody przyjęte bez ponownego wyprowadzania;
- `context/map/repo-map.md` §4–5.

ADR-ów w repo brak. `context/foundation/lessons.md` nie istnieje.

Znaczniki: **[E]** dowód (przeczytany kod, git, PR), **[I]** wnioskowanie, **[U]** nieustalone.

Zakres: eksploracja bez zmian w kodzie. Ranking na końcu jest **propozycją** dla osobnej sesji planowania, a nie decyzją.

## Research Question

Analiza źródłowa celowo zostawiła otwarte pytanie: **które** z udokumentowanych problemów warto naprawić, w jakim docelowym kształcie i w jakiej kolejności. Każdy problem z AŹ jest tu sklasyfikowany jako kandydat (naprawa zmienia strukturę kodu) albo nie-kandydat (wejście do oceny kosztu i wykonalności). Kandydaci są zbadani w trzech wymiarach i uszeregowani.

## Summary

- **9 kandydatów, 15 nie-kandydatów** (lista do audytu poniżej).
- Werdykty intencjonalności dzielą kandydatów na dwie grupy:
  - **przypadkowa złożoność** (K2, K4, K9b, brak resetu w K6, niespójności w K5);
  - **decyzje nośne** (K3 fluent API, K7 świadomie odłożone ujednolicenie, K8 polityka „publiczne API to kontrakt”, K9a PRD).
- **Proponowany ranking:**
  1. **K4**: kopiowanie reguł i strategii przez round-trip serializacji. Powstało przez lint (CF-236), było już częściowo cofnięte dla serii (`f035f9994`), ma rozjechaną dokumentację i koszt na każdy sygnał.
  2. **K2**: `chooseBest` w kontrakcie kryterium. Zawiera błąd z niedokończonej poprawki #668, nie ma konsumentów produkcyjnych, a gotowy zamiennik już istnieje.
  3. **K5 (zawężony)**: ujednolicenie wewnętrznej maszynerii serializacji (4 polityki rozwiązywania klas, rozjazd filtrów pól, ignorowany hook `toDescriptor()`), poprzedzone testem-strażnikiem round-trip po classpath.
- **Odrzuceni:**
  - K1: wygodna fasada, wysoki churn API;
  - K3: decyzja nośna, najbardziej widoczne API;
  - K6: poprawka lokalna, nie strukturalna; do zrobienia jako bugfix;
  - K7: wymaga przeprojektowania pojęcia „rozgrzewki”, czyli innej analizy;
  - K8: świadoma polityka;
  - K9: krawędź `TradingRecord→analysis.cost` jest w sygnaturach abstrakcyjnych, więc naprawa łamie binarnie przy niskim zysku.
- **Wspólny prerekwizyt** wszystkich ścieżek usuwających krawędzie: brak strażnika architektury i zgodności API. W CI nie ma japicmp, revapi, ArchUnit ani jdeps [E]. Pierwszym krokiem każdej ścieżki jest test-charakteryzacja albo strażnik, nie zmiana kodu.

## Lista problemów z AŹ i klasyfikacja (do audytu)

### Kandydaci (naprawa zmienia strukturę kodu)

| ID | Problem | Źródło w AŹ |
|---|---|---|
| K1 | Codec (`toJson/fromJson/toExpression/fromExpression`) jako metody `default`/`static` interfejsów kontraktów, z krawędziami → `serialization`, `named` | TD1, TD2 |
| K2 | `AnalysisCriterion.chooseBest`: orkiestracja backtestu w kontrakcie kryterium, krawędź → `backtest` | TD1, TD3 |
| K3 | Kombinatory `Rule.and/or/xor/negation` tworzące `rules.*`, krawędź → `rules` | TD1 |
| K4 | Kopiowanie reguł i strategii przez round-trip serializacji (`RuleCopies`, `StrategySnapshots`, gettery `BaseStrategy`), krawędź `BaseStrategy` → `rules` | TD7, TD1, weryfikacja #13–14 |
| K5 | Format JSON jako niejawny kontrakt refleksyjny (nazwy pól i parametrów, lista pakietów, rejestr, brak wersji kanonicznej, niespójny filtr `transient`) | TD2, weryfikacja #21–23 |
| K6 | Stan mutowalny w regułach bez kontraktu cyklu życia (`JustOnceRule`) | TD4 |
| K7 | Dwa niepowiązane pojęcia „niestabilności” (strategia vs wskaźnik) | TD6 |
| K8 | Brak granicy public/internal (bundle eksportuje `*org.ta4j.core*`) | TD5, mapa |
| K9 | Krawędzie `analysis` w kontraktach: K9a `AnalysisCriterion` → `analysis.*` (okna), K9b `TradingRecord` → `analysis.cost` | TD1 |

### Nie-kandydaci (wejście do oceny wykonalności i kosztu)

| Problem | Rodzaj | Gdzie wpływa |
|---|---|---|
| `chooseBest:474` liczy 1. strategię bez `tradeType` | błąd zachowania | K2 (naprawa razem z relokacją) |
| `chooseBest` na pustej liście → `NoSuchElementException` (`:473`) | błąd zachowania | K2 |
| Remis w `chooseBest`/`betterThan` nieutrwalony testem | luka testowa | K2 |
| Domyślne metody interfejsów bez implementera referencyjnego (TD5) | luka testowa / API | K1, K3, K4 |
| Rozjazd domyślnego kierunku BUY manager vs executor (TD8) | semantyka API + test | — (decyzja produktowa) |
| 5 z 15 przeciążeń `run(...)` bez bezpośredniego testu | luka testowa | K4 (ścieżka z sizerem) |
| `Rule/Indicator.toExpression/fromExpression` bez testów | luka testowa | K1 |
| `BaseStrategy.and/or/opposite` bez testów semantyki | luka testowa | K3, K4 |
| Reguły złożone testowane tylko z `TradingRecord = null` | luka testowa | K3, K6 |
| Brak `assertThrows` dla `null` w `AndRuleTest`/`OrRuleTest` | luka testowa | K3 |
| `BacktestExecutorTest` bez SELL; granica `isUnstableAt` | luka testowa | K2, K7 |
| Brak narzędzia zgodności API (revapi/japicmp) i testu architektury | brak strażnika | wszyscy (prerekwizyt) |
| Brak raportu JaCoCo dla ścieżki; brak plików golden JSON | brak danych lub strażnika | K5 |
| Współzmiany `CHANGELOG`/`README` z interfejsami | proces | koszt każdej zmiany |
| Korekta sygnału fix-rate (ryzyko strefy to zasięg, nie częstość błędów) | wniosek analityczny | uzasadnienie priorytetów |

## Detailed Findings

### K1. Codec w interfejsach kontraktów

**Obecny kształt**
- [E] Każda metoda codeca w 4 interfejsach to 1–2-liniowa delegacja bez własnej logiki (`core/Rule.java:55-58,105-135`, `core/Strategy.java:256-390`, `core/Indicator.java:127-288`, `core/AnalysisCriterion.java:52-128`).
- [E] Publiczne statyczne fasady już istnieją dla 3 z 4 typów: `StrategySerialization`, `IndicatorSerialization` i `AnalysisCriterionSerialization` mają toJson/fromJson/describe/toExpression/fromExpression. `RuleSerialization` nie ma `toJson/fromJson`, a krok JSON składa dopiero `Rule.java:55-58`.
- [E] Kod `main` prawie nie używa codeca interfejsów: `.toJson()` występuje raz (`core/indicators/lppl/LPPLResidualIndicator.java:176`). Klienci są w testach i przykładach: 184 (raport: ~178) + 28 (raport: 27) wywołań `.toJson()` oraz 50 `Strategy.fromJson(` i 72 `Indicator.fromJson(` w testach.
- [E] Cykle sięgają szerzej, niż podaje TD1:
  - `StrategySerialization` importuje konkretne reguły i wskaźniki dla parsera wyrażeń (`core/serialization/StrategySerialization.java:33-48`);
  - `RuleSerialization` importuje `ATRIndicator`, `CrossIndicator` i `ChainLink` (`:11-14`);
  - `NamedAssetRegistry` importuje `BaseStrategy` i `NamedStrategy` (`core/named/NamedAssetRegistry.java:19-21`).

**Intencjonalność: świadoma wygoda, miejsca nigdy nie rozważano.**
- [E] Helpery przyszły w generowanych przez Codex sub-PR-ach #1341/#1343, scalonych w #1373 (`b62d9bad7`, 2025-11-18). Brak ludzkiej dyskusji o miejscu codeca.
- [E] `Rule#toJson` dodano w #1391 (`a6c37545a`), żeby odciąć `getName()` od serializacji.
- [E] Codec `AnalysisCriterion` i `named` dodał `4aae9a3bf` / #1507 (CF-113).

**Wykonalność**
- Zamiennik już istnieje (fasady `*Serialization`). Brakuje tylko `RuleSerialization.toJson/fromJson`, co jest zmianą addytywną.
- Usunięcie metod łamie API binarnie i źródłowo. Możliwa ścieżka deprecate→remove, bo konwencja `@Deprecated(forRemoval)`, `DeprecationNotifier` i `RemovalReadyDeprecationScanner` w `prepare-release.yml` już istnieje [E].
- Krawędź znika dopiero po usunięciu, około 2 wydania później (cykl dwutygodniowy, `release-scheduler.yml:18`).
- Osłony: `serialization/*SerializationTest` i round-trip support w 51 (raport: 52) testach reguł i 98 (raport: 99) testach wskaźników [E].
- Pierwszy krok: testy round-trip wyrażeń `Rule`/`Indicator` przez metody interfejsu.
- Koszt: M (około 200 miejsc w testach, API widoczne dla użytkownika).

### K2. `chooseBest` w `AnalysisCriterion`

**Obecny kształt**
- [E] `BarSeriesManager` jest używany w `AnalysisCriterion` wyłącznie przez `chooseBest` (import `:20`, użycia `:460,472`).
- [E] Mechanizm „wybierz najlepszą” istnieje w dwóch miejscach:
  - `BacktestExecutor.executeAndKeepTopK` (`core/backtest/BacktestExecutor.java:926,950`): komparator `:1108-1139` z NaN na końcu, remisem po indeksie i jednym `tradeType` dla wszystkich;
  - `BacktestExecutionResult.getTopStrategies` (`:495-578` (raport: `:495-576`); 2 przeciążenia, `:495` i `:532`).
- [I] `chooseBest` to zubożony top-1 tamtej logiki: bez obsługi NaN i z niespójnym `tradeType`.
- [E] 0 konsumentów produkcyjnych; w testach 2 wywołania (AŹ, weryfikacja #1).

**Intencjonalność: przypadkowa (niedokończona poprawka).**
- [E] `chooseBest` pochodzi z 2014 (`ef02ab6c7`), w 2017 trafił do interfejsu (`848c973de`).
- [E] Issue #567 wskazało dokładnie linię `manager.run(bestStrategy)`. Poprawka #668 (`df68757bc`, 2021) zmieniła tylko pętlę (`:478`), a `:474` ma w blame `0e4909983` z 2019.
- [E] Od #1434 (`b112d34b0`, 2026-02) `run(strategy)` używa `getStartingType()`, więc rozjazd zmienił charakter.
- [E] Import `backtest` to efekt uboczny przenosin pakietu w #985 (`22da507e1`, 2023).

**Wykonalność**
- Zamiennik bez nowej abstrakcji: `executeAndKeepTopK(..., topK = 1)`. [U] Równoważności remisów i kolejności nie zweryfikowano.
- Naprawa `:474` to zmiana zachowania (wpis w CHANGELOG), bez zmiany API.
- Usunięcie metody to deprecate→remove. Blast radius: 2 wywołania testowe i 1 delegacja wewnętrzna.
- Osłona: tylko 2 testy BUY.
- Koszt: S.

### K3. Kombinatory `Rule.and/or/xor/negation`

**Obecny kształt**
- [E] Jedyna krawędź Rule→`rules` poza codekiem to 4 importy (`core/Rule.java:6-9`).
- [E] `And/Or/Xor/NotRule` zależą tylko od `Rule`/`TradingRecord`, ale ich gettery wołają `RuleCopies.copy` (`AndRule:60,65`, `OrRule:60,65`, `XorRule:45,50`, `NotRule:44`). Daje to pętlę przechodnią Rule → AndRule → RuleCopies → RuleSerialization → Rule.
- [E] `BaseStrategy.and/or` współdzieli własną regułę, a regułę drugiej strategii kopiuje (`core/BaseStrategy.java:263,269`). `opposite()` współdzieli instancje (`:258`).

**Intencjonalność: świadome fluent API, uzasadnienie nieudokumentowane.**
- [E] Dodane w 2015 (`e1e6a421a`), przeniesione do interfejsu przy migracji na Java 8 (`848c973de`, 2017, „Various internal changes in the API”).
- [E] Bez zmian od 2019.

**Wykonalność**
- Metoda `default` musi nazwać konkretny typ, więc zachowanie fluent API bez krawędzi jest niemożliwe [I].
- Usunięcie to churn użytkowników: ast-grep `$X.and($$$)`/`$X.or($$$)` daje 6/12/29 (raport: 9/12/25) i 7/14/24 (raport: 7/14/19) wywołań (main/test/examples), razem z `Strategy.and/or`. Grep w `main` liczył też Javadoc.
- Część pętli (przez `RuleCopies`) zniknie przy K4.
- Koszt: M, przy wysokim churnie względem zysku.

### K4. Kopiowanie reguł i strategii przez round-trip serializacji

**Obecny kształt**
- [E] `RuleCopies.copy` (`core/rules/RuleCopies.java:42-51`):
  1. `describe` → szukanie serii refleksją (`:67-145`) → `fromDescriptor`;
  2. przy `RuntimeException` zwraca oryginał bez logu.
- [E] `findBarSeries` ma drugą rolę: lokalizację serii w `ChainRule:45,47` (raport: `:44-47`) i `And/OrWithThresholdRule:53-54`.
- [E] 23 call-site'y w 11 plikach (AŹ #13).
- [E] `StrategySnapshots.copy` zawsze buduje `new BaseStrategy(...)` (`core/backtest/StrategySnapshots.java:21-25`). [I] Kopia `NamedStrategy` albo własnej `Strategy` traci podtyp i nadpisane `shouldOperate`.
- [E] Na ścieżce z `PositionSizer` kopia powstaje przy każdym sygnale (AŹ #14: `BarSeriesManager.java:622→698→680→709` → `PositionSizer.java:262`).
- [I] `JustOnceRule.satisfied` nie jest parametrem konstruktora, więc kopia startuje z `false` (niewykonane).
- [E] **Sprzeczność dokumentacji z kodem.** Uzasadnienie `@SuppressFBWarnings` przy `PositionSizer.Context` mówi „the context borrows the run's series view, strategy, trading record…” (`core/backtest/PositionSizer.java:246-248`, `3e51a0aad`, 2026-09-26). Konstruktor kanoniczny kopiuje jednak strategię (`:262`).
- [E] Alternatywnego mechanizmu kopiowania (`copy()`, `with*()`, konstruktory kopiujące) w `rules/`, `Rule`, `Strategy`, `BaseStrategy` i `strategy/` brak.
- [E] Stan wykonania mają tylko `JustOnceRule` i `TriggeredRule` (AŹ TD4), więc pozostałe reguły są w praktyce niemutowalne. Wyjątek: `AbstractRule.setName` (`volatile name`, `core/rules/AbstractRule.java:28`).

**Intencjonalność: przypadkowa (wymuszona lintem), już częściowo cofnięta.**
- [E] Kopie wprowadził sweep SpotBugs EI_EXPOSE_REP CF-236 (David Pang, 2026-07-02/03, #1555):
  - `7c846b3e6` „clear strategy rule accessor debt”,
  - `0d1499846` „clear composite rule accessor debt”,
  - `5dbdca639` „clear backtest strategy ownership debt”.

  Celem było usunięcie `config/spotbugs/known-debt-filter.xml` (`87e7ecc5a`).
- [E] `f035f9994` (2026-08-25) „Revert CF-236 snapshot copies to borrowed-series semantics” cofnął kopie serii na rzecz `@SuppressFBWarnings` z uzasadnieniem. Kopii reguł i strategii nie cofnięto.
- [E] Brak issue, PRD i dyskusji o wydajności kopiowania przez serializację.

**Wykonalność**
- Istniejący szew to wzorzec z `f035f9994`: zwracanie instancji („borrowed”) z udokumentowanym `@SuppressFBWarnings`. Nowa abstrakcja nie jest potrzebna [I].
- Zmiana jest zgodna źródłowo i binarnie. To zmiana semantyki (tożsamość zamiast kopii), więc wymaga wpisu w CHANGELOG.
- Ryzyko: wywołujący, który zmienia zwróconą regułę (np. `setName`), zmieni regułę strategii [I].
- Osłony:
  - `rules/RuleCopiesTest` (7 testów), `TriggeredRuleTest`;
  - brak testu `StrategySnapshots` [E];
  - brak testu, czy `Context` przenosi stan i podtyp;
  - benchmarki tylko w cronie (`test-tag-benchmark.yml`) [E].
- Koszt: M (zmiana lokalna, subtelna semantyka).

### K5. Format JSON jako niejawny kontrakt refleksyjny

**Obecny kształt**
- [E] Rozmiary: `RuleSerialization` 2033 linie, `StrategySerialization` 1280, `IndicatorSerialization` 1069, `AnalysisCriterionSerialization` 551, `NamedAssetRegistry` 1218.
- [E] Wspólne są tylko `ComponentDescriptor`, `ComponentSerialization`, pakietowo-prywatne `ComponentDescriptor.resolveSubtype` (`:104`) oraz `JsonNumberConversions`.
- [E] Każdy serializer duplikuje skan pól, dopasowanie konstruktora i konwersję wartości:
  - Rule `:355,1197,1893-1925`;
  - Indicator `:335,379,628`;
  - Criterion `:270-345,476,518`;
  - Strategy `:996`.
- [E] **4 różne polityki rozwiązywania klas:**
  - Indicator: skan pakietu z preferencją klasy nie-`@Deprecated` (`:915-970`);
  - Rule: jeden pakiet (`:35,331`);
  - Criterion: lista 6 pakietów (`:37-40`);
  - Strategy: `org.ta4j.core` (`:64`).
- [E] **Rozjazd filtrów pól:**
  - Rule pomija `transient` i pola klas abstrakcyjnych (`:1900-1906`);
  - Indicator pomija `transient` (`:898`);
  - Criterion nie pomija żadnego z nich (`:279,302,338`).
- [E] **Hook `toDescriptor()` jest honorowany niespójnie:**
  - `StrategySerialization.describe` używa nadpisania tylko dla `NamedStrategy` (`:213-214`);
  - `Indicator.toDescriptor()` domyślnie woła `IndicatorSerialization.describe(this)` (`core/Indicator.java:160-162`), a sam `IndicatorSerialization` nigdy nie woła `indicator.toDescriptor()` (jedyne `.toDescriptor(` w pliku to `registry.toDescriptor`, `:213`).
  - [I] Nadpisania w 6 (raport: 4) wskaźnikach (`AnchoredVWAPIndicator:187`, `VWAPBandIndicator:133`, `VWAPZScoreIndicator:65`, `AbstractTrendLineIndicator:678`, a także `VWAPStandardDeviationIndicator:86` i anonimowa klasa w `LPPLResidualIndicator:180`) działają przy bezpośrednim wywołaniu `toDescriptor()`, ale nie przez `toJson()`.
- [E] Istniejące haki jawności:
  - nadpisanie `toDescriptor()`;
  - konwencja statycznej fabryki `fromDescriptor` (`StrategySerialization.java:969-990`; 0 implementacji w main);
  - SPI `NamedAssetProvider` (`ServiceLoader`, `NamedAssetRegistry.java:59-71`);
  - `RuleSerialization.isSerializationSupported` (`:57`);
  - adnotacji brak.

**Intencjonalność: refleksja świadoma; niespójności i brak wersji przypadkowe lub nieustalone.**
- [E] Refleksję wybrano w #1341/#1344 („reflection-based … serialization”).
- [E] `-parameters` istniało wcześniej, dla innego celu (#1270, `5a93916ec`, 2025-06). Zależność serializacji od niego nie jest nigdzie zapisana.
- [E] `core/serialization/package-info.java:10-12`: kanoniczny JSON deskryptorów to „durable storage form”, a v2 to warstwa autorska. Dlatego v2 ma wersję.
- [U] Dlaczego kanoniczny format nie ma wersji. Brak uzasadnienia.
- [U]/przypadkowe: lista `CRITERIA_PACKAGES` (`4aae9a3bf`/`0883ff4b9`), różnice w filtrach `transient`, ignorowanie `toDescriptor()` przez wskaźniki. Uzasadnienia nie znaleziono.

**Wykonalność**
- Ujednolicenie maszynerii to zmiana wewnątrz pakietu `serialization`, przy publicznym API bez zmian. Kontraktem jest **format danych**, którego nie widzi żadne narzędzie API.
- Osłony:
  - inline JSON w 5 testach `core` i 3 testach przykładów;
  - round-trip support w 51 (raport: 52) i 98 (raport: 99) testach;
  - **brak testu, który przechodzi po wszystkich typach** (skan classpath) [E];
  - brak plików golden.
- Koszt: M dla strażnika i ujednolicenia wewnętrznego. L dla zmiany formatu, bo zewnętrzny korpus JSON jest [U] (AŹ TD2).

### K6. Stan mutowalny `JustOnceRule` bez resetu

**Obecny kształt**
- [E] `Rule` i `Strategy` nie mają haka cyklu życia (0 trafień dla reset/onRunStart). Cykl życia ma tylko `TradeExecutionModel` (`onBar`, `onRunEnd`).
- [E] `BarSeriesManager.run` tworzy nowy `TradingRecord` na każdy przebieg i używa instancji strategii bezpośrednio (`:659`).
- [E] Walk-forward przekazuje tę samą instancję strategii do każdego okna (`core/backtest/StrategyWalkForwardExecutor.java:220,253`). [I] `JustOnceRule` zadziała więc tylko w pierwszym oknie. Niezweryfikowane wykonaniem.
- [E] `TriggeredRule` sam wykrywa nowy przebieg (`TriggeredRule.java:307-317`).

**Intencjonalność**
- [E] Semantyka „raz i nigdy więcej” jest świadoma: issue #64, Javadoc „Satisfied when the rule is satisfied for the first time, then never again”.
- [E] Brak resetu nigdy nie został zgłoszony. [U] Wniosek opiera się tylko na wyszukiwaniu po słowach kluczowych.
- [E] Autoreset `TriggeredRule` powstał razem z klasą (#1530, `ca70e2777`, 2026-05).

**Wykonalność**
- Wzorzec `TriggeredRule` daje się zastosować lokalnie, bez nowej abstrakcji. To zmiana zachowania w 1 klasie.
- Ogólny cykl życia `Rule` byłby addycją API.
- Koszt: S.

### K7. Dwa pojęcia „niestabilności”

**Obecny kształt**
- [E] Strategia: indeks bezwzględny (`core/BaseStrategy.java:182-183`). Wskaźnik: liczba barów (`core/Indicator.java:51-53`).
- [E] Brak kodu, który wyprowadza jedno z drugiego. Przykłady robią to ręcznie (np. `ta4j-examples/.../SimpleMovingAverageRangeBacktest.java:210-214`).
- [E] `Rule` nie eksponuje grafu wskaźników (`Indicator.getDependencies()` istnieje, `core/Indicator.java:210`).

**Intencjonalność: świadoma, ujednolicenie jawnie odłożone.**
- [E] W #918/#919 (2023) team172011 pisał: „it should be up to the user to decide… this concept must also be implemented in the BarSeriesManager”. nimo23 odpowiadał: „We could do this in a new PR after this has been merged”, ale ten PR nie powstał.
- [E] #919: reguła widzi tylko „outermost indicator”.

**Wykonalność i werdykt: naprawa wymaga przeprojektowania pojęcia biznesowego** (co znaczy „rozgrzewka” strategii: indeks czy liczba barów, wrażliwość na look-ahead, `core/backtest/BacktestExecutor.java:55-59`). Zatrzymuję się tu, bo to przedmiot osobnej analizy. Jedyny krok czysto techniczny bez decyzji pojęciowej to ostrzeżenie typu `CachedIndicator:453-480`, ale ono nie zmienia struktury.

### K8. Brak granicy public/internal

**Obecny kształt**
- [E] Brak `module-info.java`, pakietów `internal`/`impl`/`spi` i adnotacji `@Internal`/`@Beta`. bnd eksportuje `*org.ta4j.core*` (`ta4j-core/pom.xml:129-131`).
- [E] Faktycznym mechanizmem „wewnętrzności” są typy pakietowo-prywatne (np. `StrategySnapshots`, `WindowProjectedTradingRecord`, `JsonNumberConversions`). [E] Dokładna liczba z ast-grep (deklaracja najwyższego poziomu bez `public`/`protected`/`private`): 84 (raport: ~86) z 790 plików.

**Intencjonalność: świadoma polityka.**
- [E] `.github/CONTRIBUTING.md:7` (`3ec95a90f`, 2026-05-07): „Public APIs are contracts… We only accept breaking changes when the value dramatically outweighs the disruption… deprecation shims and migration notes”.
- [E] `JAVA_REVIEW.md:20`: „package-private by default”.
- [E] Eksport OSGi pochodzi z #299 (2018).

**Wykonalność**: zawężenie eksportów łamie konsumentów OSGi i importy. Koszt: L. Cenna jest natomiast część „strażnik”: test listy dozwolonych krawędzi pakietów (koszt S) to prerekwizyt K1, K2, K3 i K9.

### K9. Krawędzie `analysis` w kontraktach

**Obecny kształt**
- [E] `AnalysisWindow` (sealed), `AnalysisContext` (record) i `OpenPositionHandling` (enum) nie importują nic z `org.ta4j`. To liście bez cyklu.
- [E] Około 230 (raport: ~250) linii projekcji okien to 10 prywatnych metod statycznych w interfejsie (`core/AnalysisCriterion.java:223-452` (raport: `:203-450`)), oparte na pakietowo-prywatnym `WindowProjectedTradingRecord` (`:24`).
- [E] `CostModel` importuje `core.Position` (`core/analysis/cost/CostModel.java:6`). `TradingRecord` używa go w **abstrakcyjnych** sygnaturach (`core/TradingRecord.java:217,222`). Prawdziwy cykl to `core`↔`analysis.cost`.

**Intencjonalność**
- [E] K9a jest świadome: PRD `docs/prd/analysiscriterion-windowed-api.md` (`7725b2991`, potem usunięty `e825db6bd`) wybrał metody `default` dla zgodności wstecznej (#1470).
- [E] K9b jest przypadkowe: #1160 „Tradingrecord getters” („missing some getters”).

**Wykonalność**: K9b wymaga przeniesienia `CostModel` (interfejs) do `core`. Most przez zdeprecjonowany podtyp jest możliwy [I], ale dotyka wszystkich modeli kosztów i implementacji `TradingRecord`. Koszt: L przy niskim zysku. K9a nie tworzy cyklu, więc nie ma czego naprawiać strukturalnie.

## Refactor opportunities

Kryterium: koszt długu (dowody szkody, częstość dotykania, przypadkowość) wobec kosztu zmiany (blast radius, łamanie API, istniejące osłony). Kandydaci z decyzją nośną albo wymagający przeprojektowania pojęć mają karę.

Wspólny prerekwizyt dla #2 (i dla przyszłych K1, K3, K9): **test architektury z listą dozwolonych krawędzi pakietów**. Ma przypiąć obecne krawędzie kontraktów i failować na nowej krawędzi w górę. Dziś nie istnieje [E], a analiza jdeps żyje tylko w dokumentach (`context/map/artifact-2-structure.md`).

### 1. K4: kopie przez serializację → semantyka „borrowed” dla reguł i strategii

- **Obecny → docelowy kształt.** Dziś gettery `BaseStrategy`, kompozytów reguł i `PositionSizer.Context` robią pełny round-trip serializacji. Na ścieżce sizera dzieje się to przy każdym sygnale, z cichym fallbackiem do oryginału i z utratą podtypu strategii. Docelowo: zwracanie instancji („borrowed”) z udokumentowanym `@SuppressFBWarnings`, tak jak już zrobiono dla serii w `f035f9994`. Rozważyć jawną kopię tylko tam, gdzie posiadanie stanu ma znaczenie (`JustOnceRule`, `TriggeredRule`).
- **Dlaczego #1.**
  - Dług jest udowodniony i przypadkowy: wymuszony lintem, bez dyskusji, a ten sam autor cofnął już analogiczny wzorzec dla serii.
  - Dokumentacja przeczy kodowi (`PositionSizer.java:246-248` vs `:262`).
  - Kopia gubi podtyp i stan [I].
  - Koszt jest w gorącej ścieżce.
  - Pętla Rule → AndRule → RuleCopies → RuleSerialization → Rule spina krawędzie z TD1.
  - Zmiana jest zgodna źródłowo i binarnie. Szew już istnieje.
- **Blast radius.** 23 call-site'y w 11 plikach. `StrategySnapshots` ma 6 call-site'ów w 3 klasach backtestu. Wszystko wewnątrz `core`, bez zmian sygnatur. Semantyka tożsamości jest obserwowalna dla użytkowników (CHANGELOG).
- **Szkic ścieżki.**
  1. Testy-charakteryzacje (patrz pierwszy krok).
  2. `StrategySnapshots`: najpierw `PositionSizer.Context`, gdzie dokumentacja już mówi „borrows”, potem raport runtime i walk-forward. Każdy krok osobno i odwracalnie.
  3. Gettery `BaseStrategy`.
  4. Gettery kompozytów.
  5. Na końcu zdecydować, czy `RuleCopies.copy` zostaje dla przypadków ze stanem, czy znika, a `findBarSeries` zostaje jako helper lokalizacji serii.
- **Pierwszy krok-prerekwizyt.** Testy-charakteryzacje dla `PositionSizer.Context.strategy()`, `BaseStrategy.getEntryRule()` i getterów `AndRule`. Mają przypiąć:
  - tożsamość albo kopię,
  - fallback dla reguły-lambdy,
  - zachowanie podtypu `NamedStrategy`,
  - przeniesienie albo utratę stanu `JustOnceRule`.

  Dziś żaden test tego nie pilnuje [E].

### 2. K2: `chooseBest` z kontraktu kryterium → `backtest`

- **Obecny → docelowy kształt.** Dziś to metoda `default` w `AnalysisCriterion` z jedyną krawędzią `core→backtest` i błędem `:474` z niedokończonej poprawki #668. Docelowo: wybór najlepszej strategii wyłącznie przez istniejące `BacktestExecutor.executeAndKeepTopK` / `BacktestExecutionResult.getTopStrategies`, a `chooseBest` zdeprecjonowane `forRemoval` ze wskazaniem zamiennika.
- **Dlaczego #2.**
  - Najlepszy stosunek zysku do kosztu: 0 konsumentów produkcyjnych, 2 wywołania testowe, zamiennik istnieje.
  - Usuwa całą krawędź `AnalysisCriterion → backtest`, czyli jedną z „pojedynczych krawędzi w górę”, które według mapy spinają splot pakietów (`context/map/repo-map.md:171`).
  - Przy okazji domyka prawdziwy błąd.
  - Niżej niż K4, bo bieżąca szkoda jest mała (metoda prawie nieużywana), a krawędź znika dopiero po usunięciu, czyli z opóźnieniem 2+ wydań.
- **Blast radius.** `core/AnalysisCriterion.java:20,455-495`, `AbstractAnalysisCriterionTest:50,58`. API publiczne usuwane przez deprecate→remove.
- **Szkic ścieżki.**
  1. Test-charakteryzacja SELL.
  2. Naprawa `:474` (`run(bestStrategy, tradeType)`) i strażnik pustej listy, z wpisem w CHANGELOG.
  3. `@Deprecated(forRemoval)` z Javadoc „use `BacktestExecutor.executeAndKeepTopK`”.
  4. Przeniesienie testów na zamiennik.
  5. Usunięcie po terminie wykrytym przez `RemovalReadyDeprecationScanner`.
  6. Wpis w teście architektury, że krawędź `core→backtest` ma zniknąć.
- **Pierwszy krok-prerekwizyt.** Test, który dziś failuje: `tradeType = SELL` i 2 strategie z domyślnym BUY, gdzie pierwsza wygrywa tylko dzięki asymetrii `:474`/`:478`. Do tego jedna kontrola: czy remisy i NaN w `executeAndKeepTopK` dają ten sam wybór co `chooseBest` ([U] dziś).

### 3. K5 (zawężony): ujednolicenie wewnętrznej maszynerii serializacji pod strażnikiem

- **Obecny → docelowy kształt.** Dziś 4 serializery mają 4 polityki rozwiązywania klas, różne filtry pól (`transient`), zduplikowany skan pól i dopasowanie konstruktorów, a hook `toDescriptor()` wskaźników jest ignorowany przez `toJson()`. Docelowo: jedna pakietowo-prywatna polityka skanu pól, rozwiązywania typów i honorowania hooka. Szwy już istnieją: `ComponentDescriptor.resolveSubtype` i `JsonNumberConversions`. Format JSON i publiczne API bez zmian. **Poza zakresem:** wersjonowanie formatu kanonicznego i przejście na deskryptory jawne, bo to decyzje polityki formatu.
- **Dlaczego #3.**
  - Kontrakt danych dotyczy 69 + 338 + 70 typów (AŹ #18), a jedyną osłoną są testy per klasa.
  - Rozjazdy są przypadkowe (brak uzasadnienia w historii) i tworzą realne ryzyko: pole `transient` w kryterium, nadpisanie `toDescriptor()` niedziałające w `toJson()`, nowy podpakiet kryteriów wypadający po cichu.
  - Niżej niż #1 i #2, bo koszt zmiany jest wyższy (około 5 tys. linii w 4 plikach) i bo bez strażnika każda zmiana grozi cichą zmianą formatu.
- **Blast radius.** Pakiet `serialization` (5 plików), pośrednio format JSON wszystkich komponentów. Wewnątrz zero zmian publicznych sygnatur.
- **Szkic ścieżki.**
  1. Strażnik (pierwszy krok).
  2. Ujednolicenie rozwiązywania typów do `resolveSubtype`.
  3. Wspólny skaner pól z jedną polityką filtrów.
  4. Honorowanie `toDescriptor()` w `IndicatorSerialization`.

  Każdy krok osobno, z porównaniem wyniku strażnika przed i po.
- **Pierwszy krok-prerekwizyt.** Test skanujący classpath: każdy konkretny `Rule`, `Indicator` i `AnalysisCriterion` z `main` robi round-trip albo jest na jawnej liście wyjątków, a każde kryterium leży w pakiecie z `CRITERIA_PACKAGES`. Najlepiej z zapisem JSON jako golden, żeby wykrywać zmiany formatu. Dziś takiego testu nie ma [E].

### Rozważeni i odrzuceni

| Kandydat | Dlaczego poza rankingiem |
|---|---|
| K1 codec w interfejsach | Delegacje są cienkie i nieszkodliwe. Zysk to tylko usunięcie krawędzi, a koszt to około 200 miejsc w testach, widoczne API i usunięcie dopiero po 2+ wydaniach. Jeśli kiedyś: najpierw addytywne `RuleSerialization.toJson/fromJson`, żeby fasady były kompletne. |
| K3 kombinatory `Rule` | Świadome fluent API od 2015, najbardziej widoczne dla użytkowników. Krawędzi nie da się usunąć bez łamania API. Część pętli zniknie przez K4. |
| K6 `JustOnceRule` | Naprawa jest lokalna (wzorzec `TriggeredRule`) i behawioralna, nie strukturalna, koszt S. Warto ją zrobić jako osobny bugfix z testem dwukrotnego `run`, w kolejności zależnej od K4, bo kopia wpływa na stan. |
| K7 dwie niestabilności | Wymaga przeprojektowania pojęcia „rozgrzewki”, świadomie odłożonego w #918/#919. To przedmiot innej analizy. |
| K8 granica public/internal | Świadoma, zapisana polityka (`CONTRIBUTING.md:7`), koszt L i łamanie OSGi. Zostaje tylko jako źródło strażnika krawędzi (prerekwizyt). |
| K9a/K9b krawędzie `analysis` | K9a to decyzja z PRD bez cyklu. K9b to prawdziwy cykl, ale w abstrakcyjnych sygnaturach `TradingRecord`, więc przeniesienie łamie binarnie wszystkich implementerów przy małym zysku. Najwyżej zapisać jako dozwoloną krawędź w strażniku. |

## Weryfikacja twierdzeń (ast-grep)

Metoda: `ast-grep 0.51.0` na commicie `e26a1be15` (`run -l java -p` oraz `scan` z regułami `kind`/`has`/`inside`/`regex`). Każde zero z ast-grep zostało potwierdzone klasycznym `grep`. Przy różnicy liczb niż grep rozstrzyga ast-grep, bo grep liczy też Javadoc i komentarze. Korekty liczb i linii naniesiono w treści w formacie „X (raport: Y)”, poza sekcją „Refactor opportunities”, której nie zmieniano.

| # | Twierdzenie (kandydat) | Werdykt | Dowód (plik:linia) | Metoda |
|---|---|---|---|---|
| V1 | `RuleCopies.copy`: 23 call-site'y w 11 plikach (K4) | potwierdzone | 23 / 11 (grep 23) | `-p 'RuleCopies.copy($$$)'` |
| V2 | `StrategySnapshots.copy`: 6 call-site'ów w 3 klasach (K4) | potwierdzone | `PositionSizer:262,272`, `BacktestRuntimeReport:109,115`, `StrategyWalkForwardExecutionResult:77,98` | `-p 'StrategySnapshots.copy($$$)'` |
| V3 | `StrategySnapshots.copy` zawsze buduje `new BaseStrategy` (K4) | potwierdzone | `backtest/StrategySnapshots.java:23` (jedyne `new` w pliku) | `-p 'new BaseStrategy($$$)'` |
| V4 | `RuleCopies.copy` przy `RuntimeException` zwraca oryginał bez logu (K4) | potwierdzone | `rules/RuleCopies.java:48-49` (`catch (RuntimeException ex) { return source; }`) | `kind: catch_clause` inside `copy` |
| V5 | `findBarSeries` w `ChainRule:44-47` i `And/OrWithThresholdRule:53-54` (K4) | doprecyzowane | `ChainRule:45,47`, `AndWithThresholdRule:54`, `OrWithThresholdRule:53` | `-p 'RuleCopies.findBarSeries($$$)'` |
| V6 | Gettery kompozytów kopiują (`AndRule:60,65`, `OrRule:60,65`, `XorRule:45,50`, `NotRule:44`) (K4) | potwierdzone + **doprecyzowane** | Wszystkie 16 getterów zwracających `Rule`/`List<Rule>` w `rules/**` i `BaseStrategy` (grep 16): 15 kopiuje przez `RuleCopies.copy`. **Wyjątek: `VoteRule.getRules()` zwraca `List.copyOf(rules)`** (`rules/VoteRule.java:98`), czyli płytką kopię listy ze współdzielonymi instancjami reguł | reguła `method_declaration` z `type ~ Rule\|List<Rule>` i `name ~ ^get` |
| V7 | Brak alternatywnego mechanizmu kopiowania (`copy()`, `with*()`, konstruktory kopiujące) (K4) | potwierdzone | Jedyne `copy` to `RuleCopies.copy` (`:42`). Konstruktory z 1 parametrem `Rule` to opakowania, nie konstruktory kopiujące: `JustOnceRule:31`, `NotRule:29`, prywatny `ElliottScenarioTimeStopRule:37`. Konstruktorów kopiujących (parametr tego samego typu): 0 (grep 0). `TriggeredRule:448-449` klonuje tylko wewnętrzne tablice | reguła `name ~ copy\|with*\|clone` + `constructor_declaration`; grep `Typ(Typ x)` |
| V8 | `JustOnceRule.satisfied` nie jest parametrem konstruktora (K4/K6) | potwierdzone | Konstruktory `JustOnceRule(Rule)` `:31` i `JustOnceRule()` `:41` | `kind: constructor_declaration` |
| V9 | `BaseStrategy.and/or` współdzieli własną regułę i kopiuje cudzą; `opposite()` współdzieli (K3/K4) | potwierdzone | `BaseStrategy.java:263,269` (`entryRule.and(strategy.getEntryRule())`; getter kopiuje `:156-158`), `:258` | odczyt + V6 |
| V10 | `JustOnceRule` bez resetu vs `TriggeredRule` z autoresetem (para lustrzana, K6) | potwierdzone | `JustOnceRule`: 0 metod `*reset*` (grep 0). `TriggeredRule`: 7 metod z `reset` w nazwie, od `:308` (`resetStagesOnEvaluationRestart`) | `method_declaration name ~ (?i)reset` |
| V11 | `BarSeriesManager` w `AnalysisCriterion` tylko przez `chooseBest` (K2) | potwierdzone + doprecyzowane | Typ użyty tylko w `:460,472` (import `:20`). `AnalysisCriterion` to jedyny plik najwyższego poziomu `core/*.java` z importem `backtest` (grep: poza nim tylko Javadoc `{@link}` w `package-info.java:24,26`) | `kind: type_identifier`, `kind: import_declaration` |
| V12 | Asymetria `:474` vs `:478` (K2) | potwierdzone | `AnalysisCriterion.java:474 manager.run(bestStrategy)`, `:478 manager.run(currentStrategy, tradeType)` | `$M.run($$$)` inside `chooseBest` |
| V13 | 0 konsumentów produkcyjnych `chooseBest` (K2) | potwierdzone | 0 wywołań poza `AnalysisCriterion.java` (grep 0) | `-p '$R.chooseBest($$$)'` |
| V14 | Zakres `chooseBest` `:455-495` (K2) | doprecyzowane | `:460-462` i `:472-487`. `:495` to `betterThan` | `method_declaration name = chooseBest` |
| V15 | `executeAndKeepTopK` `:926,950`, komparator `:1108-1139`; `getTopStrategies` `:495-576` (K2) | doprecyzowane | `executeAndKeepTopK`: 2 publiczne (`:926-932`, `:950-956`) + prywatne `:958-1083`. `createBestFirstComparator` `:1108-1139`. `getTopStrategies` `:495-505`, `:532-578` | `method_declaration name = …` |
| V16 | Rozmiary serializerów (2033/1280/1069/551, `NamedAssetRegistry` 1218) i „około 5 tys. linii w 4 plikach” (K5) | potwierdzone | `wc -l`: 2033 + 1280 + 1069 + 551 = 4933 | `wc -l` |
| V17 | 4 polityki rozwiązywania klas (K5) | potwierdzone | Rule `RULE_PACKAGE` `:35,331`; Strategy `STRATEGY_PACKAGE` `:64,1068`; Criterion lista `:37-40`; Indicator skan classpath i preferencja nie-`@Deprecated` `:926-933,951-967` | grep stałych + odczyt |
| V18 | `resolveSubtype` (`ComponentDescriptor:104`) używany przez Rule `:331`, Criterion `:437`, Strategy `:1067` (K5) | potwierdzone | jak w twierdzeniu, plus wewnętrzne przeciążenie `ComponentDescriptor:83`. `IndicatorSerialization`: 0 (grep 0) | `-p 'ComponentDescriptor.resolveSubtype($$$)'` |
| V19 | Filtr `transient`: Rule i Indicator tak, Criterion nie (para lustrzana, K5) | potwierdzone | `Modifier.isTransient`: `RuleSerialization:1900`, `IndicatorSerialization:898`; `AnalysisCriterionSerialization` 0, `StrategySerialization` 0 (grep 0). Pomijanie pól klas abstrakcyjnych: tylko Rule `:1905` | `-p 'Modifier.isTransient($$$)'`, `Modifier.isAbstract($$$)` |
| V20 | Nadpisanie `toDescriptor()` w 4 wskaźnikach i `NamedStrategy`; `IndicatorSerialization` go nie woła (K5) | **doprecyzowane (szerzej)** | Nadpisań we wskaźnikach jest 6: `AnchoredVWAPIndicator:187`, `VWAPBandIndicator:133`, `VWAPStandardDeviationIndicator:86`, `VWAPZScoreIndicator:65`, `AbstractTrendLineIndicator:678`, anonimowa w `LPPLResidualIndicator:180`. Do tego `NamedStrategy:509` oraz 4 domyślne w interfejsach. Wywołania `x.toDescriptor()` w `serialization/*`: na komponencie tylko `StrategySerialization:214`, pozostałe 8 to `registry.toDescriptor(...)` (grep zgodny) | reguła `method_declaration name = toDescriptor, params = ()`; `-p '$X.toDescriptor($$$)'` |
| V21 | Konwencja statycznej fabryki `fromDescriptor`: 0 implementacji w komponentach (K5) | potwierdzone | 5 statycznych `fromDescriptor` w `main`, wszystkie w `serialization/*` (`ACS:100`, `IS:228`, `SS:731`, `RS:242,266`). Poza `serialization/`: 0 (grep 0) | reguła `name = fromDescriptor` + `modifiers ~ static` |
| V22 | Brak adnotacji; SPI `NamedAssetProvider` przez `ServiceLoader` (K5) | potwierdzone | `annotation_type_declaration` w `main`: 0 (grep `@interface` 0); `NamedAssetRegistry.java:71` | `kind: annotation_type_declaration`; `-p 'ServiceLoader.load($$$)'` |
| V23 | Round-trip support w 52 testach reguł i 99 testach wskaźników (K1/K5) | doprecyzowane | 51 i 98 plików testowych (bez samych klas support), grep zgodny | `kind: identifier` = nazwa klasy support |
| V24 | Brak testu skanującego classpath po wszystkich typach (K5) | potwierdzone | `getResources`/`Files.walk`/`list` w testach występuje tylko w fixture'ach Elliotta i `MissingDependencyFixture` (ładowanie sondy). Testów `*All*`/`*Every*`/`*Coverage*` dla serializacji: 0 | reguła `method_invocation name ~ getResources\|walk\|list\|loadClass\|forName`; grep `ClassGraph\|Reflections\|Files.walk` |
| V25 | `.toJson()`: main 1, testy ~178, przykłady 27; `Strategy.fromJson` 50, `Indicator.fromJson` 72 (K1) | doprecyzowane | main 1 (`LPPLResidualIndicator:176`), testy 184, przykłady 28; `fromJson` 50/72 w testach, 0 w main i przykładach (grep zgodny) | `-p '$X.toJson()'`, `-p 'Strategy.fromJson($$$)'` |
| V26 | `RuleSerialization` nie ma `toJson/fromJson` (K1) | potwierdzone | 0 deklaracji (grep: 1 trafienie, odwołanie do innej klasy, nie deklaracja) | `method_declaration name ~ toJson\|fromJson` |
| V27 | Krawędź Rule→`rules` to 4 importy `:6-9`; `.and(`/`.or(` 9/12/25 i 7/14/19 (K3) | doprecyzowane | importy `Rule.java:6,7,8,9`; `.and(` 6/12/29, `.or(` 7/14/24. `.xor(` 0/9/0 i `.negation()` 0/7/0 (zera w main i przykładach potwierdzone grepem) | `kind: import_declaration`; `-p '$X.and($$$)'` |
| V28 | `Rule`/`Strategy` bez haka cyklu życia; walk-forward używa tej samej instancji (K6) | potwierdzone | 0 metod `reset/onRunStart/onRunEnd/onBar` w `Rule`, `Strategy`, `BaseStrategy` (grep 0); `StrategyWalkForwardExecutor.java:220,253` | `method_declaration name ~ (?i)reset\|onRun…`; `-p 'seriesManager.run($$$)'` |
| V29 | Brak `module-info` i pakietów `internal/impl/spi`; ~86/790 typów pakietowo-prywatnych (K8) | potwierdzone / doprecyzowane | `module-info.java`: 0; katalogi `internal/impl/spi`: 0 (`find`); typy pakietowo-prywatne: 84 z 790 | reguła deklaracji najwyższego poziomu bez modyfikatora dostępu |
| V30 | `AnalysisWindow` (sealed), `AnalysisContext` (record), `OpenPositionHandling` (enum) nie importują `org.ta4j` (K9) | potwierdzone | `:29`, `:36`, `:11`; importy `org.ta4j`: 0 (grep 0) | `kind: import_declaration` |
| V31 | `WindowProjectedTradingRecord` pakietowo-prywatny, jedynym użytkownikiem `AnalysisCriterion`; projekcja `:203-450` (K9) | potwierdzone / doprecyzowane | `WindowProjectedTradingRecord.java:24` (`final class`); referencje typu tylko w `AnalysisCriterion.java`; 10 prywatnych statyków `:223-452` | `kind: type_identifier`; `modifiers ~ private static` |
| V32 | `TradingRecord` ma abstrakcyjne gettery `CostModel` (K9) | potwierdzone | `TradingRecord.java:217,222` | `-p 'CostModel $N();'` |
| V33 | 5 × `@Deprecated(forRemoval = true)` w `core` (globalne) | potwierdzone | 5 (grep 5) | `kind: annotation`, regex `forRemoval = true` |

### Wpływ na ranking (do decyzji na etapie planowania)

Weryfikacja nie obaliła żadnego twierdzenia, na którym stoi ranking. Trzy wyniki zmieniają jednak wagę argumentów, a jedno miejsce w sekcji rankingu ma nieścisły zakres linii:

- **K4 (#1), V6.** Semantyka „borrowed” już istnieje w jednym kompozycie: `VoteRule.getRules()` zwraca listę ze współdzielonymi instancjami reguł, a 15 pozostałych getterów kopiuje. To dodatkowa niespójność w obrębie `rules/**` i kolejny precedens obok `f035f9994`. *Do decyzji na etapie planowania:* czy docelowy kształt K4 ma ujednolicić także `VoteRule`, i w którą stronę.
- **K5 (#3), V20.** Hook `toDescriptor()`, którego `toJson()` nie honoruje, dotyczy 6, a nie 4 wskaźników, w tym klasy anonimowej w `LPPLResidualIndicator:180`. Zakres ryzyka „cichego rozjazdu” jest więc szerszy. *Do decyzji na etapie planowania:* czy krok „honorowanie `toDescriptor()`” wymaga osobnego testu zgodności dla tych 6 typów przed zmianą.
- **K2 (#2), V11/V14.** Potwierdzone: `AnalysisCriterion` jest jedynym plikiem `core/*.java` z importem `backtest`, więc usunięcie `chooseBest` likwiduje krawędź `core→backtest` na poziomie kodu. Zostają linki Javadoc w `package-info.java:24,26`. W sekcji rankingu blast radius podaje `core/AnalysisCriterion.java:20,455-495`; dokładny zakres metod to `:460-462`, `:472-487` (sekcji rankingu celowo nie zmieniono). *Do decyzji na etapie planowania:* czy linki Javadoc w `package-info` też przenieść, bo nie tworzą zależności kompilacji.
- **K1 (odrzucony), V25.** Churn jest wyższy, niż podano (`.toJson()` 184 w testach i 28 w przykładach), co wzmacnia odrzucenie. Bez wpływu na ranking.

## Code References

- `core/rules/RuleCopies.java:42-51,67-145` – kopia przez serializację, cichy fallback, refleksyjne szukanie serii
- `core/backtest/StrategySnapshots.java:21-25` – kopia strategii jako `new BaseStrategy`
- `core/backtest/PositionSizer.java:246-248,262,272` – „borrows” w uzasadnieniu vs kopia w konstruktorze
- `core/AnalysisCriterion.java:20,460-487` (raport: `:455-495`) – `chooseBest` (2 przeciążenia: `:460-462`, `:472-487`), import `backtest`, asymetria `:474/:478`
- `core/backtest/BacktestExecutor.java:926,950,1108-1139` – `executeAndKeepTopK` i komparator
- `core/backtest/BacktestExecutionResult.java:495-578` (raport: `:495-576`) – `getTopStrategies`
- `core/serialization/IndicatorSerialization.java:213,243-295,898,915-970` – describe bez hooka, filtr `transient`, rozwiązywanie typów
- `core/serialization/AnalysisCriterionSerialization.java:37-40,270-345` – lista pakietów, skan pól bez filtra `transient`
- `core/serialization/RuleSerialization.java:35,57,331,1893-1925` – polityka pakietu, skan pól
- `core/serialization/StrategySerialization.java:33-48,213-214,969-990` – importy konkretnych reguł, hook tylko dla `NamedStrategy`, konwencja `fromDescriptor`
- `core/Indicator.java:160-162` – domyślne `toDescriptor()`
- `core/rules/TriggeredRule.java:307-317` – wzorzec autoresetu
- `core/TradingRecord.java:217,222`, `core/analysis/cost/CostModel.java:6` – cykl `core`↔`analysis.cost`
- `ta4j-core/pom.xml:129-131` – eksport bnd
- `.github/workflows/test.yml:39-40`, `scripts/run-full-build-quiet.sh:381` – bramka PR (`license:check spotless:check verify`: SpotBugs, JaCoCo)

## Architecture Insights

- **Bramka PR nie widzi kontraktów, które się tu liczą.** `verify` obejmuje SpotBugs i JaCoCo (linie i gałęzie 0.80; `core` gałęzie 0.75) [E]. Nie ma w nim:
  - zgodności binarnej,
  - krawędzi pakietów,
  - formatu JSON.

  `semver-rules-override.txt` to fragment promptu LLM dla release-schedulera, a nie test zgodności [E].
- **Konwencja deprecate→remove ma oprzyrządowanie.** `@Deprecated(since, forRemoval)` (5 w `core`), `DeprecationNotifier`, `RemovalReadyDeprecationScanner` w `prepare-release.yml`, cykl wydań dwutygodniowy, wersja przed 1.0 (`pom.xml:6`). Odwracalne ścieżki usuwania API są więc tanie proceduralnie, ale wolne (2+ wydania).
- **Część długu w strefie wprowadziły generatory i linty, a nie decyzje projektowe:**
  - codec w interfejsach przez sub-PR-y Codex bez ludzkiego review miejsca;
  - kopie przez sweep SpotBugs.

  Ten sam maintainer już raz cofnął skutek lintu (`f035f9994`). To precedens dla K4.

## Historical Context (from prior changes)

- `context/changes/strategy-definition-and-evaluation-analysis/research.md` to wejście tej analizy. Jej ustalenia są przyjęte jako dowody. Doprecyzowania z tej analizy:
  - TD7 [U] „czy kopia przenosi stan”: [I] nie przenosi, bo `satisfied` nie jest parametrem konstruktora. Niewykonane.
  - TD1: cykle obejmują też importy konkretnych reguł i wskaźników w `StrategySerialization`/`RuleSerialization` oraz `NamedAssetRegistry → BaseStrategy/NamedStrategy`.
  - TD3 i open question 6 („czy `:474` jest zamierzone”): nie. To niedokończona poprawka #668.
  - Open question 8 (`transient` w kryteriach): uzasadnienia brak, przypadkowe lub [U].
- `context/archive/`: brak wcześniejszych zmian.

## Related Research

- `context/changes/strategy-definition-and-evaluation-analysis/research.md`
- `context/map/repo-map.md`, `context/map/artifact-1-territory.md`, `context/map/artifact-2-structure.md`

## Open Questions

1. Czy remisy i NaN w `executeAndKeepTopK` wybierają tę samą strategię co `chooseBest` (warunek bezpiecznej deprecjacji K2).
2. Czy ktoś poza repo polega na semantyce kopii w getterach (K4). Zewnętrzni konsumenci są nieznani.
3. Zakres korpusu JSON przechowywanego przez użytkowników (K5). Rozstrzyga, czy ujednolicenie może zmienić bajty wyjścia.
4. Które kryteria mają pola `transient` (K5). Nie sprawdzono.
5. Czy walk-forward faktycznie wyłącza `JustOnceRule` po pierwszym oknie (K6). Wnioskowanie bez uruchomienia.
6. Brakujące źródła: treść ticketów CF-236/CF-113/CF-208 (wewnętrzny tracker), pełny opis PR #1555 i wątki review #1507.
