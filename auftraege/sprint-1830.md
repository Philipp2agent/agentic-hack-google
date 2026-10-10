# Sprint bis 18:20 (Philipp, 17:50) - Video 2 um 18:30 soll deutlich besser sein als Video 1
Leitidee: Wer das Video sieht, denkt "das will ich fuer MEIN Repo". Darum wird das Repo Plug-and-Play (claude-05).

## hack-chef (koordiniert, alle Agenten parallel)
1. PR 4 (claude-04, Live-Ansicht) jetzt mergen. PR 3 (claude-03) erst, wenn claude-03 bestaetigt, dass der Ton funktioniert.
2. Nicht anfassen: dawn/ (laeuft live fuer den Dreh), src/live (bis PR 4 gemerged ist).
3. Status in STAND.md, Fragen an Philipp hoechstens drei.

## Pakete
- hack-ideen: 15 Produktnamen. Idee: der Agent promptet den Menschen, nicht umgekehrt; kurz, ueber Brillen-Lautsprecher gut verstaendlich, merkbar. Top 3 mit je einem Satz Begruendung als FRAGE an Philipp in STAND.md.
- hack-marketing: Video-2-Skript (2 Minuten): Gang mit Brille, Anruf, Laptop-Live-Ansicht, Schluss "Try it on your own repo in 3 minutes". Dazu die README-Erzaehlung oben (abgestimmt mit claude-05).
- hack-visual: neutrale Titelkarte und Abspann (Repo-URL, "Built in one afternoon by 8 Gemini agents + Claude"); nach der Namenswahl Logo und Titelkarte mit Namen.
- hack-bau2: Live-Ansicht nach Philipps Gestaltungsregeln verfeinern (auf eigenem Branch nach dem Merge von PR 4): futuristisch, aber zurueckhaltend; was im Gespraech gerade dran ist, steht gross in der Mitte, alles andere tritt gedimmt zurueck; lesbar durch eine Brillenkamera.
- hack-bau3: Nachher-Ansicht der Live-Seite: "Das hat das Gespraech gebracht", drei Aussagen vorher -> nachher.
- hack-bau1: Beispiel-Ziel-Repo unter examples/ (klein, realistisch) fuer den Plug-and-Play-Test.
- hack-review: sobald der claude-05-PR da ist, frischer Klon, nur setup.sh und start.sh; Bericht an hack-chef.
