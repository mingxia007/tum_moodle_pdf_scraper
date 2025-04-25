# Moodle-TUM PDF Scraper

This Python script automates logging into the TUM Moodle platform, retrieving course documents (PDFs), and downloading them to a specified directory. It ensures only new documents are downloaded by tracking previously downloaded files.

## Features

- Log in to TUM Moodle using TUM ID credentials
- Navigate through course pages and download PDF files from available resources
- Tracks downloaded files to prevent duplicates, ensuring only new resources are downloaded

## Prerequisites

- Python 3.6+
- Selenium
- WebDriver Manager
- Requests
- ConfigParser
