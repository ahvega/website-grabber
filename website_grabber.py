#!/usr/bin/env python3
"""
Website Grabber - A comprehensive website downloading tool.

This script allows you to download entire websites while preserving their structure,
handling dynamic content, and optionally optimizing CSS. It supports various input
formats and provides detailed progress information during the download process.

Features:
    - Complete website downloading with structure preservation
    - Dynamic content handling using Selenium
    - Smart asset management (images, JS, CSS)
    - CSS optimization and consolidation
    - Proper file extension detection
    - Progress tracking and statistics

Usage:
    $ python website_grabber.py
    Then follow the prompts to enter a website URL and choose CSS optimization options.

Requirements:
    - Python 3.8+
    - Chrome/Chromium browser
    - Dependencies listed in requirements.txt

Author: Your Name
License: MIT
Version: 1.0.0
"""

import os
import re
import urllib.parse
from typing import Set, Dict, List, Tuple
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import validators
import logging
from urllib.robotparser import RobotFileParser
import time

# Configure logging with timestamp and level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebsiteGrabber:
    """
    Main class for downloading and processing websites.
    
    This class handles all aspects of website downloading, including:
    - URL normalization and validation
    - Content downloading and processing
    - Asset management
    - CSS optimization
    - Progress tracking
    
    Attributes:
        CDN_DOMAINS (Set[str]): List of known CDN domains to preserve
        CONTENT_TYPES (Dict[str, str]): Mapping of content types to file extensions
        base_url (str): The starting URL for downloading
        domain (str): The website's domain name
        output_dir (str): Directory where files will be saved
        visited_urls (Set[str]): Tracks downloaded URLs
        failed_urls (Dict[str, str]): Stores failed URLs and their errors
        total_size (int): Total bytes downloaded
        start_time (float): Download start timestamp
        optimize_css (bool): Whether to consolidate CSS
        collected_styles (Set[str]): Unique CSS rules when optimizing
    """
    
    # Known CDN domains that should be preserved
    CDN_DOMAINS = {
        'cdn.jsdelivr.net',
        'cdnjs.cloudflare.com',
        'unpkg.com',
        'fonts.googleapis.com',
        'ajax.googleapis.com',
    }
    
    # Content type to file extension mapping
    CONTENT_TYPES = {
        'text/html': '.html',
        'text/javascript': '.js',
        'application/javascript': '.js',
        'application/x-javascript': '.js',
        'text/css': '.css',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/svg+xml': '.svg',
        'image/x-icon': '.ico',
        'application/json': '.json',
        'application/xml': '.xml',
        'text/xml': '.xml',
        'text/plain': '.txt'
    }
    
    def __init__(self, url: str, optimize_css: bool = False):
        """
        Initialize the WebsiteGrabber with a URL and options.

        Args:
            url (str): The website URL or domain name to download
            optimize_css (bool, optional): Whether to consolidate CSS. Defaults to False.

        The URL can be in various formats:
            - example.com
            - www.example.com
            - http://example.com
            - https://example.com
        """
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        self.base_url = url.rstrip('/')
        parsed_url = urllib.parse.urlparse(self.base_url)
        # Strip 'www.' if present for consistent domain matching
        self.domain = parsed_url.netloc.replace('www.', '')
        self.output_dir = os.path.join('output', self.domain)
        self.visited_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.total_size: int = 0
        self.start_time = time.time()
        self.optimize_css = optimize_css
        self.collected_styles: Set[str] = set()  # Store unique CSS rules
        self.robots_parser = RobotFileParser()
        self.setup_selenium()
        self.setup_output_directory()
        self.setup_robots_txt()
    
    def setup_selenium(self):
        """
        Configure Selenium with Chrome in headless mode.
        
        This method sets up the Selenium WebDriver for Chrome in headless mode.
        If the Chrome driver fails to initialize, it falls back to basic HTML parsing.
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            # Try using Selenium in a simpler way
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            # Fallback to using requests and BeautifulSoup only
            logger.error(f"Failed to initialize Chrome driver: {e}")
            logger.info("Falling back to basic HTML parsing without JavaScript support")
            self.driver = None
            
    def setup_output_directory(self):
        """
        Create output directory structure.
        
        This method creates the output directory for the downloaded website.
        """
        os.makedirs(self.output_dir, exist_ok=True)
    
    def setup_robots_txt(self):
        """
        Parse robots.txt if available.
        
        This method attempts to read and parse the robots.txt file for the website.
        If the file is not available or cannot be parsed, it logs a warning.
        """
        robots_url = urllib.parse.urljoin(self.base_url, '/robots.txt')
        self.robots_parser.set_url(robots_url)
        try:
            self.robots_parser.read()
        except Exception as e:
            logger.warning(f"Could not read robots.txt: {e}")
    
    def is_allowed_by_robots(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        This method checks if a given URL is allowed by the website's robots.txt rules.
        
        Args:
            url (str): The URL to check
        
        Returns:
            bool: Whether the URL is allowed
        """
        return self.robots_parser.can_fetch('*', url)
    
    def is_same_domain(self, url: str) -> bool:
        """
        Check if URL belongs to the same domain, handling www and non-www versions.
        
        This method checks if a given URL belongs to the same domain as the base URL.
        
        Args:
            url (str): The URL to check
        
        Returns:
            bool: Whether the URL is in the same domain
        """
        parsed = urllib.parse.urlparse(url)
        # Strip 'www.' if present for consistent domain matching
        url_domain = parsed.netloc.replace('www.', '')
        return url_domain == self.domain
    
    def is_cdn_url(self, url: str) -> bool:
        """
        Check if URL is from a known CDN.
        
        This method checks if a given URL is from a known Content Delivery Network (CDN).
        
        Args:
            url (str): The URL to check
        
        Returns:
            bool: Whether the URL is from a known CDN
        """
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc in self.CDN_DOMAINS
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and resolving relative paths.
        
        This method normalizes a given URL by removing any fragments and resolving relative paths.
        
        Args:
            url (str): The URL to normalize
        
        Returns:
            str: The normalized URL
        """
        parsed = urllib.parse.urlparse(url)
        clean_url = parsed._replace(fragment='').geturl()
        return urllib.parse.urljoin(self.base_url, clean_url)
    
    def get_local_path(self, url: str) -> str:
        """
        Convert URL to local file path.
        
        This method converts a given URL to a local file path within the output directory.
        
        Args:
            url (str): The URL to convert
        
        Returns:
            str: The local file path
        """
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lstrip('/')
        
        # Handle empty paths or paths ending with /
        if not path or path.endswith('/'):
            path = os.path.join(path, 'index.html')
            
        return os.path.join(self.output_dir, path)
    
    def get_file_extension(self, url: str, content_type: str = None) -> str:
        """
        Determine the appropriate file extension for a URL.

        Uses multiple methods to determine the correct extension:
        1. Extracts extension from URL path
        2. Maps content-type to extension
        3. Defaults to .html for directory-like URLs

        Args:
            url (str): The URL to analyze
            content_type (str, optional): The content-type header value

        Returns:
            str: The appropriate file extension including the dot
        """
        # First try to get extension from URL
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        
        if ext and ext != '.':
            return ext
            
        # If no extension in URL, use content type
        if content_type:
            # Remove charset and other parameters
            content_type = content_type.split(';')[0].strip().lower()
            if content_type in self.CONTENT_TYPES:
                return self.CONTENT_TYPES[content_type]
        
        # Default to .html for URLs without extension
        if url.endswith('/') or '.' not in path.split('/')[-1]:
            return '.html'
            
        return ''
    
    def extract_css(self, soup: BeautifulSoup) -> Tuple[BeautifulSoup, str]:
        """
        Extract and process CSS from HTML content.

        Handles both style tags and inline styles:
        1. Extracts and removes <style> tag contents
        2. Converts inline styles to proper CSS rules
        3. Generates unique selectors for inline styles

        Args:
            soup (BeautifulSoup): The HTML content to process

        Returns:
            Tuple[BeautifulSoup, str]: Modified soup object and collected CSS
        """
        if not self.optimize_css:
            return soup, ""
            
        # Extract and remove style tags
        style_tags = soup.find_all('style')
        for style in style_tags:
            self.collected_styles.add(style.string or '')
            style.decompose()
            
        # Extract and remove inline styles
        elements_with_style = soup.find_all(style=True)
        for element in elements_with_style:
            style_content = element['style']
            # Convert inline style to a CSS rule
            selector = self.generate_unique_selector(element)
            if selector:
                css_rule = f"{selector} {{{style_content}}}"
                self.collected_styles.add(css_rule)
            del element['style']
            
        return soup, "\n".join(self.collected_styles)
    
    def generate_unique_selector(self, element) -> str:
        """
        Generate a unique CSS selector for an HTML element.

        Uses multiple strategies in order of preference:
        1. ID-based selector
        2. Class-based selector
        3. Path-based selector using nth-of-type

        Args:
            element: BeautifulSoup element to generate selector for

        Returns:
            str: A unique CSS selector for the element
        """
        if element.get('id'):
            return f"#{element['id']}"
            
        if element.get('class'):
            return f"{element.name}.{'.'.join(element['class'])}"
            
        # Generate a path-based selector
        path = []
        current = element
        while current and current.name:
            siblings = current.find_previous_siblings(current.name)
            if siblings:
                path.append(f"{current.name}:nth-of-type({len(siblings) + 1})")
            else:
                path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))
    
    def save_consolidated_css(self):
        """
        Save collected CSS to an external file.
        
        This method saves the collected CSS rules to a file named 'styles.css' in the 'css' directory.
        """
        if not self.optimize_css or not self.collected_styles:
            return
            
        css_dir = os.path.join(self.output_dir, 'css')
        os.makedirs(css_dir, exist_ok=True)
        css_file = os.path.join(css_dir, 'styles.css')
        
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write('/* Consolidated styles */\n')
            f.write('\n'.join(self.collected_styles))
            
        logger.info(f"Consolidated CSS saved to: {css_file}")
        return '/css/styles.css'
    
    def download_file(self, url: str, local_path: str):
        """
        Download a file while showing progress.

        Features:
        - Shows progress bar with tqdm
        - Handles content-type detection
        - Adds proper file extensions
        - Creates necessary directories
        - Tracks total download size

        Args:
            url (str): URL to download from
            local_path (str): Where to save the file locally
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get content type and proper extension
            content_type = response.headers.get('content-type', '')
            ext = self.get_file_extension(url, content_type)
            
            # Add extension if missing
            if not local_path.endswith(ext):
                local_path = local_path + ext
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            
            with open(local_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=os.path.basename(local_path)
            ) as pbar:
                for chunk in response.iter_content(block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        self.total_size += len(chunk)
                        
        except Exception as e:
            self.failed_urls[url] = str(e)
            logger.error(f"Failed to download {url}: {e}")
    
    def process_html(self, content: str, base_url: str) -> str:
        """
        Process HTML content and update resource links.

        Performs multiple operations:
        1. Extracts and processes CSS if optimization is enabled
        2. Updates internal and external resource links
        3. Downloads referenced resources
        4. Maintains proper file extensions

        Args:
            content (str): The HTML content to process
            base_url (str): The base URL for resolving relative links

        Returns:
            str: The processed HTML content
        """
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract CSS if optimization is enabled
        soup, _ = self.extract_css(soup)
        
        # Add link to consolidated CSS if optimization is enabled
        if self.optimize_css:
            css_link = soup.new_tag('link', rel='stylesheet', href='/css/styles.css')
            soup.head.append(css_link)
        
        # Process different types of resources
        for tag, attr in [
            ('a', 'href'),
            ('img', 'src'),
            ('link', 'href'),
            ('script', 'src'),
        ]:
            for element in soup.find_all(tag, **{attr: True}):
                url = element[attr]
                absolute_url = urllib.parse.urljoin(base_url, url)
                
                if self.is_same_domain(absolute_url):
                    if tag == 'a':
                        self.queue_url(absolute_url)
                    local_path = self.get_local_path(absolute_url)
                    ext = self.get_file_extension(absolute_url)
                    if ext and not local_path.endswith(ext):
                        local_path += ext
                    relative_path = os.path.relpath(
                        local_path,
                        os.path.dirname(self.get_local_path(base_url))
                    )
                    element[attr] = relative_path
                elif not self.is_cdn_url(absolute_url):
                    if tag != 'a':
                        local_path = self.get_local_path(absolute_url)
                        ext = self.get_file_extension(absolute_url)
                        if ext and not local_path.endswith(ext):
                            local_path += ext
                        self.download_file(absolute_url, local_path)
                        relative_path = os.path.relpath(
                            local_path,
                            os.path.dirname(self.get_local_path(base_url))
                        )
                        element[attr] = relative_path
        
        return str(soup)
    
    def queue_url(self, url: str):
        """
        Add URL to download queue if not visited.

        This method checks if a URL has not been visited before and adds it to the download queue.
        
        Args:
            url (str): The URL to add to the queue
        """
        normalized_url = self.normalize_url(url)
        if (
            normalized_url not in self.visited_urls
            and self.is_same_domain(normalized_url)
            and self.is_allowed_by_robots(normalized_url)
        ):
            self.download_page(normalized_url)
    
    def download_page(self, url: str):
        """
        Download and process a webpage.

        This method downloads a webpage, processes its content, and saves it to the output directory.
        
        Args:
            url (str): The URL of the webpage to download
        """
        if url in self.visited_urls:
            return
            
        self.visited_urls.add(url)
        logger.info(f"Downloading: {url}")
        
        try:
            if self.driver:
                # Use Selenium for dynamic content if available
                self.driver.get(url)
                content = self.driver.page_source
            else:
                # Fallback to requests if Selenium is not available
                response = requests.get(url)
                response.raise_for_status()
                content = response.text
            
            # Process the HTML content
            processed_content = self.process_html(content, url)
            
            # Save the processed HTML
            local_path = self.get_local_path(url)
            ext = self.get_file_extension(url)
            if ext and not local_path.endswith(ext):
                local_path += ext
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
                
        except Exception as e:
            self.failed_urls[url] = str(e)
            logger.error(f"Failed to process {url}: {e}")
    
    def run(self):
        """
        Execute the website download process.

        Process:
        1. Downloads the initial page
        2. Recursively processes found URLs
        3. Consolidates CSS if enabled
        4. Generates download statistics
        5. Handles cleanup and reporting
        """
        try:
            logger.info(f"Starting download of {self.base_url}")
            self.download_page(self.base_url)
            
            # Save consolidated CSS at the end
            if self.optimize_css:
                self.save_consolidated_css()
            
        finally:
            if self.driver:
                self.driver.quit()
            
            # Calculate statistics
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            total_mb = self.total_size / (1024 * 1024)
            
            # Print summary
            print("\nDownload complete:")
            print(f"Website at domain: {self.domain}")
            print(f"Local copy downloaded to: {self.output_dir}")
            print(f"Total download time: {minutes} mins {seconds} secs")
            print(f"Total download size: {total_mb:.2f} MB")
            
            if self.optimize_css:
                print(f"Consolidated CSS file: {os.path.join(self.output_dir, 'css/styles.css')}")
            
            if self.failed_urls:
                print("\nFailed URLs:")
                for url, error in self.failed_urls.items():
                    print(f"{url}: {error}")

def main():
    """
    Main entry point for the website grabber script.
    
    Workflow:
    1. Prompts for website URL/domain
    2. Validates input format
    3. Asks about CSS optimization
    4. Initiates the download process
    5. Handles interruptions and errors
    """
    print("Website Grabber")
    print("-" * 50)
    
    url = input("\nEnter website URL or domain: ").strip()
    
    # Validate URL or domain name
    if not url.startswith(('http://', 'https://')):
        # Check if it's a valid domain name
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, url):
            print("Invalid URL or domain name. Please enter a valid URL or domain.")
            return
    
    optimize_css = input("Would you like to consolidate CSS into external files? (y/N): ").lower().startswith('y')
    
    try:
        grabber = WebsiteGrabber(url, optimize_css=optimize_css)
        grabber.run()
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
