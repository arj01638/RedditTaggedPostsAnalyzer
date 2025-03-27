from rtpa.analysis import analyze
from rtpa.scraping.old_reddit import scrape as reddit_scrape

def main():
    while True:
        choice = input("Scrape or Analyze? (s/a): ").strip().lower()
        if choice == 's':
            try:
                reddit_scrape()
            except Exception as e:
                print(f"An error occurred during scraping: {e}")
        elif choice == 'a':
            try:
                analyze()
            except Exception as e:
                print(f"An error occurred during analysis: {e}")
        else:
            print("Please choose 's' for scrape or 'a' for analyze.")

if __name__ == '__main__':
    main()
