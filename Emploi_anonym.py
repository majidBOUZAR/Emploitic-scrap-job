##################################### BOUZAR ABDELMADJID / majid_bouzar22@yahoo.com #####################################

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
import re

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

    # Keep track of job titles already written to the file
    existing_jobs = set()

    # Read existing job titles from 'jobs_anonyme.txt'
    try:
        with open('jobs_anonyme.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('job_title:'):
                    job_title = line.split(': ', 1)[1].strip()
                    existing_jobs.add(job_title)
    except FileNotFoundError:
        pass  # File doesn't exist initially, which is okay

    with open('jobs_txt.txt', 'a', encoding='utf-8') as file:
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

                company_elem = job_elem.find('p', class_='MuiTypography-root MuiTypography-body1 mui-1wxxifx')
                company_name = company_elem.text.strip() if company_elem else 'N/A'

                if company_name == 'Entreprise anonyme':
                    link_elem = job_elem.find('a', class_='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineNone mui-1oiwtsn')
                    if link_elem:
                        job_url = base_url + link_elem['href']

                        driver.get(job_url)

                        try:
                            title_text = driver.title
                            job_title_match = re.match(r'Offre d\'emploi (.*?) - ', title_text)
                            job_title = job_title_match.group(1) if job_title_match else 'N/A'
                            print(f"Job Title: {job_title}")

                            # Check if job title already exists in the file
                            if job_title in existing_jobs:
                                print(f"Job '{job_title}' already exists in 'jobs_anonyme.txt'. Skipping insertion.")
                                continue

                            criteria_elem = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="job-criteria"]'))
                            )
                            print("Job criteria section loaded")
                            file.write(f"job_title: {job_title}\n")
                            file.write(f"Entreprise  :Anonyme \n")
                            file.write(f"Lien :{job_url} \n")
                            file.write("-" * 50 + "\n")
                            job_criteria_items = criteria_elem.find_elements(By.CSS_SELECTOR, '.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-md-6.css-iol86l')

                            criteria_list = []
                            for criteria in job_criteria_items:
                                label_elem = criteria.find_element(By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-vfr38d')
                                value_elem = criteria.find_element(By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-body1.css-1kmml6s')

                                label = label_elem.text.strip()
                                value = value_elem.text.strip()

                                file.write(f"{label}: {value}\n")
                                criteria_list.append(f"{label}: {value}")

                            criteria_text = '\n'.join(criteria_list)

                            try:
                                description_elem = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.css-19kzrtu'))
                                )
                                description_text = description_elem.text.strip()
                                #file.write(f"Description détaillée:\n{description_text}\n")
                                print(f"Description détaillée:\n{description_text}")

                            except Exception as desc_error:
                                description_text = 'N/A'
                                print(f"Error extracting detailed description: {str(desc_error)}")

                            file.write("-" * 50 + "\n")
                            print(f"Details scraped for job: {job_title}")
                            # Save to SQL with concatenated criteria
                            save_to_sql(job_title, 'Entreprise anonyme', criteria_text, description_text, job_url)

                            # Add job title to existing jobs set
                            existing_jobs.add(job_title)

                        except Exception as e:
                            print(f"Error scraping job criteria: {str(e)}")

    print(f"Job listings with anonymized company names saved to 'jobs_anonyme.txt' from page {start_page} to page {end_page}.")

finally:
    driver.quit()
    conn.close()
