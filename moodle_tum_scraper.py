from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from configparser import ConfigParser
import time
import requests
import os
import json


# Initialisiere den ConfigParser
config = ConfigParser()
config.read('config.ini')

#configuration
USERNAME = config.get('config', 'user')
PASSWORD = config.get('config', 'pwd')
LOG_PATH = 'downloaded_docu.json'
SEMESTER = config.get('config', 'semester')
DOCU_DIR = config.get('config', 'docu_dir')

courses_strings = config.get('config', 'courses')
COURSTITLEs = courses_strings.split(',')


def login(username, password):
# Erstelle eine neue Instanz des Webdrivers (hier Chrome)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
# Öffne die Login-Seite der Website
    login_url = "https://www.moodle.tum.de/login/index.php"
    driver.get(login_url)
# Warten bis die Seite geladen ist (optional)
    time.sleep(2)
# Klicke auf den Button "With TUM ID"
    tum_id_button = driver.find_element(By.XPATH, "//a[contains(text(),'TUM')]")
    tum_id_button.click()
# Warten, bis die Shibboleth-Seite geladen wird
    time.sleep(2)
# Ausfüllen der Anmeldedaten (abhängig von der Form auf der TUM ID-Seite):
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    password_field.send_keys(Keys.RETURN)
# Warten, um zu überprüfen, ob der Login erfolgreich war
    time.sleep(2)
    return driver



def get_doc_links(driver, course_title):
#接下来是选semester的页面进去！
# Find the dropdown element by its ID
    dropdown_element = driver.find_element(By.ID, "coc-filterterm")
# Create a Select object to interact with the dropdown
    select = Select(dropdown_element)
# Select the "SoSe 2025" option by its value
    select.select_by_value(SEMESTER)  # Select option with value="2025-1" (SoSe 2025)
    time.sleep(2)

# debug: liste alle <a>-Tags mit genau deinem course_title im title-Attribut auf
    matches = driver.find_elements(
        By.XPATH,
        f'//a[contains(@title, "{course_title}")]'
    )   
    # Filtere nur die Elemente, die Text haben (nicht leer)
    visible = [
        el for el in matches
        if el.text.strip() != ""
    ]   
    if visible:
        link = visible[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(link)
        )
        link.click()
    else:
        print(f"Kein sichtbares Element für {course_title} gefunden.")

    time.sleep(2)
#finde link to mod/resource, die unterlink to pdf
# Alle Links mit "/mod/resource/" im href finden
    links = driver.find_elements(By.XPATH, '//a[contains(@href, "/mod/resource/")]')

# Jetzt kannst du die Links extrahieren and in doc_links speichern
    resources = []
    for link in links:
    #title and links extract
    #extract file name from the link 
        link_title = link.text
        if '\nFile' in link_title:
            link_title = link_title.replace('\nFile', '')
        if '\nDatei' in link_title:
            link_title = link_title.replace('\nDatei', '')    
        #replace give a new string back
        link_title = link_title.rstrip() 
        link_href = link.get_attribute("href") 
        if link_title:
            resources.append({'title': link_title, 'url': link_href})
        else:
            resources.append({'title': None, 'url': link_href})
    return resources        


def doc_download(driver, resources, target):
    session = requests.Session()
    #log files read
    try:
        with open(LOG_PATH, 'r') as lf:
            downloaded_urls = json.load(lf)
    except (FileNotFoundError, json.JSONDecodeError):
        downloaded_urls = []

    #cookies from selemium to requests 
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    for resource_element in resources:
        url = resource_element['url']
        title = resource_element['title']
        if url in downloaded_urls:
            #if title != None:
                #print(f"\t-File {title} is already downloaded!")
            continue
        response = session.get(url)
        if response.status_code != 200:
            print("Fehler beim Herunterladen")
            continue
    
    # Überprüfe, ob die Antwort erfolgreich war (Statuscode 200)
        if response.status_code == 200:
        # Der Content-Type prüfen, um sicherzustellen, dass es eine PDF-Datei ist
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type:
            # Extrahiere den Dateinamen aus der URL oder erfinde einen Namen für die PDF
                if title == None:
                    continue
                #only duplicate pdf file has no title
                #file_name = os.path.basename(link_href) + '.pdf'
                else:
                    file_name = title + ".pdf"

                download_path = os.path.join(target, file_name)
            # Speichere die PDF-Datei als binäre Daten
                with open(download_path, 'wb') as f:
                    f.write(response.content)  # Schreibe den binären Inhalt der PDF
                print(f"\t-PDF wurde erfolgreich als {file_name} gespeichert.")

                #log file
                downloaded_urls.append(url)
            else:
                print("Die angeforderte Ressource ist keine PDF-Datei.")
    
    #write log file back
    #every course write once
    with open(LOG_PATH, 'w') as lf:
        json.dump(list(downloaded_urls), lf)

    time.sleep(2)
# Beende den Webdriver


driver = login(USERNAME, PASSWORD)
for course_title in COURSTITLEs:
    print(f"Downloading for {course_title.title()}...")
    dir_name = course_title.replace(' ', '_')
    dir_path = os.path.join(DOCU_DIR, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    resources = get_doc_links(driver, course_title)
    doc_download(driver, resources, dir_path)
    print(f"\t{course_title.title()} fertig!")
    driver.back()
    time.sleep(4)

print("Good Bye")
driver.quit()
