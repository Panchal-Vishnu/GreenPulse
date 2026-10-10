import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import requests
import streamlit as st

# Load .env when python-dotenv is installed. A small fallback parser keeps the app
# usable even if that optional package is absent.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

st.set_page_config(
    page_title="GreenPulse | Smarter Searches. Greener Choices.",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_serpapi_key():
    """Read the key from Streamlit secrets first, then the local environment/.env."""
    key = ""
    try:
        key = str(st.secrets.get("SERPAPI_KEY", "") or "").strip()
    except Exception:
        # Streamlit raises when a secrets file does not exist; environment fallback is OK.
        key = ""
    return key or os.getenv("SERPAPI_KEY", "").strip()


SERPAPI_KEY = get_serpapi_key()
SERPAPI_URL = "https://serpapi.com/search.json"

CATEGORIES = {
    "♻️  Recycling Centres": {
        "key": "recycling",
        "query": "recycling centre e-waste recycling drop off",
        "description": "Find recycling centres and e-waste drop-off points.",
        "icon": "♻️",
    },
    "🌿  Eco-Friendly Stores": {
        "key": "stores",
        "query": "eco friendly zero waste sustainable products store",
        "description": "Shop sustainable and environmentally safer products.",
        "icon": "🌿",
    },
    "🚗  Electric Vehicles": {
        "key": "ev",
        "query": "electric vehicle charging station",
        "description": "Locate EV charging stations and related services.",
        "icon": "🚗",
    },
    "🌳  Tree Plantation": {
        "key": "trees",
        "query": "tree plantation drive volunteer tree planting NGO",
        "description": "Find tree-planting drives and volunteer opportunities.",
        "icon": "🌳",
    },
    "🛍️  Sustainable Products": {
        "key": "products",
        "query": "sustainable products refill station reusable products",
        "description": "Discover reusable products, refill stations and green brands.",
        "icon": "🛍️",
    },
    "🥗  Green Food & Cafes": {
        "key": "food",
        "query": "organic food store vegan vegetarian sustainable cafe",
        "description": "Explore organic food, vegetarian options and sustainability-minded cafes.",
        "icon": "🥗",
    },
}

QUICK_SEARCHES = [
    ("♻️", "Nearby Recycling Centres", "recycling centre e-waste recycling drop off"),
    ("🌿", "Eco-Friendly Stores", "eco friendly zero waste sustainable products store"),
    ("🚗", "Electric Vehicles", "electric vehicle charging station"),
    ("🌳", "Tree Plantation", "tree plantation drive volunteer tree planting NGO"),
    ("🛍️", "Sustainable Products", "sustainable products refill station reusable products"),
]

def init_state():
    defaults = {
        "results": [],
        "organic_results": [],
        "last_query": "",
        "last_location": "",
        "last_category": "",
        "last_updated": "",
        "error": "",
        "search_history": [],
        "impact_actions": {"recycling": 0, "reuse": 0, "planting": 0},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp {
  background: radial-gradient(ellipse at 80% 0%, rgba(0, 130, 115, .14), transparent 36%),
              linear-gradient(145deg, #03111d 0%, #041b2a 54%, #03151f 100%);
  color: #e9f4ff;
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(3, 17, 29, .86); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #031521, #041b27);
  border-right: 1px solid #104052;
}
[data-testid="stSidebar"] * { color: #d8e9f5; }
h1,h2,h3 { font-family: 'Manrope', sans-serif !important; color: #f2fff9 !important; }
p, label, li { color: #c4d8e8; }
div[data-testid="stMetric"] {
  background: rgba(6, 37, 51, .88); border: 1px solid #155164;
  border-radius: 15px; padding: 14px 16px;
}
div[data-testid="stMetricLabel"] { color: #a8c4d4; }
div[data-testid="stMetricValue"] { color: #f4fff9; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
  background: #f5f9ff !important; color: #11283b !important; border-radius: 12px !important;
}
.stTextInput input::placeholder { color: #687d8e !important; }
div.stButton > button {
  border-radius: 10px; border: 1px solid #175366; background: #09283a; color: #e8fff8;
  font-weight: 600; transition: all .18s ease;
}
div.stButton > button:hover { border-color: #23dba1; color: #36f0ad; }
div.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #00bd9a, #35e58f); color: #05201d; border: 0; font-weight: 800;
}
.gp-hero {
  min-height: 290px; padding: 42px 28px 26px; border-radius: 0 0 22px 22px;
  background: linear-gradient(110deg, rgba(3, 21, 34, .94), rgba(4, 43, 49, .78)),
              radial-gradient(circle at 78% 20%, rgba(41, 224, 148, .23), transparent 34%),
              linear-gradient(135deg, #0b3446, #06212d 52%, #0b483a);
  border: 1px solid #114457; text-align: center; margin-bottom: 22px;
}
.gp-brand { font-family: 'Manrope', sans-serif; font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 800; letter-spacing: -1.5px; color: #f4fff9; }
.gp-brand span { color: #29e79a; }
.gp-tagline { font-size: 1.05rem; color: #d7e9f4; max-width: 720px; margin: 8px auto 0; }
.gp-card {
  background: linear-gradient(155deg, rgba(5, 31, 47, .96), rgba(3, 23, 36, .96));
  border: 1px solid #12485d; border-radius: 15px; padding: 17px; min-height: 170px;
  box-shadow: 0 10px 24px rgba(0,0,0,.12);
}
.gp-card h4 { color: #f0fff8; margin: 8px 0 6px; font-size: 1.03rem; }
.gp-card p { color: #aec7d9; font-size: .9rem; min-height: 43px; }
.gp-icon { font-size: 1.6rem; width: 47px; height: 47px; display:flex; align-items:center; justify-content:center;
  border-radius: 50%; background: rgba(17, 199, 137, .15); border: 1px solid #138a70; }
.gp-panel { background: rgba(4, 27, 42, .9); border: 1px solid #12465a; border-radius: 16px; padding: 18px; }
.gp-muted { color: #8eacbf; font-size: .83rem; }
.gp-result { padding: 13px 0; border-bottom: 1px solid #133e50; }
.gp-result:last-child { border-bottom: 0; }
a { color: #39e8a3 !important; }
hr { border-color: #164052 !important; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

def search_serpapi(engine, params):
    """Call SerpApi with one retry for temporary network timeouts."""
    api_key = get_serpapi_key()
    if not api_key or api_key == "your_serpapi_key_here":
        raise RuntimeError(
            "SerpApi key is missing. Add SERPAPI_KEY to your local .env file "
            "or Streamlit secrets.toml, then restart the app."
        )

    request_params = {"engine": engine, "api_key": api_key, **params}
    last_network_error = None

    # SerpApi can occasionally respond slowly. Retry once rather than failing
    # immediately; the API key is never included in displayed error messages.
    for attempt in range(2):
        try:
            response = requests.get(
                SERPAPI_URL,
                params=request_params,
                timeout=(10, 60),  # connect timeout, response-read timeout
            )
            break
        except requests.Timeout as exc:
            last_network_error = exc
            if attempt == 0:
                time.sleep(1.5)
                continue
            raise RuntimeError(
                f"Network timeout while contacting SerpApi for {engine}. "
                "The server did not respond after retrying. Check your internet "
                "connection and try again in a minute."
            ) from last_network_error
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error while contacting SerpApi for {engine}: {exc.__class__.__name__}. "
                "Check your internet connection and try again."
            ) from exc

    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.status_code >= 400:
        detail = data.get("error") if isinstance(data, dict) else None
        if not detail:
            detail = response.text[:500] or "No error details returned."
        raise RuntimeError(f"SerpApi HTTP {response.status_code}: {detail}")

    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"SerpApi error: {data['error']}")
    if not isinstance(data, dict):
        raise RuntimeError("SerpApi returned an unexpected response format.")
    return data


def do_search(location, category_label, extra_query=""):
    """Search Maps and Web using an explicit city/state context."""
    category = CATEGORIES[category_label]
    clean_location = ", ".join(part.strip() for part in location.split(",") if part.strip())
    # India is the project's primary region. Adding the country helps disambiguate
    # smaller towns with similar names; don't append it twice if the user typed it.
    if "india" not in clean_location.lower():
        clean_location = f"{clean_location}, India"

    search_terms = extra_query.strip() if extra_query and extra_query.strip() else category["query"]
    query = f"{search_terms} in {clean_location}"

    local_results = []
    organic = []
    errors = []

    # For Google Maps, put the city/state in q (not in the Maps `location`
    # parameter, which expects a map-search origin with z/m settings).
    try:
        maps_data = search_serpapi(
            "google_maps", {"q": query, "type": "search", "hl": "en"}
        )
        local_results = maps_data.get("local_results", []) or []
        if not local_results and maps_data.get("place_results"):
            local_results = [maps_data["place_results"]]
    except Exception as exc:
        errors.append(f"Google Maps search failed: {exc}")

    # Google Search supports a city-level `location` parameter, so use both that
    # and gl=in to better align web results with the requested Indian location.
    try:
        web_data = search_serpapi(
            "google",
            {"q": query, "location": clean_location, "gl": "in", "hl": "en", "num": "8"},
        )
        organic = web_data.get("organic_results", []) or []
    except Exception as exc:
        errors.append(f"Google Search failed: {exc}")

    st.session_state.results = local_results[:8]
    st.session_state.organic_results = organic[:6]
    st.session_state.last_query = query
    st.session_state.last_location = location
    st.session_state.last_category = category_label
    st.session_state.last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.session_state.error = "\n\n".join(errors)

    item = {
        "query": query,
        "location": location,
        "category": category_label,
        "time": st.session_state.last_updated,
    }
    st.session_state.search_history = [item] + [
        x for x in st.session_state.search_history
        if not (x["query"] == query and x["location"] == location)
    ]
    st.session_state.search_history = st.session_state.search_history[:5]

def show_result(item, kind="place"):
    title = item.get("title") or item.get("name") or "Local result"
    link = item.get("link") or item.get("website") or item.get("url")
    address = item.get("address") or item.get("formatted_address")
    snippet = item.get("snippet") or item.get("description") or item.get("type") or ""
    rating = item.get("rating")
    reviews = item.get("reviews")
    st.markdown('<div class="gp-result">', unsafe_allow_html=True)
    if link:
        st.markdown(f"**[{title}]({link})**")
    else:
        st.markdown(f"**{title}**")
    details = []
    if address:
        details.append("📍 " + str(address))
    if rating is not None:
        details.append(f"⭐ {rating}" + (f" · {reviews} reviews" if reviews else ""))
    if details:
        st.caption("  |  ".join(details))
    if snippet:
        st.write(snippet)
    if not link:
        st.caption("No direct website link was provided in this result. Confirm details before visiting.")
    st.markdown('</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🌱 GreenPulse")
    st.caption("Smarter Searches. Greener Choices.")
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("Go to", ["🏠 Home", "📍 Nearby Options", "📊 Impact Tracker", "ℹ️ About"], label_visibility="collapsed")
    st.markdown("---")
    location = st.text_input("📍 Search location", value=st.session_state.last_location or "", placeholder="City, town or PIN code")
    category_label = st.selectbox("What are you looking for?", list(CATEGORIES.keys()))
    st.markdown("---")
    st.markdown('<div class="gp-panel"><div style="font-size:1.2rem">🌍</div><b>Small actions.<br>Big impact.</b><p class="gp-muted">Discover local ways to make greener choices.</p></div>', unsafe_allow_html=True)
    st.caption("Powered by SerpApi · India Hackathon 2026")

# Hero
st.markdown("""
<div class="gp-hero">
  <div class="gp-brand">🌱 Green<span>Pulse</span></div>
  <div class="gp-tagline">Find eco-friendly options, support sustainable choices<br>and reduce your environmental impact.</div>
</div>
""", unsafe_allow_html=True)

if page in ["🏠 Home", "📍 Nearby Options"]:
    col_search, col_button = st.columns([5, 1.15], vertical_alignment="bottom")
    with col_search:
        query_override = st.text_input(
            "Search",
            placeholder="Search for eco-friendly options (e.g. electric vehicle, organic store, recycling centre...)",
            label_visibility="collapsed",
            key="main_search",
        )
    with col_button:
        search_clicked = st.button("Search  →", type="primary", use_container_width=True)

    qcols = st.columns(5)
    for i, (icon, label, query) in enumerate(QUICK_SEARCHES):
        with qcols[i]:
            if st.button(f"{icon} {label}", key=f"quick_{i}", use_container_width=True):
                if location.strip():
                    try:
                        do_search(location.strip(), category_label, query)
                        st.rerun()
                    except Exception as exc:
                        st.session_state.error = str(exc)
                else:
                    st.session_state.error = "Enter your town, city or PIN code in the sidebar first."

    if search_clicked:
        if not location.strip():
            st.session_state.error = "Enter your town, city or PIN code in the sidebar first."
        else:
            with st.spinner("Searching public information with SerpApi…"):
                try:
                    do_search(location.strip(), category_label, query_override)
                except requests.HTTPError as exc:
                    st.session_state.error = f"SerpApi request failed ({exc}). Check your API key, quota and request limits."
                except requests.RequestException as exc:
                    st.session_state.error = f"Network error: {exc}"
                except Exception as exc:
                    st.session_state.error = str(exc)

    if st.session_state.error:
        st.error(st.session_state.error)

    if not get_serpapi_key():
        st.warning("Live search is not connected yet. Add SERPAPI_KEY to a local `.env` file or Streamlit secrets, then restart the app.")
    if st.session_state.last_query:
        st.markdown("### 🔎 Search results")
        st.caption(f"Search: {st.session_state.last_query} · Updated {st.session_state.last_updated}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Local options", len(st.session_state.results))
        m2.metric("Web sources", len(st.session_state.organic_results))
        m3.metric("Search area", st.session_state.last_location)
        left, right = st.columns([1.35, 1])
        with left:
            st.markdown('<div class="gp-panel"><h3>📍 Nearby options</h3>', unsafe_allow_html=True)
            if st.session_state.results:
                for result in st.session_state.results:
                    show_result(result)
            else:
                st.info("No map results came back for this query. Try a broader category or nearby larger town.")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown('<div class="gp-panel"><h3>🌐 Supporting web pages</h3>', unsafe_allow_html=True)
            if st.session_state.organic_results:
                for result in st.session_state.organic_results:
                    show_result(result, "web")
            else:
                st.info("No additional web pages were returned.")
            st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Search results may be incomplete or outdated. Contact each provider to confirm services, accepted items, fees and opening hours.")
    else:
        st.markdown("### 🌿 Explore Eco-Friendly Options")
        st.write("Discover nearby places, products and services that can help you live sustainably and reduce your footprint.")
        card_rows = [list(CATEGORIES.items())[:3], list(CATEGORIES.items())[3:]]
        for row in card_rows:
            cols = st.columns(3)
            for col, (label, info) in zip(cols, row):
                with col:
                    st.markdown(f"""
                    <div class="gp-card">
                      <div class="gp-icon">{info['icon']}</div>
                      <h4>{label.split('  ',1)[-1]}</h4>
                      <p>{info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Explore →", key=f"explore_{info['key']}", use_container_width=True):
                        if location.strip():
                            try:
                                do_search(location.strip(), label)
                                st.rerun()
                            except Exception as exc:
                                st.session_state.error = str(exc)
                                st.rerun()
                        else:
                            st.session_state.error = "Enter your town, city or PIN code in the sidebar first."
                            st.rerun()

        lower_left, lower_right = st.columns([1.3, 1])
        with lower_left:
            st.markdown('<div class="gp-panel"><h3>🌎 Together for a Greener Future</h3><p>Every thoughtful choice can help reduce waste and support a cleaner community. Use GreenPulse to discover options, then verify details directly with local providers.</p></div>', unsafe_allow_html=True)
        with lower_right:
            st.markdown('<div class="gp-panel"><h3>🕘 Recent searches</h3>', unsafe_allow_html=True)
            if st.session_state.search_history:
                for item in st.session_state.search_history:
                    st.markdown(f"**{item['category']}**")
                    st.caption(f"{item['location']} · {item['time']}")
            else:
                st.caption("Your recent searches will appear here after your first search.")
            st.markdown("</div>", unsafe_allow_html=True)

elif page == "📊 Impact Tracker":
    st.markdown("### 📊 Your Environmental Impact")
    st.write("Track actions you report completing. The counters below are personal activity counts—not measured CO₂ savings.")
    actions = st.session_state.impact_actions
    c1, c2, c3 = st.columns(3)
    c1.metric("♻️ Recycling actions", actions["recycling"])
    c2.metric("🔁 Reuse actions", actions["reuse"])
    c3.metric("🌳 Planting actions", actions["planting"])
    st.markdown("#### Log an action")
    action_label = st.selectbox("What did you do?", ["Recycled an item", "Reused or donated an item", "Joined a tree-planting activity"])
    if st.button("＋ Log action", type="primary"):
        key = {"Recycled an item": "recycling", "Reused or donated an item": "reuse", "Joined a tree-planting activity": "planting"}[action_label]
        st.session_state.impact_actions[key] += 1
        st.success("Action logged in this session.")
        st.rerun()
    st.caption("This prototype stores counters in the current app session only. No CO₂ or tree-equivalent claims are made without a transparent calculation method.")

elif page == "ℹ️ About":
    st.markdown("### About GreenPulse")
    st.write("GreenPulse helps people discover public information about recycling, reuse, sustainable shopping, EV charging, tree-planting activities and greener food options.")
    st.markdown("#### How it works")
    st.markdown("1. Enter a location and choose a category.\n2. GreenPulse sends relevant searches to SerpApi's Google Maps and Google Search engines.\n3. Review returned place listings and source links.\n4. Confirm details directly with each provider before making a trip or decision.")
    st.markdown("#### Transparency")
    st.write("GreenPulse is an independent hackathon prototype, not an official waste-management directory. Search results can be incomplete, outdated, or not a perfect match for a specific item. Environmental impact counters record user-reported actions and do not estimate emissions avoided.")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#7e9fb3;font-size:.82rem">🌱 GreenPulse &nbsp; | &nbsp; Powered by SerpApi &nbsp; | &nbsp; India Hackathon 2026</div>', unsafe_allow_html=True)
