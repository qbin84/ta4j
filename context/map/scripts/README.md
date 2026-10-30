# Skrypty analizy historii gita

Skrypty do raportu `../artifact-1-territory.md`. Uruchamiaj z katalogu głównego repo; okno czasu (`SINCE`) ustawia `hot.py`.

| Krok | Polecenie | Wynik |
|---|---|---|
| 1. Parsowanie i filtry (boty, duplikaty, formatowanie, masowe zmiany, szum, zmiany nazw) | `python3 context/map/scripts/hot.py /tmp/kept.pkl` | `kept.pkl` – wejście dla pozostałych |
| 2. Ranking obszarów i plików | `python3 context/map/scripts/agg.py /tmp/kept.pkl 1` (oraz `2` dla głębszych pakietów) | stdout |
| 3. Rozkład miesięczny | `python3 context/map/scripts/time.py /tmp/kept.pkl` | stdout |
| 4. Kampanie za skokami | `python3 context/map/scripts/camp.py /tmp/kept.pkl` | stdout |
| 5. Poprawki i reverty | `python3 context/map/scripts/fix.py /tmp/kept.pkl /tmp/fix.json` | stdout + `fix.json` |
| 6. Przypisanie poprawek do PR-ów | `git rev-list --first-parent master --merges --since='13 months ago' --format='%H %s' \| grep -v '^commit' > /tmp/merges.txt`, potem `python3 context/map/scripts/fixpr.py /tmp/fix.json /tmp/merges.txt > /tmp/fixpr.txt` | `fixpr.txt` (wolne, kilka minut) |
| 7. Pary i trójki obszarów | `python3 context/map/scripts/couple.py /tmp/kept.pkl 6 40` (progi: maks. obszarów i plików na commit) | stdout |
| 8. Wspólne pliki całego repo | `python3 context/map/scripts/hub.py /tmp/kept.pkl` | stdout |
| 9. Usunięte pliki i pary na żywych plikach | `python3 context/map/scripts/exist.py /tmp/kept.pkl` | stdout |

## Struktura zależności (jdeps) – raport `../artifact-2-structure.md`

Wymaga skompilowanych klas: `mvn -pl ta4j-core,ta4j-examples -am compile`.

| Krok | Polecenie | Wynik |
|---|---|---|
| 10. Cykle (SCC, najmniejsze pętle runtime, sploty pakietów) | `python3 context/map/scripts/jdeps_cycles.py /tmp/jd` | stdout + `jdeps_cycles.json` |
| 11. Granice warstw (model L0–L7 na górze skryptu) | `python3 context/map/scripts/jdeps_layers.py /tmp/jd` | stdout + `jdeps_layers.json` |
| 12. Podgraf kontraktów `core` | `python3 context/map/scripts/jdeps_focus_graph.py /tmp/kept.pkl context/map/graphs/core-contracts-upward.dot` | plik `.dot` |
| 13. Render SVG | `dot -Tsvg in.dot -o out.svg` albo bez Graphviza: `node context/map/scripts/render_svg.mjs <katalog z @hpcc-js/wasm-graphviz> in.dot out.svg` | plik `.svg` |

Krawędź „runtime” to realne użycie w bajtkodzie (`javap`): dziedziczenie, `new`, wywołanie, pole, rzutowanie, `catch`, referencja metody. Pozostałe krawędzie z jdeps to same typy.

## Dane z GitHuba

Tylko odczyt, upstream `ta4j/ta4j`:

```sh
gh pr list -R ta4j/ta4j --state closed --limit 300 --search "is:unmerged closed:>=2025-10-30" --json number,title,closedAt,author,headRefName,files
gh issue list -R ta4j/ta4j --state open --limit 200 --json number,title,labels,createdAt
```

Uwagi:
- Obszary, pliki i progi są wpisane na sztywno pod ta4j (pakiety `org/ta4j/core`, `ta4jexamples`; top 5 obszarów w `fix.py`, top 10 w `time.py` i `camp.py`). Lista kampanii i miesięcy w `camp.py` pochodzi z wyniku `time.py`.
- Wyniki zależą od daty uruchomienia (`--since="12 months ago"`).
