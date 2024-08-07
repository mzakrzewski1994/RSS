import streamlit as st
import streamlit.components.v1 as components
import feedparser
from datetime import datetime
import pytz
import re

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

# Define keywords
keywords = ["aramco", "lotos", "obajtek", "orlen", "energetyka", "wodor", "wiatr", "pv", "offshore", "ccs/ccus", "pfas"]

# Set up default state for checkboxes
if 'source_checks' not in st.session_state:
    st.session_state['source_checks'] = {source: True for source in sources.keys()}
if 'keyword_checks' not in st.session_state:
    st.session_state['keyword_checks'] = {keyword: False for keyword in keywords}
    st.session_state['keyword_checks']['None'] = True
if 'custom_filter' not in st.session_state:
    st.session_state['custom_filter'] = ""

def fetch_and_process_feeds():
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
        return local_dt.astimezone(pytz.timezone('Europe/Warsaw'))

    filtered_entries = []
    unique_entries = set()

    for name, rss_url in sources.items():
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

    filtered_entries.sort(key=lambda x: x['published'] or datetime.min.replace(tzinfo=pytz.UTC), reverse=True)
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
                <label><input type="checkbox" class="keyword-checkbox" onclick="selectAllCheckboxes('keyword-checkbox', false)" checked> None</label>
    '''

    for keyword in keywords:
        if keyword != "None":
            checked = "checked" if st.session_state['keyword_checks'][keyword] else ""
            html += f'<label><input type="checkbox" class="keyword-checkbox" value="{keyword}" onchange="filterEntries()" {checked}> {keyword}</label>'

    html += '''
                <br><label>Or filter by custom text:</label>
                <input type="text" id="customFilter" oninput="filterEntries()" value="{}">
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
components.html(html_content, height=700, scrolling=True)
