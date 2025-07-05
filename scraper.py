from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from flask import Flask
from backend.config import Config
from backend.database import db
from backend.models import Job

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import os


def parse_relative_date(date_str):
    """Enhanced date parser that handles compact formats like '9d ago'"""
    date_str = date_str.lower().strip()
    today = datetime.now().date()

    if not date_str:
        print("Empty date string - using today's date")
        return today

    print(f"Parsing date string: '{date_str}'")

    # Handle hours/minutes (we'll treat as today)
    if "h" in date_str or "m" in date_str:
        print("Time-based date (hours/minutes) - using today")
        return today

    # Handle compact formats (Xd ago)
    compact_match = re.search(r'(\d+)([dwm])\s*ago', date_str)
    if compact_match:
        num = int(compact_match.group(1))
        unit = compact_match.group(2)

        if unit == "d":
            delta = timedelta(days=num)
        elif unit == "w":
            delta = timedelta(weeks=num)
        elif unit == "m":
            delta = relativedelta(months=num)

        result = today - delta
        print(f"Parsed as {num}{unit} ago: {result}")
        return result

    # Handle standard formats (X days ago)
    standard_match = re.search(r'(\d+)\s*(day|week|month)s?\s*ago', date_str)
    if standard_match:
        num = int(standard_match.group(1))
        unit = standard_match.group(2)

        if unit == "day":
            delta = timedelta(days=num)
        elif unit == "week":
            delta = timedelta(weeks=num)
        elif unit == "month":
            delta = relativedelta(months=num)

        result = today - delta
        print(f"Parsed as {num} {unit}s ago: {result}")
        return result

    print(f"⚠️ Unrecognized format - using today's date")
    return today


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Configure Selenium
options = Options()
options.add_argument('--headless')  # Uncomment for production
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service('drivers/chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)

# Start scraping
print("\nStarting scraping process...")
driver.get("https://www.actuarylist.com")

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "article")))
    job_cards = driver.find_elements(By.TAG_NAME, "article")
    print(f"\n✅ Successfully loaded {len(job_cards)} job cards")
except Exception as e:
    print(f"\n❌ Failed to load job cards: {e}")
    driver.quit()
    exit()

with app.app_context():
    db.create_all()
    new_jobs_count = 0
    duplicates_count = 0
    errors_count = 0

    for index, card in enumerate(job_cards, 1):
        try:
            print(f"\nProcessing job card {index}/{len(job_cards)}")

            # Extract job details
            position_elem = card.find_element(By.CLASS_NAME, "Job_job-card__position__ic1rc")
            job_title = position_elem.text.replace("Featured", "").strip()

            company_elem = card.find_element(By.CLASS_NAME, "Job_job-card__company__7T9qY")
            company = company_elem.text.strip()

            # Process locations and job type
            location_section = card.find_element(By.CLASS_NAME, "Job_job-card__locations__x1exr")
            location_links = location_section.find_elements(By.TAG_NAME, "a")

            job_type = "On-site"
            locations = []

            for loc in location_links:
                text = loc.text.strip()
                if not text:
                    continue

                href = loc.get_attribute("href").lower()
                if "remote" in href:
                    job_type = "Remote"
                elif "hybrid" in href:
                    job_type = "Hybrid"
                else:
                    locations.append(text)

            location = ", ".join(locations) if locations else "Not specified"

            # Process date
            posted_elem = card.find_element(By.CLASS_NAME, "Job_job-card__posted-on__NCZaJ")
            date_text = posted_elem.text.strip()
            date_posted = parse_relative_date(date_text)

            # Process tags
            tag_section = card.find_element(By.CLASS_NAME, "Job_job-card__tags__zfriA")
            tag_links = tag_section.find_elements(By.TAG_NAME, "a")
            tags = ", ".join([tag.text.strip() for tag in tag_links if tag.text.strip()])

            # Check for duplicates
            existing = Job.query.filter_by(
                title=job_title,
                company=company,
                date_posted=date_posted
            ).first()

            if existing:
                duplicates_count += 1
                print(f"⏭️ Duplicate skipped: {job_title[:50]}...")
                continue

            # Create and save new job
            job = Job(
                title=job_title,
                company=company,
                location=location,
                date_posted=date_posted,
                job_type=job_type,
                tags=tags
            )

            db.session.add(job)
            new_jobs_count += 1
            print(f"✅ Saved new job: {job_title[:50]}... | {date_posted}")

        except Exception as e:
            errors_count += 1
            print(f"⚠️ Error processing card {index}: {str(e)}")
            continue

    # Final commit and report
    db.session.commit()
    print("\nScraping complete!")
    print(f"Total jobs processed: {len(job_cards)}")
    print(f"New jobs saved: {new_jobs_count}")
    print(f"Duplicates skipped: {duplicates_count}")
    print(f"Errors encountered: {errors_count}")

driver.quit()
print("Browser closed. Scraping finished successfully!")