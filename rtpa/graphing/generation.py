import re
import numpy as np
import pandas as pd
from dateutil import tz
from datetime import datetime
from rtpa.stats import perform_analysis_with_groups
from rtpa.graphing.utils import plot_bar_with_ci

def format_hour(hour):
    if hour == 0:
        return '12 AM'
    elif hour == 12:
        return '12 PM'
    elif hour < 12:
        return f'{hour} AM'
    else:
        return f'{hour - 12} PM'

def generate_hourly_bar_graph(df, confidence_level, subreddit, directory):
    directory = directory + "/time"
    return generate_hour_graph(df, confidence_level, 1,
        f"graphs{directory}/upv_diff_by_hour{'_in_' + subreddit if subreddit else ''}", subreddit)

def generate_hour_block_bar_graph(df, confidence_level, subreddit, hour_block, directory):
    directory = directory + "/time"
    return generate_hour_graph(df, confidence_level, hour_block,
        f"graphs{directory}/upv_diff_by_{hour_block}_hour_block{'_in_' + subreddit if subreddit else ''}", subreddit)

def generate_hour_graph(df, confidence_level, hours_chunk, file_name, subreddit):
    hourly_results = get_hourly_analysis_results(df, 'Upvotes', confidence_level, hours_chunk)
    utc_zone = tz.tzutc()
    local_zone = tz.tzlocal()
    local_hours = [datetime(2000,1,1,hour,0,0, tzinfo=utc_zone).astimezone(local_zone).hour for hour in range(0,24, hours_chunk)]
    local_hours_12h = [format_hour(hour) for hour in local_hours]
    hourly_means = [0 if np.isnan(r[0]) else r[0] for r in hourly_results]
    hourly_cis = [np.array([0,0]) if np.isnan(r[1]).any() else r[1] for r in hourly_results]
    hourly_significant = [r[2] for r in hourly_results]
    sorted_indices = np.argsort(local_hours)
    local_hours_sorted = np.array(local_hours_12h)[sorted_indices]
    means_sorted = np.array(hourly_means)[sorted_indices]
    cis_sorted = np.array(hourly_cis).T[:, sorted_indices]
    sig_sorted = np.array(hourly_significant)[sorted_indices]
    return plot_bar_with_ci(local_hours_sorted, means_sorted, cis_sorted, sig_sorted,
        f'Average Upvote Difference by {"Hour" if hours_chunk==1 else str(hours_chunk)+" Hour Block"} {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Hour', 'Mean Difference', file_name)

def get_hourly_analysis_results(df, metric, confidence_level, hours_chunk=1):
    results = []
    for hour in range(0,24, hours_chunk):
        start = hour
        end = (hour+hours_chunk)%24
        if start < end:
            group_with = df[(df['Hour_UTC']>=start) & (df['Hour_UTC']<end)]
            group_without = df[~((df['Hour_UTC']>=start) & (df['Hour_UTC']<end))]
        else:
            group_with = df[(df['Hour_UTC']>=start) | (df['Hour_UTC']<end)]
            group_without = df[~((df['Hour_UTC']>=start) | (df['Hour_UTC']<end))]
        min_amt = (len(df)//1000)+5
        if len(group_with) > min_amt and len(group_without) > min_amt:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
            results.append((mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
        else:
            results.append((np.nan, (np.nan, np.nan), False))
    return results

def generate_day_bar_graph(df, confidence_level, subreddit, directory):
    directory = directory + "/time"
    daily_results = get_daily_analysis_results(df, 'Upvotes', confidence_level)
    days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    daily_means = [0 if np.isnan(r[0]) else r[0] for r in daily_results]
    daily_cis = [np.array([0,0]) if np.isnan(r[1]).any() else r[1] for r in daily_results]
    daily_sig = [r[2] for r in daily_results]
    sorted_indices = np.argsort([r[3] for r in daily_results])
    days_sorted = np.array(days)[sorted_indices]
    means_sorted = np.array(daily_means)[sorted_indices]
    cis_sorted = np.array(daily_cis).T[:, sorted_indices]
    sig_sorted = np.array(daily_sig)[sorted_indices]
    return plot_bar_with_ci(days_sorted, means_sorted, cis_sorted, sig_sorted,
        f'Average Upvote Difference by Day of the Week {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Day of the Week', 'Mean Difference', f"graphs{directory}/upv_diff_by_day_of_week{'_in_'+subreddit if subreddit else ''}")

def get_daily_analysis_results(df, metric, confidence_level):
    results = []
    for day in range(7):
        group_with = df[df['Day_Local']==day]
        group_without = df[df['Day_Local']!=day]
        if len(group_with)>1 and len(group_without)>1:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
            results.append((mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level, day))
        else:
            results.append((np.nan, (np.nan, np.nan), False, day))
    return results

def generate_subreddit_bar_graph(df, confidence_level, directory):
    results = get_subreddit_analysis_results(df, 'Upvotes', confidence_level)
    if len(results)==1:
        print("Only one subreddit in dataset, graph generation skipped.")
        return "[SUBREDDIT GRAPH FAILED: ONLY ONE SUBREDDIT]"
    subreddits = [r[0] for r in results]
    means = [r[1] for r in results]
    cis = np.array([r[2] for r in results]).T
    sig = [r[3] for r in results]
    return plot_bar_with_ci(subreddits, means, cis, sig,
        f'Average Upvote Difference by Subreddit\n(Conf={confidence_level*100}%)',
        'Subreddit', 'Mean Difference', f"graphs{directory}/upv_diff_by_subreddit")

def get_subreddit_analysis_results(df, metric, confidence_level):
    subs = df['Subreddit'].dropna().unique()
    results = []
    for sub in subs:
        if isinstance(sub, str):
            group_with = df[df['Subreddit']==sub]
            group_without = df[df['Subreddit']!=sub]
            if len(group_with)>1 and len(group_without)>1:
                mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
                results.append((sub, mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
            else:
                results.append((sub, np.nan, (np.nan, np.nan), False))
        else:
            results.append((sub, np.nan, (np.nan, np.nan), False))
    return results

def generate_common_tag_bar_graph(df, confidence_level, subreddit, top_n_tags, directory):
    directory = directory + "/tags"
    results = get_tags_analysis_results(df, 'Upvotes', confidence_level, top_n_tags)
    tags = [r[0] for r in results]
    means = [r[1] for r in results]
    cis = np.array([r[2] for r in results]).T
    sig = [r[3] for r in results]
    return plot_bar_with_ci(tags, means, cis, sig,
        f'Average Upvote Difference in Top {top_n_tags} Tags {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Tag', 'Mean Difference', f"graphs{directory}/upv_diff_by_top_common_{top_n_tags}_tags{'_in_'+subreddit if subreddit else ''}")

def get_tags_analysis_results(df, metric, confidence_level, n=None):
    ignored = ["script offer", "script fill"]
    tag_counts = df['Tags'].str.split('|').explode().value_counts()
    min_amt = (len(df)//1000)+5
    tag_counts = tag_counts[tag_counts>=min_amt]
    top_tags = tag_counts.index
    results = []
    count = 0
    for tag in top_tags:
        if tag in ignored:
            continue
        escaped_tag = re.escape(tag)
        group_with = df[df['Tags'].str.contains(escaped_tag, na=False, regex=True)]
        group_without = df[~df['Tags'].str.contains(escaped_tag, na=False, regex=True)]
        if len(group_with)>min_amt and len(group_without)>min_amt:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
            if np.isnan(mean_diff):
                continue
            results.append((tag, mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
            count += 1
            if n is not None and count==n:
                break
    return results

def get_top_and_worst_tags(df, metric, confidence_level, n=5):
    all_results = get_tags_analysis_results(df, metric, confidence_level, n=None)
    best = sorted(all_results, key=lambda x: x[1], reverse=True)[:n]
    worst = sorted(all_results, key=lambda x: x[1])[:n]
    return best, worst

def generate_top_and_worst_tags_graph(best_tags, worst_tags, confidence_level, subreddit, directory):
    directory = directory + "/tags"
    worst_tags.reverse()
    best_means = [tag[1] for tag in best_tags]
    best_cis = np.array([tag[2] for tag in best_tags]).T
    best_sig = [tag[3] for tag in best_tags]
    best_names = [tag[0] for tag in best_tags]
    worst_means = [tag[1] for tag in worst_tags]
    worst_cis = np.array([tag[2] for tag in worst_tags]).T
    worst_sig = [tag[3] for tag in worst_tags]
    worst_names = [tag[0] for tag in worst_tags]
    out1 = plot_bar_with_ci(best_names, best_means, best_cis, best_sig,
        f'Average Upvote Difference in Top Tags {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Tag', 'Mean Difference', f"graphs{directory}/upv_diff_by_top_{len(best_names)}_tags{'_in_'+subreddit if subreddit else ''}")
    out2 = plot_bar_with_ci(worst_names, worst_means, worst_cis, worst_sig,
        f'Average Upvote Difference in Worst Tags {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Tag', 'Mean Difference', f"graphs{directory}/upv_diff_by_bottom_{len(worst_names)}_tags{'_in_'+subreddit if subreddit else ''}")
    return out1, out2

def generate_duration_bar_graph(df, confidence_level, subreddit, block_minutes, directory):
    df = df[df['Duration'] != ''].dropna(subset=['Duration'])
    df = df[~df['Duration'].str.contains('-')]
    results = get_duration_analysis_results(df, 'Upvotes', confidence_level, block_minutes)
    if all(np.isnan(r[1]) for r in results):
        print("Not enough data for duration graph.")
        return "[DURATION GRAPH FAILED]"
    durations = [r[0] for r in results]
    means = [r[1] for r in results]
    cis = np.array([r[2] for r in results]).T
    sig = [r[3] for r in results]
    return plot_bar_with_ci(durations, means, cis, sig,
        f'Average Upvote Difference by Duration Blocks of {block_minutes} Minutes {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Duration Block', 'Mean Difference', f"graphs{directory}/upv_diff_by_duration_blocks_of_{block_minutes}_minutes{'_in_'+subreddit if subreddit else ''}")

def get_duration_analysis_results(df, metric, confidence_level, block_minutes):
    df_copy = df.dropna(subset=['Duration']).copy()
    def convert_to_minutes(tstr):
        if tstr.startswith(':'):
            tstr = '0' + tstr
        parts = tstr.split(':')
        minutes = int(parts[0]) if parts[0] else 0
        seconds = int(parts[1]) if len(parts)==2 and parts[1] else 0
        return minutes + seconds//60
    df_copy['TotalMinutes'] = df_copy['Duration'].apply(lambda x: convert_to_minutes(x) if isinstance(x, str) else np.nan)
    df_copy['DurationBlock'] = (df_copy['TotalMinutes'] // block_minutes) * block_minutes
    min_amt = (len(df)//1000)+5
    results = []
    for block in sorted(df_copy['DurationBlock'].unique()):
        group_with = df_copy[df_copy['DurationBlock']==block]
        group_without = df_copy[df_copy['DurationBlock']!=block]
        if len(group_with)>min_amt and len(group_without)>min_amt:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
            label = f"{int(block)}-{int(block)+block_minutes-1} mins"
            results.append((label, mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
        else:
            label = f"{int(block)}-{int(block)+block_minutes-1} mins"
            results.append((label, np.nan, (np.nan, np.nan), False))
    return results

def generate_tag_count_bar_graph(df, confidence_level, subreddit, directory):
    directory = directory + "/tags"
    results = get_tag_count_analysis_results(df, 'Upvotes', confidence_level)
    if all(np.isnan(r[1]) for r in results):
        print("Not enough data for tag count graph.")
        return "[TAG COUNT GRAPH FAILED]"
    tag_counts = [r[0] for r in results]
    means = [r[1] for r in results]
    cis = np.array([r[2] for r in results]).T
    sig = [r[3] for r in results]
    return plot_bar_with_ci(tag_counts, means, cis, sig,
        f'Average Upvote Difference by Number of Tags {"in "+subreddit if subreddit else ""}\n(Conf={confidence_level*100}%)',
        'Number of Tags', 'Mean Difference', f"graphs{directory}/upv_diff_by_tag_count{'_in_'+subreddit if subreddit else ''}")

def get_tag_count_analysis_results(df, metric, confidence_level):
    df['TagCount'] = df['Tags'].apply(lambda x: len(x.split('|')) if pd.notnull(x) else 0)
    min_amt = (len(df)//1000)+5
    results = []
    for count in range(1,60):
        group_with = df[df['TagCount']==count]
        group_without = df[df['TagCount']!=count]
        if len(group_with)>min_amt and len(group_without)>min_amt:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(group_with, group_without, metric, confidence_level)
            results.append((count, mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
        else:
            results.append((count, np.nan, (np.nan, np.nan), False))
    df.drop('TagCount', axis=1, inplace=True)
    return results

def generate_hour_bar_graph_for_each_day_of_week(df, confidence_level, subreddit, directory):
    directory = directory + "/time"
    for day in range(7):
        day_name = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][day]
        day_df = df[df['Day_Local']==day]
        generate_hour_graph(day_df, confidence_level, 1,
            f"graphs{directory}/days/upv_diff_by_hour{'_in_'+subreddit if subreddit else ''}{'_on_'+day_name}", subreddit)
    return f"graphs{directory}/days/"


def generate_script_length_bar_graph(df, confidence_level, subreddit, word_blocks, directory):
    # Filter rows where Duration is not empty and contains a dash (indicating script length)
    df = df.dropna(subset=['Duration'])
    df = df[df['Duration'] != '']
    df = df[df['Duration'].str.contains('-')]
    # Remove the leading '-' from the duration values
    df['Duration'] = df['Duration'].apply(lambda x: x[1:])

    # Calculate analysis results based on word count
    duration_results = get_word_count_analysis_results(df, 'Upvotes', confidence_level, word_blocks)
    if all(np.isnan(result[1]) for result in duration_results):
        print("Not enough data for script length graph.")
        return "[GENERATION FAILED FOR SCRIPT GRAPH: NOT ENOUGH DATA]"
    durations = [result[0] for result in duration_results]
    duration_means = [result[1] for result in duration_results]
    duration_cis = np.array([result[2] for result in duration_results]).T
    duration_significant = [result[3] for result in duration_results]

    return plot_bar_with_ci(
        durations, duration_means, duration_cis, duration_significant,
        f'Average Upvote Difference by Script Length of {word_blocks} Words '
        f'{"in " + subreddit if subreddit else ""}\n(Conf={confidence_level * 100}%)',
        'Script Length Block', 'Mean Difference',
        f"graphs{directory}/upv_diff_by_word_blocks_of_{word_blocks}_words{'_in_' + subreddit if subreddit else ''}"
    )


def get_word_count_analysis_results(df, metric, confidence_level, word_blocks):
    # Convert the Duration column to integer word count (assuming duration values represent word counts)
    df = df.copy()
    df['Duration'] = df['Duration'].astype(int)
    df['DurationBlock'] = (df['Duration'] // word_blocks) * word_blocks
    min_amt = (len(df) // 1000) + 5
    results = []
    for block in sorted(df['DurationBlock'].unique()):
        group_with = df[df['DurationBlock'] == block]
        group_without = df[df['DurationBlock'] != block]
        if len(group_with) > min_amt and len(group_without) > min_amt:
            mean_diff, ci_low, ci_high, p_value, _ = perform_analysis_with_groups(
                group_with, group_without, metric, confidence_level
            )
            block_label = f"{int(block)}-{int(block) + word_blocks - 1} words"
            results.append((block_label, mean_diff, (ci_low, ci_high), p_value < 1.0 - confidence_level))
        else:
            block_label = f"{int(block)}-{int(block) + word_blocks - 1} words"
            results.append((block_label, np.nan, (np.nan, np.nan), False))
    return results
