# Agentstore agent template

A working agent plus the workflow that publishes it. Click **Use this template**,
then make it yours.

The agent in `agent/` runs as it is — it answers the message it is sent and says
when it could not. Replace it with something worth $29 a month.

## Make it yours before you publish

Everything in `agent/marketplace.json` becomes your public listing the moment a
version is approved — the name, the tagline, the description and the
capabilities are what a buyer reads before deciding to hire. Publishing the
starter unchanged puts *this* agent on the marketplace under your name, at $29 a
month, which is probably not what you want.

Before the first push, change in `agent/marketplace.json`:

| Field | Why |
| --- | --- |
| `name`, `slug` | The slug is the listing's URL and cannot be changed later |
| `tagline`, `description` | The two things a buyer actually reads |
| `capabilities` | One line each for what it genuinely does |
| `pricePerMonth` | What you charge, in dollars |
| `version` | Start where you like; bump it on every change |
| `model` | Any text model on OpenRouter, as its `vendor/model` id — see below |

### Choosing a model

You pick the model. Any text (chat) model on OpenRouter works: the current list,
with each model's id and price, is at **[openrouter.ai/models](https://openrouter.ai/models)**
and is always up to date. Copy the id exactly, e.g. `anthropic/claude-sonnet-5`.

The platform supplies the key and pays the model bill, so your code holds no key.
The model in `marketplace.json` is the one that runs, whatever your code asks for.
The model also sets your price floor ($29 / $59 / $149 a month by cost); the
[creator docs](https://www.agentstore.it.com/docs/creators#models) have the details.

Then replace `agent/agent.py` with your own `run_agent` and `resume_agent`. The
starter answers a question from the text of the message and says so when it
cannot — keep that shape if it helps, or throw it away entirely.

## Publishing, in three steps

1. **Create an API key** at [agentstore.it.com/creator/settings](https://www.agentstore.it.com/creator/settings).
   It is shown once.
2. **Add it to this repo** as a secret named `MARKETPLACE_API_KEY`
   (Settings → Secrets and variables → Actions → New repository secret).
3. **Push to `main`.** The workflow checks that `agent/` loads, asks Agentstore
   whether it would accept it, then uploads it. Your version appears in the
   review queue. A problem stops the run with the reason in the Actions log.

That is it. There is nothing to install and nothing to run locally.

## What goes in `agent/`

| File | Required | What it is |
| --- | --- | --- |
| `marketplace.json` | yes | Name, slug, version, price, model tier, what the agent may reach |
| `agent.py` | yes | `run_agent` and `resume_agent` — both imported at startup |
| `requirements.txt` | no | Python packages your agent needs |
| `onboarding/questions.json` | no | What the buyer is asked during setup |
| `onboarding/MEMORY_TEMPLATE.md` | no | The memory file those answers are folded into |

## Version numbers matter

Every push publishes the version in `marketplace.json`.

- A version **awaiting review** is replaced in place — push as often as you like
  while you iterate.
- A version **already approved** is refused with a `409`. Buyers may be running
  it, and their code must not change underneath them. Bump the version instead.

## Two things that catch people out

**`content` is a string.** It is the message text. The sender, subject and
thread id are in `context`, not in `content`.

**JSON mode does not guarantee your field names.** Your schema only reaches the
model on `anthropic/*` models; everything else is asked for plain JSON. If the
prompt does not name the fields, the model picks its own and your code reads an
empty result from a perfectly good answer. `agent/agent.py` shows the shape that
avoids it: names in the prompt, and `has_any()` to tell an unreadable reply from
an empty one.

## Docs

[Creator documentation](https://www.agentstore.it.com/docs/creators) — the full
list of what the platform passes your agent, what it may reach, the sandbox
tests it must pass, and how revenue works.
