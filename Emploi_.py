from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
import re

# Chrome WebDriver path
webdriver_path = r'C:\Users\DELL i7\Desktop\chromedriver-win64\chromedriver.exe'

# Chrome options
options = Options()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(executable_path=webdriver_path), options=options)

# Connect SQLite db 
conn = sqlite3.connect('Emploi_db.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        job_title TEXT PRIMARY KEY,
        company_name TEXT,
        criteria TEXT,
        description TEXT,
        link TEXT
    )
''')

# Function to save data to SQLite
def save_to_sql(job_title, company_name, criteria, description, link):
    try:
        cursor.execute('''
            INSERT INTO jobs (job_title, company_name, criteria, description, link)
            VALUES (?, ?, ?, ?, ?)
        ''', (job_title, company_name, criteria, description, link))
        conn.commit()
        print(f"Job '{job_title}' saved to database.")
    except sqlite3.IntegrityError:
        print(f"Job '{job_title}' already exists in the database. Skipping insertion.")
        
try:
    base_url = 'https://emploitic.com'
    start_page = 11
    end_page = 11

    with open('jobs_txt.txt', 'w', encoding='utf-8') as file:
        for page in range(start_page, end_page + 1):
            url = f'https://emploitic.com/offres-d-emploi?page={page}'
            driver.get(url)
            print(f"Page {page} loaded successfully")

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'MuiListItem-root')))
            print(f"Job listings found on page {page}")

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            job_listings = soup.find_all('li', class_='MuiListItem-root MuiListItem-gutters MuiListItem-padding mui-8v06ou')

            print(f"Number of job listings found on page {page}: {len(job_listings)}")

            for job_elem in job_listings:
                # Extract job title and company name
                job_title_elem = job_elem.find('p', class_='MuiTypography-root MuiTypography-body1 mui-1bkshe8')
                job_title = job_title_elem.text.strip() if job_title_elem else 'N/A'

                company_elem = job_elem.find('p', class_='MuiTypography-root MuiTypography-body1 mui-1wxxifx')
                company_name = company_elem.text.strip() if company_elem else 'Entreprise anonyme'

                # Check if company name is not anonymized
                if company_name != 'Entreprise anonyme':
                    # Extract link to job details page
                    link_elem = job_elem.find('a', class_='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineNone mui-1oiwtsn')
                    if link_elem:
                        job_url = base_url + link_elem['href']

                        # Navigate to the job details page
                        driver.get(job_url)
                        print(f"Navigated to job details page: {job_url}")

                        try:
                            # Wait for job title and company name to be visible
                            job_title_elem = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-8zlt47'))
                            )
                            job_title = job_title_elem.text.strip()

                            company_elem = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-1qih5z1'))
                            )
                            company_name = company_elem.text.strip()

                            file.write(f"Job Title: {job_title}\n")
                            file.write(f"Company Name: {company_name}\n")
                            file.write("-" * 50 + "\n")

                            # Wait for job criteria section to be visible
                            try:
                                criteria_elem = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="job-criteria"]'))
                                )
                                print("Job criteria section loaded")

                                # Extract job criteria information
                                job_criteria = criteria_elem.find_elements(By.CSS_SELECTOR, '.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-md-6.css-iol86l')
                                criteria_list = []
                                for criteria in job_criteria:
                                    label_elem = criteria.find_element(By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-vfr38d')
                                    value_elem = criteria.find_element(By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-1kmml6s')

                                    label = label_elem.text.strip()
                                    value = value_elem.text.strip()

                                    file.write(f"{label}: {value}\n")
                                    criteria_list.append(f"{label}: {value}")
                                    print(f"{label}: {value}")
                                criteria_text = '\n'.join(criteria_list)    

                                # Extract detailed description section
                                try:
                                    description_elem = WebDriverWait(driver, 10).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.css-wuqd5c'))
                                    )
                                    description_text = description_elem.text.strip()
                                    file.write(f"Description détaillée:\n{description_text}\n")
                                    print(f"Description détaillée:\n{description_text}")

                                except Exception as desc_error:
                                    print(f"Error extracting detailed description: {str(desc_error)}")

                                file.write("-" * 50 + "\n")
                                print(f"Details scraped for job: {job_title}")
                                save_to_sql(job_title, company_name, criteria_text, description_text, job_url)
                            except Exception as e:
                                print(f"Error scraping job criteria: {str(e)}")

                        except Exception as e:
                            print(f"Error scraping job details: {str(e)}")

    print(f"Job listings with detailed descriptions saved to 'jobs_with_description.txt' from page {start_page} to page {end_page}.")

finally:
    driver.quit()
