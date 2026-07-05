---
author: null
created: 2026-04-19
description: 'LLM Knowledge BasesSomething I''m finding very useful recently: using
  LLMs to build personal knowledge bases for various topics of research interest.
  In this way, a large fraction of my recent token throughput is going less into manipulating
  code, and more into manipulating knowledge (stored as markdown and images). The
  latest LLMs are quite good at it. So:Data ingest:I index source documents (articles,
  papers, repos, datasets, images, etc.) into a raw/ directory, then I use an LLM
  to incrementally "compile" a wiki, which is just a collection of .md files in a
  directory structure. The wiki includes summaries of all the data in raw/, backlinks,
  and then it categorizes data into concepts, writes articles for them, and links
  them all. To convert web articles into .md files I like to use the Obsidian Web
  Clipper extension, and then I also use a hotkey to download all the related images
  to local so that my LLM can easily reference them.IDE:I use Obsidian as the IDE
  "frontend" where I can view the raw data, the the compiled wiki, and the derived
  visualizations. Important to note that the LLM writes and maintains all of the data
  of the wiki, I rarely touch it directly. I''ve played with a few Obsidian plugins
  to render and view data in other ways (e.g. Marp for slides).Q&A:Where things get
  interesting is that once your wiki is big enough (e.g. mine on some recent research
  is ~100 articles and ~400K words), you can ask your LLM agent all kinds of complex
  questions against the wiki, and it will go off, research the answers, etc. I thought
  I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining
  index files and brief summaries of all the documents and it reads all the important
  related data fairly easily at this ~small scale.Output:Instead of getting answers
  in text/terminal, I like to have it render markdown files for me, or slide shows
  (Marp format), or matplotlib images, all of which I then view again in Obsidian.
  You can imagine many other visual output formats depending on the query. Often,
  I end up "filing" the outputs back into the wiki to enhance it for further queries.
  So my own explorations and queries always "add up" in the knowledge base.Linting:I''ve
  run some LLM "health checks" over the wiki to e.g. find inconsistent data, impute
  missing data (with web searchers), find interesting connections for new article
  candidates, etc., to incrementally clean up the wiki and enhance its overall data
  integrity. The LLMs are quite good at suggesting further questions to ask and look
  into.Extra tools:I find myself developing additional tools to process the data,
  e.g. I vibe coded a small and naive search engine over the wiki, which I both use
  directly (in a web ui), but more often I want to hand it off to an LLM via CLI as
  a tool for larger queries. Further explorations:As the repo grows, the natural desire
  is to also think about synthetic data generation + finetuning to have your LLM "know"
  the data in its weights instead of just context windows.TLDR: raw data from a given
  number of sources is collected, then compiled by an LLM into a .md wiki, then operated
  on by various CLIs by the LLM to do Q&A and to incrementally enhance the wiki, and
  all of it viewable in Obsidian. You rarely ever write or edit the wiki manually,
  it''s the domain of the LLM. I think there is room here for an incredible new product
  instead of a hacky collection of scripts.'
published: null
source: https://xcancel.com/karpathy/status/2039805659525644595#m
status: processed
tags:
- clippings
title: Andrej Karpathy (@karpathy)
---

LLM Knowledge Bases Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. In this way, a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge (stored as markdown and images). The latest LLMs are quite good at it. So: Data ingest: I index source documents (articles, papers, repos, datasets, images, etc.) into a raw/ directory, then I use an LLM to incrementally "compile" a wiki, which is just a collection of.md files in a directory structure. The wiki includes summaries of all the data in raw/, backlinks, and then it categorizes data into concepts, writes articles for them, and links them all. To convert web articles into.md files I like to use the Obsidian Web Clipper extension, and then I also use a hotkey to download all the related images to local so that my LLM can easily reference them. IDE: I use Obsidian as the IDE "frontend" where I can view the raw data, the the compiled wiki, and the derived visualizations. Important to note that the LLM writes and maintains all of the data of the wiki, I rarely touch it directly. I've played with a few Obsidian plugins to render and view data in other ways (e.g. Marp for slides). Q&A: Where things get interesting is that once your wiki is big enough (e.g. mine on some recent research is ~100 articles and ~400K words), you can ask your LLM agent all kinds of complex questions against the wiki, and it will go off, research the answers, etc. I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries of all the documents and it reads all the important related data fairly easily at this ~small scale. Output: Instead of getting answers in text/terminal, I like to have it render markdown files for me, or slide shows (Marp format), or matplotlib images, all of which I then view again in Obsidian. You can imagine many other visual output formats depending on the query. Often, I end up "filing" the outputs back into the wiki to enhance it for further queries. So my own explorations and queries always "add up" in the knowledge base. Linting: I've run some LLM "health checks" over the wiki to e.g. find inconsistent data, impute missing data (with web searchers), find interesting connections for new article candidates, etc., to incrementally clean up the wiki and enhance its overall data integrity. The LLMs are quite good at suggesting further questions to ask and look into. Extra tools: I find myself developing additional tools to process the data, e.g. I vibe coded a small and naive search engine over the wiki, which I both use directly (in a web ui), but more often I want to hand it off to an LLM via CLI as a tool for larger queries. Further explorations: As the repo grows, the natural desire is to also think about synthetic data generation + finetuning to have your LLM "know" the data in its weights instead of just context windows. TLDR: raw data from a given number of sources is collected, then compiled by an LLM into a.md wiki, then operated on by various CLIs by the LLM to do Q&A and to incrementally enhance the wiki, and all of it viewable in Obsidian. You rarely ever write or edit the wiki manually, it's the domain of the LLM. I think there is room here for an incredible new product instead of a hacky collection of scripts.

Apr 2, 2026 · 8:42 PM UTC

2,783

6,768

56,559

20,057,368

Atm it's not a fully autonomous process, I add every source manually, one by one and I am in the loop, especially in early stages. After a while, the LLMs "gets" the pattern and the marginal document is a lot easier, I just say "file this new doc to our wiki: (path)".

23

8

311

178,564

Same, I have a similar setup. A mix of Obsidian, Cursor (for md), and vibe-coded web terminals as front-end. Since I do a podcast, the number/diversity of research interests is very large. But the knowledge-base approach has been working great. For answers, I often have it generate dynamic html (with js) that allows me to sort/filter data and to tinker with visualizations interactively. Another useful thing is I have the system generate a temporary focused mini-knowledge-base for a particular topic that I then load into an LLM for voice-mode interaction on a long 7-10 mile run. So it becomes an interactive podcast while I run, where I ask it questions and listen to the answers to learn more. Anyway, heading out for a run now, thanks for the write-up 👊

180

210

5,437

597,692

I like this approach because it mitigates the contamination risks of agent-generated content in your primary vault... the agents need a playground too!

I like [@karpathy](https://xcancel.com/karpathy "Andrej Karpathy") 's Obsidian setup as a way to mitigate contamination risks. Keep your personal vault clean and create a messy vault for your agents. I prefer my personal Obsidian vault to be high signal:noise, and for all the content to have known origins. Keeping a separation between your personally-created artifacts and agent-created artifacts prevents contaminating your primary vault with ideas you can't source. If you let the two mix too much it will likely make Obsidian harder to use as a representation of \*your\* thoughts. Search, bases, quick switcher, backlinks, graph, etc, will no longer be scoped to your knowledge. Only once your agent-facing workflow produces useful artifacts would I bring those into the primary vault.

12

9

426

72,737

I've been on this exact setup for about a year now - the biggest unlock imo is you can synthesize any k number of topics across any k domains and the possibility becomes O(n^k) For a 500-note vault: k=2: 250,000 ordered pairs k=3: 125 million paths k=4: 62.5 billion you can connect, say, "stoic philosophy" - "saas pricing" - "viral content" - "parenting" and agent can actually traverse that path and find something coherent. [elvis.so/p/obsidian-claude-c…](https://www.elvis.so/p/obsidian-claude-code-guide)

[![](https://pbs.twimg.com/card_img/2044113844226928641/XRcU9nY3?format=jpg&name=800x419)](https://www.elvis.so/p/obsidian-claude-code-guide)

3

3

143

40,251

Here's what I'm currently pondering: This idea, but implemented totally in the cloud for normies. One could imagine building a virtual file system on top of the cloud-hosted data (so it looked to the LLM like a navigable directory tree of files). That could be done with a super simple SKILL implementing the base file system primitives. Next step would be to make it multi-player so businesses/teams could use it. Content is default private (each user has their own directory). Any individual directory/file could be tagged/shared to a team, to the company or to the world (public). Make it available via API, MCP, CLI etc. so you could unless something like OpenClaw against it if you wanted. I even have the domain for it: secondbrain.com What do folks think?

24

2

70

22,653

Andrej talking about [@origin\_trail](https://xcancel.com/origin_trail "OriginTrail") Decentralized Knowledge Graph (DKG) exactly without saying it...

🆕Imagine hundreds of agents working in parallel, handing off to one another and building on each other's work. Every finding becomes a cryptographically anchored Knowledge Asset: verifiable, permanent, owned by the publisher, and queryable by any agent on the network. Enter Decentralized Knowledge Graph v9, already powering AI agent swarms to be: → up to 60% faster → up to 40% cheaper than markdown handoffs. The advantage compounds as the swarm grows. Build something exciting—or simply run a hello-world OriginTrail multiplayer game to try it!

<video controls=""><source src="https://video.twimg.com/amplify_video/2033196272166023168/vid/avc1/1920x1080/6ZYcdAYe7Vdy_JRJ.mp4" type="video/mp4"></video>

1

14

40

2,635

.[@RobertMMetcalfe](https://xcancel.com/RobertMMetcalfe "Bob Metcalfe") would put it somewhat this way to get V~ℕ^2 (value of network effects): Coordination ↑ Connectivity ↑ Context

.[@karpathy](https://xcancel.com/karpathy "Andrej Karpathy") 's model shows how LLMs turn raw research into a living knowledge base - every answer compounds into a wiki that gets smarter over time. But it has a critical gap: that wiki is local, unverifiable, and siloed to a single agent. The moment you scale to AI agent swarms with hundreds of agents collaborating across the internet, you need to answer a question Karpathy himself flagged: how do you coordinate an untrusted pool of workers? [@origin\_trail](https://xcancel.com/origin_trail "OriginTrail") 's DKG V10 solves this directly. Karpathy's Wiki becomes Working Memory: per-agent, local, never leaving the node. From there, the DKG adds what's missing: ↑ Shared Working Memory: collaborative staging, gossiped across network members ↑ Long-term Memory: permanent, chain-confirmed, immutable record ↑ Verified Memory: multi-party attested, anchored on-chain, readable by the Context Oracle across all layers What Karpathy envisioned as a smart wiki becomes trustless, multi-agent knowledge infrastructure. Every answer still compounds. But now the compounding is shared, verifiable, and owned by no single party.

<video controls=""><source src="https://video.twimg.com/amplify_video/2039979218088734720/vid/avc1/1622x1526/zCFWV887eD0EoY2_.mp4" type="video/mp4"></video>

1

8

33

1,742

The jump from personal research wiki to enterprise operations is where it gets brutal. One person’s markdown repo is manageable. Thousands of employees, millions of tickets, tribal knowledge that contradicts itself across teams, you can’t vibe-code that. We’re building this for enterprise ops at [@edra\_ai](https://xcancel.com/edra_ai "Edra"). Agentic learning that reverse-engineers executable knowledge from existing systems (tickets, logs, emails), outputs a white-box knowledge library, and keeps it current as the business changes. Same core loop you’re describing, ingest, compile, lint, enhance - but at organizational scale. The instinct that “there is room here for an incredible new product” is right. The knowledge layer for AI agents is the next great system of record. Live today with the likes of HubSpot, ASOS, Cushman & Wakefield.

4

23

10,556

The 'queries always add up' part is what makes this interesting. Most knowledge systems are static, you put data in, you get answers out. This is compounding. The scaling question is worth watching though. At 400K words the LLM can still reason over index files naturally. At 4M words that same approach starts to break, and suddenly you do need the RAG you skipped. The 'no fancy RAG needed' conclusion might be scale-dependent. The deeper idea here is agent memory that writes itself. That problem shows up everywhere, not just personal knowledge bases.

2

17

5,717

same, i just baked it all into one system tho so it researches and renders all in one place lately i like to use the file system instead of obsidian so it works with other file types too, but if only.md obsidian is great

<video controls=""><source src="https://video.twimg.com/ext_tw_video/2039891233074561024/pu/vid/avc1/1280x720/KhkNbgcvUeF7q-wr.mp4" type="video/mp4"></video>

1

20

5,900

Working on (and continuously thinking about) something quite similar. Currently looking for a method outside of the LLM itself to tell the LLM when to stop "fetching" information, because it fails to do that accurately. Some times it decides to answer after fetching too little information, and some times it "wastes" time fetching more information than it really needs. I suppose it also depends on the size of the knowledge base, but for the singular project I'm using to test this, it appears to already fail on knowledge that's linked across 5 or so "hops" (both horizontally and vertically). And that's with Opus 4.6. Really trying to find ways to help it traverse better. Want to try laying out the data in both relational and graph databases that are utilized (perhaps by another agent, or just by a tool?) before the LLM gets to reason about the question. Extremely curious to see how this develops, because I see this becoming the "brain" of processes for both people and companies.

1

1

15

2,148

I've been doing something similar (which I call "vibe research") for a SoK/market map project. - All sources are ingested and summarized via LLMs - I query the knowledge base to come up with hypotheses, frameworks, and interesting ways to organize data - Different visualizations and reports are simply "compiled" outputs with tuned instructions, automatically pushed to say google docs. One key issue, though, with "vibe research" (vs say "vibe coding") is that there is no equivalent of tests, evals, benchmarks, etc. for knowledge bases. You basically just have to trust that the LLM ingested, summarized, and transformed information correctly.

1

17

4,248

Yeah this is golden tips This is the methodology I've found the best for self-improving agents too btw, human readable Obsidian knowledge bases work great as an agent memory too And you can read what's in them, and improve how your agent/LLM store things because on most other options, you are just blind, and that leaves things with a bunch of primitive telemetry [xcancel.com/meta\_alchemist/status/…](https://xcancel.com/meta_alchemist/status/2037830936331690472)

2

14

6,692

Love the thoughtfulness in designing systems that actually compound thinking, not just generate outputs. I'm inspired to revisit and expand a “Knowledge Tree” workflow I built a few months ago.

Vibe Coding: how I (try to) get smarter alongside AI -- Building a Knowledge Tree Vibe coding is real. You can ship a working app in minutes. What’s harder is knowing what you actually understand. This is the 3-part workflow I use to keep learning while I vibe-code. 1. Critical Thinking: parallel window for questions When I vibe code, I keep a second window open. That’s where I ask my coding agent to explain things as we go, especially when something feels non-obvious. Example: yesterday while installing [@openclaw](https://xcancel.com/openclaw), I noticed it was using bun. That triggered a quick detour: • what bun is • how they work • why bun instead of npm Nothing fancy. Just slowing down enough to ask why instead of blindly accepting output. 2. Memory: build your knowledge tree One thing I noticed early on: good explanations disappear into chat history way too easily. To avoid that, I connected my coding agent ([@claudeai](https://xcancel.com/claudeai "Claude")) to a memory layer ([@ensue\_ai](https://xcancel.com/ensue_ai "ensue") ). Whenever the agent explains a concept, gives an overview, or shares a mental model, I ask it to save it into a structured personal knowledge base. Over time, this turns into something like a knowledge tree - things build on each other. I automated this by forking the ensue-memory-network skill and creating a new Claude skill called learning-memory, which saves what I learn using a consistent structure. 3. Recall: make things stick Perhaps it's just me, but even when something clicks in the moment, I tend to forget it if I don’t revisit it. What’s helped is baking recall into the workflow: • at the end of a session, I ask the agent to summarize what I learned • when I start the next session, it looks at that memory and quizzes me on it It refreshes my own context fast and makes it easier to keep building on previous knowledge, putting me in a much better place to continue. The learning-memory skill has hooks that automates this. Why this feels useful I’ve started using this approach recently, and it’s already paying off. I still get the speed and leverage of vibe coding. But over time, I feel more confident reasoning about: • what the code is doing • why certain tools or patterns are used • what tradeoffs I’m actually making Speed doesn’t have to kill understanding. With the right loop, even vibe coding can develop taste. If You Want To Try It Out: setup You could probably implement something similar with other tools, but this is my current setup: • AI agent: Claude Code • Memory skill: enter "/plugin christinetyip/ensue-learning-memory" in Claude to install the skill • Memory layer: Ensue (you can generate a free API key at ensue-network(dot)ai after signing up) • Last step: enjoy vibe coding and growing your knowledge tree.

<video controls=""><source src="https://video.twimg.com/amplify_video/2008936853051695108/vid/avc1/882x596/4JjB1OBaxZCV-xFy.mp4" type="video/mp4"></video>

1

12

4,466

Have been experimenting with a similar setup for a few weeks - stitching together work context into a markdown library an agent/LLM maintains. Two learnings: – Sanity checks are critical or they slowly decay – The magic is when queries feed back into the system to make a flywheel

2

13

5,463

[Load more](https://xcancel.com/karpathy/status/2039805659525644595?cursor=DAAKCgABHGRsqHw__scLAAIAAAGQRW1QQzZ3QUFBZlEvZ0dKTjB2R3AvQUFBQUNNY1Q1bWNYOXJ3M2h4UGtVNGRGcUFpSEZDMFRkN2FBY2djVHlKZ2lkYkFPeHhQZnowaVZuRjJIRTdkUFFpV1VhY2NUdmkzVXB0aEZSeE8ySENpMjRFekhFN2dVdm5ha09rY1R3RGI4Sm9CUUJ4TzRmc25tMkdoSEU4TkNCUld3UDBjVC9xdk14WWhOQnhQbkR3elY3RXhIRThtVVh0V3NYNGNUdW9jNDV0dzFoeE8rV1hZbWtEVEhFOEpmSFRiVWIwY1R2QXlVdGR4ZFJ4TzNwTHlteEd3SEUrMDhXUWF3T0FjVDlYQVpwWmhReHhQZjZDUUY2R0xIRTd3cVY0YmtkSWNUdThEeTlxZzFCeFBoU3pKVjZEeEhGSnZwUEpYQUJNY1QzNXc1WmRRWlJ4UFovVW9sd0ZVSEUrUyszNFcwR1VjVHZXVlE5dVFweHhQekVCZkZ0Qm5IRTcvZ3NmYlFOc2NUdUJ1Z2hvd2V4eE8zUHJWRzZBaAgAAwAAAAILAAQAAAAGQm90dG9tAAA#r)