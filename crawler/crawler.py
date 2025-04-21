import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import time

BASE_URL = "https://www.shl.com"
START_URL = urljoin(BASE_URL, "/solutions/products/product-catalog/")

def get_test_type_mapping(letter):
    mapping = {
        "A": "Ability & Aptitude",
        "B": "Biodata & Situational Judgement",
        "C": "Competencies",
        "D": "Development & 360",
        "E": "Assessment Exercises",
        "K": "Knowledge & Skills",
        "P": "Personality & Behaviour",
        "S": "Simulations"
    }
    return mapping.get(letter, f"Unknown ({letter})")

def get_assessment_details(session, url):
    """Scrape duration (as integer) and description from assessment page"""
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        details = {'duration': -1, 'description': "N/A"}

        # Scrape duration
        duration_header = soup.find('h4', string=lambda t: t and 'assessment length' in t.lower())
        if duration_header:
            duration_text = duration_header.find_next('p').get_text(strip=True)
            if '=' in duration_text:
                duration_value = duration_text.split('=')[-1].strip()
                digits = ''.join(filter(str.isdigit, duration_value))
                if digits:
                    details['duration'] = int(digits)

        # Fallback duration search
        if details['duration'] == -1:
            duration_element = soup.find('dt', string='Duration:')
            if duration_element:
                duration_text = duration_element.find_next('dd').get_text(strip=True)
                digits = ''.join(filter(str.isdigit, duration_text))
                if digits:
                    details['duration'] = int(digits)

        # Scrape description
        description_header = soup.find('h4', string='Description')
        if description_header:
            description_div = description_header.find_parent('div', class_='product-catalogue-training-calendar__row')
            if description_div:
                description_p = description_div.find('p')
                if description_p:
                    details['description'] = description_p.get_text(strip=True)

        return details

    except Exception as e:
        print(f"⚠️ Detail scraping error for {url}: {str(e)}")
        return {'duration': -1, 'description': "N/A"}

def scrape_shl_assessments():
    assessments = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    })

    current_url = START_URL
    seen_ids = set()
    page_number = 1
    is_first_page = True

    while current_url:
        print(f"\n [Page {page_number}] Scraping: {current_url}")
        try:
            time.sleep(1.5)
            response = session.get(current_url)
            
            if response.status_code != 200:
                print(f" [Page {page_number}] Failed to fetch (HTTP {response.status_code})")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            rows = []

            # Handle first page structure
            if is_first_page:
                header = soup.find('th', class_='custom__table-heading__title', 
                                 string='Individual Test Solutions')
                if header:
                    table = header.find_parent('table')
                    if table:
                        rows = table.select('tr[data-entity-id]')
                is_first_page = False
            else:
                table_container = soup.find('div', class_='product-catalogue__list')
                if table_container:
                    rows = table_container.select('tr[data-entity-id]')

            print(f" [Page {page_number}] Found {len(rows)} individual assessments")

            for row in rows:
                try:
                    uid = row.get('data-entity-id')
                    if not uid or uid in seen_ids:
                        continue
                    seen_ids.add(uid)

                    # Extract base information
                    name = row.select_one('.custom__table-heading__title a').get_text(strip=True)
                    url = urljoin(BASE_URL, row.select_one('.custom__table-heading__title a')['href'])
                    
                    # Get detailed information
                    time.sleep(0.7)  # Respectful delay
                    details = get_assessment_details(session, url)
                    
                    # Extract other metadata
                    remote = "Yes" if row.select('td:nth-of-type(2) .catalogue__circle.-yes') else "No"
                    adaptive = "Yes" if row.select('td:nth-of-type(3) .catalogue__circle.-yes') else "No"
                    test_letters = [span.get_text(strip=True) for span in row.select('.product-catalogue__key')]
                    
                    assessments.append({
                        "id": uid,
                        "name": name,
                        "url": url,
                        "duration": details['duration'],
                        "description": details['description'],
                        "remote_support": remote,
                        "adaptive_support": adaptive,
                        "test_type": [get_test_type_mapping(l) for l in test_letters]
                    })

                except Exception as e:
                    print(f" [Page {page_number}] Error processing row: {str(e)}")
                    continue

            # Handle pagination
            parsed_url = urlparse(current_url)
            base_path = urljoin(BASE_URL, parsed_url.path)
            query_params = parse_qs(parsed_url.query)
            
            current_start = int(query_params.get('start', ['0'])[0])
            new_start = current_start + 12
            
            query_params['start'] = [str(new_start)]
            if not is_first_page and 'type' not in query_params:
                query_params['type'] = ['1']
            
            next_url = f"{base_path}?{urlencode(query_params, doseq=True)}"
            
            next_btn = soup.select_one('.pagination__item.-arrow.-next:not(.-disabled) a')
            current_url = next_url if next_btn else None

            page_number += 1

        except Exception as e:
            print(f" [Page {page_number}] Critical error: {str(e)}")
            break

    return assessments

if __name__ == "__main__":
    print(" Starting enhanced SHL assessment scraper...")
    print(" This will collect durations as integers (-1 = N/A) and descriptions")
    
    data = scrape_shl_assessments()
    
    with open("shl_assessments_full.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n Successfully scraped {len(data)} assessments")
    print(" Saved to shl_assessments_full.json")
    print("Sample entry:")
    print(json.dumps(data[0], indent=2) if data else "No data collected")