# Asking an AI agent for your numbers

Once dotTide is connected (see [Connecting AI clients](clients.md)), you ask in plain words and the agent picks the tools. These examples work in Claude Code, Claude Desktop and any other MCP client. Swap `example.com` for a site name from your profile.

## Start every session the same way

> Use dotTide to list my sites and tell me whether each one has access.

The agent calls `sites`. If a site shows a problem, fix it first: every other answer depends on access working.

## A weekly check

> Compare last week with the week before for every site in dotTide. Which site gained or lost the most clicks, and which queries or pages caused it?

The agent calls `search_queries` with `compare` for each site, then looks at `change_clicks` on the totals and the rows. Good follow-ups:

> Show me the five pages on example.com that lost the most clicks, with the numbers from both weeks.

> For the biggest drop, did impressions fall too, or only clicks? What does that suggest?

When impressions hold steady and clicks fall, the page still shows up in search but fewer people choose it, so the title and description are the first things to check. When impressions fall too, the page is showing up less.

## Finding content to refresh

> On example.com, find queries from the last 28 days where the average position is between 8 and 20, sorted by impressions. Which pages rank for them?

Positions 8 to 20 are the bottom of page one and the top of page two, where a small improvement moves a page into view. Follow up with:

> Pick the three with the most impressions and suggest what each page is missing for that query.

## AI referrals

> How many visits did AI assistants send to example.com this month compared with last month? Break it down by assistant.

The agent calls `traffic` with `compare` and reads `ai_referrals`. This only works for sites with GA4. The count is a floor: some assistant visits arrive without a referrer and show up as `(direct)`.

> Which sources besides Google sent the most engaged sessions to example.com in the last 28 days?

## Store numbers

> Use dotTide store_stats. How many downloads did each of my WordPress.org plugins get over the last seven days, and is any support thread unresolved?

> What's the daily user count for my Firefox add-on, and how many ratings does it have?

These need no Google setup, so they work from the first minute.

## Exact date ranges

> Search Console clicks and impressions for example.com from 2026-09-01 to 2026-09-30, by page, top 20.

> Compare September with August for example.com.

Search Console data settles about three days after the fact, so "this week" really means the seven days ending three days ago. Name dates when you need a fixed window.

## Reading the weekly snapshot

Agents that can read files can work from the snapshot instead of calling Google:

> Read ~/growth/main-2026-W44.json and give me the three biggest changes from last week, each with its number.

This is cheaper and faster for a weekly report, and every answer comes from the same saved numbers.

## A saved weekly prompt in Claude Code

Save a prompt as a slash command so the weekly check is one line. Create `.claude/commands/weekly-numbers.md` in any project:

```
Use dotTide. Check access with `sites` first. Then, for every site:

1. Compare last week with the week before using search_queries with compare.
2. List the three queries or pages with the biggest change in clicks, with both weeks' numbers.
3. For sites with GA4, show AI assistant referrals for both weeks.

End with store_stats: downloads and ratings changes only.
Keep it to five lines per site, and quote the numbers you used.
```

Then type `/weekly-numbers` in Claude Code.

## Tips for good answers

- **Ask for the numbers, not only the conclusion.** "Quote the numbers you used" keeps the answer honest and easy to check.
- **Use the site names from your profile.** If the agent uses a different name, it gets an `unknown site` error listing the right ones.
- **Ask for comparisons.** A single number rarely tells you much. `compare` puts it next to the previous period.
- **Small sites have small numbers.** A move from 4 clicks to 2 is noise. Ask the agent to say so instead of calling it a trend.
- **Everything is read-only.** The agent can't change your sites, Search Console or GA4 through dotTide, so you can let it explore freely.
