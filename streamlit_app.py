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

# Domyślna konfiguracja - minimalna struktura na wypadek braku pliku
FALLBACK_CONFIG = {
    "channels": ["paid", "owned", "earned", "affiliate", "offline"],
    "markets": ["medica", "education", "lifestyle", "business", "technology"],
    "stages": ["reach", "engage", "consider", "convert", "retain", "upsell", "advocate"],
    "goals": ["sales", "traffic", "leads"],
    "channel_source_medium_mapping": {},
    "campaign_templates": {},
    "validation_rules": {"warnings": [], "success": []},
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
    st.session_state[CONFIG_KEY] = FALLBACK_CONFIG.copy()

if "live_preview_url" not in st.session_state:
    st.session_state.live_preview_url = ""

# Funkcje pomocnicze
def clear_source_medium():
    """Wyczyść source i medium gdy zmieni się channel"""
    if "utm_source_select" in st.session_state:
        st.session_state["utm_source_select"] = ""
    if "utm_source_custom" in st.session_state:
        st.session_state["utm_source_custom"] = ""
    if "utm_medium_select" in st.session_state:
        st.session_state["utm_medium_select"] = ""
    if "utm_medium_custom" in st.session_state:
        st.session_state["utm_medium_custom"] = ""
def clear_source_medium():
    """Wyczyść source i medium gdy zmieni się channel"""
    if "utm_source_select" in st.session_state:
        st.session_state["utm_source_select"] = ""
    if "utm_source_custom" in st.session_state:
        st.session_state["utm_source_custom"] = ""
    if "utm_medium_select" in st.session_state:
        st.session_state["utm_medium_select"] = ""
    if "utm_medium_custom" in st.session_state:
        st.session_state["utm_medium_custom"] = ""

def load_config():
    config_path = "utm_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                st.session_state[CONFIG_KEY] = config
                return config
        except Exception as e:
            st.error(f"Błąd ładowania konfiguracji z pliku utm_config.json: {e}")
            st.info("Używam minimalnej konfiguracji awaryjnej. Sprawdź plik utm_config.json")
            config = FALLBACK_CONFIG.copy()
            st.session_state[CONFIG_KEY] = config
            return config
    else:
        st.warning("Nie znaleziono pliku utm_config.json. Używam minimalnej konfiguracji.")
        st.info("Stwórz plik utm_config.json w katalogu aplikacji dla pełnej funkcjonalności.")
        config = FALLBACK_CONFIG.copy()
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
    
    # Tylko ostrzeżenia - pomijamy sukcesy
    for rule in validation_rules.get("warnings", []):
        if (rule.get("channel") == channel and rule.get("medium") == medium):
            messages.append(("warning", rule["message"]))
    
    return messages

def apply_template(template_name, config):
    campaign_templates = config.get("campaign_templates", {})
    if template_name and template_name in campaign_templates:
        template = campaign_templates[template_name]
        for key, value in template.items():
            if key != "description":
                if key == "utm_source":
                    st.session_state["utm_source_select"] = value
                elif key == "utm_medium":
                    st.session_state["utm_medium_select"] = value
                else:
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

def generate_utm_params_only(params):
    """Generuje tylko parametry UTM bez URL bazowego"""
    filtered_params = {k: v for k, v in params.items() if v}
    
    if "utm_id" in filtered_params:
        filtered_params["a"] = filtered_params["utm_id"]
    
    encoded_params = []
    for key, value in filtered_params.items():
        encoded_value = urllib.parse.quote(value, safe='')
        encoded_params.append(f"{key}={encoded_value}")
    
    params_string = "&".join(encoded_params)
    return f"?{params_string}" if params_string else ""

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

# Pokaż status konfiguracji
if os.path.exists("utm_config.json"):
    st.success("✅ Załadowano konfigurację z utm_config.json")
else:
    st.warning("⚠️ Brak pliku utm_config.json - używam konfiguracji awaryjnej")

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

# Podstawowe pola POZA formularzem (żeby działały callbacki)
st.markdown('<div class="section-header">Podstawowe parametry (wymagane)</div>', unsafe_allow_html=True)

col_basic_1, col_basic_2, col_basic_3 = st.columns(3)

with col_basic_1:
    st.markdown('**URL bazowy** *', unsafe_allow_html=True)
    base_url = st.text_input(
        "",
        value=st.session_state.get("base_url", ui_settings.get("default_base_url", "https://example.com")),
        help="Wprowadź adres strony docelowej",
        key="base_url",
        placeholder="https://example.com/strona-docelowa",
        label_visibility="collapsed"
    )

with col_basic_2:
    st.markdown('**utm_market (rynek)** *', unsafe_allow_html=True)
    utm_market = st.selectbox(
        "",
        options=[""] + config.get("markets", []),
        help="Wybierz rynek docelowy",
        key="utm_market",
        label_visibility="collapsed"
    )

with col_basic_3:
    st.markdown('**utm_channel (najwyższy poziom)** *', unsafe_allow_html=True)
    utm_channel = st.selectbox(
        "",
        options=[""] + config.get("channels", []),
        help="Wybierz najwyższy poziom źródła ruchu - po zmianie automatycznie wyczyści się source i medium",
        key="utm_channel",
        label_visibility="collapsed",
        on_change=clear_source_medium
    )

# Potwierdzenie wyborów
if base_url and utm_market and utm_channel:
    st.success(f"✅ Podstawowe parametry: **{utm_market}** → **{utm_channel}** → {base_url}")
elif utm_channel:
    st.info(f"📝 Wybrany kanał: **{utm_channel}** (uzupełnij pozostałe pola)")

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
    # TRACKING - pozostałe pola wymagane
    st.markdown('<div class="section-header">Identyfikacja i źródło</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('**utm_id (numer akcji)** *', unsafe_allow_html=True)
        utm_id = st.text_input(
            "",
            value=st.session_state.get("utm_id", ""),
            help="Wprowadź numer akcji",
            key="utm_id",
            placeholder="np. 43234/1",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('**utm_source (platforma/dostawca)** *', unsafe_allow_html=True)
        
        source_suggestions = get_sources_for_channel(utm_channel, config)
        
        # Informacja o braku sugestii
        if utm_channel and not source_suggestions:
            st.info(f"Brak predefiniowanych źródeł dla kanału '{utm_channel}'. Użyj pola tekstowego.")
        
        # Combo: selectbox + text_input 
        utm_source_select = st.selectbox(
            "",
            options=[""] + source_suggestions + (["Inne..."] if source_suggestions else []),
            key="utm_source_select",
            label_visibility="collapsed"
        )
        
        utm_source_custom = st.text_input(
            "",
            key="utm_source_custom",
            placeholder="lub wpisz własną wartość",
            label_visibility="collapsed"
        )
        
        # Logika wyboru - własna wartość ma priorytet
        if utm_source_custom.strip():
            utm_source = utm_source_custom.strip()
        elif utm_source_select and utm_source_select != "Inne...":
            utm_source = utm_source_select
        else:
            utm_source = ""
    
    with col3:
        st.markdown('**utm_medium (taktyka/typ ruchu)** *', unsafe_allow_html=True)
        
        medium_suggestions = get_mediums_for_channel(utm_channel, config)
        
        # Informacja o braku sugestii
        if utm_channel and not medium_suggestions:
            st.info(f"Brak predefiniowanych mediów dla kanału '{utm_channel}'. Użyj pola tekstowego.")
        
        # Combo: selectbox + text_input
        utm_medium_select = st.selectbox(
            "",
            options=[""] + medium_suggestions + (["Inne..."] if medium_suggestions else []),
            key="utm_medium_select",
            label_visibility="collapsed"
        )
        
        utm_medium_custom = st.text_input(
            "",
            key="utm_medium_custom",
            placeholder="lub wpisz własną wartość",
            label_visibility="collapsed"
        )
        
        # Logika wyboru - własna wartość ma priorytet
        if utm_medium_custom.strip():
            utm_medium = utm_medium_custom.strip()
        elif utm_medium_select and utm_medium_select != "Inne...":
            utm_medium = utm_medium_select
        else:
            utm_medium = ""
    
    # Walidacja - tylko ostrzeżenia
    if ui_settings.get("show_validation", True) and utm_channel and utm_source and utm_medium:
        validation_messages = validate_combination(utm_channel, utm_source, utm_medium, config)
        for msg_type, message in validation_messages:
            if msg_type == "warning":
                st.markdown(f'<div class="validation-warning">⚠️ {message}</div>', unsafe_allow_html=True)
    
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
        utm_params_only = generate_utm_params_only(utm_params_preview)
        
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
        
        st.markdown('<div class="section-header">Parametry UTM (bez URL)</div>', unsafe_allow_html=True)
        
        # Kolorowane parametry bez URL
        if utm_params_only:
            params_text = ""
            params_part = utm_params_only[1:]  # Usuwamy "?" z początku
            params = params_part.split("&")
            for i, param in enumerate(params):
                if "=" in param:
                    param_name, param_value = param.split("=", 1)
                    params_text += f'<span style="color: #ff9d4f;">{param_name}</span>=<span style="color: #4ade80;">{param_value}</span>'
                else:
                    params_text += f'<span style="color: #ff9d4f;">{param}</span>'
                
                if i < len(params) - 1:
                    params_text += '<span style="color: #ffffff;">&amp;</span>'
            
            st.markdown(f"""
            <div style="background-color: #2a3746; padding: 16px; border-radius: 4px; margin-bottom: 10px; font-family: monospace; overflow-wrap: break-word; line-height: 1.5;">
                <span style="color: #ffffff;">?</span>{params_text}
            </div>
            <p style="font-size: 0.8em; color: #9ca3af; margin-top: 5px;">Kliknij ikonę po prawej stronie poniżej, aby skopiować tylko parametry</p>
            """, unsafe_allow_html=True)
            
            st.code(utm_params_only, language=None)
        
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

with st.expander("Etapy lejka marketingowego"):
    st.markdown("""
    ### Stages - Etapy lejka marketingowego
    
    **1. Reach** - Budowanie świadomości marki i dotarcie do jak najszerszego grona nowych odbiorców
    - KPI: wyświetlenia, zasięg, liczba unikalnych użytkowników
    - Działania: kampanie display, współpraca z influencerami, video awareness
    
    **2. Engage** - Pierwsze zaangażowanie odbiorcy, wzbudzenie ciekawości i zachęcenie do interakcji
    - KPI: CTR, czas na stronie, reakcje, komentarze, udostępnienia
    - Działania: interaktywne posty, konkursy, remarketing, newslettery
    
    **3. Consider** - Faza rozważenia, użytkownik szuka informacji i porównuje rozwiązania
    - KPI: pobrania materiałów, formularze kontaktowe, rejestracje na wydarzenia
    - Działania: case studies, webinary, oferty demo/trial, landing pages z kalkulatorami
    
    **4. Convert** - Faza konwersji, przekonanie do zakupu lub pożądanej akcji końcowej
    - KPI: liczba konwersji, CVR, zamówienia/subskrypcje, CAC
    - Działania: remarketing na porzucających koszyk, oferty limitowane, kupony rabatowe
    
    **5. Retain** - Utrzymanie klienta i budowanie lojalności wśród obecnych klientów
    - KPI: retention rate, powtarzalność zakupów, aktywność w aplikacji
    - Działania: programy lojalnościowe, personalizowane rekomendacje, maile post-sale
    
    **6. Upsell** - Zwiększenie wartości klienta przez sprzedaż produktów premium lub dodatków
    - KPI: średnia wartość koszyka, liczba sprzedanych dodatków, upgrade'ów
    - Działania: cross-selling, dynamiczne rekomendacje, e-maile z ofertami upgrade'ów
    
    **7. Advocate** - Budowanie armii ambasadorów, motywowanie do polecania marki
    - KPI: liczba poleceń, ilość opinii online, zasięg organiczny dzięki UGC
    - Działania: programy poleceń, zachęty za opinie, konkursy na historie klienta
    """)