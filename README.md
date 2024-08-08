### `README.md`

```markdown
# Broken Link Checker

A simple Python script to check for broken links on a website. This script can crawl a website to find and report broken links, with support for different output formats and custom headers.

## Features

- Check for broken links on a single URL or a list of URLs.
- Crawl web pages to find all links and check their status.
- Customize the depth of crawling.
- Generate reports in various formats: TXT, JSON, HTML, CSV, and XLSX.
- Exclude specific domains from being checked.

## Prerequisites

Ensure you have Python 3.x installed on your system. You will also need `pip` to install the required libraries.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Xnuvers007/brokenlink
   ```

2. **Navigate to the directory:**

   ```bash
   cd brokenlink
   ```

3. **Create a virtual environment (optional but recommended):**

   ```bash
   python3 -m venv env
   ```

4. **Activate the virtual environment:**

   - On Windows:

     ```bash
     .\env\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source env/bin/activate
     ```

5. **Install the required libraries:**

   Create a file named `requirements.txt` in the same directory as the script with the following content:

   ```plaintext
   requests
   beautifulsoup4
   lxml
   pandas
   ```

   Then, install the libraries using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the script, use the following command:

```bash
python3 br.py -u <URL> [options]
```

### Options:

- `-u, --url <URL>`: The URL of the website to check for broken links (required).
- `-t, --threads <NUM>`: Number of threads to use for checking links (default: 10).
- `-o, --output <FILE>`: Output file path (supports .txt, .json, .html, .csv, .xlsx).
- `--depth <NUM>`: Depth of crawling for links (default: 1).
- `--headers <JSON>`: Custom headers to send with the requests (JSON format, default: '{}').
- `-e, --exclude <DOMAINS>`: Comma-separated list of domains to exclude from checking (default: '').

### Examples:

1. **Check a single URL and save results in a TXT file:**

   ```bash
   python3 br.py -u https://example.com -o results.txt
   ```

2. **Check a URL with custom headers and depth of crawling:**

   ```bash
   python3 br.py -u https://example.com --headers '{"User-Agent": "Mozilla/5.0"}' --depth 2
   ```

3. **Check URLs from a file and save results in JSON format:**

   ```bash
   python3 br.py -i urls.txt -o results.json
   ```

4. **Exclude specific domains from being checked:**

   ```bash
   python3 br.py -u https://example.com -e example.com,anotherdomain.com
   ```

## Running the Script

1. **Clone the repository and navigate to the directory:**

   ```bash
   git clone https://github.com/Xnuvers007/brokenlink
   cd brokenlink
   ```

2. **Run the script with your desired options. For example:**

   ```bash
   ./br.py -u https://example.com -o test.html
   or you can run it in everywhere just type
   Linux:
alias brokenlink='path\to\file\br.py'
   windows:
setx PATH "%PATH%;C:\path\to\file\br.py" /M
   ```

   Replace `https://example.com` with the URL you want to check and `test.html` with your desired output file name and format.

## Troubleshooting

- Ensure `figlet` is installed if you want to see the fancy banner. Install it using your package manager (e.g., `sudo apt install figlet` on Ubuntu).
- If you encounter network-related errors, check your internet connection and try running the script again.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- **figlet**: For the fancy banner display.
- **Requests**: For simplifying HTTP requests.
- **BeautifulSoup**: For HTML and XML parsing.
- **Pandas**: For handling and exporting data in various formats.
