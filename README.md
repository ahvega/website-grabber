# Website Grabber

A powerful Python script that recursively downloads entire websites while preserving their structure, handling dynamic content, and optimizing CSS. Perfect for creating offline copies of websites or migrating web content.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Features

- **Complete Website Downloading**
  - Downloads all internal pages and assets
  - Preserves original directory structure
  - Handles dynamic content using Selenium
  - Maintains relative links between pages

- **Smart Asset Handling**
  - Downloads images, JavaScript, CSS, and other static assets
  - Preserves CDN links for popular providers
  - Maintains external resource links
  - Automatically detects and adds proper file extensions

- **CSS Optimization**
  - Optional CSS consolidation
  - Extracts inline styles and style tags
  - Creates a single external CSS file
  - Generates unique selectors for inline styles

- **Robust Error Handling**
  - Graceful fallback for JavaScript-heavy sites
  - Detailed error logging
  - Progress tracking for downloads
  - Download size and time statistics

## 📋 Requirements

- Python 3.8 or higher
- Chrome/Chromium browser (for JavaScript support)
- Required Python packages (see `requirements.txt`)

## 🛠️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ahvega/website-grabber.git
   cd website-grabber
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

Run the script:

```bash
python website_grabber.py
```

You'll be prompted for:

1. Website URL or domain name (supports multiple formats):
   - `example.com`
   - `www.example.com`
   - `http://example.com`
   - `https://example.com`

2. CSS optimization preference:
   - Choose whether to consolidate CSS into a single external file
   - Improves maintainability and potentially reduces page load time

### Output

Downloaded websites are saved in the `output` directory:

```bash
output/
└── example.com/
    ├── index.html
    ├── css/
    │   └── styles.css      # Consolidated CSS (if enabled)
    ├── js/
    │   └── script.js
    └── images/
        └── logo.png
```

## 📊 Statistics

After completion, the script provides:

- Total download time
- Total download size
- Location of downloaded files
- List of any failed downloads

## 🔧 Advanced Features

### CSS Optimization

When enabled, the CSS optimization:

- Extracts all `<style>` tag contents
- Converts inline styles to proper CSS rules
- Generates unique selectors for inline styles
- Creates a consolidated `/css/styles.css` file
- Updates HTML files to reference the external CSS

### Content Type Detection

Automatically detects and applies proper file extensions based on:

- URL path analysis
- Content-Type headers
- Default mappings for common file types

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔍 Known Limitations

- Some JavaScript-heavy sites may not render completely
- Dynamic content loaded via AJAX might not be captured
- Some complex CSS selectors might need manual adjustment
- Rate limiting may be necessary for large sites

## 🛡️ Security Notes

- The script respects robots.txt
- CDN links are preserved by default
- No automatic execution of downloaded scripts
- Safe handling of file paths and URLs

## 📫 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/ahvega/website-grabber/issues) page
2. Open a new issue with detailed information about your problem
3. Include the Python version and operating system details
