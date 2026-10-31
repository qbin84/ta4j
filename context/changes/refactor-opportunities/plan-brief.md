# Refactor opportunities (K2, K4 zawężony, strażnicy) — Plan Brief

> Full plan: `context/changes/refactor-opportunities/plan.md`
> Research: `context/changes/refactor-opportunities/research.md`

## What & Why

Spłacamy dwa długi z rankingu research, w wersji, która nie zmienia ogłoszonych kontraktów:
- **K2.** `AnalysisCriterion.chooseBest` ma błąd z niedokończonej poprawki #668: pierwsza strategia jest liczona innym kierunkiem niż reszta. Metoda jest też jedynym powodem importu `core → backtest`.
- **K4.** `PositionSizer.Context` robi pełną kopię strategii przez serializację przy każdym sygnale, a jego dokumentacja twierdzi coś przeciwnego.

Wcześniej zamieniamy dwa niejawne kontrakty (krawędzie importów i format JSON) w testy, żeby zmiany szły pod osłoną.

## Starting Point

- W CI nie ma ani strażnika krawędzi pakietów, ani testu pokrycia serializacji.
- `chooseBest` ma 0 konsumentów produkcyjnych.
- Kontrakt „gettery zwracają kopie” (CF-208/CF-236) jest przypięty asercjami `assertNotSame` w około 10 klasach testów i musi zostać nienaruszony.

## Desired End State

- Bramka PR failuje, gdy kontrakt `core` zyska nowy import „w górę”, albo gdy typ Rule, Indicator lub Criterion przestanie przechodzić round-trip JSON, a nie ma go na jawnej liście wyjątków.
- `chooseBest` liczy wszystkich kandydatów tym samym `tradeType`, odrzuca pustą listę czytelnym wyjątkiem i jest zdeprecjonowany do usunięcia w 0.29.0.
- Backtest z sizerem nie kopiuje strategii przy każdym sygnale. `VoteRule.getRules()` kopiuje reguły jak pozostałe kompozyty.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Zakres | K2 + K4 zawężony + test-strażnik K5 | Każda faza odwracalna osobno; brak zmiany bajtów JSON i kontraktu kopii | Plan |
| Kierunek K4 | Koszt i spójność, kontrakt kopii bez zmian | Kopie to ogłoszony i przetestowany kontrakt CF-208; zysk wydajności nie wymaga jego łamania | Plan (nowe ustalenie: `assertNotSame` w ~10 testach) |
| Forma K2 | Naprawa `:474` + deprecjacja forRemoval, własna implementacja | `executeAndKeepTopK` inaczej rozstrzyga NaN i remisy; delegacja zmieniłaby wyniki | Plan |
| Pusta lista w `chooseBest` | `IllegalArgumentException` z komunikatem | Brak „najlepszej” strategii to błąd wywołania, a nie przypadkowy `NoSuchElementException` | Plan |
| Strażnik krawędzi | Test JUnit czytający importy `core/*.java`, bez nowej zależności | Wzorzec `WalkForwardPublicSincePolicyTest` już istnieje; wchodzi w `verify` | Plan |
| Strażnik K5 | Auto-round-trip + lista wyjątków + `CRITERIA_PACKAGES` | Około 75% typów testowanych automatycznie; nowy typ bez wsparcia failuje | Plan |
| Klasyfikacja CHANGELOG | Naprawy w Fixed, deprecjacja i K4 w Changed | Konwencja sekcji `Unreleased` (`CHANGELOG.md:1-30`) | Plan (wyprowadzone) |
| Termin usunięcia | 0.29.0 | Co najmniej 2 wydania przy cyklu dwutygodniowym; fraza dla skanera | Plan (wyprowadzone) |
| Ranking kandydatów | K4 → K2 → K5 | Koszt długu vs koszt zmiany | Research |

## Scope

**In scope:**
- strażnik importów `org.ta4j.core/*.java` z listą dozwolonych krawędzi;
- strażnik round-trip JSON wszystkich typów z listą wyjątków;
- naprawa, walidacja i deprecjacja `chooseBest`;
- `Context` bez kopii w konstruktorze;
- `VoteRule.getRules()` z kopiami;
- wpisy w CHANGELOG.

**Out of scope:**
- odwrócenie kontraktu kopii („borrowed”);
- podwójne kopie w `BacktestRuntimeReport` i walk-forward;
- utrata podtypu w `StrategySnapshots`;
- usunięcie `chooseBest`;
- delegacja do `executeAndKeepTopK`;
- ujednolicenie serializerów i wersjonowanie JSON;
- naprawa defektów wykrytych przez strażnika;
- K1, K3, K6, K7, K8, K9;
- ArchUnit.

## Architecture / Approach

Strażnicy najpierw (zero zmian produkcyjnych, przechodzą na dziś, failują przy regresji). Potem K2 test-first: test SELL failuje przed naprawą. Na końcu K4, który zmienia tylko wnętrze `Context` i jeden getter, a istniejące asercje kopii zostają bez zmian. Import `AnalysisCriterion → backtest` zostaje na liście dozwolonej z adnotacją do usunięcia w 0.29.0.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Strażnicy kontraktów | 2 testy-polityki: krawędzie importów, round-trip JSON | Strażnik ujawni defekty round-trip, a lista wyjątków będzie długa (~110) |
| 2. K2 `chooseBest` | Spójny `tradeType`, IAE dla pustej listy, deprecjacja, CHANGELOG | Zmiana wyniku dla użytkowników SELL (udokumentowana w Fixed) |
| 3. K4 kopie | Brak kopii na każdy sygnał, spójny `VoteRule`, CHANGELOG | SpotBugs `EI_EXPOSE_REP2` w `Context` (obsługa przez uzasadnione suppress) |

**Prerequisites:** zielona bramka `scripts/run-full-build-quiet.sh` na bazie; Java 25 (`pom.xml:67`).
**Estimated effort:** około 2–3 sesji; faza 1 jest największa (lista wyjątków).

## Open Risks & Assumptions

- Strażnik round-trip może ujawnić typy, które dziś nie przechodzą round-tripu. Trafią na listę jako `KNOWN_ROUND_TRIP_DEFECT`, bez naprawy w tej zmianie.
- Termin 0.29.0 zakłada, że do tego czasu wyjdą co najmniej 2 wydania. Wersję wybiera release-scheduler (LLM), więc nie jest deterministyczna.
- `Context.equals` zmienia się dla kontekstów z tą samą strategią. Nie znaleziono konsumentów, którzy na tym polegają (assumption).

## Success Criteria (Summary)

- Pełna bramka przechodzi po każdej fazie, a dwa nowe testy-strażnicy failują przy celowo wprowadzonej regresji.
- `chooseBest(manager, SELL, …)` wybiera strategię na podstawie jednolitego kierunku, a skaner deprecjacji rozpoznaje termin usunięcia.
- Istniejące testy kontraktu kopii przechodzą bez żadnej modyfikacji.
