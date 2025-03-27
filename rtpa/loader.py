import os
import pandas as pd
from dateutil import tz
from rtpa.exceptions import InsufficientData


def add_adjusted_upvotes(df):
    if len(df) < 1000:
        print("Error: Less than 1,000 posts. Inflation adjustment would probably be inaccurate. Aborting adjustment.")
        return df

    df['YearMonth'] = df['Timestamp'].dt.to_period('M')
    monthly_upvotes = df.groupby('YearMonth')['Upvotes'].mean()
    window_size = 1
    monthly_upvotes = monthly_upvotes.rolling(window_size, center=False).mean()

    # Fill NaN values for the first and last few points
    for i in range(window_size - 1):
        monthly_upvotes.iloc[i] = monthly_upvotes.iloc[i + 1:i + window_size].mean()
    for i in range(window_size - 1, 0, -1):
        monthly_upvotes.iloc[-i] = monthly_upvotes.iloc[-i - window_size:-i].mean()

    baseline_upvotes = monthly_upvotes.max()
    baseline_period = monthly_upvotes.idxmax()
    print(f"Baseline period: {baseline_period}, Baseline mean upvotes: {baseline_upvotes}")

    scaling_factors = baseline_upvotes / monthly_upvotes
    df['Adjusted Upvotes'] = df.apply(
        lambda row: row['Upvotes'] * scaling_factors.get(row['Timestamp'].to_period('M'), 1),
        axis=1
    )
    df['Scaling Factor'] = df['Timestamp'].apply(lambda ts: scaling_factors.get(ts.to_period('M'), 1))
    df['Upvotes'] = df['Adjusted Upvotes']
    return df


def normalize_upvotes_across_subreddits(df):
    subreddit_upvotes = df.groupby('Subreddit')['Upvotes'].mean()
    baseline_upvotes = subreddit_upvotes.max()
    scaling_factors = baseline_upvotes / subreddit_upvotes

    df['NormalizedUpvotes'] = df.apply(
        lambda row: row['Upvotes'] * scaling_factors.get(row['Subreddit'], 1),
        axis=1
    )
    print(df.groupby('Subreddit').apply(lambda x: x.sample(min(len(x), 3)))[
              ['Subreddit', 'Upvotes', 'NormalizedUpvotes']])
    df['Upvotes'] = df['NormalizedUpvotes']
    return df


def load_df(filenames, subreddit, filter_tags, time_cutoff, normalize_subreddits=False, adjust_inflation=False):
    dfs = []
    local_zone = tz.tzlocal()
    for filename in filenames:
        if not filename.endswith(".csv"):
            filename += ".csv"
        if not os.path.exists("data"):
            os.mkdir("data")
        print(f"Loading {filename}...")
        df = pd.read_csv(f"data/{filename}")
        dfs.append(df)
    df = pd.concat(dfs)
    print(f"Loaded {len(filenames)} file(s) for a total of {len(df)} posts.")

    # Drop duplicates by Title, Subreddit, and Author
    size = len(df)
    df = df.groupby(['Title', 'Subreddit', 'Author'], as_index=False).agg({
        'Tags': 'first', 'Upvotes': 'max', 'Comments': 'max',
        'Post URL': 'first', 'Timestamp': 'first', 'Audio Link': 'first',
        'Duration': 'first', 'Fills': 'first'
    })
    print(f"Dropped {size - len(df)} duplicate posts. ({size} -> {len(df)})")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Hour_UTC'] = df['Timestamp'].dt.hour
    df['Timestamp_Local'] = df['Timestamp'].dt.tz_convert(local_zone)
    df['Hour_Local'] = df['Timestamp_Local'].dt.hour
    df['Day_Local'] = df['Timestamp_Local'].dt.dayofweek

    if normalize_subreddits:
        print("Normalizing upvotes across subreddits...")
        df = normalize_upvotes_across_subreddits(df)
    if adjust_inflation:
        print("Adjusting upvotes for inflation...")
        df = add_adjusted_upvotes(df)

    size = len(df)
    for filter_tag in filter_tags:
        tag = filter_tag.strip().lower()
        df = df[df['Tags'].str.contains(tag, na=False)]
        print(f"Filtered out {size - len(df)} posts not containing {tag}.")
        size = len(df)
    if subreddit:
        df = df[df['Subreddit'].str.lower() == subreddit.lower()]
        print(f"Filtered out {size - len(df)} posts from other subreddits.")

    if len(df) < 1:
        raise InsufficientData()
    size = len(df)
    df = df[df['Timestamp_Local'] < df['Timestamp_Local'].max() - pd.Timedelta(days=14)]
    print(f"Filtered out {size - len(df)} posts within 2 weeks of the latest post.")

    if len(df.groupby('Subreddit').filter(lambda x: len(x) < 3)) > 0:
        size = len(df)
        print("Filtering out subreddits with insufficient data...")
        df = df.groupby('Subreddit').filter(lambda x: len(x) >= 3)
        print(f"Filtered out subreddits with less than 3 posts. ({size} -> {len(df)})")

    if time_cutoff is not None:
        size = len(df)
        df = df[df['Timestamp_Local'] > df['Timestamp_Local'].max() - pd.Timedelta(days=30 * time_cutoff)]
        print(f"Filtered out {size - len(df)} posts before {time_cutoff} months ago.")
    return df
