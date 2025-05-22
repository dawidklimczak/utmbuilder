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

# Zaawansowany CSS
st.markdown("""
<style>    
    /* Ogólne style */
    .main { padding-top: 1rem; }
    
    /* Nagłówki sekcji z ikonami */
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #ffffff;
        padding: 0.8rem;
        background: linear-gradient(90deg, #1e2730 0%, #2a3746 100%);
        border-radius: 0.5rem;
        border-left: 4px solid #3d68ff;
    }

    /* Pojemniki dla kategorii */
    .category-container {
        background-color: #1e2730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #374151;
    }
    
    /* Live preview */
    .live-preview {
        background-color: #0f1419;
        border: 2px solid #3d68ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        overflow-wrap: break-word;
        line-height: 1.6;
    }
    
    /* Pole wynikowe */
    .result-container {
        background-color: #1e2730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-top: 1.5rem;
        border: 1px solid #374151;
    }
    
    /* Oznaczenie wymaganych pól */
    .required {
        color: #ff4b4b;
        font-weight: bold;
    }
    
    /* Ostrzeżenia walidacji */
    .validation-warning {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    
    .validation-success {
        background-color: rgba(40, 167, 69, 0.1);
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    
    .validation-info {
        background-color: rgba(61, 104, 255, 0.1);
        border-left: 4px solid #3d68ff;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    
    /* Szablony kampanii */
    .template-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
        border-radius: 1rem;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        transition: transform 0.2s;
    }
    
    .template-button:hover {
        transform: translateY(-2px);
    }
    
    /* Lepsze przyciski */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3d68ff 0%, #5a7cff 100%);
        color: white;
        padding: 0.75rem 1rem;
        font-weight: 600;
        border-radius: 0.5rem;
    }
    
    /* Required info */
    .required-explanation {
        margin-bottom: 1.5rem;
        color: #9ca3af;
        font-size: 0.9rem;
        background-color: #1e2730;
        padding: 0.8rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# Domyślna konfiguracja parametrów UTM (backup gdy brak pliku JSON)
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
        "🔍 Google Ads": {
            "utm_channel": "paid",
            "utm_source": "google",
            "utm_medium": "cpc",
            "description": "Kampania Google Ads - wyszukiwanie płatne"
        },
        "📱 Facebook Ads": {
            "utm_channel": "paid", 
            "utm_source": "facebook",
            "utm_medium": "cpc",
            "description": "Kampania Facebook Ads - reklamy społecznościowe"
        },
        "📧 Email Newsletter": {
            "utm_channel": "owned",
            "utm_source": "newsletter", 
            "utm_medium": "email",
            "description": "Newsletter email - własny kanał komunikacji"
        }
    },
    "validation_rules": {
        "warnings": [
            {"channel": "paid", "medium": "organic", "message": "⚠️ Channel 'paid' z medium 'organic' - czy to na pewno poprawne?"}
        ],
        "success": [
            {"channel": "paid", "medium": "cpc", "message": "✅ Świetnie! Klasyczna kombinacja dla paid search"}
        ],
        "suggestions": [
            {"source": "facebook", "message": "💡 Dla Facebook dodaj utm_content z formatem kreacji"}
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
    
    # Sprawdź ostrzeżenia
    for rule in validation_rules.get("warnings", []):
        if (rule.get("channel") == channel and rule.get("medium") == medium):
            messages.append(("warning", rule["message"]))
    
    # Sprawdź sukces
    for rule in validation_rules.get("success", []):
        if (rule.get("channel") == channel and rule.get("medium") == medium):
            messages.append(("success", rule["message"]))
    
    # Sprawdź sugestie
    for rule in validation_rules.get("suggestions", []):
        if rule.get("source") == source:
            messages.append(("info", rule["message"]))
    
    return messages

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

def apply_template(template_name, config):
    campaign_templates = config.get("campaign_templates", {})
    if template_name in campaign_templates:
        template = campaign_templates[template_name]
        for key, value in template.items():
            if key != "description":
                st.session_state[key] = value
        # Dodajemy flagę, że szablon został zastosowany
        st.session_state["template_applied"] = template_name

# Nagłówek aplikacji
st.title("🚀 UTM Builder Pro")
st.markdown("**Profesjonalne narzędzie do generowania linków UTM z inteligentną walidacją**")

st.markdown('<div class="required-explanation">📋 Pola oznaczone <span class="required">*</span> są wymagane</div>', unsafe_allow_html=True)

# Ładowanie konfiguracji
config = load_config()

# Quick Templates - tylko jeśli włączone w konfiguracji
ui_settings = config.get("ui_settings", {})
if ui_settings.get("show_templates", True):
    st.markdown('<div class="section-header">⚡ Szybkie szablony kampanii</div>', unsafe_allow_html=True)

    campaign_templates = config.get("campaign_templates", {})
    template_cols = st.columns(3)
    template_names = list(campaign_templates.keys())

    for i, template_name in enumerate(template_names):
        col_idx = i % 3
        with template_cols[col_idx]:
            if st.button(template_name, key=f"template_{i}", help=campaign_templates[template_name].get("description", "")):
                apply_template(template_name, config)
                st.success(f"Zastosowano szablon: {template_name}")

# Sprawdź czy szablon został zastosowany i wyczyść flagę
if "template_applied" in st.session_state:
    st.info(f"✅ Aktywny szablon: {st.session_state['template_applied']}")
    # Opcjonalnie wyczyść po pewnym czasie
    if st.button("Wyczyść szablon", key="clear_template"):
        # Wyczyść tylko pola związane z szablonem
        fields_to_clear = ["utm_channel", "utm_source", "utm_medium", "template_applied"]
        for field in fields_to_clear:
            if field in st.session_state:
                del st.session_state[field]

# Live Preview - tylko jeśli włączone w konfiguracji
if ui_settings.get("show_live_preview", True) and st.session_state.live_preview_url:
    st.markdown('<div class="section-header">👁️ Podgląd na żywo</div>', unsafe_allow_html=True)
    
    # Kolorowanie linku
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
    # 📊 TRACKING (wymagane)
    st.markdown('<div class="section-header">📊 TRACKING (wymagane)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<span class="required">*</span> **URL bazowy strony:**', unsafe_allow_html=True)
        base_url = st.text_input(
            "",
            st.session_state.get("base_url", ui_settings.get("default_base_url", "https://example.com")),
            help="Wprowadź adres strony docelowej",
            key="base_url",
            placeholder="https://example.com/strona-docelowa",
            label_visibility="collapsed"
        )
        
        st.markdown('<span class="required">*</span> **utm_market (rynek):**', unsafe_allow_html=True)
        utm_market = st.selectbox(
            "",
            options=[""] + config.get("markets", []),
            index=0 if not st.session_state.get("utm_market") else config.get("markets", []).index(st.session_state.get("utm_market")) + 1 if st.session_state.get("utm_market") in config.get("markets", []) else 0,
            help="Wybierz rynek docelowy",
            key="utm_market",
            label_visibility="collapsed"
        )
        
        st.markdown('<span class="required">*</span> **utm_channel (najwyższy poziom):**', unsafe_allow_html=True)
        utm_channel = st.selectbox(
            "",
            options=[""] + config.get("channels", []),
            index=0 if not st.session_state.get("utm_channel") else config.get("channels", []).index(st.session_state.get("utm_channel")) + 1 if st.session_state.get("utm_channel") in config.get("channels", []) else 0,
            help="Wybierz najwyższy poziom źródła ruchu",
            key="utm_channel",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<span class="required">*</span> **utm_source (platforma/dostawca):**', unsafe_allow_html=True)
        
        # Source suggestions based on channel
        source_suggestions = get_sources_for_channel(utm_channel, config)
        source_options = source_suggestions + ["🖊️ Własna wartość..."]
        
        utm_source_choice = st.selectbox(
            "",
            options=[""] + source_options,
            key="utm_source_choice",
            label_visibility="collapsed"
        )
        
        if utm_source_choice == "🖊️ Własna wartość...":
            utm_source = st.text_input("Wprowadź własną wartość:", key="utm_source_custom", placeholder="np. custom_source")
        else:
            utm_source = utm_source_choice if utm_source_choice else ""
        
        st.markdown('<span class="required">*</span> **utm_medium (taktyka/typ ruchu):**', unsafe_allow_html=True)
        
        # Medium suggestions based on channel
        medium_suggestions = get_mediums_for_channel(utm_channel, config)
        medium_options = medium_suggestions + ["🖊️ Własna wartość..."]
        
        utm_medium_choice = st.selectbox(
            "",
            options=[""] + medium_options,
            key="utm_medium_choice",
            label_visibility="collapsed"
        )
        
        if utm_medium_choice == "🖊️ Własna wartość...":
            utm_medium = st.text_input("Wprowadź własną wartość:", key="utm_medium_custom", placeholder="np. custom_medium")
        else:
            utm_medium = utm_medium_choice if utm_medium_choice else ""
        
        st.markdown('<span class="required">*</span> **utm_id (numer akcji):**', unsafe_allow_html=True)
        utm_id = st.text_input(
            "",
            st.session_state.get("utm_id", ""),
            help="Wprowadź numer akcji",
            key="utm_id",
            placeholder="np. 43234/1",
            label_visibility="collapsed"
        )
    
    # Walidacja na żywo - tylko jeśli włączona w konfiguracji
    if ui_settings.get("show_validation", True) and utm_channel and utm_source and utm_medium:
        validation_messages = validate_combination(utm_channel, utm_source, utm_medium, config)
        for msg_type, message in validation_messages:
            if msg_type == "warning":
                st.markdown(f'<div class="validation-warning">{message}</div>', unsafe_allow_html=True)
            elif msg_type == "success":
                st.markdown(f'<div class="validation-success">{message}</div>', unsafe_allow_html=True)
            elif msg_type == "info":
                st.markdown(f'<div class="validation-info">{message}</div>', unsafe_allow_html=True)
    
    # 🎯 KAMPANIA (opcjonalne)
    st.markdown('<div class="section-header">🎯 KAMPANIA (opcjonalne)</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        utm_campaign = st.text_input(
            "utm_campaign (nazwa kampanii/inicjatywy)",
            st.session_state.get("utm_campaign", ""),
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
    
    # 🎨 KREACJA (opcjonalne)
    st.markdown('<div class="section-header">🎨 KREACJA (opcjonalne)</div>', unsafe_allow_html=True)
    
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
    
    # Update live preview podczas wypełniania
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
    submit = st.form_submit_button("🚀 Generuj finalny link UTM")

# Przetwarzanie po kliknięciu
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
        st.markdown('<div class="section-header">🎉 Finalny link UTM</div>', unsafe_allow_html=True)
        
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
with st.expander("📖 Informacje o parametrach UTM"):
    st.markdown("""
    ### Parametry UTM
    
    #### 📊 Źródło ruchu
    - **utm_market** - rynek: medica, education, lifestyle
    - **utm_channel** - najwyższy poziom źródła: paid, owned, earned, affiliate, offline
    - **utm_source** - platforma/dostawca: google, facebook, salesmanago
    - **utm_medium** - taktyka/typ ruchu: cpc, cpm, organic
    
    #### 🎯 Kampania
    - **utm_id** - numer akcji
    - **utm_campaign** - nazwa kampanii/inicjatywy
    - **utm_goal** - cel kampanii: sales, traffic, leads
    - **utm_stage** - etap lejka: reach, engage, consider, convert, retain, upsell, advocate
    - **utm_cohort** - kohorta/persona
    
    #### 🎨 Kreacja
    - **utm_content** - wersja kreacji
    - **utm_creative_id** - id z adserwera
    - **utm_term** - argument, słowo kluczowe
    """)