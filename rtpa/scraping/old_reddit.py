import csv
import os
import re
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

def scrape():
    valid = ['profile','p','subreddit','s']
    while True:
        mode = input("Enter 'profile'/'p' or 'subreddit'/'s': ").strip().lower()
        if mode in valid:
            break
        else:
            print("Invalid input. Try again.")
    subreddit = None
    username = None
    if mode in ('profile','p'):
        username = input("Enter the Reddit username: ").strip()
    elif mode in ('subreddit','s'):
        subreddit = input("Enter the subreddit: ").strip()
    time_frame = None
    if mode in ('subreddit','s'):
        time_frame = input("Enter the time frame (all time, past year, past month, past week): ").strip().lower()
        while time_frame not in ["all time", "past year", "past month", "past week"]:
            print("Invalid time frame.")
            time_frame = input("Enter the time frame (all time, past year, past month, past week): ").strip().lower()
    scrape_old_reddit(username, subreddit, time_frame)

def scrape_old_reddit(username, subreddit, time_frame="all time"):
    if username:
        url = f'https://old.reddit.com/user/{username}/submitted/'
    elif subreddit:
        if time_frame == "all time":
            url = f'https://old.reddit.com/r/{subreddit}/top/?t=all'
        elif time_frame == "past year":
            url = f'https://old.reddit.com/r/{subreddit}/top/?t=year'
        elif time_frame == "past month":
            url = f'https://old.reddit.com/r/{subreddit}/top/?t=month'
        elif time_frame == "past week":
            url = f'https://old.reddit.com/r/{subreddit}/top/?t=week'
        else:
            print("Invalid time frame.")
            return
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=options)
    print(f"Scraping {url}...")
    driver.get(url)
    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    time.sleep(3)
    try:
        btn = driver.find_element(By.XPATH, "//button[@name='over18'][@value='yes']")
        btn.click()
        print("Over 18 warning accepted.")
    except Exception as e:
        print(f"No over 18 warning or error: {e}")
    posts_data = []
    j = 0
    while True:
        print(f"Scrolling batch {j+1}...")
        try:
            new_post_locator = (By.XPATH, '//div[contains(@class, "thing") and not(@already-seen)]')
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(new_post_locator))
            elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".expando-button.collapsed.hide-when-pinned.selftext")))
            for el in elements:
                try:
                    el.click()
                except Exception as ex:
                    print(f"Element click failed: {ex}")
                time.sleep(0.5)
            new_posts = driver.find_elements(*new_post_locator)
            for post in new_posts:
                title_el = post.find_element(By.CSS_SELECTOR, '.title > a.title')
                raw_title = title_el.text
                time_el = post.find_element(By.CSS_SELECTOR, '.tagline > time')
                timestamp = time_el.get_attribute('datetime')
                upvotes = post.get_attribute('data-score')
                comments = post.get_attribute('data-comments-count')
                post_url = "https://reddit.com" + post.get_attribute('data-url')
                author = post.get_attribute('data-author')
                links = post.find_elements(By.TAG_NAME, 'a')
                soundgasm_link = ""
                for link in links:
                    href = link.get_attribute('href')
                    if href and "soundgasm" in href:
                        soundgasm_link = href
                        break
                duration = ""
                if soundgasm_link:
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(soundgasm_link)
                    try:
                        duration_div = WebDriverWait(driver, 10).until(
                            lambda d: d.find_element(By.CSS_SELECTOR,
                                "#jp_container_1 > div > div.jp-gui.jp-interface > div.jp-time-holder > div.jp-duration")
                                if d.find_element(By.CSS_SELECTOR,
                                "#jp_container_1 > div > div.jp-gui.jp-interface > div.jp-time-holder > div.jp-duration").text != "00:00" else False
                        )
                    except TimeoutException:
                        print("No duration found or timed out.")
                        duration = ""
                    if duration_div:
                        duration = duration_div.text.strip('-')
                        print(f"Found duration {duration}.")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                else:
                    print("No soundgasm link found.")
                post_data = {
                    'title': raw_title,
                    'timestamp': timestamp,
                    'upvotes': upvotes,
                    'comments': comments,
                    'post_url': post_url,
                    'author': author,
                    'subreddit': subreddit or post.get_attribute('data-subreddit'),
                    'audiolink': soundgasm_link,
                    'duration': duration
                }
                posts_data.append(post_data)
                driver.execute_script('arguments[0].setAttribute("already-seen", "true");', post)
        except TimeoutException:
            print("No more posts found or timeout.")
            break
        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".next-button a"))
            )
            next_btn.click()
            j += 1
        except TimeoutException:
            print("No next button found or timed out.")
            break
    print(f"Found {len(posts_data)} posts.")
    if time_frame:
        time_frame = time_frame.replace(" ", "_")
    filename = f"{'s' if subreddit else 'u'}_{subreddit if subreddit else username}{'_' + time_frame if time_frame else ''}.csv"
    if not os.path.exists("data"):
        os.mkdir("data")
    with open(f"data/{filename}", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Tags', 'Upvotes', 'Subreddit', 'Comments', 'Post URL', 'Timestamp', 'Author', 'Audio Link', 'Duration', 'Fills'])
        for idx, post in enumerate(posts_data, start=1):
            print(f"Processing post {idx}/{len(posts_data)}...")
            try:
                title = re.findall(r'(?<=])(?![\s\[\]]*$)[^\[\]]+\w+[^\[\]]+(?=\[)', post['title'])[0].strip()
            except IndexError:
                try:
                    title = re.findall(r'^(?![\s\[\]]*$)[^\[\]]+\w+[^\[\]]+(?=\[)', post['title'])[0].strip()
                except IndexError:
                    print(f"No title found in {post['title']}. Skipping.")
                    continue
            tags = re.findall(r'(?<=\[).+?(?=])', post['title'])
            tags_str = '|'.join(tags).lower()
            writer.writerow([title, tags_str, post['upvotes'], post['subreddit'], post['comments'], post['post_url'], post['timestamp'], post['author'], post['audiolink'], post['duration'], ''])
    print(f"Scraping complete. Data saved to {filename}.")
    driver.quit()
