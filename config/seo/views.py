import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.conf import settings
import spacy
from openai import OpenAI
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Initialize OpenAI client and Spacy NLP model
client = OpenAI(api_key=settings.OPENAI_API_KEY)
nlp = spacy.load('en_core_web_sm')

# Function to fetch fully-rendered page content using Selenium
def fetch_dynamic_page(url):
    # Specify the Chrome binary path
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.binary_location = '/usr/bin/google-chrome'  # Specify the path to the Chrome binary

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    
    html = driver.page_source
    driver.quit()
    return html

# Fetch PageSpeed data from Google's PageSpeed Insights API
def fetch_pagespeed_data(url):
    api_key = settings.GOOGLE_PAGESPEED_API_KEY
    api_url = f'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}'
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            speed_score = data['lighthouseResult']['categories']['performance']['score'] * 100
            return speed_score
        else:
            print(f"Failed to fetch PageSpeed data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching PageSpeed data: {e}")
        return None

# AI Function to analyze content for readability and keyword extraction
def analyze_content(content):
    doc = nlp(content)
    keyword_recommendations = set()

    # Extract named entities as potential keyword recommendations
    for ent in doc.ents:
        keyword_recommendations.add(ent.text)

    # Calculate readability score using word-to-sentence ratio
    word_count = len(content.split())
    sentence_count = len([sent for sent in doc.sents])
    readability_score = word_count / sentence_count if sentence_count > 0 else 0

    return {
        'readability_score': readability_score,
        'keyword_recommendations': list(keyword_recommendations)
    }

# Main view for AI-enhanced SEO analysis
def seo_analysis_with_ai(request):
    if request.method == "POST":
        url = request.POST.get("url")

        try:
            # Fetch fully rendered page using Selenium
            html_content = fetch_dynamic_page(url)
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract page content for analysis
            page_content = ' '.join([p.get_text() for p in soup.find_all(['p', 'div', 'section'])])

            # Perform AI content analysis
            ai_analysis = analyze_content(page_content)

            # Generate meta description and keywords using OpenAI
            meta_description = suggest_meta_description(page_content)
            meta_keywords = suggest_meta_keywords(page_content)

            # Extract manual SEO data
            title = soup.find('title').text if soup.find('title') else 'No Title Found'
            meta_description_manual = soup.find('meta', attrs={'name': 'description'})
            meta_description_manual = meta_description_manual['content'] if meta_description_manual else 'No Meta Description Found'
            meta_keywords_manual = soup.find('meta', attrs={'name': 'keywords'})
            meta_keywords_manual = meta_keywords_manual['content'] if meta_keywords_manual else 'No Meta Keywords Found'

            # Extract headings
            h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
            h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]

            # Canonical and Meta Robots tags
            canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
            canonical_url = canonical_tag['href'] if canonical_tag else 'No Canonical Tag Found'

            robots_meta = soup.find('meta', attrs={'name': 'robots'})
            robots_content = robots_meta['content'] if robots_meta else 'No Meta Robots Tag Found'

            # Image Alt Attributes (including lazy-loaded images)
            images = soup.find_all('img')
            image_alts = [{'src': img.get('src') or img.get('data-src'), 'alt': img.get('alt', 'No Alt Text')} for img in images]

            # Check broken links
            links = [a['href'] for a in soup.find_all('a', href=True)]
            broken_links = check_broken_links(links, url)

            # Word Count
            word_count = len(page_content.split())

            # Keyword Density
            target_keyword = request.POST.get("keyword", "").lower() or "your-primary-keyword"
            keyword_count = page_content.lower().count(target_keyword)
            keyword_density = (keyword_count / word_count) * 100 if word_count > 0 else 0

            # Internal and External Links
            internal_links = [link for link in links if link.startswith('/')]
            external_links = [link for link in links if not link.startswith('/')]

            # Viewport Meta Tag for Mobile Usability
            viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
            viewport_content = viewport_meta['content'] if viewport_meta else 'No Viewport Meta Tag Found'

            # Schema Markup Detection
            schema_scripts = [script for script in soup.find_all('script', type='application/ld+json')]

            # SSL/HTTPS Check
            is_https = url.startswith('https')

            # Fetch PageSpeed Data
            page_speed_score = fetch_pagespeed_data(url)

            # Check for Social Media Tags
            social_tags = check_social_tags(soup)

            # Scoring System
            seo_score = 0
            recommendations = []

            # Content Quality Score
            if word_count >= 800:
                seo_score += 10  # Full points for long content
            elif 300 <= word_count < 800:
                seo_score += 5  # Partial points for medium-length content
            else:
                recommendations.append("Your content is too short. Aim for at least 300 words.")
            
            if 1 <= keyword_density <= 3:
                seo_score += 10
            else:
                recommendations.append("Adjust your keyword density. Aim for 1-3%.")

            # Technical SEO Score
            if title != 'No Title Found':
                seo_score += 10
            else:
                recommendations.append("No Title tag found.")

            if meta_description_manual != 'No Meta Description Found':
                seo_score += 10
            else:
                recommendations.append("No Meta Description found.")

            if h1_tags:
                seo_score += 5
            else:
                recommendations.append("Add an H1 tag for better SEO.")

            if page_speed_score > 90:
                seo_score += 10
            elif 50 < page_speed_score <= 90:
                seo_score += 5
            else:
                recommendations.append("Improve page speed for better SEO performance.")

            # User Experience Score
            if not broken_links:
                seo_score += 10  # Full points for no broken links
            elif len(broken_links) < 3:
                seo_score += 5
            else:
                recommendations.append(f"{len(broken_links)} broken link(s) found. Fix them.")

            # Social Tags
            if social_tags.get('og_tags') and social_tags.get('twitter_tags'):
                seo_score += 5  # Full points for social media optimization
            else:
                recommendations.append("Add Open Graph and Twitter tags for better social media integration.")

            # Schema Markup
            if schema_scripts:
                seo_score += 5  # Bonus points for schema markup

            # Pass all data to the template
            context = {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'meta_description_manual': meta_description_manual,
                'meta_keywords_manual': meta_keywords_manual,
                'h1_tags': h1_tags,
                'h2_tags': h2_tags,
                'canonical_url': canonical_url,
                'robots_content': robots_content,
                'image_alts': image_alts,
                'broken_links': broken_links,
                'word_count': word_count,
                'keyword_density': keyword_density,
                'internal_links': internal_links,
                'external_links': external_links,
                'viewport_content': viewport_content,
                'schema_present': bool(schema_scripts),
                'is_https': is_https,
                'readability_score': ai_analysis['readability_score'],
                'keyword_recommendations': ai_analysis['keyword_recommendations'],
                'recommendations': recommendations,
                'page_speed_score': page_speed_score,
                'seo_score': seo_score,  # Final SEO Score
            }

            return render(request, 'seo/report_combined.html', context)

        except requests.exceptions.RequestException as e:
            return render(request, 'seo/form.html', {'error': f"Failed to fetch the URL. {e}"})

    return render(request, 'seo/form.html')

# Helper function to generate AI content (meta description or keywords)
def generate_ai_content(content, prompt, task):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert SEO assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return f"Failed to generate {task}"

# Generate Meta Description using OpenAI
def suggest_meta_description(content):
    prompt = f"Generate a concise and SEO-friendly meta description for the following content:\n\n{content}"
    return generate_ai_content(content, prompt, "meta description")

# Generate Meta Keywords using OpenAI
def suggest_meta_keywords(content):
    prompt = f"Generate 10 concise and SEO-friendly meta keywords for the following content:\n\n{content}"
    return generate_ai_content(content, prompt, "meta keywords")

# Function to check broken links on the page
def check_broken_links(links, base_url):
    broken_links = []
    for link in links:
        parsed_url = urlparse(link)
        if parsed_url.scheme in ['mailto', 'javascript']:
            continue
        if not parsed_url.netloc:  # Convert relative links to absolute URLs
            link = urljoin(base_url, link)
        try:
            response = requests.get(link)
            if response.status_code == 404:
                broken_links.append(link)
        except requests.exceptions.RequestException:
            continue
    return broken_links

# Function to check for OpenGraph and Twitter Cards
def check_social_tags(soup):
    og_tags = {tag['property']: tag['content'] for tag in soup.find_all('meta', property=True) if tag['property'].startswith('og:')}
    twitter_tags = {tag['name']: tag['content'] for tag in soup.find_all('meta', attrs={'name': True}) if tag['name'].startswith('twitter:')}
    return {'og_tags': og_tags, 'twitter_tags': twitter_tags}