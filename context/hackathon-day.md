# Context: Hackathon day, 10 Oct 2026 (source: infrastructure chat, times CEST)

## Timeline (Version 1 is built today)
- 12:15 Coordinator chat starts: read-in of the VPS, the Buzz relay and existing agents.
- 13:30 Private GitHub repo; deploy key for the agents; commit guard that blocks API keys.
- 13:40 Buzz channel and steering agent hack-chef (Gemini 3.8 Flash); thread sessions; the repo is the shared memory.
- 14:00 Claude cloud lane connected via GitHub; first cloud task delivered as a branch.
- 14:20 Builders with their own git worktrees; Nano Banana image tool; first title image.
- 14:40 Show me, dont tell me status format; Gantt timeline; rules for escalating to the frontier model.
- 14:50 Hackathon rules ingested: submission 19:00, partner technologies Google DeepMind and Gradium, abuse rule.
- 15:30 Gradium key and credits; Python runtime with gradbot; HTTPS tunnel.
- 15:35 WhatsApp calling ruled out for today; decision: web call, audio via Ray-Ban glasses over Bluetooth.
- 15:55 Glasses test passed (gradbot demo with Gradium STT/TTS and Gemini; fixed a 404 from a trailing slash).
- 16:10 Vision handed to hack-chef: incoming call screen, How much time do you have, rapid fire questions, before/after knowledge graph.
- 16:20 Fable (Claude) delivers architecture and shared contract (PR 2); 8 Gemini agents build in parallel.
- 16:40 Integration and voice handed to Fable as claude-03; MVP target 17:15.

## Decisions taken
- No Twilio and no WhatsApp today; WhatsApp Business Calling is a Version 2 topic.
- Claude only through the cloud session credit; Gemini through the hackathon key, used sparingly.
- Everything is reversible with one rollback script; the repo becomes public at submission.

## Open for Version 2 (candidates for the call)
- Real phone or WhatsApp calling instead of the simulated call.
- Stable domain with login instead of a temporary tunnel.
- A night shift: agents run overnight and the morning call starts automatically.
- The agent speaks with a cloned voice of the user.
- Decisions from the call become the work queue of an autonomous build pipeline.
