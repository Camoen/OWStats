import praw     # imports the reddit API wrapper
import time
import os
import get_stats
import weekly_stats
from datetime import datetime


# Get Reddit instance and authenticate
def authenticate():
    print("Authenticating.")
    # A properly set up 'praw.ini' file is required for authentication
    reddit = praw.Reddit('overwatch_stats_bot',
                         user_agent=('Overwatch Statistics Bot for Reddit:'
                                     'Returns hero pick rates and win rates.'))
    print("Authenticated as {}\n".format(reddit.user.me()))

    return reddit


# Save comment IDs in external file
def get_comment_history():
    if not os.path.isfile("comment_history.txt"):
        already_replied = []
    else:
        with open("comment_history.txt", "r") as x:  # "r" = read from file
            already_replied = x.read()
            # separating comment IDs by \n
            already_replied = already_replied.split(",")

    return already_replied


# Main Program
def run_program(reddit, keywords, hero_list, already_replied, stats_dict):
    # Choose subreddit to run on, pick "all" for all
    subreddit = reddit.subreddit('test+OWStatsArchive+Overwatch+'
                                 'Competitiveoverwatch+OverwatchUniversity')
    print("Loaded subreddits:  " + subreddit.display_name)
    print("Loading comments...")

    # Limit to 200 comments or less at a time.
    for comment in subreddit.comments(limit=100):
        # .body is text of the comment.
        comment_text = comment.body.lower()
        # check if any keywords match words in the comment's text
        exists = any(string in comment_text for string in keywords)
        # if comment hasn't been replied to, matching string is found
        # to prevent self replies, add "and comment.author != reddit.user.me()"
        if comment.id not in already_replied and exists:
            print("Comment found:   " + comment.body)

            keyword_flag = False
            hero = None
            # Finds keyword, then sets next word as hero name
            for word in comment_text.split():
                if keyword_flag is True:
                    hero = word
                    break
                elif word in keywords:
                    keyword_flag = True

            # Check if hero is a key in stats dictionary or hero_list
            if hero in stats_dict['Month_All'] or hero in hero_list:
                # If not in stats_dict, ensure key from hero_list is valid
                if hero not in stats_dict:
                    if hero == hero_list[2]:
                        hero = "mcCree"
                    elif hero in hero_list[5:9]:
                        hero = "soldier: 76"
                    elif hero in hero_list[15:17]:
                        hero = "torbjörn"
                    elif hero in hero_list[18:20]:
                        hero = "d.Va"
                    elif hero in hero_list[26:28]:
                        hero = "brigitte"
                    elif hero in hero_list[28:30]:
                        hero = "lúcio"
                    elif hero in ["wrecking", "wrecking ball", "hammond"]:
                        hero = "wrecking"

                # print(hero, "\n")
                # Get reply
                reply_string = get_reply(hero, stats_dict)
                # print(reply_string)
                comment.reply(reply_string)
                print("Reply completed.")

            # Add comment ID to comment history to prevent reposting
            already_replied.append(comment.id)

            # If comment ID file is > 200, clear oldest 100 IDs
            if len(already_replied) > 200:
                print("Deleting first oldest 100 comment IDs.")
                del already_replied[:-100]
                # overwrite comment_history file
                print("Overwriting comment_history file.")
                with open("comment_history.txt", "w") as x:
                    for comment_id in already_replied:
                        x.write(comment_id+",")
            # Otherwise, simply append to file
            else:
                # "a" to append to file
                with open("comment_history.txt", "a") as x:
                    x.write(comment.id+",")


# Returns statistics from past month only
def get_reply(hero, stats_dict):
    rank_list = ["All", "Grandmaster", "Master", "Diamond", "Platinum",
                 "Gold", "Silver", "Bronze"]
    hero = hero.capitalize()
    if hero == 'Mccree':
        hero = 'McCree'
    elif hero == 'D.va':
        hero = 'D.Va'
    elif hero == 'Wrecking':
        hero = 'Wrecking Ball'

    reply = ("#### Statistics for {} over the past month:\n"
             " Rank | Pick Rate | Win Rate | Tie Rate | On Fire\n"
             ":----:|:---------:|:--------:|:--------:|:------:\n"
             .format(hero))

    for rank in rank_list:
        grp = 'Month_{}'.format(rank)
        reply += (" {} | {} | {} | {} | {}\n".format(rank,
                  stats_dict[grp][hero][1], stats_dict[grp][hero][2],
                  stats_dict[grp][hero][3], stats_dict[grp][hero][4]))

    reply += ("-----\n ^(I'm a bot that provides hero stats from) ^[Overbuff]"
              "(https://www.overbuff.com/heroes), ^(updated once daily.)  "
              "^(Call me using the command '!OWstats Hero'.)\n\n^(PSA: Please "
              "consider setting your in-game profile to 'public'.  Websites "
              "such as Overbuff rely on public profiles to function.)")
    return reply


def main():
    # Check if program has been run yet today
    current_date = datetime.now().strftime('%Y-%m-%d')
    if not os.path.isfile("run_history.txt"):
        lastrun = ''
        hist = open("run_history.txt", "w+")
        hist.close()
    else:
        with open("run_history.txt", "r") as hist:
            lastrun = hist.readline().strip()

    # If program hasn't been run yet today, get new statistics
    if (lastrun != current_date):
        print('Gathering new data.')
        get_stats.retrieve()
        with open("run_history.txt", "w+") as hist:
            hist.write(current_date)

    # Load keywords and comment IDs that have already been replied to
    keywords = ["!owstats", "!owstat", "!herostats"]
    hero_list = ["doomfist", "genji", "mccree", "pharah", "reaper",
                 "soldier:76", "soldier76", "soldier", "s76", "sombra",
                 "tracer", "bastion", "hanzo", "junkrat", "mei", "torbjorn",
                 "torbjörn", "widowmaker", "d.va", "dva", "orisa", "reinhardt",
                 "roadhog", "winston", "zarya", "ana", "brigitte", "baguette",
                 "lucio", "lúcio", "mercy", "moira", "symmetra", "zenyatta",
                 "wrecking", "wreckingball", "hammond"]
    already_replied = get_comment_history()
    print("\nAlready replied to {} comments.".format(len(already_replied)))

    # Get reddit instance and import statistics to stats_dict
    reddit = authenticate()
    time_period = ["Month", "Week"]
    rank_list = ["All", "Grandmaster", "Master", "Diamond", "Platinum",
                 "Gold", "Silver", "Bronze"]
    stats_dict = weekly_stats.get_all_stats_dict(time_period, rank_list, current_date)

    # Uncomment to print a sample reply:
    # print(get_reply("sombra", stats_dict)+"\n")

    while True:
        run_program(reddit, keywords, hero_list, already_replied, stats_dict)

        # Adjust variable "sleeptime" to increase/decrease inactivity time
        sleeptime = 5
        print("Sleeping for ", end='')
        print(sleeptime, end='')
        print(" seconds.\n")
        # Sleep for 5 seconds
        time.sleep(sleeptime)


if __name__ == '__main__':
    main()
