import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlencode, urlunparse, parse_qs
import time
from PyQt5.QtWidgets import QApplication, QFileDialog


def generate_urls(base_url, max_page):
    urls = []
    parsed_url = urlparse(base_url)
    query_params = parse_qs(parsed_url.query)

    start_page = int(query_params.get('page', [1])[0])

    for page in range(start_page, max_page + 1):
        query_params['page'] = [str(page)]
        encoded_query = urlencode(query_params, doseq=True)
        parsed_url = parsed_url._replace(query=encoded_query)
        updated_url = urlunparse(parsed_url)
        urls.append(updated_url)

    return urls


def download_image(url, directory):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(directory, filename)

        if os.path.exists(filepath):
            print(f"Skipping image (already exists): {url}")
            return

        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Downloaded: {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
    except IOError as e:
        print(f"IOError while saving {url}: {e}")


def download_images_from_website(website_url, target_directory, minimum_image_size, delay):
    # Create target directory if it doesn't exist
    os.makedirs(target_directory, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36",
        "Referer": website_url
    }

    try:
        response = requests.get(website_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing website: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    for img_tag in soup.find_all("img"):
        img_url = img_tag.get("src")

        if img_url:
            absolute_img_url = urljoin(website_url, img_url)
            print(f"\nChecking image: {absolute_img_url}")
            try:
                image_response = requests.head(absolute_img_url)
                image_size = int(image_response.headers.get("content-length", 0))

                if image_size > minimum_image_size * 1024:  # Convert to bytes
                    print(f"Downloading image: {absolute_img_url}")
                    download_image(absolute_img_url, target_directory)
                    time.sleep(delay)  # Delay of 1 second between each request
                else:
                    print(f"Skipping image (less than {minimum_image_size} KB): {absolute_img_url}")
            except requests.exceptions.RequestException as e:
                print(f"Error accessing image: {e}")


def get_query_text(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_text = query_params.get('query', [''])[0]
    return query_text


def get_valid_link(prompt):
    while True:
        link = input(prompt)

        if link:
            response = requests.get(link)
            if response.status_code == 200:
                print("Valid link!")
                return link
            else:
                print("Invalid link!")


def choose_output_directory():
    app = QApplication([])
    target_directory = QFileDialog.getExistingDirectory(None, "Select output folder")
    return target_directory


def get_integer_input(prompt):
    while True:
        try:
            value = int(input(prompt))
            return value
        except ValueError:
            print("Invalid input! Please enter an integer.")


link = get_valid_link("Type in link: ")
target_directory = choose_output_directory()
max_page = get_integer_input("Enter the maximum page number: ")
minimum_image_size = get_integer_input("Enter the minimum picture size in KB: ")
delay = get_integer_input("Enter the delay in seconds: ")

generated_urls = generate_urls(link, max_page)

for i, url in enumerate(generated_urls, 1):
    domain = urlparse(url).netloc
    query_text = get_query_text(url)
    domain_directory = os.path.join(target_directory, domain)
    query_directory = os.path.join(domain_directory, query_text)

    os.makedirs(query_directory, exist_ok=True)
    print(f"\nDownloading images from page {i} to directory: {query_directory}")
    download_images_from_website(url, query_directory, minimum_image_size, delay)