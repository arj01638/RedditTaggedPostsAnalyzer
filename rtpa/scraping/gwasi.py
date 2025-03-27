import csv
import json
import os
import re
from datetime import timezone, datetime
import requests

def scrape_gwasi():
    file_name = "gwa.json"
    response_delta = requests.get('https://gwasi.com/delta.json')
    delta = response_delta.json()
    url = f"https://gwasi.com/base_{delta['base']}.json"
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {file_name} successfully.")
    else:
        print(f"Failed to download {file_name}. Status code: {response.status_code}")

    with open(file_name, 'r') as f:
        data = json.load(f)
    if not os.path.exists("data"):
        os.mkdir("data")
    csv_filename = "data/gwa.csv"
    posts = data['entries']
    fills = data['fills']
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Title', 'Tags', 'Upvotes', 'Subreddit', 'Comments', 'Post URL',
                         'Timestamp', 'Author', 'Audio Link', 'Duration', 'Fills'])
        total_posts = len(posts)
        checkpoints = len(posts) // 10 or 1
        j = 0
        skip_counts = {}
        subreddit_skips = 0
        script_offer_appends = 0
        script_fill_appends = 0
        for i, post in enumerate(posts, start=1):
            if i % checkpoints == 0:
                print(f"{i} / {total_posts} posts processed.")
            post_url = f"www.reddit.com/{post[0]}"
            subreddit = post[1]
            if subreddit not in ['gonewildaudio', 'GWAScriptGuild']:
                subreddit_skips += 1
                continue
            author = post[2]
            raw_title = post[4]
            if "verification" in post[3].lower():
                continue
            if "script offer" in post[3].lower():
                if "script offer" not in raw_title.lower():
                    raw_title = "[Script Offer] " + raw_title
            if "script fill" in post[3].lower():
                if "script fill" not in raw_title.lower():
                    raw_title = "[Script Fill] " + raw_title

            if post[7] > 0:
                duration = str(post[7])
                duration = duration[:-1] + ':' + str(int((float(duration[-1])/10.0) * 60)) + '0'
                if duration[0] == ':':
                    duration = '0' + duration
                if "script offer" in raw_title.lower():
                    duration = ''
                elif "script fill" not in raw_title.lower():
                    script_fill_appends += 1
                    raw_title = "[Script Fill] " + raw_title
            elif post[7] < 0:
                duration = str(post[7] * 100)
                if "script fill" in raw_title.lower():
                    duration = ''
                elif "script offer" not in raw_title.lower():
                    script_offer_appends += 1
                    raw_title = "[Script Offer] " + raw_title
            else:
                duration = '0'
            blacklist = ["[request]", "verification", "check-in", "check in", "[introduction]", "[discussion]"]
            if any(b.lower() in raw_title.lower() for b in blacklist):
                continue
            try:
                title = re.findall(r'(?<=])(?![\s\[\]]*$)[^\[\]]+\w+[^\[\]]+(?=\[)', raw_title)[0].strip()
            except IndexError:
                try:
                    title = re.findall(r'^(?![\s\[\]]*$)[^\[\]]+\w+[^\[\]]+(?=\[)', raw_title)[0].strip()
                except IndexError:
                    continue
            tags = re.findall(r'(?<=\[).+?(?=])', raw_title)
            tags_str = '|'.join(tags).lower()
            for bad in ["azeru official"]:
                tags_str = tags_str.replace(bad, '')
            timestamp = datetime.fromtimestamp(post[5], tz=timezone.utc).isoformat()
            upvotes = post[6]
            amt_fills = len(fills[post[0]]) if post[0] in fills else ''
            writer.writerow([title, tags_str, upvotes, subreddit, -1, post_url, timestamp, author, '', duration, amt_fills])
            j += 1
        print(f"Saved {csv_filename} successfully. {j} posts processed.")
        print(f"{(total_posts - j) / total_posts * 100:.2f}% posts skipped.")
    print("GWASI scraping complete.")
