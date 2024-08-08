import requests
from bs4 import BeautifulSoup
import threading
import argparse
from urllib.parse import urlparse


def check_link_status(url):
    try:
        response = requests.head(url)
        status_code = response.status_code
        if status_code >= 400:
            print('\033[91m' + f"Broken link found: {url} (Status code: {status_code})" + '\033[0m')
        else:
            print('\033[92m' + f"Valid link: {url} (Status code: {status_code})" + '\033[0m')
    except requests.RequestException as e:
        print('\033[91m' + f"An error occurred while checking link: {url} ({str(e)})" + '\033[0m')


def check_broken_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')

    print(f"Checking broken links on {url}...\n")

    thread_list = []

    parsed_url = urlparse(url)
    host = parsed_url.netloc

    for link in links:
        href = link.get('href')
        if href and href.startswith('http'):
            thread = threading.Thread(target=check_link_status, args=(href,))
            thread_list.append(thread)
            thread.start()
        else:
            if href.startswith('/'):
                skipped_link = f"{parsed_url.scheme}://{host}{href}"
                print(f"Skipping link: {href} (Not an absolute URL)\n{skipped_link}")
            else:
                print(f"Skipping link: {href} (Not an absolute URL)")

    for thread in thread_list:
        thread.join()

    print("\nLink checking completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check broken links on a website.')
    parser.add_argument('-u', '--url', type=str, help='URL of the website to check')
    args = parser.parse_args()

    if args.url:
        parsed_url = urlparse(args.url)
        if not parsed_url.scheme:
            args.url = "http://" + args.url
        check_broken_links(args.url)
    else:
        print("Please provide a URL using the -u or --url option.")
