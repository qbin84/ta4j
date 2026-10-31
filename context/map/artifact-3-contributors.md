# Obszary do kontaktu i kluczowi kontrybutorzy ta4j (XI 2025 – X 2026)

Analiza z 2026-10-30, oparta na [`artifact-1-territory.md`](artifact-1-territory.md) (aktywność, stabilność, sprzężenia) i [`artifact-2-structure.md`](artifact-2-structure.md) (cykle, warstwy), uzupełniona o autorstwo z gita i dane z GitHuba (tylko odczyt, upstream `ta4j/ta4j`).

## Metodyka

- **Commity:** te same 1826 commitów po filtrach co w mapie terytorium (bez botów, automatyzacji wydań, duplikatów, formatowania i masowych zmian mechanicznych).
- **Agenci:** pominięto commity, których autorem jest agent (Claude, Jules, Copilot), od 4 do 24 na obszar. Commity człowieka ze współautorem-agentem w `Co-authored-by` zostały (łącznie 20), bo to człowiek prowadził zmianę.
- **Tożsamości:** połączono po wspólnych adresach i loginie GitHub. W dokumencie są tylko nazwy, bez adresów.
- **„David Pang” i „TheCookieLab”** występują jako jedna osoba, bo podpisują się tym samym adresem. To mocna przesłanka, ale nie potwierdzenie. Pod nazwą TheCookieLab są głównie scalone PR-y z funkcjami i wydaniami.
- **Tematy aktywności:** przypisane automatycznie po słowach kluczowych z tematów commitów, więc liczby są przybliżone.

## Najważniejsze ustalenie: wielkość zespołu

| Fakt | Wartość |
|---|---|
| Udział jednej osoby w commitach każdego z 5 obszarów | 97–100% |
| PR-y otwarte z konta `TheCookieLab` (scalone w okresie) | 242 z ~266 |
| PR-y scalone przez `TheCookieLab` (merge na `master`) | 172 ze 176 |
| Pozostali ludzie w tych obszarach | 0–1 na obszar (Francesco, Saulo Gil) |

Zespół to w praktyce **jeden maintainer i okazjonalni kontrybutorzy**. Przy takiej wielkości skupienie wiedzy w jednej głowie to norma, a nie ryzyko. Ważniejsze pytanie brzmi: w jakich tematach ta osoba realnie pomoże i czy do konkretnych wątków jest ktoś drugi.

## Top 5 obszarów wymagających kontaktu

**Kryteria:** ryzyko zmiany (poprawki po wydaniu, cykle, złamane granice), decyzje niemożliwe bez autora (zwłaszcza zmiany publicznego API) oraz otwarte wątki z udziałem innych osób.

| # | Obszar | Dlaczego kontakt | Z kim | O co zapytać |
|---|---|---|---|---|
| 1 | **Kontrakt mutacji barów i serii** (`BaseBar`, `BaseBarSeries`, `ConcurrentBarSeries`) | Otwarte zgłoszenia #1642/#1643 bez osoby przypisanej. CF-727 tylko dokumentuje kontrakt. Pętla runtime `BaseBar`↔`BaseBarSeries`. `core` ma 25% poprawek. | Maintainer. `anandaanv` (OnChange: #1503 otwarte, #1504 zamknięty). Zgłoszenie #1216. Francesco (pod-serie, #1410). | Czy naprawa jest w toku i jaki ma kształt (interfejs lub listener zamiast `BaseBar → BaseBarSeries`)? Czy zdarzenia z #1503 wracają jako część tej zmiany? |
| 2 | **Silnik cache wskaźników** (`CachedIndicator`, `RecursiveCachedIndicator`, pakiet główny `indicators`) | 4 błędy po wydaniu w tym samym mechanizmie (#1638, #1646, #1676, #1704). Brak granicy pakietowej wobec rodzin wskaźników. | Maintainer. `vstoyanov` (zgłosił #1666, użytkownik przesuwnych serii). | Jakie są niezmienniki cache (głowa serii, rekurencja, rewizje) i gdzie je spisać? Czy przenieść klasy bazowe do osobnego pakietu? Czy jest scenariusz regresji od użytkownika? |
| 3 | **Badania fal Elliotta** (`analysis/elliott`, `swing`, `indicators/elliott`, dema) | Najaktywniejszy i rosnący obszar. Protokół badań (CF-525, CF-585 – CF-590) istnieje głównie w commitach. 14 typów łamie regułę `indicators/AGENTS.md`. `swing` ma zależności w obie strony z `indicators`. | Maintainer. Saulo Gil (#1528, `ElliottWaveFacade`). `arun-vjkumar` (#1437, `DonchianChannelFacade`). | Formalny wyjątek czy przeniesienie fasad, runnerów i wyników z okresem `@Deprecated`? Wpływ na użytkowników fasad? Gdzie udokumentować protokół badań? |
| 4 | **Krzywa kapitału i semantyka zwrotów** (`CashFlow`, `Returns`, `criteria`, `ReturnRepresentation`) | `CashFlow` to plik nr 1. Najwyższy udział agentów (24 pominięte commity). Enum `ReturnRepresentation` leży w `criteria`, a używa go 17 plików niżej. Globalna `ReturnRepresentationPolicy` to ukryty stan. | Maintainer. **Francesco** (#1405, #1425, #1406, #1439, #1431). `sgflt` (#1219 → #1475). | Czy przeniesienie enuma (zmiana publicznego API) jest akceptowalne? Kto ustawia `setDefaultRepresentation`? Jakie są oczekiwane semantyki trybów `CashFlow` jako wzorzec testów? |
| 5 | **Publiczne API kontraktów `core`** (`Rule`, `Indicator`, `Strategy`, `AnalysisCriterion`, `analysis.cost`, `serialization`) | Najtańsze cięcia cykli to zmiany łamiące API: `chooseBest(BarSeriesManager)`, `Rule.and()/or()` tworzące implementacje, `toJson()` w interfejsach, `CostModel` w `analysis.cost`. Brak pakietów `internal`. | Maintainer. `btezergil` (#1428 reguły z progiem). `nsk90` (#1443 reguły stop z ATR). | Jaka jest polityka zmian łamiących (okres `@Deprecated`, wersja)? Czy wprowadzić pakiet `internal`? Czy metody wygody mogą przejść do fabryk? |

**Poza top 5:** proces wydań i ręczny `CHANGELOG.md`. Jedna osoba ma 92% zmian w `scripts`, a CHANGELOG jest punktem kolizji wszystkich PR-ów. Warto zapytać o fragmenty changelogu per PR.

## Kontrybutorzy według obszarów

### 1. Kontrakt mutacji barów i serii

Commity: 101 ludzkich, 5 agentów pominiętych.

| Osoba | Commity | Okres | Tematy | Support |
|---|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | 98 (97%), w tym 27 poprawek, 5 ze współautorem-agentem | XI 2025 – X 2026 | Współbieżność, mutacje i rewizje: 38. Snapshoty, okna i granice serii: 14 (VII–IX). Walidacja OHLC i budowniczowie: 13. Serializacja barów: 5 (X). CF-236: 8, CF-727. Autor `ConcurrentBarSeries` (#1347). | Główny i jedyny pełny punkt kontaktu dla #1642/#1643. Aktywny do 2026-10-28. |
| **Francesco** | 3 (3%) | 15–21 I 2026 | Pod-serie z zachowaniem `maxBarCount` (#1410, #1412, #1413). `NumFactory` z pierwszego dostępnego baru (#1408). | Wąsko: semantyka pod-serii i limitów barów. |

### 2. Silnik cache wskaźników

Commity: 87 ludzkich, 9 agentów pominiętych.

| Osoba | Commity | Okres | Tematy | Support |
|---|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | 86 (99%), w tym 26 poprawek, 3 ze współautorem-agentem | XII 2025 – X 2026 | Rekurencja, rozgrzewka, głowa serii: 31 (VIII–X). Propagacja i inwalidacja cache: 20 (VII–X). Wydajność bufora: 7 (#1393). CF-729, CF-236. | Jedyna osoba z wiedzą o niezmiennikach cache. Fale prac pokrywają się z błędami po wydaniu. |
| **Francesco** | 1 | I 2026 | Sharpe (#1406), które dotknęło pliku cache przy okazji. | Brak realnego wsparcia w tym obszarze. |

### 3. Badania fal Elliotta

Commity: 430 ludzkich, 4 agentów pominięte.

| Osoba | Commity | Okres | Tematy | Support |
|---|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | 428 (~100%), w tym 72 poprawki | XII 2025 – X 2026 | Protokół badań, ślady, replay, raporty: 188 (CF-525, CF-586–590). Detektory swingów i ZigZag: 41. Dema BTC i kalibracja: 43 (III–VII). Analiza live i wieloramowa: 35 (#1448). Iteracje review: 21. Jądro hipotez topologii i inne: ok. 100. | Jedyny autor protokołu badań. Kontakt konieczny przed zmianami i przed przenoszeniem typów z przestrzeni `indicators`. |
| **Saulo Gil** | 2 | 15–18 V 2026 | Tolerancja Fibonacciego w `ElliottWaveFacade.scenarios()` (#1528). Test fasady bez refleksji. | Użytkownik API fasady: ocena skutków przeniesienia, nie wnętrze badań. |

### 4. Krzywa kapitału i semantyka zwrotów

Commity: 169 ludzkich, 24 agentów pominięte (głównie Claude w `CashFlow`, `CumulativePnL`, `Returns`).

| Osoba | Commity | Okres | Tematy | Support |
|---|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | 164 (97%), w tym 44 poprawki | XI 2025 – X 2026 | CashFlow, PnL i krzywa kapitału: 45. Kryteria ryzyka i zwrotu: 33 (Calmar, Omega, Cpk, drawdown). Okna i granice analizy: 26. Wydajność kryteriów: 6 (#1613). Autor `ReturnRepresentationPolicy` (#1376) i open-position handling (#1434). | Główny kontakt, także w sprawie przeniesienia `ReturnRepresentation` i globalnej polityki. |
| **Francesco** | 5 (3%) | 15 I – 5 II 2026 | `CashFlow` z pozycjami o tym samym indeksie (#1405). Realized equity (#1425). Sharpe (#1406), Sortino (#1439), czas trwania pozycji (#1431). Zamknięte bez merge'a: #1458 (trade-sampled Sharpe), #1427 (equity curve mode). | Drugi realny rozmówca o trybach `CashFlow` i miarach ryzyka. Jedyny obszar z sensownym drugim źródłem wiedzy. |

### 5. Publiczne API kontraktów `core`

Commity: 146 ludzkich, 4 agentów pominięte.

| Osoba | Commity | Okres | Tematy | Support |
|---|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | 144 (99%), w tym 17 poprawek, 9 ze współautorem-agentem | XI 2025 – X 2026 | Serializacja komponentów: 55 (#1373, #1372, #1375, nazwane aktywa). Reguły i śledzenie reguł: 13. Kontrakty kryteriów i strategii: 11. Model transakcji, pozycji i kosztów: 9 (#1434, opłaty, borrowing cost). Wydania i dokumentacja: 7 (#1378, #1521). CF-236: 6. Inne: ok. 40. | Jedyna osoba decydująca o polityce zmian łamiących API. Autor serializacji. |
| **Francesco** | 2 | I–II 2026 | Sharpe i Sortino (kontrakt `AnalysisCriterion`). | Pośrednio: zna kontrakt z perspektywy implementującego. |

## Profile osób

| Osoba | Aktywność | Specjalizacja | Rola przy kontakcie |
|---|---|---|---|
| **David Pang** (także jako TheCookieLab) | Cały rok, wszystkie obszary, ostatni commit 2026-10-28 | Badania Elliotta, serializacja, współbieżność serii, silnik cache, krzywa kapitału. Prowadzi wydania i scala PR-y. | Jeden punkt kontaktu dla każdej decyzji. Warto zgrupować pytania z 5 obszarów w jedną rozmowę według tematów. |
| **Francesco** | I–II 2026 (commity), do VII 2026 (PR-y), 10 scalonych PR-ów | `CashFlow`, Sharpe, Sortino, czas trwania pozycji, pod-serie (`maxBarCount`), `NumFactory` | Drugi kontakt dla obszaru 4 i częściowo 1. Od ok. VII nieaktywny, dostępność do sprawdzenia. |
| **Saulo Gil** | V 2026, 2 commity | `ElliottWaveFacade` | Ocena wpływu zmian API Elliotta. |

**Osoby spoza commitów w tych obszarach** (pomocne przy testach i ocenie wpływu zmian):
- `vstoyanov`: zgłosił #1666 (cache EMA na przesuwnej serii),
- `anandaanv`: propozycja OnChange dla serii (#1503),
- `arun-vjkumar`: autor `DonchianChannelFacade` (#1437),
- `btezergil`: reguły z progiem (#1428),
- `nsk90`: reguły stop z ATR (#1443).

## Zastrzeżenia

- **Autorstwo commitów to nie to samo co wiedza.** Część pracy maintainera powstaje z pomocą agentów (wzmianki o review Codexa, poprawki Claude), więc faktyczne skupienie wiedzy może być jeszcze większe.
- **Połączenie „David Pang” i „TheCookieLab”** warto potwierdzić u maintainera przy pierwszym kontakcie. Jeśli to dwie osoby, w obszarach 1, 4 i 5 pojawia się drugi rozmówca (TheCookieLab: 8, 12 i 22 commity, głównie scalone PR-y z funkcjami).

## Odtworzenie

```sh
python3 context/map/scripts/hot.py /tmp/kept.pkl
python3 context/map/scripts/contributors.py /tmp/kept.pkl /tmp/contrib.json
gh pr list -R ta4j/ta4j --state merged --limit 300 --search "merged:>=2025-10-30" --json author
gh issue view 1642 -R ta4j/ta4j; gh issue view 1643 -R ta4j/ta4j; gh issue view 1666 -R ta4j/ta4j
```

Podział tematyczny wykonano w sesji jednorazowo, na podstawie słów kluczowych z tematów commitów w `contrib.json`.
