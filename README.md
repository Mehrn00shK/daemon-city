# Daemon's City

**Live demo: https://mehrn00shk.github.io/daemon-city/**

Five daemons study famous architects, misread their theories, and rebuild each architect's house as the opposite while they are out.

## Author and course

- **Author:** Mehrnoosh
- **Studio:** Pandaemonium: Daemons for Weimar
- **Course:** M.Sc. Digital Technologies in Architecture and Design (DTAD), WiSe 2026/27
- **Chair:** Informatics in Architecture and Urbanism (InfAU), Faculty of Architecture and Urbanism, Bauhaus-Universität Weimar
- **Teaching staff:** Reinhard König, Martin Bielik, Egor Gaydukov, Egor Gavrilov, Jan Willmann, Michael Braun, Thomas Pearce
- **Exercise:** Nonsense Project, 15.10. to 29.10.2026
- **Submission date:** 13.11.2026

## Links

- **Live demo:** https://mehrn00shk.github.io/daemon-city/
- **Source repo:** https://github.com/Mehrn00shK/daemon-city
- **Miro frame:** https://miro.com/app/board/uXjVHn1RS88=/?moveToWidget=3458764689890764830
- **60-second showreel:** on the Miro frame

## The task

The Nonsense Project is the two-week, individual start of the studio. I drew one theme, a strange situation in a city where things have spirits, and one constraint, a limit on the daemon I imagined for it. With a coding agent I built a prototype that shows what my daemon would do. Sensors and AI services could be faked, as long as the result was specific and believable. A daemon is not a script, so even a fake one had to decide for itself.

## Theme and constraint

- **Theme:** The City is shaped by decisions nobody is responsible for.
- **Constraint:** Your daemon misunderstands the world, and the misunderstanding must be useful.

## The daemon

### Concept

In this city, famous architects and philosophers live among ordinary people, each in a house built exactly to their own theory. Five daemons live there too: Antonym, Paraphrase, Literal, Typo and Footnote. They want to learn, so they follow the great figures and read their books, but each one misreads in its own way. Antonym hears "less" as "more". Literal takes "a house is a machine" at its word. Typo gets one word wrong. Footnote reads only the small print. While the architect is out, a daemon breaks in and rebuilds the house according to what it understood. Nobody ordered this and nobody can be blamed, yet the city keeps changing. The misunderstanding is useful because it works like a mirror. Seeing a famous principle turned inside out shows you more clearly what the principle was, and how much a building depends on being read the right way.

### Perceive, think, act

- **It perceives:** The architect's house, the architect's book, and the moment the architect leaves and comes home. The daemons also watch a short film of an Iranian farewell custom (*Safar Bekheyr*). They cannot perceive meaning: they get the words and gestures, never the intention behind them.
- **It thinks:** A daemon wants to understand a great mind and to surprise it. It picks one architect, reads the theory through its own flaw, and turns that reading into building rules.
- **It acts:** It takes the house apart and rebuilds it with the inverted or literal version of the theory: new forms, colours and tilts. It also performs its own wrong version of the farewell and welcome rituals as the architect leaves and returns.
- **Real or faked:** What really runs in the browser: each showing picks the daemons' order and the architects at random (every architect has an equal chance), and the rebuilt house is generated new each time from the original house's geometry, using rules that belong to each daemon. That means no two showings look the same. The voices are the browser's built-in text-to-speech, and the music is synthesised live. What I faked: the daemons perceive nothing and no AI runs while the page is open. Their "reading" is a set of rules and lines written in advance, and their "decisions" are random picks from those options. They do not really watch the film or understand anything. The city, the architects' houses and the fixed daemon versions shown in Story mode were generated beforehand in Rhino 8 with a Python script, and the citizens follow a fixed timetable.

### One visitor

Lena is a second-year architecture student with a jury at nine tomorrow. Her project borrows from Mies van der Rohe, and she still can't explain "less is more" without stumbling. At midnight she walks past Mies's house on her way home, hoping that looking at it will help.

The lights are on, but Mies has gone out. Inside, something is moving. Wall by wall, the glass pavilion comes apart and goes back up covered in cornices, columns and gold. A thin voice says, cheerfully, "When you say less, I hear more." It is Antonym, finishing its homework.

Lena stays and watches. Mies comes back, stops at the door and puts his head in his hands. Antonym has already gone to choose its next architect.

At first Lena laughs. Then she feels a little uneasy, because the overloaded house shows her exactly what was missing before. Every ornament marks a place where Mies had chosen nothing. On the walk home she rewrites her opening sentence. At the jury she doesn't explain "less". She describes everything that isn't there.

## How to use it

1. Open the live demo, preferably in Chrome or Edge on a computer, with the sound on. First you see the whole city from above, while the citizens' morning clock runs, and a title card with three buttons.
2. Click **Play the film** (about 9 minutes). The five daemons introduce themselves, watch *Safar Bekheyr* in the open-air theatre and give their readings of it. Then five episodes follow: a daemon chooses an architect, waits until the architect leaves, rebuilds the house, and the architect comes home to it.
3. Or click **Read the story** to go through it chapter by chapter, or **Explore the city**. In Explore mode, drag to orbit and scroll to zoom. Use the tabs to find an architect, philosopher, public building or daemon, then **Follow** a person or **Watch** a daemon at work.
4. Tips: play the film more than once, because the daemons, the architects, the rebuilt houses and the architects' reactions change every time. Use the **×8** button to speed up the clock in Story and Explore mode.

## Technical implementation

- **Frontend:** a single HTML page with vanilla JavaScript and Three.js (WebGL). The *Safar Bekheyr* film is drawn on a 2D canvas.
- **Hosting:** GitHub Pages, serving the `docs/` folder. The site is static, so it needs no server. A copy is also published as a claude.ai artifact.
- **Data sources and APIs:** none called at run time apart from the CDNs for Three.js and the Google Fonts. All the people, timetables, labels and descriptions are built into the page. The voices use the browser's Web Speech API (`speechSynthesis`), and the music uses the Web Audio API.
- **Models while it runs:** none.
- **Notable libraries:** Three.js 0.160 (GLTFLoader, DRACOLoader, OrbitControls, BufferGeometryUtils) and the Draco decoder. The city model was generated with Rhino 8 and its Python scripting (`Claude conversation/daemon_city.py`).

### Run locally

```bash
git clone https://github.com/Mehrn00shK/daemon-city.git
cd daemon-city/docs
python -m http.server 8000
# open http://localhost:8000
```

To rebuild the page after editing `Claude conversation/web/template.html`, run `python build.py` inside `Claude conversation/web/`. This rewrites `docs/`. The script contains absolute paths to the author's own drive (the people JSON and the *Safar Bekheyr* animation), so adjust those paths first. To rebuild the 3D model, run `daemon_city.py` in Rhino 8. The `.3dm` file itself is not in the repo because of its size.

## Working with AI

- **Coding agents used:** Claude Code, model Claude Opus 5.5 (`claude-opus-5-5`)
- **Key prompts:**
  1. *"I want you to build the city that I am describing: There is a city where famous architects and philosophers live alongside ordinary people. […] every famous figure has a house or office designed strictly according to their own theories and principles. Ordinary people also live in simple houses, though each comes in a unique shape."*
  2. *"There are also a few daemons living in the city. Throughout the day, they randomly target and follow famous figures, trying to study their philosophies. However, these daemons have a fatal flaw: they completely misunderstand everything they observe, read, or learn. […] They break into their houses and reconstruct them completely based on their own misunderstandings, turning the original theories entirely upside down. […] I want to see the process of breaking and reconstructing."*
  3. *"The animation opens with the daemons introducing themselves one by one through voiceover rather than text. Afterwards, they randomly select an architect to observe […] When the architect returns home, they are shocked by the distorted structure."*
  4. *"All architects should have an equal chance of being selected. Second, the result of the reconstruction should be different in each run. […] I want to see a different result every time."*
  5. *"Now I want daemons see this animation and get familiar with this tradition and interpret it themselves. Then, when the selected architect goes out of the house or comes back, daemons behave with them based on their understanding."*

### Reflection

Writing the story in full sentences first, then handing it over one part at a time, unlocked progress: the city, then the daemons, then the film. The agent built a lot from each paragraph. Asking for randomness made the biggest difference: once the daemons, architects and rebuilt houses changed every run, the daemons felt as if they chose for themselves. The agent went sideways on timing and sound. Voices were cut off, two daemons were silent because of slow online voices, and the subtitles drifted out of sync with the camera. Each problem took a few rounds, because I could only report them after watching the film. Next time I would plan the film's timing and voices before adding more scenes, and keep the folder in git from the first day.

## Credits, assets, licenses

- **Fonts:** Big Shoulders Display, Public Sans, JetBrains Mono and Vazirmatn, all from Google Fonts, under the SIL Open Font License 1.1.
- **Data:** no external datasets. The architects' and philosophers' principles, house descriptions, daemon lines and citizens were written with Claude for this project and are paraphrased general knowledge.
- **Images and sounds:** no external images or recordings. The 3D city and houses were generated by `daemon_city.py` in Rhino 8. *Safar Bekheyr* (the animation and its music in dastgah-e Shur) is my own earlier project, made with Claude and synthesised in code. The voices are the visitor's own system text-to-speech voices.
- **Third-party code:** Three.js (MIT); the Draco decoder from Google (Apache 2.0).
- **This repo:** the code is under the MIT License (see `LICENSE`), and the text, models and film are under CC BY 4.0.
