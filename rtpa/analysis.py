import os
from datetime import datetime
import pandas as pd
from dateutil import tz
from rtpa.graphing.generation import (
    generate_hourly_bar_graph, generate_hour_block_bar_graph, generate_subreddit_bar_graph,
    generate_common_tag_bar_graph, get_top_and_worst_tags, generate_top_and_worst_tags_graph,
    generate_day_bar_graph, generate_duration_bar_graph, generate_tag_count_bar_graph,
    generate_hour_bar_graph_for_each_day_of_week
)
from rtpa.loader import load_df
from rtpa.stats import perform_analysis_with_groups


def debug_print(message, debug_mode):
    if debug_mode:
        print(message)


def average_scores(group):
    return group.mean()


def perform_analysis(df, group_by, metric, value, confidence_level, debug_mode, duration_hours=1):
    df_grouped = df.copy()

    if group_by == 'Timestamp':
        local_hour = int(value)
        now_local = datetime.now(tz.tzlocal())
        now_utc = now_local.astimezone(tz.tzutc())
        target_hour_utc = (now_local.replace(hour=local_hour, minute=0, second=0, microsecond=0) +
                           (now_utc - now_local)).hour
        df_grouped['Hour_UTC'] = df_grouped['Timestamp'].dt.hour
        end_hour_utc = (target_hour_utc + duration_hours) % 24
        if end_hour_utc <= target_hour_utc:
            hour_mask = (df_grouped['Hour_UTC'] >= target_hour_utc) | (df_grouped['Hour_UTC'] < end_hour_utc)
        else:
            hour_mask = df_grouped['Hour_UTC'].between(target_hour_utc, end_hour_utc, inclusive='both')
        group_with_value = df_grouped[hour_mask]
        group_without_value = df_grouped[~hour_mask]
        debug_print(f"Group with value:\n{group_with_value.head()}", debug_mode)
    else:
        size = len(df)
        df_grouped = df.groupby('Title').agg({group_by: 'first', metric: average_scores}).reset_index()
        print(f"Filtered out {size - len(df_grouped)} duplicate posts. ({size} -> {len(df_grouped)})")
        group_with_value = df_grouped[df_grouped[group_by].str.contains(value, na=False)]
        group_without_value = df_grouped[~df_grouped[group_by].str.contains(value, na=False)]
        debug_print(f"Group with '{value}':\n{group_with_value.head()}", debug_mode)

    mean_diff, ci_low, ci_high, p_value, t_stat = perform_analysis_with_groups(
        group_with_value, group_without_value, metric, confidence_level
    )

    output = f"Analysis based on {metric.lower()} by {group_by.lower()}:\n\n"
    if group_by == "Tags":
        output += (
            f"You have made {len(group_with_value)} posts with '{value}' and {len(group_without_value)} posts without '{value}' "
            f"({len(group_with_value) / len(df_grouped) * 100:.2f}%, total posts = {len(df_grouped)}).\n")
    elif group_by == "Subreddit":
        output += (
            f"You have made {len(group_with_value)} posts in '{value}' and {len(group_without_value)} posts in other subreddits.\n")
    elif group_by == "Timestamp":
        output += (
            f"You have made {len(group_with_value)} posts between {target_hour_utc}:00 and {(target_hour_utc + duration_hours) % 24}:00, "
            f"and {len(group_without_value)} posts at other times.\n")
    output += (
        f"There is a {'significant' if p_value < 1.0 - confidence_level else 'not significant'} difference in {metric.lower()}.\n"
        f"Mean difference: {mean_diff:.2f} (CI: {ci_low:.2f} to {ci_high:.2f}).\n"
        f"T-statistic: {t_stat:.2f}, P-value: {p_value:.4f}\n")
    return output


def analyze():
    debug_mode = input("Run in debug mode? (yes/no): ").strip().lower() == 'yes'
    while True:
        filename = input("Enter the CSV filename to analyze: ").strip()
        if not filename.endswith(".csv"):
            filename += ".csv"
        if not os.path.isfile(os.path.join("data", filename)) and ',' not in filename:
            print("File not found. Please try again.")
        else:
            break

    subreddit_input = None
    if filename[0].lower() == 'u':
        subreddit_input = input("Enter the subreddit to filter (or leave blank for all): ").lower().strip()

    filter_tag = input("Enter a tag to filter by (or leave blank): ").lower().strip()
    filter_tags = filter_tag.split(',') if filter_tag else []

    if ',' in filename:
        files = filename.split(',')
        df = load_df(files, subreddit_input, filter_tags, 24)
    else:
        df = load_df([filename], subreddit_input, filter_tags, 24, adjust_inflation=(filename in ["gwa.csv", "gwa"]))

    debug_print(f"Data loaded:\n{df.head()}", debug_mode)
    analysis_mode = None
    while analysis_mode not in ['graphs', 'questions', 'g', 'q']:
        analysis_mode = input("Generate graphs (g) or perform questions analysis (q)? ").lower().strip()

    if analysis_mode.startswith('g'):
        directory = "/" + " ".join([file.replace(".csv", "") for file in filename.split(',')])
        print(f"Graphs will be stored in {directory}/")
        generate_subreddit_bar_graph(df, 0.95, directory)
        print("Subreddit graph generated.")
        generate_hourly_bar_graph(df, 0.95, subreddit_input, directory)
        print("Hourly graph generated.")
        generate_hour_block_bar_graph(df, 0.95, subreddit_input, 3, directory)
        print("Hour block graph generated.")
        generate_day_bar_graph(df, 0.95, subreddit_input, directory)
        print("Day graph generated.")
        top_n_tags = input("Enter number of top common tags (default 10): ").strip()
        top_n_tags = int(top_n_tags) if top_n_tags else 10
        generate_common_tag_bar_graph(df, 0.95, subreddit_input, top_n_tags, directory)
        print("Tag graph generated.")
        best_tags, worst_tags = get_top_and_worst_tags(df, 'Upvotes', 0.95, 5)
        generate_top_and_worst_tags_graph(best_tags, worst_tags, 0.95, subreddit_input, directory)
        print("Best/worst tags graph generated.")
        generate_duration_bar_graph(df, 0.95, subreddit_input, 3, directory)
        print("Duration graph generated.")
        generate_tag_count_bar_graph(df, 0.95, subreddit_input, directory)
        print("Tag count graph generated.")
        generate_hour_bar_graph_for_each_day_of_week(df, 0.95, subreddit_input, directory)
        print("Hourly graph for each day generated.")
    else:
        analysis_type = None
        while analysis_type not in ['tag', 'subreddit', 'time']:
            analysis_type = input("Analyze by 'tag', 'subreddit', or 'time': ").strip().lower()
        if analysis_type == 'time':
            value = input("Enter the hour (0-23): ").strip()
        else:
            value = input(f"Enter the {analysis_type} to analyze: ").strip()
        print(perform_analysis(df, analysis_type.capitalize(), 'Upvotes', value, 0.95, debug_mode))
    return
