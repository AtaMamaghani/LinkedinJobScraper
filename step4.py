from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class LinkedInJobScraper:
    def __init__(self):
        self.driver = None
        self._initialize_driver()

    def _initialize_driver(self):
        try:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            print("WebDriver initialized successfully.")
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            raise

    def _navigate_to_jobs_page(self):
        try:
            self.driver.get("https://www.linkedin.com/jobs/search?trk=guest_homepage-basic_guest_nav_menu_jobs&position=1&pageNum=0")
            print("Navigated to LinkedIn jobs page.")
        except Exception as e:
            print(f"Error navigating to jobs page: {e}")
            raise

    def _dismiss_modal(self):
        try:
            dismiss_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']"))
            )
            time.sleep(2)
            dismiss_button.click()
            print("Dismissed sign-in modal.")
        except Exception:
            print("Could not dismiss sign-in modal, it might not be present or an error occurred.")

    def _perform_search(self, query):
        try:
            search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "job-search-bar-keywords"))
                )
            search_box.send_keys(query)
            print(f"Typed: '{query}' into the search box.")
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)
            print("Search performed.")
        except Exception as e:
            print(f"Error interacting with search box: {e}")
            raise

    def _scrape_visible_job_cards(self):
        job_cards_data = []
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")

        for card in job_cards:
            try:
                job_name_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__title")
                company_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle")
                location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")

                job_name = job_name_element.text.strip()
                company = company_element.text.strip()
                location = location_element.text.strip()

                job_cards_data.append({
                    "Job Name": job_name,
                    "Company": company,
                    "Location": location
                })
            except Exception:
                continue
        return job_cards_data

    def scrape_jobs(self, search_query, num_results_to_scrape):
        if not self.driver:
            print("WebDriver is not initialized. Exiting.")
            return []

        self._navigate_to_jobs_page()
        self._dismiss_modal()
        self._perform_search(search_query)

        all_job_listings = []
        scraped_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while scraped_count < num_results_to_scrape:
            current_page_jobs = self._scrape_visible_job_cards()

            for job in current_page_jobs:
                if job not in all_job_listings:
                    all_job_listings.append(job)
                    scraped_count += 1
                    print(f"Scraped {scraped_count}/{num_results_to_scrape}: Job: {job['Job Name']}, Company: {job['Company']}, Location: {job['Location']}")
                if scraped_count >= num_results_to_scrape:
                    break

            if scraped_count >= num_results_to_scrape:
                break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more new results to load by scrolling.")
                break
            last_height = new_height

        return all_job_listings[:num_results_to_scrape]

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


if __name__ == "__main__":
    user_search_query = input("Enter the job title or company you want to search for: ")
    num_results_to_scrape = int(input("How many job results do you want to scrape? "))

    scraper = LinkedInJobScraper()
    try:
        scraped_data = scraper.scrape_jobs(user_search_query, num_results_to_scrape)

        print("\n--- Scraped Job Information ---")
        if scraped_data:
            for job in scraped_data:
                print(f"Job Name: {job['Job Name']}")
                print(f"Company: {job['Company']}")
                print(f"Location: {job['Location']}")
                print("-" * 30)
        else:
            print("No job listings were scraped.")

    except Exception as e:
        print(f"An error occurred during the scraping process: {e}")
    finally:
        scraper.close_browser()
        input("Press Enter to exit...")
