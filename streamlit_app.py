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

# Styl CSS
st.markdown("""
<style>    
    /* Nagłówki sekcji */
    .section-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #ffffff;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #374151;
    }

    /* Pojemniki dla kategorii */
    .category-container {
        background-color: #1e2730;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
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
    
    /* Wyjaśnienie wymaganych pól */
    .required-explanation {
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        color: #9ca3af;
        font-size: 0.9rem;
    }
    
    /* Lepsze przyciski formularza */
    .stButton>button {
        width: 100%;
        background-color: #3d68ff;
        color: white;
        padding: 0.75rem 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Domyślna konfiguracja parametrów UTM
DEFAULT_CONFIG = {
    "channels": ["paid", "owned", "earned", "affiliate", "offline"],
    "markets": ["medica", "education", "lifestyle", "finance", "technology"],
    "stages": ["reach", "engage", "consider", "convert", "retain", "upsell", "advocate"],
    "goals": ["sales", "traffic", "leads"]
}

# Klucz dla przechowywania konfiguracji w session_state
CONFIG_KEY = "utm_config"

# Inicjalizacja konfiguracji w session_state z pełną kopią
if CONFIG_KEY not in st.session_state:
    st.session_state[CONFIG_KEY] = DEFAULT_CONFIG.copy()

# Funkcja do ładowania konfiguracji
def load_config():
    # W wersji cloud używamy session_state zamiast pliku
    config = st.session_state.get(CONFIG_KEY, DEFAULT_CONFIG.copy())
    
    # Sprawdzamy czy wszystkie klucze istnieją i dodajemy brakujące
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
    
    st.session_state[CONFIG_KEY] = config
    return config

# Funkcja do zapisywania konfiguracji
def save_config(config):
    st.session_state[CONFIG_KEY] = config

# Generowanie linku UTM
def generate_utm_link(base_url, params):
    # Filtrowanie parametrów, które nie są puste
    filtered_params = {k: v for k, v in params.items() if v}
    
    # Dodanie parametru "a" z wartością utm_id
    if "utm_id" in filtered_params:
        filtered_params["a"] = filtered_params["utm_id"]
    
    # Ręczne kodowanie parametrów dla zachowania ukośników wstecznych
    encoded_params = []
    for key, value in filtered_params.items():
        # Kodowanie URL z zachowaniem ukośników wstecznych
        encoded_value = urllib.parse.quote(value, safe='')
        encoded_params.append(f"{key}={encoded_value}")
    
    # Łączenie zakodowanych parametrów
    params_string = "&".join(encoded_params)
    
    # Tworzenie pełnego URL
    if "?" in base_url:
        final_url = base_url + "&" + params_string
    else:
        final_url = base_url + "?" + params_string
    
    return final_url

# Nagłówek aplikacji
st.title("UTM Builder")
st.markdown("Narzędzie do generowania linków z parametrami UTM dla kampanii marketingowych.")
st.markdown('<div class="required-explanation">Pola oznaczone <span class="required">*</span> są wymagane</div>', unsafe_allow_html=True)

# Ładowanie konfiguracji
config = load_config()

# Główny formularz
with st.form("utm_form"):
    # Sekcja URL bazowy
    st.markdown('<div class="section-header">URL bazowy</div>', unsafe_allow_html=True)
    st.markdown('<span class="required">*</span> URL bazowy strony:', unsafe_allow_html=True)
    base_url = st.text_input(
        "",
        "https://example.com",
        help="Wprowadź adres strony docelowej",
        key="base_url",
        placeholder="https://example.com/strona-docelowa",
        label_visibility="collapsed"
    )
    
    # Dwie kolumny na parametry
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="category-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Źródło ruchu</div>', unsafe_allow_html=True)
        
        # Market (rynek)
        st.markdown('<span class="required">*</span> utm_market (rynek):', unsafe_allow_html=True)
        utm_market = st.selectbox(
            "",
            options=[""] + config.get("markets", []),
            help="Wybierz rynek docelowy",
            key="utm_market",
            label_visibility="collapsed"
        )
        
        # Channel (kanał)
        st.markdown('<span class="required">*</span> utm_channel (najwyższy poziom):', unsafe_allow_html=True)
        utm_channel = st.selectbox(
            "",
            options=[""] + config.get("channels", []),
            help="Wybierz najwyższy poziom źródła ruchu",
            key="utm_channel",
            label_visibility="collapsed"
        )
        
        # Source (źródło)
        st.markdown('<span class="required">*</span> utm_source (platforma/dostawca):', unsafe_allow_html=True)
        utm_source = st.text_input(
            "",
            "",
            help="Wprowadź platformę lub dostawcę",
            key="utm_source",
            placeholder="np. google, facebook, salesmanago",
            label_visibility="collapsed"
        )
        
        # Medium (medium)
        st.markdown('<span class="required">*</span> utm_medium (taktyka/typ ruchu):', unsafe_allow_html=True)
        utm_medium = st.text_input(
            "",
            "",
            help="Wprowadź taktykę lub typ ruchu",
            key="utm_medium",
            placeholder="np. cpc, cpm, organic",
            label_visibility="collapsed"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sekcja Kreacja
        st.markdown('<div class="category-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Kreacja</div>', unsafe_allow_html=True)
        
        # Content (treść)
        st.markdown('utm_content (wersja kreacji):', unsafe_allow_html=True)
        utm_content = st.text_input(
            "",
            "",
            help="Wprowadź wersję kreacji",
            key="utm_content",
            placeholder="np. email_short, banner_900x344_blue",
            label_visibility="collapsed"
        )
        
        # Creative ID (ID kreacji)
        st.markdown('utm_creative_id (id z adserwera):', unsafe_allow_html=True)
        utm_creative_id = st.text_input(
            "",
            "",
            help="Wprowadź ID z adserwera",
            key="utm_creative_id",
            placeholder="np. 123456",
            label_visibility="collapsed"
        )
        
        # Term (słowo kluczowe)
        st.markdown('utm_term (argument, słowo kluczowe):', unsafe_allow_html=True)
        utm_term = st.text_input(
            "",
            "",
            help="Wprowadź argument lub słowo kluczowe",
            key="utm_term",
            placeholder="np. marketing, analytics",
            label_visibility="collapsed"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Sekcja Kampania
        st.markdown('<div class="category-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Kampania</div>', unsafe_allow_html=True)
        
        # ID (numer akcji)
        st.markdown('<span class="required">*</span> utm_id (numer akcji):', unsafe_allow_html=True)
        utm_id = st.text_input(
            "",
            "",
            help="Wprowadź numer akcji",
            key="utm_id",
            placeholder="np. 43234/1",
            label_visibility="collapsed"
        )
        
        # Campaign (kampania)
        st.markdown('utm_campaign (nazwa kampanii/inicjatywy):', unsafe_allow_html=True)
        utm_campaign = st.text_input(
            "",
            "",
            help="Wprowadź nazwę kampanii lub inicjatywy",
            key="utm_campaign",
            placeholder="np. cel_marketingowy-linia_produktowa-segment-rodzaj",
            label_visibility="collapsed"
        )
        
        # Goal (cel kampanii)
        st.markdown('utm_goal (cel kampanii):', unsafe_allow_html=True)
        utm_goal = st.selectbox(
            "",
            options=[""] + config.get("goals", []),
            help="Wybierz cel kampanii",
            key="utm_goal",
            label_visibility="collapsed"
        )
        
        # Stage (etap)
        st.markdown('utm_stage (etap lejka):', unsafe_allow_html=True)
        utm_stage = st.selectbox(
            "",
            options=[""] + config.get("stages", []),
            help="Wybierz etap lejka marketingowego",
            key="utm_stage",
            label_visibility="collapsed"
        )
        
        # Cohort (kohorta)
        st.markdown('utm_cohort (kohorta/persona):', unsafe_allow_html=True)
        utm_cohort = st.text_input(
            "",
            "",
            help="Wprowadź kohortę lub personę",
            key="utm_cohort",
            placeholder="np. new_customers, loyal_clients",
            label_visibility="collapsed"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Przycisk generowania - musi być ostatnim elementem w formularzu
    submit = st.form_submit_button("Generuj link UTM")

# Przetwarzanie po kliknięciu przycisku
if submit:
    # Walidacja wymaganych pól
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
        # Parametry UTM
        utm_params = {
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
        
        # Generowanie linku
        final_url = generate_utm_link(base_url, utm_params)
        
        # Wyświetlenie wyniku
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Wygenerowany link UTM</div>', unsafe_allow_html=True)
        
        # Kolorowanie linku z podziałem na nazwy parametrów i ich wartości
        parts = final_url.split("?")
        base_part = parts[0]
        
        # Jeśli są parametry, podziel je i pokoloruj
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
        
        # Standardowe pole z kodem również dla łatwego kopiowania
        st.code(final_url, language=None)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Informacje o parametrach UTM
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
    - **utm_campaign** - nazwa kampanii/inicjatywy (Wg. konwencji: cel_marketingowy-linia_produktowa-segment-rodzaj)
    - **utm_goal** - cel kampanii: sales, traffic, leads
    - **utm_stage** - etap lejka: reach, engage, consider, convert, retain, upsell, advocate
    - **utm_cohort** - kohorta/persona
    
    **Etapy lejka marketingowego:**
    - **reach** - Budowanie świadomości marki (dotarcie do nowych odbiorców)
    - **engage** - Pierwsze zaangażowanie odbiorcy (wzbudzenie ciekawości)
    - **consider** - Rozważenie oferty (zachęcenie do zapoznania się z subskrypcją)
    - **convert** - Zakup lub subskrypcja (przekonanie do podjęcia decyzji zakupowej)
    - **retain** - Utrzymanie klienta
    - **upsell** - Zwiększenie wartości klienta (przedłużenie subskrypcji, sprzedaż dodatków)
    - **advocate** - Rekomendacje od klientów (pozyskanie nowych subskrybentów przez obecnych)
    
    #### Kreacja
    - **utm_content** - wersja kreacji: email_short, banner_900x344_blue, popup_blue
    - **utm_creative_id** - id z adserwera
    - **utm_term** - argument, słowo kluczowe
    """)