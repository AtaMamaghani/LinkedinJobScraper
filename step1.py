from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver.webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

user_search_query = input("Enter the job title or company you want to search for: ")
num_results_to_scrape = int(input("How many job results do you want to scrape? "))

service = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

driver.get("https://www.linkedin.com/jobs/search?trk=guest_homepage-basic_guest_nav_menu_jobs&position=1&pageNum=0")

try:
    dismiss_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']"))
    )
    time.sleep(2)
    dismiss_button.click()
    print("Dismissed sign-in modal.")
except Exception as e:
    print(f"Could not dismiss sign-in modal, it might not be present or an error occurred: {e}")

try:
    search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "job-search-bar-keywords"))
        )
    search_box.send_keys(user_search_query)
    print(f"Typed: '{user_search_query}' into the search box.")
    search_box.send_keys(Keys.ENTER)
    time.sleep(5) 
except Exception as e:
    print(f"Error interacting with search box: {e}")
    driver.quit()
    exit()

job_listings = []
scraped_count = 0
last_height = driver.execute_script("return document.body.scrollHeight")

while scraped_count < num_results_to_scrape:
    job_cards = driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")

    for card in job_cards:
        if scraped_count >= num_results_to_scrape:
            break

        try:
            job_name_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__title")
            company_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle")
            location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")

            job_name = job_name_element.text.strip()
            company = company_element.text.strip()
            location = location_element.text.strip()

            job_listings.append({
                "Job Name": job_name,
                "Company": company,
                "Location": location
            })
            scraped_count += 1
            print(f"Scraped {scraped_count}/{num_results_to_scrape}: Job: {job_name}, Company: {company}, Location: {location}")

        except Exception as e:
            continue 

    if scraped_count < num_results_to_scrape:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3) 
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No more new results to load by scrolling.")
            break
        last_height = new_height

print("\n--- Scraped Job Information ---")
for job in job_listings:
    print(f"Job Name: {job['Job Name']}")
    print(f"Company: {job['Company']}")
    print(f"Location: {job['Location']}")
    print("-" * 30)

input("Press Enter to close the browser...")
driver.quit()