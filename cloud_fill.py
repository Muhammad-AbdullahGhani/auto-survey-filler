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

# --- THE MAPPING ---
COLUMN_MAP = {
    # Section 1: Demographics
    'Gender': 'What is your Gender',
    'Age': 'What is your age',
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
    'Status': 'employment status',

    # Section 2: Sentiment
    'Job_Support_Rating': 'support in helping you secure a job',
    'Job_Support_Explain': 'Job placement support',
    'Job_Ready': 'Did your university help you become job-ready',
    'Faculty_Rating': 'Faculty & teaching quality',
    'Faculty_Explain': 'explain your rating.(Faculty)',
    'Resources_Rating': 'learning resources',
    'Resources_Explain': 'explain your rating.(learning resources)',
    'Labs_Rating': 'laboratory/practical facilities',
    'Labs_Explain': 'explain your rating.(labs)',
    'Sports_Rating': 'Sports facilities',
    'Sports_Explain': 'explain your rating.(Sports)',
    'Cafe_Rating': 'Cafeteria / Food services',
    'Cafe_Explain': 'explain your rating.(Cafeteria)',
    'Hostel_Rating': 'Hostel facilities',
    'Hostel_Explain': 'explain your rating.(Hostels)',
    'Events_Rating': 'Events & co-curricular activities',
    'Events_Explain': 'explain your rating.(Events)',
    'Campus_Rating': 'Campus environment',
    'Campus_Explain': 'explain your rating.(Environment)',
    'Mgmt_Rating': 'experience in terms management',
    'Mgmt_Explain': 'explain your rating.(Management)',
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

# --- NEW ROBUST HELPER FUNCTIONS ---
def get_question_container(driver, question_text):
    """Finds the specific 'box' (div) that contains the question text."""
    try:
        # 1. Find all question containers (role='listitem')
        containers = driver.find_elements(By.XPATH, "//div[@role='listitem']")
        for container in containers:
            if question_text in container.text:
                return container
    except:
        pass
    return None

def fill_smart(driver, question_text, answer_text):
    """Smartly detects if the question needs typing or clicking."""
    try:
        container = get_question_container(driver, question_text)
        if not container:
            # Silent skip if question isn't on this page
            return

        # 1. Try Typing (Input/Textarea)
        try:
            input_field = container.find_element(By.XPATH, ".//input[@type='text'] | .//textarea")
            input_field.clear()
            input_field.send_keys(str(answer_text))
            print(f"  [Type] Filled '{answer_text}' for '{question_text}'")
            return
        except:
            pass # Not a text field

        # 2. Try Clicking (Radio/Checkbox/Dropdown)
        try:
            # Look for the specific answer text inside this container
            option = container.find_element(By.XPATH, f".//span[contains(text(), '{answer_text}')]")
            option.click()
            print(f"  [Click] Selected '{answer_text}' for '{question_text}'")
            return
        except:
            pass # Not a simple option

        # 3. Try Rating Scale (Linear Scale)
        try:
            # Look for aria-label="5" or just the number inside the container
            rating_btn = container.find_element(By.XPATH, f".//div[@aria-label='{answer_text}']")
            rating_btn.click()
            print(f"  [Rate] Rated '{answer_text}' for '{question_text}'")
            return
        except:
            pass
            
        print(f"  [FAIL] Found question '{question_text}' but couldn't fill '{answer_text}'")

    except Exception as e:
        print(f"  [ERR] Error on '{question_text}': {e}")

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
        if 'Submission_Status' not in df.columns: df['Submission_Status'] = ""
    except:
        print("Dataset not found!")
        return

    remaining = df[df['Submission_Status'] != 'Done']
    if len(remaining) == 0:
        print("All rows completed.")
        return

    # Use head(1) to be safe and verify first
    batch = remaining.head(1)
    print(f"Starting batch of {len(batch)} forms...")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    for index, row in batch.iterrows():
        print(f"\n=== Processing Row {index + 1} ===")
        try:
            driver.get(FORM_URL)
            time.sleep(3)

            # --- DYNAMIC FILLING LOOP ---
            # Instead of section-by-section hardcoding, we loop through the map.
            # This is safer because if a question is on Page 2 but we check Page 1, it just skips gracefully.
            
            # Page 1 Check
            for key, q_text in COLUMN_MAP.items():
                if key in row and pd.notna(row[key]):
                    fill_smart(driver, q_text, row[key])
            
            click_next(driver)
            time.sleep(2)
            
            # Page 2 Check (Re-run filler for questions on page 2)
            for key, q_text in COLUMN_MAP.items():
                if key in row and pd.notna(row[key]):
                    fill_smart(driver, q_text, row[key])
            
            click_next(driver)
            time.sleep(2)

            # Page 3 Check (Personality)
            for key, q_text in COLUMN_MAP.items():
                if key in row and pd.notna(row[key]):
                    fill_smart(driver, q_text, row[key])
            
            click_next(driver)
            time.sleep(2)

            # Page 4 Check (Feedback)
            for key, q_text in COLUMN_MAP.items():
                if key in row and pd.notna(row[key]):
                    fill_smart(driver, q_text, row[key])

            # SUBMIT
            submit_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Submit')]")
            if submit_btn:
                submit_btn[0].click()
                time.sleep(3)
                df.at[index, 'Submission_Status'] = 'Done'
                print(f"✅ Row {index + 1} Submitted Successfully.")
            else:
                print(f"❌ Submit button not found for Row {index + 1}")

        except Exception as e:
            print(f"❌ Critical Error on Row {index + 1}: {e}")

    driver.quit()
    df.to_csv(DATA_FILE, index=False)

if __name__ == "__main__":
    run_automation()
