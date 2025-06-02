import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd 


class LinkedInJobScraper:
    def __init__(self):
        self.driver = None
        self._initialize_driver()

    def _initialize_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            st.toast("WebDriver initialized successfully (headless mode).")
        except Exception as e:
            st.error(f"Error initializing WebDriver: {e}")
            raise

    def _navigate_to_jobs_page(self):
        try:
            self.driver.get("https://www.linkedin.com/jobs/search?trk=guest_homepage-basic_guest_nav_menu_jobs&position=1&pageNum=0")
            st.toast("Navigated to LinkedIn jobs page.")
        except Exception as e:
            st.error(f"Error navigating to jobs page: {e}")
            raise

    def _dismiss_modal(self):
        try:
            dismiss_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']"))
            )
            time.sleep(2)
            dismiss_button.click()
            st.toast("Dismissed sign-in modal.")
        except Exception:
            st.toast("Could not dismiss sign-in modal, it might not be present or an error occurred.")

    def _perform_search(self, query):
        try:
            search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "job-search-bar-keywords"))
                )
            search_box.send_keys(query)
            st.toast(f"Typed: '{query}' into the search box.")
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)
            st.toast("Search performed.")
        except Exception as e:
            st.error(f"Error interacting with search box: {e}")
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
            st.error("WebDriver is not initialized. Exiting.")
            return []

        self._navigate_to_jobs_page()
        self._dismiss_modal()
        self._perform_search(search_query)

        all_job_listings = []
        scraped_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        # Use a placeholder to update progress dynamically
        progress_text = st.empty()

        while scraped_count < num_results_to_scrape:
            current_page_jobs = self._scrape_visible_job_cards()

            for job in current_page_jobs:
                if job not in all_job_listings:
                    all_job_listings.append(job)
                    scraped_count += 1
                    progress_text.info(f"Scraped {scraped_count}/{num_results_to_scrape}: Job: {job['Job Name']}, Company: {job['Company']}, Location: {job['Location']}")
                if scraped_count >= num_results_to_scrape:
                    break

            if scraped_count >= num_results_to_scrape:
                break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                st.warning("No more new results to load by scrolling.")
                break
            last_height = new_height
        
        progress_text.empty() 
        return all_job_listings[:num_results_to_scrape]

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            st.toast("Browser closed.")


st.set_page_config(page_title="LinkedIn Job Scraper", layout="centered")

st.title("LinkedIn Job Scraper")
st.markdown("Enter your job search criteria below to scrape listings from LinkedIn.")

job_query = st.text_input("Job Title or Company:",  placeholder="e.g Python Developer ,  Google")
num_results = st.number_input("Number of results to scrape:", min_value=1, max_value=10, value=1, step=1)

if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

if st.button("Scrape Jobs"):
    if not job_query:
        st.toast("Please enter a search query.")
    else:
        scraper = None
        st.session_state.scraped_data = []
        st.session_state.last_query = job_query

        try:
            with st.spinner("Initializing WebDriver and navigating..."):
                scraper = LinkedInJobScraper()
            
            scraped_data = scraper.scrape_jobs(job_query, num_results)
            st.session_state.scraped_data = scraped_data

            if scraped_data:
                st.success(f"Successfully scraped {len(scraped_data)} job listings!")
                st.subheader("Scraped Job Information:")
                st.dataframe(scraped_data)
            else:
                st.toast("No job listings were scraped.")
        except Exception as e:
            st.error(f"An error occurred during the scraping process: {e}")
        finally:
            if scraper:
                scraper.close_browser()

if st.session_state.scraped_data:
    df = pd.DataFrame(st.session_state.scraped_data)
    csv_file = df.to_csv(index=False).encode('utf-8')
    
    file_name = f"linkedin_jobs_{st.session_state.last_query.replace(' ', '_').replace('/', '_')}.csv"
    
    st.download_button(
        label="Download Scraped Data as CSV",
        data=csv_file,
        file_name=file_name,
        mime="text/csv",
        help="Click to download the scraped job listings as a CSV file."
    )

st.markdown("---")
st.markdown("This app uses Selenium in headless mode to scrape job data from LinkedIn.")
