import os
import glob
import praw
import csv
from collections import defaultdict
from datetime import datetime, timedelta


# Authenticate and get reddit instance
def authenticate():
    print("Authenticating.")
    reddit = praw.Reddit('overwatch_stats_bot',
                         user_agent=('Overwatch Statistics Bot for Reddit:'
                                     'Returns hero pick rates and win rates.'))
    print("Authenticated as {}\n".format(reddit.user.me()))

    return reddit


def data_gathering():
    stat_diff = {}
    archive_files = glob.glob('Archive/*.csv')
    newest_file = max(archive_files, key=os.path.getctime)
    global new_date
    new_date = datetime.fromtimestamp(os.path.getctime(newest_file))
    newest_date = new_date.strftime('%Y-%m-%d')
    print("Newest file is from {}".format(newest_date))
    # Find archive file closest to a week ago.
    global old_date
    old_date = (datetime.now() - timedelta(days=6))
    target_date = old_date.strftime('%Y-%m-%d')
    print("Target_date is {}".format(target_date))

    # Check for existence of a file (default is 'Month_All') on target date
    last_date = target_date
    # While file doesn't exist, check for nearby files
    day_check = 0
    while not os.path.isfile('Archive/{}_Month_All.csv'.format(last_date)) and day_check < 5:
        day_check += 1
        # Check one day previous
        old_date = (datetime.now() - timedelta(days=6+day_check))
        last_date = old_date.strftime('%Y-%m-%d')
        if os.path.isfile('Archive/{}_Month_All.csv'.format(last_date)):
            break
        # Check one day following
        old_date = (datetime.now() - timedelta(days=6-day_check))
        last_date = old_date.strftime('%Y-%m-%d')
        if os.path.isfile('Archive/{}_Month_All.csv'.format(last_date)):
            break

    # If no files exist within a 5 day radius of target date, don't post
    if not os.path.isfile('Archive/{}_Month_All.csv'.format(last_date)):
        print("No files within a five day radius of {}.\n".format(target_date))
        return stat_diff
    else:
        print("File found for {}. This is within a five day"
              " radius of {}.\n".format(last_date, target_date))

    time_period = ["Month", "Week"]
    rank_list = ["All", "Grandmaster", "Master", "Diamond", "Platinum",
                 "Gold", "Silver", "Bronze"]
    global new_stats
    new_stats = get_all_stats_dict(time_period, rank_list, newest_date)
    old_stats = get_all_stats_dict(time_period, rank_list, last_date)

    stat_diff = get_stats_difference(time_period, rank_list, new_stats, old_stats)
    return stat_diff


def weekly_post():
    # stats_dif contains data such as "New_Month_All - Old_Month_All"
    # stats_dif = {  'Time_Rank' :
    # {'HeroName  : [Role, PR Change, WRC, TRC, OFC]'}, 'Time_Rank2' (etc.)  }
    stat_dif = data_gathering()
    stat_new = new_stats
    date_range = '{} - {}'.format(old_date.strftime('%A, %B %d'),
                                  new_date.strftime('%A, %B %d'))

    if len(stat_dif) == 0:
        print("No stats found.")
        return

    # Get instance of reddit
    reddit = authenticate()

    post_title = "Overwatch Statistical Analysis: Week of {}".format(date_range)

    # Post Header
    post = '# Weekly Statistical Breakdown for {}\n\n'.format(date_range)
    post += ("Here's a statistical breakdown of the past week in Overwatch. "
             "All tables show details for the last month or week, as well as"
             " the amount a particular statistic has changed over the past "
             "week. \n\n*Hero statistics are obtained from [Overbuff]"
             "(https://www.overbuff.com/heroes).*\n\n")
    time_period = ["Month", "Week"]
    rank_list = ["All", "Grandmaster"]

    # Add data tables to post (by time period, then rank)
    for rank in rank_list:
        if rank == "All":
            rankname = "All Ranks"
        else:
            rankname = rank

        for time in time_period:
            tr = '{}_{}'.format(time, rank)

    # print(stat_diff['Month_All']['Soldier: 76'][0])

    # For posting in personal subreddit, use all stats
    # Separate Table for each bracket = 16 tables?

            post += "### *Past {}, {}*\n".format(time, rankname)
            post += ("Hero | Role | Pick Rate | PR Change | Win Rate | WR Change | Tie Rate | TR Change | On Fire | OF Change \n"
                     ":---:|:----:|:---------:|:---------:|:--------:|:---------:|:--------:|:---------:|:-------:|:---------:\n")

            for hero in stat_dif[tr]:
                post += ("{}   |  {}  |    {}     |    {}     |    {}    |     {}    |    {}    |     {}    |   {}    |    {}\n"
                         .format(hero, stat_new[tr][hero][0],
                                 stat_new[tr][hero][1], stat_dif[tr][hero][1],
                                 stat_new[tr][hero][2], stat_dif[tr][hero][2],
                                 stat_new[tr][hero][3], stat_dif[tr][hero][3],
                                 stat_new[tr][hero][4], stat_dif[tr][hero][4]))

        post += "\n\n-----\n\n"

    print(post)
    # Submit Post
    reddit.subreddit('OWStatsArchive').submit(title=post_title, selftext=post)


def get_stats_difference(time_period, rank_list, new_stats, old_stats):
    stat_diff = defaultdict(lambda: 'None')
    for time in time_period:
        for rank in rank_list:
            # Gives key such as 'Month_All'
            time_rank = '{}_{}'.format(time, rank)

            # Workaround for potentially nonexistent files
            if time_rank not in new_stats or time_rank not in old_stats:
                continue

            # Create dictionary where time_period and rank are keys
            trdict = defaultdict(lambda: 'None')

            # For every hero in stats dictionaries
            # Iterate through new dict.  Includes stats for new heroes
            # Also maintains order from highest pickrate to lowest.
            for hero in new_stats[time_rank]:
                # If hero existed last week
                if hero in old_stats[time_rank]:
                    # [2] = Pick Rate, [3] = Win Rate, [4] = Tie Rate, etc.
                    trdict[hero] = [new_stats[time_rank][hero][0],
                                    '{}%'.format(pos_or_neg(format(float((new_stats[time_rank][hero][1])[:-1])
                                                                   - float((old_stats[time_rank][hero][1])[:-1]), '.2f'))),
                                    '{}%'.format(pos_or_neg(format(float((new_stats[time_rank][hero][2])[:-1])
                                                                   - float((old_stats[time_rank][hero][2])[:-1]), '.2f'))),
                                    '{}%'.format(pos_or_neg(format(float((new_stats[time_rank][hero][3])[:-1])
                                                                   - float((old_stats[time_rank][hero][3])[:-1]), '.2f'))),
                                    '{}%'.format(pos_or_neg(format(float((new_stats[time_rank][hero][4])[:-1])
                                                                   - float((old_stats[time_rank][hero][4])[:-1]), '.2f')))
                                    ]
                else:
                    trdict[hero] = [new_stats[time_rank][hero][0],
                                    new_stats[time_rank][hero][1],
                                    new_stats[time_rank][hero][2],
                                    new_stats[time_rank][hero][3],
                                    new_stats[time_rank][hero][4]]

            stat_diff.update({'{}'.format(time_rank): trdict})

    # print(stat_diff['Month_All']['Soldier: 76'][4])
    return stat_diff


def pos_or_neg(check_str):
    if float(check_str) <= 0:
        return check_str
    else:
        positive = '+'
        positive += check_str
        return positive


def get_all_stats_dict(time_period, rank_list, date):
    all_stats = defaultdict(lambda: 'None')
    for time in time_period:
        for rank in rank_list:
            # Workaround for potentially nonexistent files
            if not os.path.isfile("Archive/{}_{}_{}.csv".format(date, time, rank)):
                continue

            stats_dict = defaultdict(lambda: 'None')
            with open("Archive/{}_{}_{}.csv".format(date, time, rank), "r") as data:
                read_data = csv.reader(data, delimiter=',', quotechar='|')
                # Skip headers
                next(read_data, None)
                for row in read_data:
                    stats_dict[row[0]] = [row[1], row[2], row[3], row[4], row[5]]
            all_stats.update({'{}_{}'.format(time, rank): stats_dict})

    # Uncomment to print sample stats
    # print(all_stats['Week_Silver']['Sombra'][1])
    return all_stats


if __name__ == '__main__':
    weekly_post()
