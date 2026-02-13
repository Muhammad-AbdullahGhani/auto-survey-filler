import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
FORM_URL = "https://docs.google.com/forms/d/1rGyn_Vh31Z6_ZzYrOaDfJ7x1BrfscmUM83qqlfSs178/viewform"
DATA_FILE = "FINAL_DATASET.csv"

# --- THE MAPPING (CSV Header -> Google Form Question Text) ---
COLUMN_MAP = {
    # Section 1: Demographics
    'Gender': 'What is your Gender',
    'Age': 'What is your age (current)?',
    'Batch': 'Bachelor’s Batch',
    'Grad_Year': 'graduating year',
    'Background': 'educational background',
    'Major': 'Bachelor’s major',
    'Specialization': 'specialization',
    'University': 'Which university did you attend?',
    'City': 'city your university is located',
    'Student_Type': 'During your university studies',
    'Selection_Reason': 'How did you select your university',
    'Job_Domain': 'current job domain',
    'Job_Role': 'job role/designation',
    'Salary': 'monthly salary range',
    'Satisfaction': 'How satisfied are you with your current career',
    
    # *** CORRECTED MAPPING HERE ***
    'Status': 'employment status',  # Matches your CSV header 'Status'

    # Section 2: Sentiment
    'Job_Support_Rating': 'support in helping you secure a job',
    'Job_Support_Explain': 'Please explain your rating. (Job placement support)',
    'Job_Ready': 'Did your university help you become job-ready',
    
    'Faculty_Rating': 'Faculty & teaching quality',
    'Faculty_Explain': 'Please explain your rating.(Faculty)',
    
    'Resources_Rating': 'learning resources',
    'Resources_Explain': 'Please explain your rating.(learning resources)',
    
    'Labs_Rating': 'laboratory/practical facilities',
    'Labs_Explain': 'Please explain your rating.(labs)',
    
    'Sports_Rating': 'Sports facilities',
    'Sports_Explain': 'Please explain your rating.(Sports)',
    
    'Cafe_Rating': 'Cafeteria / Food services',
    'Cafe_Explain': 'Please explain your rating.(Cafeteria)',
    
    'Hostel_Rating': 'Hostel facilities',
    'Hostel_Explain': 'Please explain your rating.(Hostels)',
    
    'Events_Rating': 'Events & co-curricular activities',
    'Events_Explain': 'Please explain your rating.(Events)',
    
    'Campus_Rating': 'Campus environment',
    'Campus_Explain': 'Please explain your rating.(Environment)',
    
    'Mgmt_Rating': 'experience in terms management',
    'Mgmt_Explain': 'Please explain your rating.(Management)',
    
    'Overall_Rating': 'Overall student satisfaction',
    'Overall_Explain': 'Overall student satisfaction',

    'Hardships': 'What hardships did you face',
    'Lessons': 'What did you learn from those',
    'Recommend': 'recommend your university',
    'Recommend_Why': 'explain Why or Why not',

    # Section 3: Personality
    'Repairing_Things': 'repairing mechanical things',
    'Working_Outdoors': 'working outdoors',
    'Building_Things': 'building things with my hands',
    'Fixing_Appliances': 'fix household appliances',
    'Operating_Machines': 'operating different machines',
    'Building_Models': 'building practical models',
    'Organizing_Info': 'organizing messy information',
    'Handling_Records': 'handling records',
    'Balancing_Budgets': 'balancing budgets',
    'Meeting_Records': 'records of meetings',
    'Solving_Problems': 'solving difficult problems',
    'Experimenting': 'experimenting to see what happens',
    'Investigating_Causes': 'investigating causes',
    'Logic_Discussion': 'discussions based on logic',
    'Analyzing_Graphs': 'analyzing graphs',
    'Systematic_Schedules': 'systematic schedules',
    'Finding_Errors': 'find errors in reports',
    'Music_Activities': 'music-related activities',
    'Designing_Posters': 'designing posters',
    'Writing_Plays': 'writing or performing plays',
    'Acting_Films': 'acting or writing films',
    'Creative_Ideas': 'new creative ideas',
    'Teaching_Others': 'teaching and guiding others',
    'Helping_People': 'help other people',
    'Volunteer_Work': 'volunteer work',
    'Charity_Activities': 'organizing charity',
    'Including_Others': 'include others',
    'Training_Others': 'training other',
    'Taking_Lead': 'taking the lead',
    'Presenting_Ideas': 'present and promote',
    'Persuading_People': 'persuading people',
    'Leadership_Goal': 'become a leader',
    'Taking_Risks': 'take risks',
    'Competitive_Situations': 'competitive situations',
    
    # Section 4: Feedback
    'Final_Comments': 'Anything that we missed',
    'Platform_Wish': 'wish you had a platform'
}

# --- HELPER FUNCTIONS ---
def safe_click(driver, xpath):
    try:
        el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        el.click()
        return True
    except:
        return False

def click_option(driver, question_text, answer_text):
    try:
        # Tries to find unique text match first
        xpath = f"//div[contains(@data-params, '{question_text}')]//span[contains(text(), '{answer_text}')]"
        if not safe_click(driver, xpath):
             driver.find_element(By.XPATH, f"//span[contains(text(), '{answer_text}')]").click()
    except:
        pass

def fill_text(driver, question_text, answer_text):
    try:
        inputs = driver.find_elements(By.XPATH, "//input[@type='text'] | //textarea")
        for inp in inputs:
            parent_text = inp.find_element(By.XPATH, "./../../../../..").text
            if question_text in parent_text:
                inp.clear()
                inp.send_keys(str(answer_text))
                break
    except:
        pass

def rate_scale(driver, question_text, rating):
    try:
        xpath = f"//div[contains(@data-params, '{question_text}')]//div[@aria-label='{rating}']"
        driver.find_element(By.XPATH, xpath).click()
    except:
        pass

def click_next(driver):
    try:
        driver.find_element(By.XPATH, "//span[contains(text(), 'Next')]").click()
        time.sleep(2)
    except: pass

# --- MAIN AUTOMATION ---
def run_automation():
    print("Loading dataset...")
    try:
        df = pd.read_csv(DATA_FILE)
        # *** FIX: Use 'Submission_Status' instead of 'Status' to avoid overwriting employment data
        if 'Submission_Status' not in df.columns: df['Submission_Status'] = ""
    except:
        print("Dataset not found!")
        return

    # Filter for rows not yet done
    remaining = df[df['Submission_Status'] != 'Done']
    if len(remaining) == 0:
        print("All rows completed.")
        return

    # Fill 3 forms per run
    batch = remaining.head(3)
    print(f"Starting batch of {len(batch)} forms...")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    for index, row in batch.iterrows():
        print(f"Processing Row {index + 1}...")
        try:
            driver.get(FORM_URL)
            time.sleep(3)

            # === SECTION 1 ===
            click_option(driver, COLUMN_MAP['Gender'], row['Gender'])
            fill_text(driver, COLUMN_MAP['Age'], row['Age'])
            fill_text(driver, COLUMN_MAP['Batch'], row['Batch'])
            fill_text(driver, COLUMN_MAP['Grad_Year'], row['Grad_Year'])
            click_option(driver, COLUMN_MAP['Background'], row['Background'])
            click_option(driver, COLUMN_MAP['Major'], row['Major'])
            fill_text(driver, COLUMN_MAP['Specialization'], row['Specialization'])
            click_option(driver, COLUMN_MAP['University'], row['University'])
            click_option(driver, COLUMN_MAP['City'], row['City'])
            click_option(driver, COLUMN_MAP['Student_Type'], row['Student_Type'])
            click_option(driver, COLUMN_MAP['Selection_Reason'], row['Selection_Reason'])
            fill_text(driver, COLUMN_MAP['Job_Domain'], row['Job_Domain'])
            fill_text(driver, COLUMN_MAP['Job_Role'], row['Job_Role'])
            click_option(driver, COLUMN_MAP['Salary'], row['Salary'])
            rate_scale(driver, COLUMN_MAP['Career_Satisfaction'], row['Career_Satisfaction'])
            
            # Use 'Status' from CSV for 'employment status' question
            click_option(driver, COLUMN_MAP['Status'], row['Status'])
            
            click_next(driver)

            # === SECTION 2 ===
            rate_scale(driver, COLUMN_MAP['Job_Support_Rating'], row['Job_Support_Rating'])
            fill_text(driver, COLUMN_MAP['Job_Support_Explain'], row['Job_Support_Explain'])
            click_option(driver, COLUMN_MAP['Job_Ready'], row['Job_Ready'])
            
            rate_scale(driver, COLUMN_MAP['Faculty_Rating'], row['Faculty_Rating'])
            fill_text(driver, COLUMN_MAP['Faculty_Explain'], row['Faculty_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Resources_Rating'], row['Resources_Rating'])
            fill_text(driver, COLUMN_MAP['Resources_Explain'], row['Resources_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Labs_Rating'], row['Labs_Rating'])
            fill_text(driver, COLUMN_MAP['Labs_Explain'], row['Labs_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Sports_Rating'], row['Sports_Rating'])
            fill_text(driver, COLUMN_MAP['Sports_Explain'], row['Sports_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Cafe_Rating'], row['Cafe_Rating'])
            fill_text(driver, COLUMN_MAP['Cafe_Explain'], row['Cafe_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Hostel_Rating'], row['Hostel_Rating'])
            fill_text(driver, COLUMN_MAP['Hostel_Explain'], row['Hostel_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Events_Rating'], row['Events_Rating'])
            fill_text(driver, COLUMN_MAP['Events_Explain'], row['Events_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Campus_Rating'], row['Campus_Rating'])
            fill_text(driver, COLUMN_MAP['Campus_Explain'], row['Campus_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Mgmt_Rating'], row['Mgmt_Rating'])
            fill_text(driver, COLUMN_MAP['Mgmt_Explain'], row['Mgmt_Explain'])
            
            rate_scale(driver, COLUMN_MAP['Overall_Rating'], row['Overall_Rating'])
            fill_text(driver, COLUMN_MAP['Overall_Explain'], row['Overall_Explain'])
            
            fill_text(driver, COLUMN_MAP['Hardships'], row['Hardships'])
            fill_text(driver, COLUMN_MAP['Lessons'], row['Lessons'])
            click_option(driver, COLUMN_MAP['Recommend'], row['Recommend'])
            fill_text(driver, COLUMN_MAP['Recommend_Why'], row['Recommend_Why'])
            
            click_next(driver)

            # === SECTION 3 ===
            personality_cols = [
                'Repairing_Things', 'Working_Outdoors', 'Building_Things', 'Fixing_Appliances',
                'Operating_Machines', 'Building_Models', 'Organizing_Info', 'Handling_Records',
                'Balancing_Budgets', 'Meeting_Records', 'Solving_Problems', 'Experimenting',
                'Investigating_Causes', 'Logic_Discussion', 'Analyzing_Graphs', 'Systematic_Schedules',
                'Finding_Errors', 'Music_Activities', 'Designing_Posters', 'Writing_Plays',
                'Acting_Films', 'Creative_Ideas', 'Teaching_Others', 'Helping_People',
                'Volunteer_Work', 'Charity_Activities', 'Including_Others', 'Training_Others',
                'Taking_Lead', 'Presenting_Ideas', 'Persuading_People', 'Leadership_Goal',
                'Taking_Risks', 'Competitive_Situations'
            ]
            for col in personality_cols:
                if col in row:
                    q_text = COLUMN_MAP.get(col, "")
                    val = row[col]
                    if q_text:
                        rate_scale(driver, q_text, val)

            click_next(driver)

            # === SECTION 4 ===
            fill_text(driver, COLUMN_MAP['Final_Comments'], row['Final_Comments'])
            click_option(driver, COLUMN_MAP['Platform_Wish'], row['Platform_Wish'])
            
            # SUBMIT
            driver.find_element(By.XPATH, "//span[contains(text(), 'Submit')]").click()
            time.sleep(3)
            
            # Mark Done using the NEW column
            df.at[index, 'Submission_Status'] = 'Done'
            print(f"Row {index + 1} Submitted.")

        except Exception as e:
            print(f"Error on Row {index + 1}: {e}")

    driver.quit()
    df.to_csv(DATA_FILE, index=False)

if __name__ == "__main__":
    run_automation()