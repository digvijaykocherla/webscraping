from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from tabulate import tabulate
import seaborn as sns
import matplotlib.pyplot as plt

# Set up the WebDriver
driver = webdriver.Chrome()

# Lists to store data
property_list, price_list, beds_list, baths_list, sqft_list = [], [], [], [], []

# Loop through pages to scrape data
for page_num in range(2, 4):  # Adjust page range as needed
    try:
        url = f'https://www.landwatch.com/land/page-{page_num}'
        driver.get(url)

        # Wait for elements to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, '_39065'))
        )

        # Scroll the page to load content
        scroll_pause = 2
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)


        driver.switch_to.alert

        # Parse the page content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        property_names_divs = soup.find_all('div', class_='_39065')
        prices = soup.find_all('span', class_='_6ae86')
        features = soup.find_all('div', class_='d416f')

        # Extract the data
        property_list.extend([div.find('a').get_text(strip=True) for div in property_names_divs])
        price_list.extend([span.get_text(strip=True) for span in prices])

        # Extract beds, baths, and sqft from features
        for feature in features:
            feature_text = feature.get_text(strip=True)
            beds, baths, sqft = '', '', ''
            parts = feature_text.split('•')
            for part in parts:
                if 'beds' in part:
                    beds = part.strip().split()[0]
                elif 'baths' in part:
                    baths = part.strip().split()[0]
                elif 'sqft' in part:
                    sqft = part.strip()
            beds_list.append(beds)
            baths_list.append(baths)
            sqft_list.append(sqft)

    except TimeoutException:
        print(f"Timed out waiting for page {page_num}. Skipping...")
        continue

# Make sure all lists are of the same length
max_length = max(len(property_list), len(price_list), len(beds_list), len(baths_list), len(sqft_list))
property_list.extend([''] * (max_length - len(property_list)))
price_list.extend([''] * (max_length - len(price_list)))
beds_list.extend([''] * (max_length - len(beds_list)))
baths_list.extend([''] * (max_length - len(baths_list)))
sqft_list.extend([''] * (max_length - len(sqft_list)))

# Create a DataFrame
data = {
    'Property': property_list,
    'Price': price_list,
    'Beds': beds_list,
    'Baths': baths_list,
    'Size': sqft_list
}
df = pd.DataFrame(data)

# Display the table format in console
print(tabulate(df, headers='keys', tablefmt='grid'))

# Save to CSV
csv_file_path = os.path.join(os.getcwd(), 'real_estate_listings.csv')
try:
    df.to_csv(csv_file_path, index=False)
    print(f"Data saved to {csv_file_path}")
except Exception as e:
    print(f"Failed to save CSV: {e}")

# Close the WebDriver
driver.quit()

# --- Data Visualization with Seaborn ---

# Load the data
df['Price'] = pd.to_numeric(df['Price'].replace('[\$,]', '', regex=True), errors='coerce')
df['Beds'] = pd.to_numeric(df['Beds'], errors='coerce')
df['Baths'] = pd.to_numeric(df['Baths'], errors='coerce')
df['Size'] = pd.to_numeric(df['Size'].str.replace('sqft', '').str.replace(',', '').str.strip(), errors='coerce')

# Drop rows with any missing values
df.dropna(subset=['Price', 'Beds', 'Baths', 'Size'], inplace=True)

# Plot settings
sns.set(style="whitegrid")

# Bar Plot: Number of properties by number of beds
plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='Beds', palette='viridis')
plt.title('Number of Properties by Number of Beds')
plt.xlabel('Number of Beds')
plt.ylabel('Count')
plt.show()

# Histogram: Distribution of Property Prices
plt.figure(figsize=(10, 6))
sns.histplot(df['Price'], bins=20, kde=True, color='skyblue')
plt.title('Distribution of Property Prices')
plt.xlabel('Price (in $)')
plt.ylabel('Frequency')
plt.show()

# Scatter Plot: Property Size vs Price
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='Size', y='Price', hue='Beds', palette='viridis')
plt.title('Property Size vs Price')
plt.xlabel('Size (in sqft)')
plt.ylabel('Price (in $)')
plt.legend(title='Beds')
plt.show()



