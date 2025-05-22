import streamlit as st
import urllib.parse
import json
import os

# Konfiguracja strony
st.set_page_config(
    page_title="UTM Builder",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Prosty CSS
st.markdown("""
<style>
    .main { 
        padding-top: 1rem; 
    }
    
    .section-header {
        font-size: 1.1rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #ffffff;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #374151;
    }

    .category-container {
        background-color: #1e2730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #374151;
    }
    
    .result-container {
        background-color: #1e2730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-top: 1.5rem;
        border: 1px solid #374151;
    }
    
    .required {
        color: #ff4b4b;
        font-weight: bold;
    }
    
    .validation-warning {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
        font-size: 0.9rem;
    }
    
    .validation-success {
        background-color: rgba(40, 167, 69, 0.1);
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
        font-size: 0.9rem;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #3d68ff;
        color: white;
        padding: 0.75rem 1rem;
        font-weight: 600;
        border-radius: 0.5rem;
    }
    
    .live-preview {
        background-color: #0f1419;
        border: 1px solid #3d68ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        overflow-wrap: break-word;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Domyślna konfiguracja
DEFAULT_CONFIG = {
    "channels": ["paid", "owned", "earned", "affiliate", "offline"],
    "channel_source_medium_mapping": {
        "paid": {
            "sources": ["google", "facebook", "linkedin", "twitter", "bing", "youtube"],
            "mediums": ["cpc", "cpm", "display", "video"]
        },
        "owned": {
            "sources": ["website", "newsletter", "email", "blog"],
            "mediums": ["email", "referral", "organic"]
        },
        "earned": {
            "sources": ["press", "media", "blog", "review"],
            "mediums": ["organic", "referral", "social"]
        },
        "affiliate": {
            "sources": ["partner", "affiliate"],
            "mediums": ["affiliate", "referral"]
        },
        "offline": {
            "sources": ["print", "tv", "radio", "event"],
            "mediums": ["qr", "direct", "promo"]
        }
    },
    "markets": ["medica", "education", "lifestyle", "finance", "technology"],
    "stages": ["reach", "engage", "consider", "convert", "retain", "upsell", "advocate"],
    "goals": ["sales", "traffic", "leads"],
    "campaign_templates": {
        "Google Ads": {
            "utm_channel": "paid",
            "utm_source": "google",
            "utm_medium": "cpc",
            "description": "Kampania Google Ads - wyszukiwanie płatne"
        },
        "Facebook Ads": {
            "utm_channel": "paid", 
            "utm_source": "facebook",
            "utm_medium": "cpc",
            "description": "Kampania Facebook Ads - reklamy społecznościowe"
        },
        "Email Newsletter": {
            "utm_channel": "owned",
            "utm_source": "newsletter", 
            "utm_medium": "email",
            "description": "Newsletter email - własny kanał komunikacji"
        },
        "YouTube Ads": {
            "utm_channel": "paid",
            "utm_source": "youtube",
            "utm_medium": "video", 
            "description": "Reklamy wideo na YouTube"
        },
        "Press Release": {
            "utm_channel": "earned",
            "utm_source": "press",
            "utm_medium": "organic",
            "description": "Komunikat prasowy - earned media"
        },
        "Retargeting": {
            "utm_channel": "paid",
            "utm_source": "facebook",
            "utm_medium": "display",
            "description": "Remarketing Facebook - wyświetlenia"
        }
    },
    "validation_rules": {
        "warnings": [
            {"channel": "paid", "medium": "organic", "message": "Channel 'paid' z medium 'organic' - czy to na pewno poprawne?"},
            {"channel": "owned", "medium": "cpc", "message": "Channel 'owned' z medium 'cpc' - sprawdź czy to płatna reklama"},
            {"channel": "earned", "medium": "cpc", "message": "Earned media zwykle nie używa medium 'cpc'"}
        ],
        "success": [
            {"channel": "paid", "medium": "cpc", "message": "Świetnie! Klasyczna kombinacja dla paid search"},
            {"channel": "paid", "medium": "display", "message": "Dobra kombinacja dla remarketing/display ads"},
            {"channel": "owned", "medium": "email", "message": "Idealne dla newsletter i email marketing"}
        ]
    },
    "ui_settings": {
        "show_live_preview": True,
        "show_templates": True,
        "show_validation": True,
        "default_base_url": "https://example.com"
    }
}

CONFIG_KEY = "utm_config"

# Inicjalizacja
if CONFIG_KEY not in st.session_state:
    st.session_state[CONFIG_KEY] = DEFAULT_CONFIG.copy()

if "live_preview_url" not in st.session_state:
    st.session_state.live_preview_url = ""

# Funkcje pomocnicze
def load_config():
    config_path = "utm_config.json"
    file_config = None
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
        except Exception as e:
            st.warning(f"Błąd ładowania konfiguracji z pliku: {e}")
    
    if file_config:
        config = file_config
    else:
        config = st.session_state.get(CONFIG_KEY, DEFAULT_CONFIG.copy())
    
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
    
    st.session_state[CONFIG_KEY] = config
    return config

def get_sources_for_channel(channel, config):
    if not channel or "channel_source_medium_mapping" not in config:
        return []
    return config["channel_source_medium_mapping"].get(channel, {}).get("sources", [])

def get_mediums_for_channel(channel, config):
    if not channel or "channel_source_medium_mapping" not in config:
        return []
    return config["channel_source_medium_mapping"].get(channel, {}).get("mediums", [])

def validate_combination(channel, source, medium, config):
    messages = []
    validation_rules = config.get("validation_rules", {})
    
    for rule in validation_rules.get("warnings", []):
        if (rule.get("channel") == channel and rule.get("medium") == medium):
            messages.append(("warning", rule["message"]))
    
    for rule in validation_rules.get("success", []):
        if (rule.get("channel") == channel and rule.get("medium") == medium):
            messages.append(("success", rule["message"]))
    
    return messages

def apply_template(template_name, config):
    campaign_templates = config.get("campaign_templates", {})
    if template_name and template_name in campaign_templates:
        template = campaign_templates[template_name]
        for key, value in template.items():
            if key != "description":
                st.session_state[key] = value

def generate_utm_link(base_url, params):
    filtered_params = {k: v for k, v in params.items() if v}
    
    if "utm_id" in filtered_params:
        filtered_params["a"] = filtered_params["utm_id"]
    
    encoded_params = []
    for key, value in filtered_params.items():
        encoded_value = urllib.parse.quote(value, safe='')
        encoded_params.append(f"{key}={encoded_value}")
    
    params_string = "&".join(encoded_params)
    
    if "?" in base_url:
        final_url = base_url + "&" + params_string
    else:
        final_url = base_url + "?" + params_string
    
    return final_url

def update_live_preview(base_url, params):
    if base_url:
        preview_url = generate_utm_link(base_url, params)
        st.session_state.live_preview_url = preview_url

# Nagłówek aplikacji
st.title("UTM Builder")
st.markdown("Narzędzie do generowania linków z parametrami UTM")
st.markdown("Pola oznaczone * są wymagane")

# Ładowanie konfiguracji
config = load_config()

# Szablony kampanii - prosty selectbox
ui_settings = config.get("ui_settings", {})
if ui_settings.get("show_templates", True):
    st.markdown('<div class="section-header">Szablony kampanii</div>', unsafe_allow_html=True)
    
    campaign_templates = config.get("campaign_templates", {})
    template_options = [""] + list(campaign_templates.keys())
    
    selected_template = st.selectbox(
        "Wybierz szablon kampanii (opcjonalnie)",
        options=template_options,
        help="Wybierz gotowy szablon, aby automatycznie wypełnić podstawowe pola"
    )
    
    if selected_template:
        apply_template(selected_template, config)
        template_desc = campaign_templates.get(selected_template, {}).get("description", "")
        if template_desc:
            st.info(f"Zastosowano szablon: {template_desc}")

# Live Preview
if ui_settings.get("show_live_preview", True) and st.session_state.live_preview_url:
    st.markdown('<div class="section-header">Podgląd linku</div>', unsafe_allow_html=True)
    
    parts = st.session_state.live_preview_url.split("?")
    base_part = parts[0]
    
    if len(parts) > 1:
        params_text = ""
        params = parts[1].split("&")
        for i, param in enumerate(params):
            if "=" in param:
                param_name, param_value = param.split("=", 1)
                params_text += f'<span style="color: #ff9d4f;">{param_name}</span>=<span style="color: #4ade80;">{param_value}</span>'
            else:
                params_text += f'<span style="color: #ff9d4f;">{param}</span>'
            
            if i < len(params) - 1:
                params_text += '<span style="color: #ffffff;">&amp;</span>'
    else:
        params_text = ""
    
    query_part = f'<span style="color: #ffffff;">?</span>{params_text}' if params_text else ""
    
    st.markdown(f"""
    <div class="live-preview">
        <span style="color: #3d68ff; font-weight: bold;">{base_part}</span>{query_part}
    </div>
    """, unsafe_allow_html=True)

# Główny formularz
with st.form("utm_form"):
    # TRACKING (wymagane)
    st.markdown('<div class="section-header">Podstawowe parametry (wymagane)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('**URL bazowy** *', unsafe_allow_html=True)
        base_url = st.text_input(
            "",
            value=st.session_state.get("base_url", ui_settings.get("default_base_url", "https://example.com")),
            help="Wprowadź adres strony docelowej",
            key="base_url",
            placeholder="https://example.com/strona-docelowa",
            label_visibility="collapsed"
        )
        
        st.markdown('**utm_market (rynek)** *', unsafe_allow_html=True)
        utm_market = st.selectbox(
            "",
            options=[""] + config.get("markets", []),
            help="Wybierz rynek docelowy",
            key="utm_market",
            label_visibility="collapsed"
        )
        
        st.markdown('**utm_channel (najwyższy poziom)** *', unsafe_allow_html=True)
        utm_channel = st.selectbox(
            "",
            options=[""] + config.get("channels", []),
            help="Wybierz najwyższy poziom źródła ruchu",
            key="utm_channel",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('**utm_source (platforma/dostawca)** *', unsafe_allow_html=True)
        
        source_suggestions = get_sources_for_channel(utm_channel, config)
        
        utm_source = st.selectbox(
            "",
            options=[""] + source_suggestions,
            key="utm_source",
            label_visibility="collapsed"
        )
        
        st.markdown('**utm_medium (taktyka/typ ruchu)** *', unsafe_allow_html=True)
        
        medium_suggestions = get_mediums_for_channel(utm_channel, config)
        
        utm_medium = st.selectbox(
            "",
            options=[""] + medium_suggestions,
            key="utm_medium",
            label_visibility="collapsed"
        )
        
        st.markdown('**utm_id (numer akcji)** *', unsafe_allow_html=True)
        utm_id = st.text_input(
            "",
            value=st.session_state.get("utm_id", ""),
            help="Wprowadź numer akcji",
            key="utm_id",
            placeholder="np. 43234/1",
            label_visibility="collapsed"
        )
    
    # Walidacja
    if ui_settings.get("show_validation", True) and utm_channel and utm_source and utm_medium:
        validation_messages = validate_combination(utm_channel, utm_source, utm_medium, config)
        for msg_type, message in validation_messages:
            if msg_type == "warning":
                st.markdown(f'<div class="validation-warning">⚠️ {message}</div>', unsafe_allow_html=True)
            elif msg_type == "success":
                st.markdown(f'<div class="validation-success">✅ {message}</div>', unsafe_allow_html=True)
    
    # KAMPANIA (opcjonalne)
    st.markdown('<div class="section-header">Kampania (opcjonalne)</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        utm_campaign = st.text_input(
            "utm_campaign (nazwa kampanii/inicjatywy)",
            value=st.session_state.get("utm_campaign", ""),
            placeholder="np. cel_marketingowy-linia_produktowa-segment-rodzaj"
        )
        
        utm_goal = st.selectbox(
            "utm_goal (cel kampanii)",
            options=[""] + config.get("goals", [])
        )
    
    with col4:
        utm_stage = st.selectbox(
            "utm_stage (etap lejka)",
            options=[""] + config.get("stages", [])
        )
        
        utm_cohort = st.text_input(
            "utm_cohort (kohorta/persona)",
            placeholder="np. new_customers, loyal_clients"
        )
    
    # KREACJA (opcjonalne)
    st.markdown('<div class="section-header">Kreacja (opcjonalne)</div>', unsafe_allow_html=True)
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        utm_content = st.text_input(
            "utm_content (wersja kreacji)",
            placeholder="np. email_short, banner_900x344_blue"
        )
    
    with col6:
        utm_creative_id = st.text_input(
            "utm_creative_id (id z adserwera)",
            placeholder="np. 123456"
        )
    
    with col7:
        utm_term = st.text_input(
            "utm_term (argument, słowo kluczowe)",
            placeholder="np. marketing, analytics"
        )
    
    # Update live preview
    utm_params_preview = {
        "utm_market": utm_market,
        "utm_channel": utm_channel,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_id": utm_id,
        "utm_campaign": utm_campaign,
        "utm_goal": utm_goal,
        "utm_stage": utm_stage,
        "utm_cohort": utm_cohort,
        "utm_content": utm_content,
        "utm_creative_id": utm_creative_id,
        "utm_term": utm_term
    }
    
    if base_url:
        update_live_preview(base_url, utm_params_preview)
    
    # Przycisk generowania
    submit = st.form_submit_button("Generuj link UTM")

# Przetwarzanie
if submit:
    required_fields = {
        "URL bazowy": base_url,
        "utm_market": utm_market,
        "utm_channel": utm_channel,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_id": utm_id
    }
    
    missing_fields = [name for name, value in required_fields.items() if not value]
    
    if missing_fields:
        st.error(f"Proszę wypełnić następujące wymagane pola: {', '.join(missing_fields)}")
    else:
        final_url = generate_utm_link(base_url, utm_params_preview)
        
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Wygenerowany link UTM</div>', unsafe_allow_html=True)
        
        # Kolorowany URL
        parts = final_url.split("?")
        base_part = parts[0]
        
        if len(parts) > 1:
            params_text = ""
            params = parts[1].split("&")
            for i, param in enumerate(params):
                if "=" in param:
                    param_name, param_value = param.split("=", 1)
                    params_text += f'<span style="color: #ff9d4f;">{param_name}</span>=<span style="color: #4ade80;">{param_value}</span>'
                else:
                    params_text += f'<span style="color: #ff9d4f;">{param}</span>'
                
                if i < len(params) - 1:
                    params_text += '<span style="color: #ffffff;">&amp;</span>'
        else:
            params_text = ""
        
        query_part = f'<span style="color: #ffffff;">?</span>{params_text}' if params_text else ""
        
        st.markdown(f"""
        <div style="background-color: #2a3746; padding: 16px; border-radius: 4px; margin-bottom: 10px; font-family: monospace; overflow-wrap: break-word; line-height: 1.5;">
            <span style="color: #3d68ff; font-weight: bold;">{base_part}</span>{query_part}
        </div>
        <p style="font-size: 0.8em; color: #9ca3af; margin-top: 5px;">Kliknij ikonę po prawej stronie poniżej, aby skopiować cały link</p>
        """, unsafe_allow_html=True)
        
        st.code(final_url, language=None)
        st.markdown('</div>', unsafe_allow_html=True)

# Informacje
with st.expander("Informacje o parametrach UTM"):
    st.markdown("""
    ### Parametry UTM
    
    #### Źródło ruchu
    - **utm_market** - rynek: medica, education, lifestyle
    - **utm_channel** - najwyższy poziom źródła: paid, owned, earned, affiliate, offline
    - **utm_source** - platforma/dostawca: google, facebook, salesmanago
    - **utm_medium** - taktyka/typ ruchu: cpc, cpm, organic
    
    #### Kampania
    - **utm_id** - numer akcji
    - **utm_campaign** - nazwa kampanii/inicjatywy
    - **utm_goal** - cel kampanii: sales, traffic, leads
    - **utm_stage** - etap lejka: reach, engage, consider, convert, retain, upsell, advocate
    - **utm_cohort** - kohorta/persona
    
    #### Kreacja
    - **utm_content** - wersja kreacji
    - **utm_creative_id** - id z adserwera
    - **utm_term** - argument, słowo kluczowe
    """)