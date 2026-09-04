#!/usr/bin/env python3
"""
Otaniemi Campus Lunch Scraper
Fetches and structures lunch menus for 6 restaurants in Otaniemi / Innopoli area:
1. Ravintola Maukas (Vuorimiehentie 5)
2. Ravintola Nova Maukas (Tietotie 3)
3. Factory Maarinportti (Maarintie 6)
4. Tastory Innopoli 2 (Tekniikantie 14)
5. Min Innopoli / Sodexo (Tekniikantie 12)
6. Prandia Din Maari (Vaisalantie 4)
"""

import os
import sys
import json
import re
import ssl
import http.cookiejar
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# Setup SSL & Headers
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
}

DAYS_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri']
DAY_NAMES = {
    'mon': {'fi': 'Maanantai', 'en': 'Monday', 'short_fi': 'Ma', 'short_en': 'Mon'},
    'tue': {'fi': 'Tiistai', 'en': 'Tuesday', 'short_fi': 'Ti', 'short_en': 'Tue'},
    'wed': {'fi': 'Keskiviikko', 'en': 'Wednesday', 'short_fi': 'Ke', 'short_en': 'Wed'},
    'thu': {'fi': 'Torstai', 'en': 'Thursday', 'short_fi': 'To', 'short_en': 'Thu'},
    'fri': {'fi': 'Perjantai', 'en': 'Friday', 'short_fi': 'Pe', 'short_en': 'Fri'}
}

def make_opener():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [(k, v) for k, v in HEADERS.items()]
    return opener

def extract_diets(text):
    """
    Extracts dietary symbols (G, L, M, VL, VE, Veg, VS, etc.) from dish text.
    """
    diets = set()
    
    # 1. Matches enclosed in parentheses like (G, L, M) or (VL+VS+G) or (g,m,v)
    for match in re.findall(r'\(([A-Za-z0-9\*\+\s,\/–\-]+)\)', text):
        tokens = [t.strip().upper() for t in re.split(r'[\+,\/\s]+', match) if t.strip()]
        known = {'G', 'L', 'VL', 'M', 'VE', 'VEG', 'V', 'VEGAANINEN', 'VS', 'ILM', '*', 'SO', 'PÄ', 'SE', 'KA', 'PA', 'SI', 'K', 'A'}
        if tokens and any(t in known for t in tokens):
            for t in tokens:
                if t in ['VEG', 'VEGAANINEN', 'V']:
                    diets.add('VE')
                elif t in known:
                    diets.add(t)
                    
    # 2. Matches trailing codes like 'G, M, VS *' or 'L, KA, VS'
    trailing = re.search(r'(?:,\s*|\s+)([GgLlMmVvSsKkPpAaEe\*\,\s]+)$', text)
    if trailing:
        cand = trailing.group(1)
        tokens = [t.strip().upper() for t in re.split(r'[\+,\/\s]+', cand) if t.strip()]
        known = {'G', 'L', 'VL', 'M', 'VE', 'VEG', 'V', 'VS', 'ILM', '*', 'SO', 'PÄ', 'SE', 'KA', 'PA', 'SI', 'K', 'A'}
        if tokens and all(t in known for t in tokens) and len(tokens) >= 1:
            for t in tokens:
                if t in ['VEG', 'V']:
                    diets.add('VE')
                elif t in known:
                    diets.add(t)
                    
    # 3. Detect keywords in dish description
    lower = text.lower()
    if 'vegaan' in lower or 'vegan' in lower:
        diets.add('VE')
    if 'kasvis' in lower or 'vegetarian' in lower or 'tofu' in lower:
        diets.add('KASVIS')
    if 'gluteeniton' in lower or 'gluten-free' in lower:
        diets.add('G')
    if 'laktoositon' in lower or 'lactose-free' in lower:
        diets.add('L')
    if 'maidoton' in lower or 'dairy-free' in lower:
        diets.add('M')
        
    return sorted(list(diets))

def clean_dish_title(text):
    """
    Cleans up dish name by normalizing whitespace and removing unnecessary formatting artifacts.
    """
    clean = text.strip()
    clean = re.sub(r'\s+', ' ', clean)
    return clean

# -------------------------------------------------------------
# 1. MAUKAS PARSER
# -------------------------------------------------------------
def fetch_maukas():
    print("Fetching Maukas...")
    url = "https://www.mau-kas.fi/en/maukas"
    opener = make_opener()
    
    try:
        opener.open('https://www.mau-kas.fi/libtent/none/19/2300/style_set_ext_id-muuttujan%20asettaja.html?style_set_ext_id=4&redirect_url=https%3A%2F%2Fwww.mau-kas.fi%2Fen%2Fmaukas', timeout=12)
        html = opener.open(url, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error loading Maukas HTML: {e}")
        html = ""

    soup = BeautifulSoup(html, 'html.parser')
    
    day_map = {
        'MONDAY': 'mon', 'TUESDAY': 'tue', 'WEDNESDAY': 'wed', 'THURSDAY': 'thu', 'FRIDAY': 'fri',
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri'
    }
    
    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    cur_day = None
    
    for p in soup.find_all('p'):
        t = p.get_text(' ', strip=True)
        if not t:
            continue
        u = t.upper().strip()
        
        matched_day = None
        for day_name, d_code in day_map.items():
            if u == day_name or u.startswith(day_name + ' ') or u.startswith(day_name + ':'):
                matched_day = d_code
                break
                
        if matched_day:
            cur_day = matched_day
        elif cur_day:
            if any(term in u for term in ['WEEK ', 'WELCOME', 'BREAKFAST', 'G = GLUTEN', 'SOUP OF THE DAY', 'SALAD PORTION', 'YOU CAN PAY', 'DURING OFFICE', 'FOR MORE INFO', 'PLEASE DO NOTE', 'ALL OF OUR FOOD', 'RAVINTOLA MAUKAS', 'ZWO OY', 'ONLINE.FI']):
                if 'WEEK ' not in u:
                    cur_day = None
                continue
            if len(t) > 3:
                diets = extract_diets(t)
                dish_obj = {
                    'title': clean_dish_title(t),
                    'diets': diets
                }
                if not any(d['title'] == dish_obj['title'] for d in days_data[cur_day]['dishes']):
                    days_data[cur_day]['dishes'].append(dish_obj)

    return {
        'id': 'maukas',
        'name': 'Ravintola Maukas',
        'url': 'https://www.mau-kas.fi/en/maukas',
        'maps_query': 'Ravintola Maukas, Vuorimiehentie 5, Espoo',
        'location': 'Vuorimiehentie 5, 02150 Espoo',
        'area': 'Otaniemi',
        'distance_tag': 'Otaniemi keskus',
        'walk_time': '4 min metroasemalta',
        'lunch_hours': '10:30 – 14:00',
        'breakfast_hours': '08:00 – 09:30',
        'price': '9,50 € – 13,00 €',
        'price_info': 'Keittolounas 11,00 € | Salaattiannos 12,00 € | Keitto + Salaatti 13,00 € | Salaattipöytä 9,50 €',
        'description_fi': 'Itse valmistettua aamiaista ja lounasta tuoreista raaka-aineista. Luomua, lähituotantoa ja MSC-kalaa.',
        'description_en': 'Homemade breakfast & lunch from fresh organic and local ingredients with MSC-certified fish.',
        'accent_color': '#43a047',
        'days': days_data
    }

# -------------------------------------------------------------
# 2. NOVA MAUKAS PARSER
# -------------------------------------------------------------
def fetch_nova_maukas():
    print("Fetching Nova Maukas...")
    url = "https://www.mau-kas.fi/nova"
    opener = make_opener()

    try:
        opener.open(
            'https://www.mau-kas.fi/libtent/none/19/2300/style_set_ext_id-muuttujan%20asettaja.html'
            '?style_set_ext_id=4&redirect_url=https%3A%2F%2Fwww.mau-kas.fi%2Fnova',
            timeout=12
        )
        html = opener.open(url, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error loading Nova Maukas HTML: {e}")
        html = ""

    soup = BeautifulSoup(html, 'html.parser')

    day_map = {
        'MONDAY': 'mon', 'TUESDAY': 'tue', 'WEDNESDAY': 'wed', 'THURSDAY': 'thu', 'FRIDAY': 'fri',
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri'
    }

    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    cur_day = None

    stop_terms = [
        'WEEK ', 'WELCOME', 'BREAKFAST', 'G = GLUTEN', 'ALLERGEENIT', 'LOUNASBUFFET',
        'KASVISLOUNAS', 'KEITTOLOUNAS', 'ANNOSSALAATTI', 'SALAATTIPÖYTÄ', 'MAKSUVÄLINE',
        'OPISKELIJA', 'TARJOLLA JOKA', 'RAVINTOLA NOVA', 'RAVINTOLA MAUKAS',
        'ZWO OY', 'ONLINE.FI', 'NOVA@', 'TIETOTIE', 'SYYSKUUN AJAN',
    ]

    for p in soup.find_all('p'):
        t = p.get_text(' ', strip=True)
        if not t:
            continue
        u = t.upper().strip()

        matched_day = None
        for day_name, d_code in day_map.items():
            if u == day_name or u.startswith(day_name + ' ') or u.startswith(day_name + ':'):
                matched_day = d_code
                break

        if matched_day:
            cur_day = matched_day
        elif cur_day:
            if any(term in u for term in stop_terms):
                if 'WEEK ' not in u:
                    cur_day = None
                continue
            if len(t) > 3:
                dish_obj = {
                    'title': clean_dish_title(t),
                    'diets': extract_diets(t)
                }
                if not any(d['title'] == dish_obj['title'] for d in days_data[cur_day]['dishes']):
                    days_data[cur_day]['dishes'].append(dish_obj)

    return {
        'id': 'nova_maukas',
        'name': 'Ravintola Nova Maukas',
        'url': 'https://www.mau-kas.fi/nova',
        'maps_query': 'Ravintola Nova Maukas, Tietotie 3, Espoo',
        'location': 'Tietotie 3, 02150 Espoo',
        'area': 'Otaniemi',
        'distance_tag': 'Otaniemi / Innopoli',
        'walk_time': '8 min metroasemalta',
        'lunch_hours': '10:30 – 14:00',
        'breakfast_hours': '08:00 – 09:30',
        'price': '9,50 € – 13,00 €',
        'price_info': 'Lounasbuffet 13,00 € | Kasvislounas 11,50 € | Keittolounas 11,00 € | Annossalaatti 12,00 € | Salaattipöytä 9,50 €',
        'description_fi': 'Ravintola Nova Maukas – kotitekoista, tuoreista luomuaineksista valmistettua lounasruokaa Tietotiellä.',
        'description_en': 'Nova Maukas – homemade lunch from fresh organic ingredients at Tietotie 3.',
        'accent_color': '#2e7d32',
        'days': days_data
    }

# -------------------------------------------------------------
# 3. FACTORY MAARINPORTTI PARSER
# -------------------------------------------------------------
def fetch_factory():
    print("Fetching Factory Maarinportti...")
    url = "https://ravintolafactory.com/lounasravintolat/ravintolat/factory-maarinportti/#"
    opener = make_opener()
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = opener.open(req, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error loading Factory HTML: {e}")
        html = ""

    soup = BeautifulSoup(html, 'html.parser')
    
    day_map = {
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri',
        'MONDAY': 'mon', 'TUESDAY': 'tue', 'WEDNESDAY': 'wed', 'THURSDAY': 'thu', 'FRIDAY': 'fri'
    }
    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    
    def is_real_day_header(tag):
        if not tag or tag.name not in ['h3', 'h4']:
            return None
        txt = tag.get_text(strip=True)
        first_word = txt.split()[0].upper() if txt.split() else ''
        if first_word in day_map:
            return day_map[first_word]
        return None

    headings = soup.find_all(['h3', 'h4'])
    for h in headings:
        d_key = is_real_day_header(h)
        if d_key:
            node = h.next_sibling
            while node:
                if is_real_day_header(node):
                    break
                if hasattr(node, 'find_all'):
                    lines = []
                    html_content = getattr(node, 'decode_contents', lambda: str(node))()
                    for line in re.split(r'<br\s*\/?>', html_content, flags=re.I):
                        s_line = BeautifulSoup(line, 'html.parser')
                        clean_line = s_line.get_text(strip=True)
                        if clean_line and len(clean_line) > 3 and not clean_line.startswith('<img'):
                            lines.append(clean_line)
                    for item in lines:
                        if not any(d['title'] == item for d in days_data[d_key]['dishes']):
                            days_data[d_key]['dishes'].append({
                                'title': clean_dish_title(item),
                                'diets': extract_diets(item)
                            })
                node = node.next_sibling

    return {
        'id': 'factory',
        'name': 'Factory Maarinportti',
        'url': 'https://ravintolafactory.com/lounasravintolat/ravintolat/factory-maarinportti/#',
        'maps_query': 'Factory Maarinportti, Maarintie 6, Espoo',
        'location': 'Maarintie 6, 02150 Espoo',
        'area': 'Otaniemi',
        'distance_tag': 'Maarinportti',
        'walk_time': '6 min metroasemalta',
        'lunch_hours': '10:30 – 14:00',
        'price': '13,70 €',
        'price_info': 'Lounasbuffet 13,70 € (sis. salaattipöytä, keitto, 3 lämmintä ruokaa, leipä, jälkiruoka & kahvi/tee)',
        'description_fi': 'Runsas ja suosittu lounasbuffet sekä kattava salaattibaari.',
        'description_en': 'Famous lunch buffet with wide salad bar, daily soup, hot mains, freshly baked bread & dessert.',
        'accent_color': '#e53935',
        'days': days_data
    }

# -------------------------------------------------------------
# 3. TASTORY INNOPOLI 2 (COMPASS GROUP) PARSER
# -------------------------------------------------------------
def fetch_tastory():
    print("Fetching Tastory Innopoli 2...")
    url = "https://www.compass-group.fi/ravintolat-ja-ruokalistat/tastory/kaupungit/espoo/innopoli2/"
    opener = make_opener()
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = opener.open(req, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error loading Tastory HTML: {e}")
        html = ""

    soup = BeautifulSoup(html, 'html.parser')
    
    day_map = {
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri'
    }
    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    
    articles = soup.find_all('article')
    for art in articles:
        h = art.find(['h2', 'h3', 'h4'])
        if not h:
            continue
        h_text = h.get_text(strip=True)
        first_word = h_text.split()[0].upper() if h_text.split() else ''
        if first_word in day_map:
            d_key = day_map[first_word]
            
            list_items = art.find_all('li')
            if list_items:
                for li in list_items:
                    strong = li.find('strong')
                    span = li.find('span')
                    title = strong.get_text(strip=True) if strong else li.get_text(' ', strip=True)
                    span_text = span.get_text(strip=True) if span else ''
                    
                    if title and len(title) > 2:
                        diets = extract_diets(span_text) or extract_diets(title)
                        dish_obj = {
                            'title': clean_dish_title(title),
                            'diets': diets
                        }
                        if not any(d['title'] == dish_obj['title'] for d in days_data[d_key]['dishes']):
                            days_data[d_key]['dishes'].append(dish_obj)
            else:
                for elem in art.find_all(['p', 'h4', 'div']):
                    t = elem.get_text(' ', strip=True)
                    if not t or t == h_text or 'Lounas tarjolla' in t or 'Tekniikantie' in t:
                        continue
                    if t.startswith('(') and t.endswith(')') and len(t) < 30:
                        continue
                    if len(t) > 3:
                        dish_obj = {
                            'title': clean_dish_title(t),
                            'diets': extract_diets(t)
                        }
                        if not any(d['title'] == dish_obj['title'] for d in days_data[d_key]['dishes']):
                            days_data[d_key]['dishes'].append(dish_obj)

    return {
        'id': 'tastory',
        'name': 'Tastory Innopoli 2',
        'url': 'https://www.compass-group.fi/ravintolat-ja-ruokalistat/tastory/kaupungit/espoo/innopoli2/',
        'maps_query': 'Tastory Innopoli 2, Tekniikantie 14, Espoo',
        'location': 'Tekniikantie 14, 02150 Espoo',
        'area': 'Innopoli 2, Otaniemi',
        'distance_tag': 'Innopoli 2',
        'walk_time': '8 min metroasemalta',
        'lunch_hours': '10:30 – 13:30',
        'price': '13,50 € – 14,50 €',
        'price_info': 'Lounasbuffet, salaattipöytä ja keitto',
        'description_fi': 'Tastory suosii tuoreita, raikkaita ja sesonginmukaisia makuja sekä monipuolisia kasvisvaihtoehtoja.',
        'description_en': 'Fresh, seasonal lunch buffet featuring healthy options, daily soups and rich salads.',
        'accent_color': '#0288d1',
        'days': days_data
    }

# -------------------------------------------------------------
# 4. MIN INNOPOLI (SODEXO) PARSER
# -------------------------------------------------------------
def fetch_sodexo():
    print("Fetching Sodexo Min Innopoli...")
    url = "https://www.sodexo.fi/ravintolat/min-innopoli"
    opener = make_opener()
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = opener.open(req, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error loading Sodexo HTML: {e}")
        html = ""

    soup = BeautifulSoup(html, 'html.parser')
    
    day_map = {
        'MA': 'mon', 'TI': 'tue', 'KE': 'wed', 'TO': 'thu', 'PE': 'fri',
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri'
    }
    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    
    menu_view = soup.find('div', class_='block-sxo-menu-view-block')
    if menu_view:
        tab_links = menu_view.find_all('li')
        for li in tab_links:
            a = li.find('a')
            if not a:
                continue
            tab_href = a.get('href', '').replace('#', '')
            tab_text = a.get_text(strip=True).upper()
            
            d_key = None
            for prefix, k in day_map.items():
                if tab_text.startswith(prefix):
                    d_key = k
                    break
            
            if not d_key:
                continue
                
            tab_div = menu_view.find('div', id=tab_href)
            if tab_div:
                for row in tab_div.find_all('div', class_='mealrow'):
                    name_wrap = row.find('div', class_='meal-name-wrapper')
                    title = name_wrap.get_text(' ', strip=True) if name_wrap else ''
                    price_elem = row.find('div', class_='mealprices')
                    price = price_elem.get_text(strip=True) if price_elem else ''
                    diet_elem = row.find('div', class_='mealdietcodes')
                    
                    diets = []
                    if diet_elem:
                        spans = [s.get_text(strip=True) for s in diet_elem.find_all('span') if s.get_text(strip=True)]
                        if spans:
                            diets = spans
                        else:
                            diets = [d.strip() for d in re.split(r'[\s,\|]+', diet_elem.get_text(strip=True)) if d.strip()]
                    
                    if title:
                        cleaned = re.sub(r'^(MIN Chef|Buffet|Dessert)\s*(\1:?)\s*', r'\1: ', title)
                        if not diets:
                            diets = extract_diets(cleaned)
                        dish_obj = {
                            'title': clean_dish_title(cleaned),
                            'price': price,
                            'diets': diets
                        }
                        if not any(d['title'] == dish_obj['title'] for d in days_data[d_key]['dishes']):
                            days_data[d_key]['dishes'].append(dish_obj)

    return {
        'id': 'sodexo',
        'name': 'Min Innopoli (Sodexo)',
        'url': 'https://www.sodexo.fi/ravintolat/min-innopoli',
        'maps_query': 'MIN Innopoli Sodexo, Tekniikantie 12, Espoo',
        'location': 'Tekniikantie 12, 02150 Espoo',
        'area': 'Innopoli 1, Otaniemi',
        'distance_tag': 'Innopoli 1',
        'walk_time': '7 min metroasemalta',
        'lunch_hours': '11:00 – 13:30',
        'price': '14,00 € – 17,05 €',
        'price_info': 'MIN Lunch buffet 14,00 € | MIN Chef annokset 14,00 € – 17,05 €',
        'description_fi': 'Moderni lounasravintola ja kahvila Innopoli 1:ssä.',
        'description_en': 'Modern lunch restaurant and cafe located in Innopoli 1.',
        'accent_color': '#7b1fa2',
        'days': days_data
    }

# -------------------------------------------------------------
# 5. PRANDIA DIN MAARI PARSER
# -------------------------------------------------------------
def fetch_prandia():
    print("Fetching Prandia Din Maari...")
    api_url = "https://prandialounas.mainostoimistokompassi.fi/api/lunch-menu.php?restaurant=prandia-din-maari"
    web_url = "https://prandia.fi/prandia-din-maari-lounas-otaniemi-tapiola.html"
    
    day_map = {
        'MAANANTAI': 'mon', 'TIISTAI': 'tue', 'KESKIVIIKKO': 'wed', 'TORSTAI': 'thu', 'PERJANTAI': 'fri',
        'MONDAY': 'mon', 'TUESDAY': 'tue', 'WEDNESDAY': 'wed', 'THURSDAY': 'thu', 'FRIDAY': 'fri'
    }
    days_data = {
        k: {
            'day_key': k,
            'day_fi': DAY_NAMES[k]['fi'],
            'day_en': DAY_NAMES[k]['en'],
            'short_fi': DAY_NAMES[k]['short_fi'],
            'short_en': DAY_NAMES[k]['short_en'],
            'dishes': []
        } for k in DAYS_ORDER
    }
    
    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        data = json.loads(urllib.request.urlopen(req, context=CTX, timeout=12).read().decode('utf-8'))
        
        if data.get('weekly_text') and data['weekly_text'].get('content'):
            html_content = data['weekly_text']['content']
            parts = re.split(r'<h3>Week\s+\d+</h3>', html_content, flags=re.I)
            fi_html = parts[0]
            
            soup = BeautifulSoup(fi_html, 'html.parser')
            text_lines = [line.strip() for line in soup.get_text('\n').split('\n') if line.strip()]
            cur_day = None
            for line in text_lines:
                first_word = line.split()[0].upper() if line.split() else ''
                if first_word in day_map:
                    cur_day = day_map[first_word]
                elif cur_day:
                    if any(w in line.upper() for w in ['WEEK ', 'VKO ', 'ENJOY', 'WELCOME', 'LOUNASBUFFET']):
                        continue
                    if len(line) > 3:
                        dish_obj = {
                            'title': clean_dish_title(line),
                            'diets': extract_diets(line)
                        }
                        if not any(d['title'] == dish_obj['title'] for d in days_data[cur_day]['dishes']):
                            days_data[cur_day]['dishes'].append(dish_obj)
        elif data.get('menu'):
            for m in data['menu']:
                day_title = m.get('title') or m.get('day') or ''
                first_word = day_title.split()[0].upper() if day_title.split() else ''
                if first_word in day_map:
                    d_key = day_map[first_word]
                    soup = BeautifulSoup(m.get('content', ''), 'html.parser')
                    for line in soup.get_text('\n').split('\n'):
                        l = line.strip()
                        if l and len(l) > 3 and not any(w in l.upper() for w in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']):
                            dish_obj = {
                                'title': clean_dish_title(l),
                                'diets': extract_diets(l)
                            }
                            if not any(d['title'] == dish_obj['title'] for d in days_data[d_key]['dishes']):
                                days_data[d_key]['dishes'].append(dish_obj)
    except Exception as e:
        print(f"Error fetching Prandia: {e}")

    return {
        'id': 'prandia',
        'name': 'Prandia Din Maari',
        'url': web_url,
        'maps_query': 'Prandia Din Maari, Vaisalantie 4, Espoo',
        'location': 'Vaisalantie 4 (Innopoli 3, B-talo), 02130 Espoo',
        'area': 'Innopoli 3, Otaniemi',
        'distance_tag': 'Innopoli 3',
        'walk_time': '10 min metroasemalta',
        'lunch_hours': '11:00 – 13:30',
        'price': '12,60 € – 14,00 €',
        'price_info': 'Lounasbuffet 14,00 € | Keitto ja salaatti 12,60 €',
        'description_fi': 'Lounasbuffet sisältää kolme eri lämmintä ruokaa, runsaan salaattipöydän, päivän keiton ja leivän.',
        'description_en': 'Lunch buffet includes 3 hot dishes, extensive salad bar, daily soup, fresh bread and coffee/tea.',
        'accent_color': '#f57c00',
        'days': days_data
    }

def main():
    print(f"Starting Otaniemi lunch scrape at {datetime.now(timezone.utc).isoformat()}...")
    
    restaurants = []
    
    for scraper in [fetch_maukas, fetch_nova_maukas, fetch_factory, fetch_tastory, fetch_sodexo, fetch_prandia]:
        try:
            res = scraper()
            dish_count = sum(len(d['dishes']) for d in res['days'].values())
            print(f"✓ Parsed {res['name']}: {dish_count} total dishes across the week")
            restaurants.append(res)
        except Exception as e:
            print(f"✗ Failed to scrape {scraper.__name__}: {e}")
            
    now = datetime.now(timezone(timedelta(hours=3)))
    output = {
        'metadata': {
            'generated_at': now.isoformat(),
            'generated_at_readable': now.strftime('%d.%m.%Y %H:%M'),
            'restaurant_count': len(restaurants),
            'area': 'Otaniemi / Espoo',
            'version': '1.0.0'
        },
        'restaurants': restaurants
    }
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'menus.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"\nSuccessfully wrote {output_file} ({os.path.getsize(output_file)} bytes).")

if __name__ == '__main__':
    main()
