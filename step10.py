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
    JOB_TYPE_MAPPING = {
        "Any": "",
        "Full-time": "F",
        "Part-time": "P",
        "Contract": "C",
        "Temporary": "T",
        "Volunteer": "V",
        "Internship": "I"
    }

    EXPERIENCE_LEVEL_MAPPING = {
        "Any": "",
        "Internship": "1",
        "Entry level": "2",
        "Associate": "3",
        "Mid-Senior level": "4",
        "Director": "5",
        "Executive": "6"
    }

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

    def _navigate_to_jobs_page(self, query, location, job_type_code, experience_level_code):
        try:
            base_url = "https://www.linkedin.com/jobs/search?"
            
            params = []
            if query:
                params.append(f"keywords={query.replace(' ', '%20')}")
            if location:
                params.append(f"location={location.replace(' ', '%20').replace(',', '%2C')}")
            if job_type_code:
                params.append(f"f_JT={job_type_code}")
            if experience_level_code:
                params.append(f"f_E={experience_level_code}")

            full_url = base_url + "&".join(params)
            
            self.driver.get(full_url)
            st.toast(f"Navigated to LinkedIn jobs page with filters: {query}, {location}, {job_type_code}, {experience_level_code}")
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

    def _scrape_visible_job_cards(self):
        job_cards_data = []
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")

        for card in job_cards:
            try:
                job_name_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__title")
                company_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle")
                location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                
                job_link_element = card.find_element(By.CSS_SELECTOR, ".base-card__full-link")
                job_link = job_link_element.get_attribute('href')

                job_name = job_name_element.text.strip()
                company = company_element.text.strip()
                location = location_element.text.strip()

                job_cards_data.append({
                    "Job Name": job_name,
                    "Company": company,
                    "Location": location,
                    "Job Link": job_link
                })
            except Exception:
                continue
        return job_cards_data

    def scrape_jobs(self, search_query, location_query, job_type, experience_level, num_results_to_scrape):
        if not self.driver:
            st.error("WebDriver is not initialized. Exiting.")
            return []

        job_type_code = self.JOB_TYPE_MAPPING.get(job_type, "")
        experience_level_code = self.EXPERIENCE_LEVEL_MAPPING.get(experience_level, "")

        self._navigate_to_jobs_page(search_query, location_query, job_type_code, experience_level_code)
        self._dismiss_modal()

        all_job_listings = []
        scraped_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        progress_text = st.empty()

        while scraped_count < num_results_to_scrape:
            current_page_jobs = self._scrape_visible_job_cards()

            for job in current_page_jobs:
                if job['Job Link'] not in [j['Job Link'] for j in all_job_listings]:
                    all_job_listings.append(job)
                    scraped_count += 1
                    progress_text.info(f"Scraped {scraped_count}/{num_results_to_scrape}: Job: {job['Job Name']}, Company: {job['Company']}")
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

job_query = st.text_input("Job Title or Company:",  placeholder="e.g. Python Developer, Google")
location_query = st.text_input("Location (Optional):", placeholder="e.g. Berlin, Germany")
job_type_options = list(LinkedInJobScraper.JOB_TYPE_MAPPING.keys())
job_type_selected = st.selectbox("Job Type:", options=job_type_options, index=0)

experience_level_options = list(LinkedInJobScraper.EXPERIENCE_LEVEL_MAPPING.keys())
experience_level_selected = st.selectbox("Experience Level:", options=experience_level_options, index=0)

num_results = st.number_input("Number of results to scrape:", min_value=1, max_value=20, value=5, step=1)

if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'last_location_query' not in st.session_state:
    st.session_state.last_location_query = ""
if 'last_job_type' not in st.session_state:
    st.session_state.last_job_type = ""
if 'last_experience_level' not in st.session_state:
    st.session_state.last_experience_level = ""


if st.button("Scrape Jobs"):
    if not job_query:
        st.toast("Please enter a search query.")
    else:
        scraper = None
        st.session_state.scraped_data = []
        st.session_state.last_query = job_query
        st.session_state.last_location_query = location_query
        st.session_state.last_job_type = job_type_selected
        st.session_state.last_experience_level = experience_level_selected

        try:
            with st.spinner("Initializing WebDriver and navigating..."):
                scraper = LinkedInJobScraper()
            
            scraped_data = scraper.scrape_jobs(job_query, location_query, job_type_selected, experience_level_selected, num_results)
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
    
    file_name_parts = ["linkedin_jobs"]
    if st.session_state.last_query:
        file_name_parts.append(st.session_state.last_query.replace(' ', '_').replace('/', '_'))
    if st.session_state.last_location_query:
        file_name_parts.append(st.session_state.last_location_query.replace(' ', '_').replace('/', '_'))
    if st.session_state.last_job_type and st.session_state.last_job_type != "Any":
        file_name_parts.append(st.session_state.last_job_type.replace(' ', '_'))
    if st.session_state.last_experience_level and st.session_state.last_experience_level != "Any":
        file_name_parts.append(st.session_state.last_experience_level.replace(' ', '_'))
    file_name = "_".join(file_name_parts) + ".csv"

    st.download_button(
        label="Download Scraped Data as CSV",
        data=csv_file,
        file_name=file_name,
        mime="text/csv",
        help="Click to download the scraped job listings as a CSV file."
    )

st.markdown("---")
st.markdown("This app uses Selenium in headless mode to scrape job data from LinkedIn.")