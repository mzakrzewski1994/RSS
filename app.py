import streamlit as st
import streamlit.components.v1 as components
import feedparser
from datetime import datetime
import pytz
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh

# Function to set custom page container style
def set_page_container_style(
        max_width: int = 1100, max_width_100_percent: bool = False,
        padding_top: int = 1, padding_right: int = 1, padding_left: int = 1, padding_bottom: int = 1,
        color: str = 'black', background_color: str = 'white',
    ):
    st.set_page_config(layout="wide")
    if max_width_100_percent:
        max_width_str = 'max-width: 100%;'
    else:
        max_width_str = f'max-width: {max_width}px;'
    st.markdown(
        f'''
        <style>
            .reportview-container .sidebar-content {{
                padding-top: {padding_top}rem;
            }}
            .reportview-container .main .block-container {{
                {max_width_str}
                padding-top: {padding_top}rem;
                padding-right: {padding_right}rem;
                padding-left: {padding_left}rem;
                padding-bottom: {padding_bottom}rem;
            }}
            .reportview-container .main {{
                color: {color};
                background-color: {background_color};
            }}
            .st-emotion-cache-1jicfl2 {{
                padding-top: 3rem;
                padding-right: 0rem;
                padding-left: 0rem;
                padding-bottom: 0rem;
            }}
            html, body {{
                overflow: hidden;
            }}
        </style>
        ''',
        unsafe_allow_html=True,
    )

# Apply the custom page container style
set_page_container_style(max_width_100_percent=True, padding_top=0, padding_right=0, padding_left=0, padding_bottom=0)

# Set up auto-refresh every 60 seconds
#st_autorefresh(interval=60000, key="datarefresh")

# Add Rerun button
if st.button("Rerun"):
    st.experimental_rerun()

# Define sources with manual names
sources = {
    "Energetyka24": "https://energetyka24.com/_rss",
    "Green News": "https://www.green-news.pl/rss",
    "WNP": "https://www.wnp.pl/rss/serwis_rss.xml",
    "Biznes Alert": "https://biznesalert.pl/feed/",
    "Zielona Gospodarka": "https://zielonagospodarka.pl/articles/rss",
    "Teraz Srodowisko": "https://www.teraz-srodowisko.pl/rss/",
    "Wysokie Napiecie": "https://wysokienapiecie.pl/feed/",
    "CIRE": "https://www.cire.pl/rss/energetyka.xml",
    "Kierunek Energetyka": "https://www.kierunekenergetyka.pl/rss.html",
    "RP Energetyka": "https://energia.rp.pl/rss/4351-energetyka",
    "Wyborcza Energetyka": "https://wyborcza.biz/pub/rss/wyborcza_biz_energetyka.xml",
    "Offshore Wind Poland": "https://offshorewindpoland.pl/feed/",
    "Gospodarka Morska": "https://www.gospodarkamorska.pl/articles/rss",
    "Business Insider": "https://businessinsider.com.pl/.feed",
    "Money": "https://www.money.pl/rss/",
    "Puls Biznesu": "https://www.pb.pl/rss/najnowsze.xml?utm_source=RSS&utm_medium=RSS&utm_campaign=Z%20ostatniej%20chwili",
    "Zielona Interia": "https://zielona.interia.pl/feed",
    "Gazeta Prawna": "https://biznes.gazetaprawna.pl/.feed",
    "Forbes": "https://www.forbes.pl/rss.xml",
    "Bankier": "https://www.bankier.pl/rss/wiadomosci.xml",
    "Gazeta": "https://www.gazeta.pl/pub/rss/wiadomosci.xml",
    "Strefa Inwestorow": "https://strefainwestorow.pl/w-zielonej-strefie/rss.xml",
    "300Gospodarka": "https://300gospodarka.pl/feed",
    "Polsat News": "https://www.polsatnews.pl/rss/biznes.xml",
    "RP Najnowsze": "https://rp.pl/rss_main?unknown-old-rss",
    "Wyborcza Najnowsze": "https://rss.gazeta.pl/pub/rss/najnowsze_wyborcza.xml",
    "TVN24 Biznes": "https://tvn24.pl/biznes.xml",
    "Forsal": "https://forsal.pl/.feed",
    "Onet": "https://wiadomosci.onet.pl/.feed",
    "WP": "https://wiadomosci.wp.pl/rss.xml",
    "Newsweek": "https://www.newsweek.pl/.feed",
    "TOK FM": "https://www.tokfm.pl/pub/rss/tokfmpl_glowne.xml",
    "Wprost": "https://www.wprost.pl/rss/wiadomosci",
    "RMF24": "https://www.rmf24.pl/feed",
    "300Polityka": "https://300polityka.pl/feed",
}

# Define keywords for the original filters
original_keywords = ["aramco", "lotos", "obajtek", "orlen", "energetyk", "wodor", "wiatr", "pv", "offshore", "ccs/ccus", "pfas"]

# Define expanded list of keywords for the new "Wiadomości Sektorowe" button
sector_keywords = [
  "aramco", "lotos", "obajtek", "orlen", "energetyka", "energetyki", "energetyce", "energetykę", 
    "wodór", "wodoru", "wodorem", "wiatr", "wiatru", "wiatrze", "wiatrak", "wiatraka", "wiatraku", 
    "pv", "fotowoltaika", "fotowoltaiki", "fotowoltaice", "fotowoltaikę", "offshore", 
    "ccs", "ccsu", "ccus", "pfas", 
    "odnawialne źródła energii", "odnawialnych źródeł energii", "odnawialnym źródłom energii", 
    "energia słoneczna", "energii słonecznej", "energię słoneczną", 
    "elektrownie wiatrowe", "elektrowni wiatrowych", "elektrowniom wiatrowym", "fotowoltaika", "fotowoltaiki", "fotowoltaice",
    "farmy wiatrowe", "farm wiatrowych", "farmom wiatrowym", 
    "biogaz", "biogazu", "biogazem", 
    "energia geotermalna", "energii geotermalnej", "energię geotermalną", 
    "elektromobilność", "elektromobilności", 
    "transformacja energetyczna", "transformacji energetycznej", 
    "neutralność klimatyczna", "neutralności klimatycznej", 
    "emisje CO2", "emisji CO2", "emisjom CO2", 
    "ślad węglowy", "śladu węglowego", "śladem węglowym", 
    "efektywność energetyczna", "efektywności energetycznej", "ETS",
    "panele słoneczne", "paneli słonecznych", "panelom słonecznym", 
    "sieci energetyczne", "sieci energetycznych", "sieciom energetycznym", 
    "magazynowanie energii", "magazynowania energii", "magazynowaniu energii", 
    "akumulatory", "akumulatorów", "akumulatorom", 
    "zielona energia", "zielonej energii", "zieloną energię", 
    "zielony wodór", "zielonego wodoru", "zielonym wodorem", 
    "hydroelektryczność", "hydroelektryczności", 
    "gaz łupkowy", "gazu łupkowego", "gazem łupkowym", 
    "energia jądrowa", "energii jądrowej", "energię jądrową", 
    "reaktory modularne", "reaktorów modularnych", "reaktorom modularnym", 
    "polska energetyka", "polskiej energetyki", "polskiej energetyce", 
    "globalne ocieplenie", "globalnego ocieplenia", "globalnemu ociepleniu", 
    "zmiany klimatyczne", "zmian klimatycznych", "zmianom klimatycznym", 
    "emisje metanu", "emisji metanu", "emisjom metanu", 
    "zrównoważony rozwój", "zrównoważonego rozwoju", "zrównoważonemu rozwojowi", 
    "gospodarka w obiegu zamkniętym", "gospodarki w obiegu zamkniętym", "gospodarce w obiegu zamkniętym", 
    "inteligentne sieci", "inteligentnych sieci", "inteligentnym sieciom", 
    "elektrownie atomowe", "elektrowni atomowych", "elektrowniom atomowym", 
    "reaktory jądrowe", "reaktorów jądrowych", "reaktorom jądrowym", 
    "farmy fotowoltaiczne", "farm fotowoltaicznych", "farmom fotowoltaicznym", 
    "dekarbonizacja", "dekarbonizacji", 
    "recykling energii", "recyklingu energii", "recyklingowi energii", 
    "polityka klimatyczna", "polityki klimatycznej", "polityce klimatycznej", 
    "konwencjonalne źródła energii", "konwencjonalnych źródeł energii", "konwencjonalnym źródłom energii", 
    "odnawialna energia", "odnawialnej energii", "odnawialną energię", 
    "międzynarodowe porozumienia klimatyczne", "międzynarodowych porozumień klimatycznych", "międzynarodowym porozumieniom klimatycznym", 
    "efektywność zasobowa", "efektywności zasobowej", 
    "gospodarka niskoemisyjna", "gospodarki niskoemisyjnej", 
    "regulacje środowiskowe", "regulacji środowiskowych", "regulacjom środowiskowym", 
    "konwencje chemiczne", "konwencji chemicznych", "konwencjom chemicznym", 
    "substancje chemiczne", "substancji chemicznych", "substancjom chemicznym", 
    "regulacje REACH", "regulacji REACH", "regulacjom REACH", 
    "substancje toksyczne", "substancji toksycznych", "substancjom toksycznym", 
    "zanieczyszczenie powietrza", "zanieczyszczenia powietrza", "zanieczyszczeniu powietrza", 
    "normy emisji", "norm emisji", "normom emisji", 
    "paliwa alternatywne", "paliw alternatywnych", "paliwom alternatywnym", 
    "paliwa kopalniane", "paliw kopalnianych", "paliwom kopalnianym", 
    "kryzys energetyczny", "kryzysu energetycznego", "kryzysowi energetycznemu", 
    "bezpieczeństwo energetyczne", "bezpieczeństwa energetycznego", "bezpieczeństwu energetycznemu", 
    "ceny energii", "cen energii", "cenom energii", 
    "taryfy energetyczne", "taryf energetycznych", "taryfom energetycznym", 
    "polska polityka energetyczna", "polskiej polityki energetycznej", "polskiej polityce energetycznej", 
    "elektrownie węglowe", "elektrowni węglowych", "elektrowniom węglowym", 
    "zamknięcie kopalni", "zamknięcia kopalni", "zamknięciu kopalni", 
    "transformacja węglowa", "transformacji węglowej", 
    "pompy ciepła", "pomp ciepła", "pompom ciepła", 
    "ogrzewanie elektryczne", "ogrzewania elektrycznego", "ogrzewaniu elektrycznemu", 
    "technologie niskoemisyjne", "technologii niskoemisyjnych", "technologiom niskoemisyjnym", 
    "infrastruktura energetyczna", "infrastruktury energetycznej", "infrastrukturze energetycznej", 
    "sieci przesyłowe", "sieci przesyłowych", "sieciom przesyłowym", 
    "polskie farmy wiatrowe", "polskich farm wiatrowych", "polskim farmom wiatrowym", 
    "zielony ład", "zielonego ładu", "zielonemu ładowi", 
    "energetyka konwencjonalna", "energetyki konwencjonalnej", "energetyce konwencjonalnej", 
    "regulacje energetyczne", "regulacji energetycznych", "regulacjom energetycznym", 
    "smog", "smogu", "smogiem", 
    "oczyszczanie powietrza", "oczyszczania powietrza", "oczyszczaniu powietrza", 
    "technologie OZE", "technologii OZE", "technologiom OZE", 
    "fundusze klimatyczne", "funduszy klimatycznych", "funduszom klimatycznym", 
    "zielone inwestycje", "zielonych inwestycji", "zielonym inwestycjom", 
    "ESG", "ekorozwój", "ekorozwoju", 
    "certyfikaty CO2", "certyfikatów CO2", "certyfikatom CO2", 
    "ETS", "system handlu emisjami", "systemu handlu emisjami", "systemowi handlu emisjami", 
    "odnawialne paliwa", "odnawialnych paliw", "odnawialnym paliwom", 
    "produkcja energii", "produkcji energii", "produkcję energii", 
    "polityka środowiskowa", "polityki środowiskowej", "polityce środowiskowej", 
    "adaptacja klimatyczna", "adaptacji klimatycznej", 
    "przetwarzanie odpadów", "przetwarzania odpadów", "przetwarzaniu odpadów", 
    "energetyka morska", "energetyki morskiej", "energetyce morskiej", 
    "biopaliwa", "biopaliw", "biopaliwom", 
    "zmniejszenie emisji", "zmniejszenia emisji", "zmniejszeniu emisji", 
    "zeroemisyjność", "zeroemisyjności", 
    "modernizacja energetyczna", "modernizacji energetycznej", 
    "nowe technologie energetyczne", "nowych technologii energetycznych", "nowym technologiom energetycznym"
]

# Set up default state for checkboxes
if 'source_checks' not in st.session_state:
    st.session_state['source_checks'] = {source: True for source in sources.keys()}
if 'keyword_checks' not in st.session_state:
    st.session_state['keyword_checks'] = {keyword: False for keyword in original_keywords}
if 'custom_filter' not in st.session_state:
    st.session_state['custom_filter'] = ""
if 'sector_news' not in st.session_state:
    st.session_state['sector_news'] = False

def clean_html(html):
    html = re.sub(r'<img[^>]*>', '', html)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'<[^>]+>', '', html)
    return html

def process_summary(summary):
    if '\n\n\n\n' in summary:
        parts = summary.split('\n\n\n\n')
        return parts[0] + ". " + parts[1]
    else:
        return summary

def parse_date(date_str):
    date_str = re.sub(r'^[a-z]{2,3}\.,\s', '', date_str.lower(), flags=re.IGNORECASE)
    date_formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
        "%a, %d %b %Y %H:%M %Z",
        "%a, %d %b %Y %H:%M",
        "%d/%m/%Y - %H:%M"
    ]
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    raise ValueError(f"time data '{date_str}' does not match any known format")

def normalize_to_utc_plus_two(published_parsed, published, source):
    if published_parsed is not None:
        if source == 'wnp.pl':
            local_dt = datetime(*published_parsed[:6], tzinfo=pytz.UTC)
        else:
            local_dt = datetime(*published_parsed[:6])
    else:
        try:
            local_dt = parse_date(published)
        except Exception as e:
            st.error(f"Failed to parse date {published}: {e}")
            return None
    return local_dt.astimezone(pytz.UTC)

def fetch_feed(name, rss_url):
    filtered_entries = []
    unique_entries = set()
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            summary = entry.summary if 'summary' in entry else (entry.description if 'description' in entry else '')
            summary = clean_html(summary)
            summary = process_summary(summary)
            entry_id = entry.link

            if entry_id not in unique_entries:
                unique_entries.add(entry_id)
                published_dt = normalize_to_utc_plus_two(entry.published_parsed, entry.published, feed.feed.title)

                filtered_entries.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': published_dt,
                    'published_str': published_dt.strftime('%a, %d %b %Y %H:%M') if published_dt else 'Unknown',
                    'summary': summary,
                    'source': name
                })
    except Exception as e:
        st.error(f"Failed to process feed {rss_url}: {e}")

    return filtered_entries

def fetch_and_process_feeds():
    filtered_entries = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_source = {executor.submit(fetch_feed, name, rss_url): name for name, rss_url in sources.items()}
        for future in as_completed(future_to_source):
            source_entries = future.result()
            filtered_entries.extend(source_entries)

    filtered_entries.sort(key=lambda x: x['published'] or datetime.min.replace(tzinfo=pytz.timezone('Europe/Warsaw')), reverse=True)
    return filtered_entries

def display_entries(entries):
    html = '''
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; display: flex; margin: 0; padding: 0; overflow: hidden; }
            .sidebar { flex: 0 0 200px; padding: 5px; border-right: 1px solid #ddd; height: 100vh; overflow-y: auto; position: fixed; }
            .topbar { position: fixed; top: 0; left: 200px; right: 0; background-color: white; padding: 5px; border-bottom: 1px solid #ddd; z-index: 1000; }
            .content { margin-top: 70px; margin-left: 210px; flex: 1; padding: 5px; height: calc(100vh - 70px); overflow-y: auto; }
            .entry { border-bottom: 1px solid #ddd; padding: 5px 0; }
            .title a { text-decoration: none; color: #000; font-weight: bold; font-size: 1.1em; }
            .summary { margin: 5px 0; font-size: 0.9em; color: #333; }
            .meta { font-size: 0.8em; color: #777; }
            .highlight { background-color: yellow; }
            .source-checkbox, .keyword-checkbox { margin-right: 5px; }
        </style>
        <script>
            let debounceTimeout;
            function debounce(func, delay) {
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(func, delay);
            }

            function selectAllCheckboxes(className, isChecked) {
                var checkboxes = document.getElementsByClassName(className);
                for (var i = 0; i < checkboxes.length; i++) {
                    checkboxes[i].checked = isChecked;
                }
                filterEntries();
            }

            function filterEntries() {
                var selectedSources = document.querySelectorAll('.source-checkbox:checked');
                var sources = Array.from(selectedSources).map(cb => cb.value);
                var selectedKeywords = document.querySelectorAll('.keyword-checkbox:checked');
                var keywords = Array.from(selectedKeywords).map(cb => cb.value.toLowerCase());
                if (keywords.includes("ccs/ccus")) {
                    keywords.push("ccs");
                    keywords.push("ccus");
                    keywords = keywords.filter(k => k !== "ccs/ccus");
                }
                var customFilter = document.getElementById("customFilter").value.toLowerCase();
                var entries = document.getElementsByClassName("entry");

                var sectorNewsChecked = document.getElementById("sectorNews").checked;
                if (sectorNewsChecked) {
                    keywords = ''' + str(sector_keywords).replace("'", '"') + '''.map(keyword => keyword.toLowerCase());
                }

                for (var i = 0; i < entries.length; i++) {
                    var entry = entries[i];
                    var title = entry.getElementsByClassName("title")[0].innerText.toLowerCase();
                    var summary = entry.getElementsByClassName("summary")[0].innerText.toLowerCase();
                    var source = entry.getElementsByClassName("meta")[0].innerText.toLowerCase();
                    var matchesSource = sources.length === 0 || sources.some(s => source.includes(s.toLowerCase()));
                    var matchesKeyword = keywords.length === 0 || keywords.some(keyword => title.includes(keyword) || summary.includes(keyword));
                    var matchesCustomFilter = !customFilter || title.includes(customFilter) || summary.includes(customFilter);

                    if (matchesSource && matchesKeyword && matchesCustomFilter) {
                        entry.style.display = "block";
                    } else {
                        entry.style.display = "none";
                    }
                }
            }
        </script>
    </head>
    <body onload="filterEntries()">
        <div class="sidebar">
            <div>
                <label>Select sources:</label><br>
                <label><input type="checkbox" onclick="selectAllCheckboxes('source-checkbox', this.checked)" checked> All</label>
                <label><input type="checkbox" onclick="selectAllCheckboxes('source-checkbox', false)"> None</label><br>
    '''

    for source in sources.keys():
        checked = "checked" if st.session_state['source_checks'][source] else ""
        html += f'<label><input type="checkbox" class="source-checkbox" value="{source}" onchange="filterEntries()" {checked}> {source}</label><br>'

    html += '''
            </div>
        </div>
        <div class="topbar">
            <div>
                <label>Select keywords to filter by:</label>
                <label><input type="checkbox" class="keyword-checkbox" value="aramco" onchange="filterEntries()"> Aramco</label>
                <label><input type="checkbox" class="keyword-checkbox" value="lotos" onchange="filterEntries()"> lotos</label>
                <label><input type="checkbox" class="keyword-checkbox" value="obajtek" onchange="filterEntries()"> Obajtek</label>
                <label><input type="checkbox" class="keyword-checkbox" value="orlen" onchange="filterEntries()"> Orlen</label>
                <label><input type="checkbox" class="keyword-checkbox" value="energetyk" onchange="filterEntries()"> Energetyka</label>
                <label><input type="checkbox" class="keyword-checkbox" value="wodor" onchange="filterEntries()"> Wodór</label>
                <label><input type="checkbox" class="keyword-checkbox" value="wiatr" onchange="filterEntries()"> Wiatr</label>
                <label><input type="checkbox" class="keyword-checkbox" value="pv" onchange="filterEntries()"> PV</label>
                <label><input type="checkbox" class="keyword-checkbox" value="offshore" onchange="filterEntries()"> Offshore</label>
                <label><input type="checkbox" class="keyword-checkbox" value="ccs/ccus" onchange="filterEntries()"> CCS/CCUS</label>
                <label><input type="checkbox" class="keyword-checkbox" value="pfas" onchange="filterEntries()"> PFAS</label>
                <label><input type="checkbox" id="sectorNews" onchange="filterEntries()"> Wiadomości Sektorowe</label>
                <br><label>Or filter by custom text:</label>
                <input type="text" id="customFilter" oninput="debounce(filterEntries, 300)" value="{}">
            </div>
        </div>
        <div class="content">
    '''.format(st.session_state['custom_filter'])

    for entry in entries:
        html += '''
        <div class="entry">
            <div class="title"><a href="{}" target="_blank">{}</a></div>
            <div class="summary">{}</div>
            <div class="meta">{} • {}</div>
        </div>
        '''.format(entry['link'], entry['title'], entry['summary'], entry['source'], entry['published_str'])

    html += '''
        </div>
    </body>
    </html>
    '''

    return html

# Fetch and process feeds
entries = fetch_and_process_feeds()

# Display entries in Streamlit
html_content = display_entries(entries)
components.html(html_content, height=650, scrolling=True)
