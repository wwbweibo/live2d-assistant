---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	research(research)
	decision_maker(decision_maker)
	music_player(music_player)
	__end__([<p>__end__</p>]):::last
	__start__ --> decision_maker;
	decision_maker -.-> __end__;
	decision_maker -.-> music_player;
	decision_maker -.-> research;
	music_player -.-> __end__;
	music_player -.-> decision_maker;
	music_player -.-> research;
	research -.-> __end__;
	research -.-> decision_maker;
	research -.-> music_player;
	decision_maker -.-> decision_maker;
	music_player -.-> music_player;
	research -.-> research;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
