# Daemon City

A Weimar introduction-project city where 20 famous architects and 17 philosophers live in houses that embody their theories, alongside ~300 ordinary citizens. Five daemons (Antonym, Paraphrase, Literal, Typo, Footnote) misread those theories and rebuild the houses.

## Contents

- `Claude conversation/daemon_city.py`: generates the full Rhino 8 model and writes `daemon_city_people.json` (people, traffic, daemon timetable).
- `Claude conversation/web/`: the interactive website (three.js) with Story, Explore and Film modes.
  - Edit `template.html`, then run `python build.py` inside `web/` to produce `daemon_city.html`. This also regenerates the `*_glb.txt` files from the `.glb` models.
- `There is a city where famous architects and philosophers live alongside ordinary people.docx`: the project text.

The Rhino file (`Daemon_City.3dm`) is not in the repo because of its size. Run `daemon_city.py` in Rhino 8 to rebuild it.

## Live website

https://mehrn00shk.github.io/daemon-city/

GitHub Pages serves the `docs/` folder. `web/build.py` regenerates it (a standalone copy of the page that loads the `.glb` files directly), so after a change run `python build.py`, then commit and push.
