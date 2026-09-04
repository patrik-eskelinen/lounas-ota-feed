/**
 * Otaniemi Campus Lunch Feed - Frontend Logic
 * Supports: Live Day Filtering, Instant Search, Dietary Filters, Slack Markdown Export,
 * Pinned Restaurants, Dark/Light Mode, Multi-language (FI/EN).
 */

(() => {
  'use strict';

  // -------------------------------------------------------------
  // Internationalization (FI / EN)
  // -------------------------------------------------------------
  const I18N = {
    fi: {
      campus_feed_subtitle: 'Otaniemen & Innopolin kampuksen lounaslistat',
      today: 'Tänään',
      all_week: 'Koko viikko',
      day_mon: 'Ma',
      day_mon_full: 'Maanantai',
      day_tue: 'Ti',
      day_tue_full: 'Tiistai',
      day_wed: 'Ke',
      day_wed_full: 'Keskiviikko',
      day_thu: 'To',
      day_thu_full: 'Torstai',
      day_fri: 'Pe',
      day_fri_full: 'Perjantai',
      search_placeholder: 'Etsi ruokaa tai ravintolaa (esim. lohi, keitto, tofu)...',
      copy_slack: 'Kopioi lounaat Slackiin',
      refresh: 'Päivitä',
      filter_by_diet: 'Erityisruokavalio:',
      diet_all: 'Kaikki',
      diet_vegan: 'Vegaani',
      diet_vegetarian: 'Kasvis',
      diet_gluten_free: 'Gluteeniton',
      diet_lactose_free: 'Laktoositon',
      diet_milk_free: 'Maidoton',
      diet_no_garlic: 'Valkosipuliton',
      reset_filters: 'Tyhjennä suodattimet',
      status_open: 'Lounas avoinna nyt',
      status_opens_at: 'Lounas alkaa klo',
      status_closed: 'Lounas päättynyt',
      status_weekend: 'Suljettu viikonloppuna',
      no_dishes_match: 'Ei valittuja hakuehtoja vastaavia annoksia tälle päivälle.',
      no_lunch_today: 'Ei lounaslistaa saatavilla tälle päivälle.',
      copy_menu_btn: 'Kopioi lista',
      open_maps: 'Kartta',
      visit_site: 'Verkkosivu',
      copied_toast: '✅ Kopioitu leikepöydälle!',
      copied_slack_toast: '✅ Päivän lounaslista kopioitu Slack/Teams-muodossa!',
      campus_guide_title: 'Otaniemen lounaskartta & ravintolat',
      campus_guide_subtitle: '5 laadukasta lounaspaikkaa Otaniemen ja Innopolin alueella',
      footer_title: 'Otaniemi Campus Lunch Feed',
      footer_disclaimer: 'Ruokalistat haetaan suoraan ravintoloiden virallisilta verkkosivuilta. Muutokset mahdollisia.',
      updated_prefix: 'Päivitetty:',
      found_dishes_prefix: 'Näytetään',
      dishes_unit: 'annosta',
      pin_tooltip: 'Kiinnitä suosikiksi kärkeen'
    },
    en: {
      campus_feed_subtitle: 'Otaniemi & Innopoli Campus Lunch Menus',
      today: 'Today',
      all_week: 'Full Week',
      day_mon: 'Mon',
      day_mon_full: 'Monday',
      day_tue: 'Tue',
      day_tue_full: 'Tuesday',
      day_wed: 'Wed',
      day_wed_full: 'Wednesday',
      day_thu: 'Thu',
      day_thu_full: 'Thursday',
      day_fri: 'Fri',
      day_fri_full: 'Friday',
      search_placeholder: 'Search food or restaurant (e.g. salmon, soup, tofu)...',
      copy_slack: 'Copy to Slack / Teams',
      refresh: 'Refresh',
      filter_by_diet: 'Dietary filter:',
      diet_all: 'All',
      diet_vegan: 'Vegan',
      diet_vegetarian: 'Vegetarian',
      diet_gluten_free: 'Gluten-free',
      diet_lactose_free: 'Lactose-free',
      diet_milk_free: 'Dairy-free',
      diet_no_garlic: 'Garlic-free',
      reset_filters: 'Clear filters',
      status_open: 'Lunch open now',
      status_opens_at: 'Lunch opens at',
      status_closed: 'Lunch closed today',
      status_weekend: 'Closed on weekends',
      no_dishes_match: 'No dishes match the selected filters for this day.',
      no_lunch_today: 'No lunch menu available for this day.',
      copy_menu_btn: 'Copy Menu',
      open_maps: 'Map',
      visit_site: 'Website',
      copied_toast: '✅ Copied to clipboard!',
      copied_slack_toast: '✅ Today\'s lunch menu copied in Slack/Teams format!',
      campus_guide_title: 'Otaniemi Campus Lunch Guide',
      campus_guide_subtitle: '5 quality lunch restaurants in Otaniemi & Innopoli area',
      footer_title: 'Otaniemi Campus Lunch Feed',
      footer_disclaimer: 'Menus are fetched directly from official restaurant websites. Changes possible.',
      updated_prefix: 'Updated:',
      found_dishes_prefix: 'Showing',
      dishes_unit: 'dishes',
      pin_tooltip: 'Pin as favorite to top'
    }
  };

  // -------------------------------------------------------------
  // App State
  // -------------------------------------------------------------
  const state = {
    menuData: null,
    activeDay: 'today', // 'today', 'mon', 'tue', 'wed', 'thu', 'fri', 'all'
    dietFilter: 'all',  // 'all', 'VE', 'KASVIS', 'G', 'L', 'M', 'NO_GARLIC'
    searchQuery: '',
    currentLang: localStorage.getItem('otaniemi_lunch_lang') || 'fi',
    theme: localStorage.getItem('otaniemi_lunch_theme') || 'system',
    pinnedRestaurants: JSON.parse(localStorage.getItem('otaniemi_lunch_pinned') || '[]')
  };

  const DAYS_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri'];

  // -------------------------------------------------------------
  // Helper: Get Current Helsinki Day Code & Time
  // -------------------------------------------------------------
  function getHelsinkiDate() {
    // Return Date adjusted to Finnish timezone (EEST / EET)
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    // Finland is UTC+3 (summer) or UTC+2 (winter).
    // Using Intl.DateTimeFormat for robust timezone representation
    try {
      const helsinkiStr = new Intl.DateTimeFormat('en-US', {
        timeZone: 'Europe/Helsinki',
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: false
      }).format(now);
      return new Date(helsinkiStr);
    } catch (e) {
      return new Date(utcTime + (3 * 3600000));
    }
  }

  function getTodayDayKey() {
    const hDate = getHelsinkiDate();
    const dayOfWeek = hDate.getDay(); // 0 = Sunday, 1 = Mon, ..., 5 = Fri, 6 = Sat
    const map = { 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri' };
    return map[dayOfWeek] || 'mon'; // If weekend, default to Monday
  }

  function isWeekend() {
    const day = getHelsinkiDate().getDay();
    return day === 0 || day === 6;
  }

  // -------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initLanguage();
    initClock();
    initEventListeners();
    fetchMenuData();
  });

  // -------------------------------------------------------------
  // Theme Management
  // -------------------------------------------------------------
  function initTheme() {
    applyTheme(state.theme);
  }

  function applyTheme(theme) {
    state.theme = theme;
    localStorage.setItem('otaniemi_lunch_theme', theme);
    document.body.setAttribute('data-theme', theme);

    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (isDark) {
      sunIcon.classList.remove('hidden');
      moonIcon.classList.add('hidden');
    } else {
      sunIcon.classList.add('hidden');
      moonIcon.classList.remove('hidden');
    }
  }

  function toggleTheme() {
    const isDark = document.body.getAttribute('data-theme') === 'dark' || 
                   (state.theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    applyTheme(isDark ? 'light' : 'dark');
  }

  // -------------------------------------------------------------
  // Language Management
  // -------------------------------------------------------------
  function initLanguage() {
    applyLanguage(state.currentLang);
  }

  function applyLanguage(lang) {
    state.currentLang = lang;
    localStorage.setItem('otaniemi_lunch_lang', lang);
    document.documentElement.lang = lang;

    // Update Lang button label
    document.getElementById('lang-label').textContent = lang === 'fi' ? '🇫🇮 FI' : '🇬🇧 EN';

    // Update all i18n text nodes
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (I18N[lang][key]) {
        el.textContent = I18N[lang][key];
      }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (I18N[lang][key]) {
        el.placeholder = I18N[lang][key];
      }
    });

    // Update Today Subtitle on Day Picker
    updateTodaySubtitle();

    if (state.menuData) {
      renderFeed();
    }
  }

  function toggleLanguage() {
    applyLanguage(state.currentLang === 'fi' ? 'en' : 'fi');
  }

  function updateTodaySubtitle() {
    const todayKey = getTodayDayKey();
    const lang = state.currentLang;
    const badgeEl = document.getElementById('today-name-badge');
    if (badgeEl) {
      badgeEl.textContent = isWeekend() 
        ? (lang === 'fi' ? 'Viikonloppu' : 'Weekend') 
        : I18N[lang][`day_${todayKey}_full`];
    }
  }

  // -------------------------------------------------------------
  // Live Clock
  // -------------------------------------------------------------
  function initClock() {
    function tick() {
      const hDate = getHelsinkiDate();
      const hours = String(hDate.getHours()).padStart(2, '0');
      const mins = String(hDate.getMinutes()).padStart(2, '0');
      const clockEl = document.getElementById('clock-text');
      if (clockEl) {
        clockEl.textContent = `${hours}:${mins}`;
      }
    }
    tick();
    setInterval(tick, 1000);
  }

  // -------------------------------------------------------------
  // Event Listeners
  // -------------------------------------------------------------
  function initEventListeners() {
    // Theme button
    document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);

    // Lang button
    document.getElementById('lang-toggle-btn').addEventListener('click', toggleLanguage);

    // Day tabs
    document.querySelectorAll('.day-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const btn = e.currentTarget;
        document.querySelectorAll('.day-tab').forEach(t => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        state.activeDay = btn.getAttribute('data-day');
        renderFeed();
      });
    });

    // Search Input
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.trim().toLowerCase();
      if (state.searchQuery.length > 0) {
        searchClearBtn.classList.remove('hidden');
      } else {
        searchClearBtn.classList.add('hidden');
      }
      renderFeed();
    });

    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      state.searchQuery = '';
      searchClearBtn.classList.add('hidden');
      searchInput.focus();
      renderFeed();
    });

    // Diet chips
    document.querySelectorAll('.diet-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        document.querySelectorAll('.diet-chip').forEach(c => c.classList.remove('active'));
        e.currentTarget.classList.add('active');
        state.dietFilter = e.currentTarget.getAttribute('data-diet');
        renderFeed();
      });
    });

    // Reset Filters button
    document.getElementById('filter-reset-btn').addEventListener('click', () => {
      state.searchQuery = '';
      state.dietFilter = 'all';
      searchInput.value = '';
      searchClearBtn.classList.add('hidden');
      document.querySelectorAll('.diet-chip').forEach(c => {
        c.classList.toggle('active', c.getAttribute('data-diet') === 'all');
      });
      renderFeed();
    });

    // Copy Slack/Teams button (if present)
    const copySlackBtn = document.getElementById('copy-slack-btn');
    if (copySlackBtn) {
      copySlackBtn.addEventListener('click', copySlackMarkdown);
    }

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
      const icon = document.getElementById('refresh-icon');
      icon.style.animation = 'spin 0.8s linear infinite';
      fetchMenuData().finally(() => {
        setTimeout(() => { icon.style.animation = 'none'; }, 600);
      });
    });
  }

  // -------------------------------------------------------------
  // Data Fetching
  // -------------------------------------------------------------
  async function fetchMenuData() {
    const feedContainer = document.getElementById('restaurant-feed');
    const skeleton = document.getElementById('skeleton-container');
    
    try {
      // Add timestamp to prevent aggressive browser caching
      const response = await fetch(`data/menus.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }
      const data = await response.json();
      state.menuData = data;
      
      // Save in localStorage as offline fallback
      localStorage.setItem('otaniemi_menus_cached', JSON.stringify(data));
      
      // Update footer timestamp
      if (data.metadata && data.metadata.generated_at_readable) {
        const updateEl = document.getElementById('footer-update-time');
        if (updateEl) {
          updateEl.textContent = `${I18N[state.currentLang].updated_prefix} ${data.metadata.generated_at_readable}`;
        }
      }
      
      renderFeed();
    } catch (err) {
      console.warn('Direct fetch error, attempting offline cache:', err);
      const cached = localStorage.getItem('otaniemi_menus_cached');
      if (cached) {
        state.menuData = JSON.parse(cached);
        renderFeed();
        showToast('⚠️ Näytetään tallennettu välimuistiversio.');
      } else {
        if (skeleton) skeleton.classList.add('hidden');
        feedContainer.innerHTML = `
          <div class="empty-dishes" style="grid-column: 1 / -1; padding: 3rem 1rem;">
            <h3>❌ Lounaslistojen lataus epäonnistui</h3>
            <p style="margin-top: 0.5rem;">Tarkista verkkoyhteys ja kokeile päivittää sivu.</p>
          </div>
        `;
      }
    }
  }

  // -------------------------------------------------------------
  // Status Pill Calculator
  // -------------------------------------------------------------
  function getRestaurantStatus(restaurant) {
    const hDate = getHelsinkiDate();
    const day = hDate.getDay();
    const lang = state.currentLang;
    
    if (day === 0 || day === 6) {
      return { class: 'closed', text: I18N[lang].status_weekend };
    }
    
    const curHour = hDate.getHours();
    const curMin = hDate.getMinutes();
    const curTotalMins = curHour * 60 + curMin;
    
    // Parse lunch hours e.g. "10:30 – 14:00" or "11:00 – 13:30"
    let startMins = 10 * 60 + 30; // default 10:30
    let endMins = 14 * 60;        // default 14:00
    
    if (restaurant.lunch_hours) {
      const match = restaurant.lunch_hours.match(/(\d{1,2})[:.](\d{2})\s*[-–]\s*(\d{1,2})[:.](\d{2})/);
      if (match) {
        startMins = parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
        endMins = parseInt(match[3], 10) * 60 + parseInt(match[4], 10);
      }
    }
    
    if (curTotalMins >= startMins && curTotalMins < endMins) {
      return { class: 'open', text: `${I18N[lang].status_open} (${restaurant.lunch_hours})` };
    } else if (curTotalMins < startMins && curTotalMins >= startMins - 60) {
      const startStr = `${Math.floor(startMins / 60)}:${String(startMins % 60).padStart(2, '0')}`;
      return { class: 'opening-soon', text: `${I18N[lang].status_opens_at} ${startStr}` };
    } else {
      return { class: 'closed', text: `${I18N[lang].status_closed} (${restaurant.lunch_hours})` };
    }
  }

  // -------------------------------------------------------------
  // Filter Matching Logic
  // -------------------------------------------------------------
  function matchDiet(dish, filter) {
    if (filter === 'all') return true;
    const diets = dish.diets || [];
    
    if (filter === 'VE') {
      return diets.includes('VE') || diets.includes('VEG') || diets.includes('VEGAANINEN');
    }
    if (filter === 'KASVIS') {
      return diets.includes('KASVIS') || diets.includes('VE') || diets.includes('VEG') || diets.includes('VEGAANINEN');
    }
    if (filter === 'G') {
      return diets.includes('G') || diets.includes('GLUTEENITON');
    }
    if (filter === 'L') {
      return diets.includes('L') || diets.includes('VL') || diets.includes('LAKTOOSITON');
    }
    if (filter === 'M') {
      return diets.includes('M') || diets.includes('MAIDOTON');
    }
    if (filter === 'NO_GARLIC') {
      return !diets.includes('VS') && !dish.title.toLowerCase().includes('valkosipuli');
    }
    return true;
  }

  function matchSearch(dish, restaurantName, query) {
    if (!query) return true;
    const titleMatch = dish.title.toLowerCase().includes(query);
    const restMatch = restaurantName.toLowerCase().includes(query);
    const dietMatch = (dish.diets || []).some(d => d.toLowerCase().includes(query));
    return titleMatch || restMatch || dietMatch;
  }

  function highlightText(text, query) {
    if (!query) return escapeHtml(text);
    const escapedText = escapeHtml(text);
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return escapedText.replace(regex, '<mark class="highlight-search">$1</mark>');
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // -------------------------------------------------------------
  // Render Feed
  // -------------------------------------------------------------
  function renderFeed() {
    if (!state.menuData || !state.menuData.restaurants) return;

    const feed = document.getElementById('restaurant-feed');
    const skeleton = document.getElementById('skeleton-container');
    if (skeleton) skeleton.classList.add('hidden');

    const effectiveDayKey = state.activeDay === 'today' ? getTodayDayKey() : state.activeDay;
    const isAllWeek = state.activeDay === 'all';
    const lang = state.currentLang;

    let totalMatchedDishes = 0;

    // Sort restaurants: Pinned first, then standard order
    const restaurants = [...state.menuData.restaurants].sort((a, b) => {
      const aPinned = state.pinnedRestaurants.includes(a.id);
      const bPinned = state.pinnedRestaurants.includes(b.id);
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
      return 0;
    });

    let html = '';

    restaurants.forEach(rest => {
      const isPinned = state.pinnedRestaurants.includes(rest.id);
      const status = getRestaurantStatus(rest);
      const desc = lang === 'en' ? (rest.description_en || rest.description_fi) : (rest.description_fi || rest.description_en);

      let daysToRender = isAllWeek ? DAYS_KEYS : [effectiveDayKey];
      let cardDishesHtml = '';
      let restDishCount = 0;

      daysToRender.forEach(dKey => {
        const dayData = rest.days ? rest.days[dKey] : null;
        if (!dayData) return;

        const dayName = lang === 'en' ? (dayData.day_en || dKey) : (dayData.day_fi || dKey);
        
        // Filter dishes
        const matchedDishes = (dayData.dishes || []).filter(dish => {
          return matchDiet(dish, state.dietFilter) && matchSearch(dish, rest.name, state.searchQuery);
        });

        restDishCount += matchedDishes.length;
        totalMatchedDishes += matchedDishes.length;

        if (isAllWeek) {
          cardDishesHtml += `
            <div class="day-header-badge">
              <span>${dayName}</span>
              <span style="font-weight: 500; font-size: 0.72rem;">${matchedDishes.length} ${I18N[lang].dishes_unit}</span>
            </div>
          `;
        }

        if (matchedDishes.length === 0) {
          cardDishesHtml += `
            <div class="empty-dishes">
              ${(state.dietFilter !== 'all' || state.searchQuery) ? I18N[lang].no_dishes_match : I18N[lang].no_lunch_today}
            </div>
          `;
        } else {
          cardDishesHtml += '<ul class="dishes-list">';
          matchedDishes.forEach(dish => {
            const dietsBadges = (dish.diets || []).map(d => {
              const dCode = d.toUpperCase();
              let cls = 'other';
              if (['VE', 'VEG', 'VEGAANINEN', 'V'].includes(dCode)) cls = 've';
              else if (dCode === 'KASVIS') cls = 'kasvis';
              else if (dCode === 'G') cls = 'g';
              else if (['L', 'VL'].includes(dCode)) cls = 'l';
              else if (dCode === 'M') cls = 'm';
              else if (dCode === 'VS') cls = 'vs';
              return `<span class="diet-tag ${cls}">${escapeHtml(d)}</span>`;
            }).join('');

            const highlightedTitle = highlightText(dish.title, state.searchQuery);
            const priceTag = dish.price ? `<span class="dish-price">${escapeHtml(dish.price)}</span>` : '';

            cardDishesHtml += `
              <li class="dish-item">
                <div class="dish-main">
                  <span class="dish-title">${highlightedTitle}</span>
                  ${priceTag}
                </div>
                ${dietsBadges ? `<div class="dish-diets">${dietsBadges}</div>` : ''}
              </li>
            `;
          });
          cardDishesHtml += '</ul>';
        }
      });

      // Google Maps URL
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(rest.maps_query || rest.location)}`;

      html += `
        <article class="restaurant-card ${isPinned ? 'pinned' : ''}" data-id="${rest.id}">
          <!-- Card Header -->
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-title-row">
                <h2 class="card-title">
                  <a href="${rest.url}" target="_blank" rel="noopener noreferrer">${escapeHtml(rest.name)}</a>
                </h2>
                <span class="area-badge">${escapeHtml(rest.area || 'Otaniemi')}</span>
              </div>
              <div class="card-status-row">
                <span class="status-pill ${status.class}">${status.text}</span>
              </div>
            </div>
            <button class="pin-btn ${isPinned ? 'active' : ''}" data-pin="${rest.id}" title="${I18N[lang].pin_tooltip}" aria-label="Pin restaurant">
              ${isPinned ? '★' : '☆'}
            </button>
          </div>

          <!-- Card Meta Row -->
          <div class="card-meta">
            <span class="meta-item">
              📍 ${escapeHtml(rest.location)} ${rest.walk_time ? `• ${escapeHtml(rest.walk_time)}` : ''}
            </span>
            ${rest.price ? `<span class="meta-price" title="${escapeHtml(rest.price_info || '')}">💶 ${escapeHtml(rest.price)}</span>` : ''}
          </div>

          <!-- Card Body: Dishes -->
          <div class="card-body">
            ${cardDishesHtml}
          </div>

          <!-- Card Footer: Actions -->
          <div class="card-footer">
            <div style="display: flex; gap: 0.4rem;">
              <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="card-action-btn">
                🗺️ ${I18N[lang].open_maps}
              </a>
              <a href="${rest.url}" target="_blank" rel="noopener noreferrer" class="card-action-btn">
                🌐 ${I18N[lang].visit_site}
              </a>
            </div>
            <button class="card-action-btn copy-single-btn" data-rest-id="${rest.id}" title="Kopioi tämän ravintolan menu">
              📋 ${I18N[lang].copy_menu_btn}
            </button>
          </div>
        </article>
      `;
    });

    feed.innerHTML = html;

    // Attach pin button listeners
    feed.querySelectorAll('.pin-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-pin');
        togglePin(id);
      });
    });

    // Attach single copy listeners
    feed.querySelectorAll('.copy-single-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const restId = e.currentTarget.getAttribute('data-rest-id');
        copySingleRestaurantMenu(restId);
      });
    });

    // Update Filter Status Bar
    updateFilterStatusBar(totalMatchedDishes);
  }

  // -------------------------------------------------------------
  // Filter Status Bar Updater
  // -------------------------------------------------------------
  function updateFilterStatusBar(matchedCount) {
    const bar = document.getElementById('filter-status-bar');
    const textEl = document.getElementById('filter-status-text');
    const lang = state.currentLang;

    const hasFilters = state.searchQuery || state.dietFilter !== 'all';
    if (hasFilters) {
      bar.classList.remove('hidden');
      textEl.textContent = `${I18N[lang].found_dishes_prefix} ${matchedCount} ${I18N[lang].dishes_unit} (${state.searchQuery ? `"${state.searchQuery}" ` : ''}${state.dietFilter !== 'all' ? `[${state.dietFilter}]` : ''})`;
    } else {
      bar.classList.add('hidden');
    }
  }

  // -------------------------------------------------------------
  // Pin Restaurant
  // -------------------------------------------------------------
  function togglePin(id) {
    if (state.pinnedRestaurants.includes(id)) {
      state.pinnedRestaurants = state.pinnedRestaurants.filter(x => x !== id);
    } else {
      state.pinnedRestaurants.push(id);
    }
    localStorage.setItem('otaniemi_lunch_pinned', JSON.stringify(state.pinnedRestaurants));
    renderFeed();
  }

  // -------------------------------------------------------------
  // Copy Slack / Teams Markdown Export
  // -------------------------------------------------------------
  function copySlackMarkdown() {
    if (!state.menuData || !state.menuData.restaurants) return;

    const effectiveDayKey = state.activeDay === 'today' ? getTodayDayKey() : state.activeDay;
    const lang = state.currentLang;
    const dayTitle = I18N[lang][`day_${effectiveDayKey}_full`] || effectiveDayKey;

    let md = `🍲 *Otaniemi Lounas • ${dayTitle}*\n\n`;

    state.menuData.restaurants.forEach(rest => {
      const dayData = rest.days ? rest.days[effectiveDayKey] : null;
      if (!dayData || !dayData.dishes || dayData.dishes.length === 0) return;

      md += `*${rest.name}* (${rest.lunch_hours} | ${rest.price || ''})\n`;
      dayData.dishes.forEach(dish => {
        const dietsStr = dish.diets && dish.diets.length > 0 ? ` _[${dish.diets.join(', ')}]_` : '';
        md += `• ${dish.title}${dietsStr}\n`;
      });
      md += `\n`;
    });

    md += `📍 _Lounaslistat Otaniemen kampukselta • ${new Date().toLocaleDateString('fi-FI')}_`;

    navigator.clipboard.writeText(md).then(() => {
      showToast(I18N[lang].copied_slack_toast);
    }).catch(err => {
      console.error('Clipboard copy error:', err);
      showToast('Kopiointi epäonnistui');
    });
  }

  function copySingleRestaurantMenu(restId) {
    if (!state.menuData || !state.menuData.restaurants) return;
    const rest = state.menuData.restaurants.find(r => r.id === restId);
    if (!rest) return;

    const effectiveDayKey = state.activeDay === 'today' ? getTodayDayKey() : state.activeDay;
    const lang = state.currentLang;
    const dayData = rest.days ? rest.days[effectiveDayKey] : null;
    const dayTitle = I18N[lang][`day_${effectiveDayKey}_full`] || effectiveDayKey;

    let text = `🍲 ${rest.name} - ${dayTitle} (${rest.lunch_hours})\n`;
    if (dayData && dayData.dishes) {
      dayData.dishes.forEach(d => {
        const diets = d.diets && d.diets.length > 0 ? ` (${d.diets.join(', ')})` : '';
        text += `• ${d.title}${diets}\n`;
      });
    }

    navigator.clipboard.writeText(text).then(() => {
      showToast(I18N[lang].copied_toast);
    });
  }

  // -------------------------------------------------------------
  // Toast Helper
  // -------------------------------------------------------------
  let toastTimer = null;
  function showToast(message) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    if (!toast || !msgEl) return;

    msgEl.textContent = message;
    toast.classList.remove('hidden');

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.add('hidden');
    }, 2800);
  }

})();
