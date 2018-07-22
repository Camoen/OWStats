# OWStats
This repository contains the code for a Reddit bot that automatically responds to comments with statistics (win rates, popularity, etc.) about a particular Overwatch hero.  Once a week, the bot also posts a weekly statistical breakdown.

### main.py
This is the code that runs [Overwatch_Stats_Bot](https://www.reddit.com/user/overwatch_stats_bot/posts/).  It uses PRAW to access the Reddit API and automatically reply to comments.  When called via the "!owstats  hero-name", "!owstat hero-name", or "!herostats hero-name" commands,  the bot automatically replies with the requested hero's statistics from the past month.

If the bot hasn't run yet on the current day, it gathers and archives new statistical data via `get_stats.py`.  Additionally, if it's the first run on a Tuesday, the bot posts a weekly statistical breakdown to [r/OWStatsArchive](https://www.reddit.com/r/OWStatsArchive/), via `weekly_stats.py`.

### get_stats.py
Uses Selenium and BeautifulSoup to scrape a table of statistical data on [Overbuff](https://www.overbuff.com/heroes).

### weekly_stats.py
Uses archived data to post a weekly statistical breakdown.  This breakdown calculates the change in win rate, pick rate, tie rate, and "on fire" percentages over the past week from both a monthly and weekly point of reference.

### praw.ini
Example `praw.ini` file that's required to authenticate the bot and allow usage of Reddit's API.