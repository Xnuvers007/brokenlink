#!/usr/bin/env python3

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import json
import csv
import pandas as pd
import os
import time
import warnings
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

GREEN = '\033[92m'
RESET = '\033[0m'

def print_banner():
    try:
        result = subprocess.run(['figlet', 'brokenlink'], capture_output=True, text=True)
        print(result.stdout)
    except FileNotFoundError:
        print("figlet is not installed. Please install figlet to see the banner.")
    print("\nCredit: Xnuvers007")
    print(f'''Copyright (c) 2024 Xnuvers007 - MIT License\n\n''')
    usage_text = (
        f"{GREEN}Usage: ./brokenlink.py or python3 brokenlink.py "
        "-u e-example.com -t 15 -v -o downloads/broken_links.txt "
        '-ua "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"\n\n'
        "Check a single URL with default settings:\n"
        "./brokenlink.py -u http://example.com\n\n"
        "Check multiple URLs listed in a file:\n"
        "./brokenlink.py -i urls.txt -o results.json\n\n"
        "Check a URL with custom headers and a higher depth level:\n"
        './brokenlink.py -u http://example.com -t 5 --depth 2 '
        '--headers \'{"X-Custom-Header": "value"}\'\n\n'
        "Exclude certain domains from being checked:\n"
        "./brokenlink.py -u http://example.com -e example.com,anotherdomain.com"
        f"{RESET}\n"
    )
    print(usage_text)

def generate_default_filename(url, extension):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('.', '_')
    return f"{domain}.{extension}"

def format_bytes(size):
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024**2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024**3:
        return f"{size / 1024**2:.2f} MB"
    elif size < 1024**4:
        return f"{size / 1024**3:.2f} GB"
    else:
        return f"{size / 1024**4:.2f} TB"

def get_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def check_link_status(url, results, headers, connection_counter):
    try:
        session = get_session_with_retries()
        response = session.get(url, headers=headers, timeout=10)
        status_code = response.status_code
        size = int(response.headers.get('Content-Length', 0))

        if 400 <= status_code < 500:
            status = 'Client Error'
        elif 500 <= status_code < 600:
            status = 'Server Error'
        elif status_code >= 400:
            status = 'Broken'
        else:
            status = 'Valid'

        results.append({'url': url, 'status_code': status_code, 'status': status})
        connection_counter['size'] += size
    except (requests.RequestException, NewConnectionError, ConnectionError) as e:
        results.append({'url': url, 'status_code': None, 'status': f'Error ({str(e)})'})
    finally:
        connection_counter['count'] += 1

def crawl(url, max_depth, current_depth, headers, results, connection_counter, seen_urls):
    if current_depth > max_depth:
        return
    
    if not url.startswith(('http://', 'https://')):
        print(f"Skipping non-HTTP URL: {url}")
        return

    try:
        session = get_session_with_retries()
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f'Failed to retrieve the webpage: {url} ({str(e)})')
        return

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        content_type = response.headers.get('Content-Type', '')
        if 'xml' in content_type:
            parser = 'lxml-xml'
        else:
            parser = 'html.parser'

        soup = BeautifulSoup(response.text, parser)
    
    links = soup.find_all('a')
    links_to_check = []

    for link in links:
        href = link.get('href')
        if href:
            full_url = urljoin(url, href)
            if full_url not in seen_urls:
                links_to_check.append(full_url)
                seen_urls.add(full_url)

    # Check links in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_link_status, link, results, headers, connection_counter) for link in links_to_check]
        for future in as_completed(futures):
            future.result()  # Ensure exceptions are raised

    # Recurse into found links
    for link in links_to_check:
        crawl(link, max_depth, current_depth + 1, headers, results, connection_counter, seen_urls)

def check_broken_links(url, max_threads, output_path, headers, max_depth):
    results = []
    connection_counter = {'count': 0, 'size': 0}
    seen_urls = set()

    try:
        session = get_session_with_retries()
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print('\033[91m' + f"Failed to retrieve the webpage: {url} ({str(e)})" + '\033[0m')
        return

    print(f"Checking broken links on {url}...\n")
    seen_urls.add(url)
    crawl(url, max_depth, 0, headers, results, connection_counter, seen_urls)

    print("\nLink checking completed.")
    print(f"Total connections made: {connection_counter['count']}")
    print(f"Total data transferred: {format_bytes(connection_counter['size'])}")

    status_code_counts = {}
    for result in results:
        code = result['status_code']
        if code not in status_code_counts:
            status_code_counts[code] = 0
        status_code_counts[code] += 1

    print("\nStatus Code Breakdown:")
    for code, count in status_code_counts.items():
        print(f"{code}: {count}")

    if not output_path:
        output_file = generate_default_filename(url, 'txt')
    else:
        if '.' not in output_path:
            output_file = f"{output_path}.txt"
        else:
            output_file = output_path

    if output_file.endswith('.txt'):
        with open(output_file, 'w') as f:
            for result in results:
                f.write(f"{result['url']} - {result['status']}\n")
    elif output_file.endswith('.json'):
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
    elif output_file.endswith('.html'):
        with open(output_file, 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Broken Links Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }
        h1 {
            color: #007BFF;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f4f4f4;
        }
    </style>
</head>
<body>
    <h1>Broken Links Report</h1>
    <table>
        <thead>
            <tr>
                <th>URL</th>
                <th>Status</th>
                <th>Status Code</th>
            </tr>
        </thead>
        <tbody>
''')
            for result in results:
                f.write(f"<tr><td>{result['url']}</td><td>{result['status']}</td><td>{result['status_code']}</td></tr>\n")
            f.write('''</tbody>
    </table>
</body>
</html>''')
    elif output_file.endswith('.csv'):
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'status', 'status_code'])
            writer.writeheader()
            writer.writerows(results)
    elif output_file.endswith('.xlsx'):
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)

    print(f"\nResults saved to {output_file}")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Check for broken links on a website.")
    parser.add_argument('-u', '--url', type=str, required=True, help='URL to check for broken links')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads to use for checking links')
    parser.add_argument('-o', '--output', type=str, help='Output file path (supports .txt, .json, .html, .csv, .xlsx)')
    parser.add_argument('--depth', type=int, default=1, help='Depth of crawling for links')
    parser.add_argument('--headers', type=str, default='{}', help='Custom headers to send with the requests (JSON format)')
    parser.add_argument('-e', '--exclude', type=str, default='', help='Comma-separated list of domains to exclude')

    args = parser.parse_args()

    headers = json.loads(args.headers)
    excluded_domains = set(args.exclude.split(',')) if args.exclude else set()

    def check_link_status_with_exclusion(url, results, headers, connection_counter):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if any(domain.endswith(excluded_domain) for excluded_domain in excluded_domains):
            print(f"Skipping excluded domain: {url}")
            return

        check_link_status(url, results, headers, connection_counter)

    def crawl_with_exclusions(url, max_depth, current_depth, headers, results, connection_counter, seen_urls):
        if current_depth > max_depth:
            return

        if not url.startswith(('http://', 'https://')):
            print(f"Skipping non-HTTP URL: {url}")
            return

        try:
            session = get_session_with_retries()
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f'Failed to retrieve the webpage: {url} ({str(e)})')
            return

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            content_type = response.headers.get('Content-Type', '')
            if 'xml' in content_type:
                parser = 'lxml-xml'
            else:
                parser = 'html.parser'

            soup = BeautifulSoup(response.text, parser)

        links = soup.find_all('a')
        links_to_check = []

        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                if full_url not in seen_urls:
                    links_to_check.append(full_url)
                    seen_urls.add(full_url)

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [executor.submit(check_link_status_with_exclusion, link, results, headers, connection_counter) for link in links_to_check]
            for future in as_completed(futures):
                future.result()  # Ensure exceptions are raised

        for link in links_to_check:
            crawl_with_exclusions(link, max_depth, current_depth + 1, headers, results, connection_counter, seen_urls)

    check_broken_links(args.url, args.threads, args.output, headers, args.depth)

if __name__ == "__main__":
    main()
