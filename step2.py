from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class LinkedInJobScraper:
    \
    def __init__(self):
      
        self.service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service)
        self.wait = WebDriverWait(self.driver, 15) 

        self.JOB_SEARCH_URL = "https://www.linkedin.com/jobs/search?trk=guest_homepage-basic_guest_nav_menu_jobs&position=1&pageNum=0"
        self.DISMISS_MODAL_BUTTON = (By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']")
        self.SEARCH_BAR_KEYWORDS = (By.ID, "job-search-bar-keywords")

    def open_linkedin_jobs_page(self):
        print(f"Navigating to {self.JOB_SEARCH_URL}")
        self.driver.get(self.JOB_SEARCH_URL)

    def dismiss_sign_in_modal(self):
       
        print("Attempting to dismiss sign-in modal...")
        try:
            dismiss_button = self.wait.until(
                EC.element_to_be_clickable(self.DISMISS_MODAL_BUTTON)
            )
            dismiss_button.click()
            print("Sign-in modal dismissed.")
        except Exception as e:
            print(f"Could not dismiss sign-in modal (it might not have appeared or timed out): {e}")

    def search_for_job(self, query):
        
        print(f"Searching for job: '{query}'")
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(self.SEARCH_BAR_KEYWORDS)
            )
            search_box.send_keys(query)
            print(f"Typed: '{query}' into the search box.")
            search_box.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"Error while searching for job: {e}")
            raise 

    def quit_driver(self):
        print("Closing the browser.")
        self.driver.quit()

if __name__ == "__main__":
    scraper = None
    try:
        user_search_query = input("Enter the job title or company you want to search for: ")

        scraper = LinkedInJobScraper()
        scraper.open_linkedin_jobs_page()
        scraper.dismiss_sign_in_modal() 
        scraper.search_for_job(user_search_query)

        print("\nSearch results loaded. Press Enter to close the browser...")
        input() 
    except Exception as e:
        print(f"An unexpected error occurred during the scraping process: {e}")

    finally:
        if scraper: 
            scraper.quit_driver()