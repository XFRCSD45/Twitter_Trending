from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from flask import Flask, render_template_string, request
import time
import uuid
from dotenv import load_dotenv
import os


load_dotenv()


proxy_url = os.getenv('ProxymeshUrl')
twitterUsername = os.getenv('TwitterUsername')
twitterPassword = os.getenv('TwitterPassword')


client = MongoClient("mongodb://localhost:27017/")
db = client["twitter_trends"]
collection = db["trends"]


app = Flask(__name__)


def fetch_trending_topics():
    
    proxy_options = {
        'proxy': {
            'https': proxy_url,
            'http': proxy_url,
            'no_proxy': 'localhost,127.0.0.1' 
        }
    }

    
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(seleniumwire_options=proxy_options, options=chrome_options)

    try:
        
        driver.get("https://twitter.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@name='text']")))

        
        username = driver.find_element(By.XPATH, "//input[@name='text']")
        username.send_keys(twitterUsername)
        next_button = driver.find_element(By.XPATH, "//span[contains(text(),'Next')]")
        next_button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']")))
        password = driver.find_element(By.XPATH, "//input[@name='password']")
        password.send_keys(twitterPassword)
        log_in = driver.find_element(By.XPATH, "//span[contains(text(),'Log in')]")
        log_in.click()

        WebDriverWait(driver, 10).until(EC.url_contains("home"))
        trends = driver.find_elements(By.XPATH, "//div[@aria-label='Timeline: Trending now']//span")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Timeline: Trending now']//span")))
        parent_spans = driver.find_elements(By.XPATH, "//span[contains(@class, 'r-18u37iz')]/span")
        span_texts = [span.text for span in parent_spans]

        
        unique_id = str(uuid.uuid4())
        ip_address = driver.execute_script("return window.navigator.userAgent")

        
        record = {
            "_id": unique_id,
            "trend1": span_texts[0],
            "trend2": span_texts[1],
            "trend3": span_texts[2],
            "trend4": span_texts[3],
            "timestamp": time.ctime(),
            "ip_address": ip_address,
        }
        collection.insert_one(record)
        return record

    finally:
        driver.quit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = fetch_trending_topics()
        return render_template_string(
            """
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    max-width: 100vw;
                    overflow-x: hidden;
                }
                .container {
                    max-width: 100%;
                    margin: 0 auto;
                    padding: 20px;
                    box-sizing: border-box;
                }
                pre {
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
            </style>
            <div class="container">
                <h1>These are the most happening topics as on {{ data['timestamp'] }}</h1>
                <ul>
                    <li>{{ data['trend1'] }}</li>
                    <li>{{ data['trend2'] }}</li>
                    <li>{{ data['trend3'] }}</li>
                    <li>{{ data['trend4'] }}</li>
                </ul>
                <p>The IP address used for this query was {{ data['ip_address'] }}.</p>
                <h2>JSON Extract:</h2>
                <pre>{{ data | tojson(indent=4) }}</pre>
                <form method="post">
                <button type="submit">Click here to run the query again.</button>
                </form>
            </div>
            """,
            data=data,
        )

    return render_template_string(
        """
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                max-width: 100vw;
                overflow-x: hidden;
            }
            .container {
                max-width: 100%;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
            }
        </style>
        <div class="container">
            <h1>Click below to fetch trending topics</h1>
            <form method="post">
                <button type="submit">Run Script</button>
            </form>
        </div>
        """
    )

if __name__ == "__main__":
    app.run(debug=True)
