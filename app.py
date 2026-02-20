import streamlit as st
from geopy.geocoders import Nominatim
import google.generativeai as genai
import json

st.title("NeuroMap Brasil")
st.markdown("Assistente especializado em buscas de clínicas para TEA, Síndrome de Down e Paralisia Cerebral, com restrição geográfica absoluta.")
st.warning("Nota: As buscas são realizadas pela IA do Google (Gemini), baseada em conhecimento treinado. Os resultados podem não ser exaustivos ou atualizados em tempo real. Verifique sempre as informações diretamente com as clínicas.")

gemini_api_key = st.text_input("Chave API Google Gemini (obrigatória para buscas)", type="password")

if not gemini_api_key:
    st.warning("Insira a chave API do Google Gemini para realizar buscas. Obtenha em: https://aistudio.google.com/app/apikey")
    st.stop()

# Configurar Gemini
genai.configure(api_key=AIzaSyBnWuGeLAj7IzYXgFj2zz9fXQN45dVvyMM)

# Parâmetros de entrada
cidade_bairro = st.text_input("Cidade/Bairro (ex: Vila Mariana)", value="Vila Mariana")
estado = st.text_input("Estado (padrão: SP)", value="SP")
endereco_opc = st.text_input("Endereço específico (opcional)")
raio = st.number_input("Raio de busca (km)", min_value=1, max_value=20, value=5)

condicoes_options = ["Autismo (TEA)", "Síndrome de Down", "Paralisia Cerebral"]
condicoes = st.multiselect("Filtros de Condição (selecione um ou mais)", condicoes_options)

especialidades_options = [
    "Psicologia", "Terapia Ocupacional", "Fonoaudiologia", "Fisioterapia",
    "Psicomotricidade", "Nutrição", "Psicopedagogia", "Musicoterapia",
    "Educação Física", "Cinoterapia", "Pediasuit", "Neuropsicologia"
]
especialidades = st.multiselect("Filtros de Especialidade (selecione um ou mais)", especialidades_options)

if st.button("Realizar Busca"):
    # Fase 1: Geocoding (opcional, para incluir coordenadas no prompt)
    geolocator = Nominatim(user_agent="neuromap_brasil")
    location_str = f"{endereco_opc if endereco_opc else cidade_bairro}, {estado}, Brasil"
    location = geolocator.geocode(location_str)
    
    center_info = ""
    if location:
        center_lat, center_lng = location.latitude, location.longitude
        center_info = f"Coordenadas aproximadas do centro: latitude {center_lat}, longitude {center_lng}. Use isso para estimar distâncias e respeitar rigorosamente o raio de {raio} km."
    
    # Preparar prompt para Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')  # Ou 'gemini-1.5-pro' se disponível
    prompt = f"""
    Você é um assistente especializado em buscar clínicas no Brasil para Transtorno do Espectro Autista (TEA), Síndrome de Down e Paralisia Cerebral.
    Localização central: {location_str}.
    {center_info}
    Raio máximo: {raio} km. DESCARTE qualquer clínica fora desse raio.
    Condições a atender (pelo menos uma): {', '.join(condicoes) if condicoes else 'Qualquer uma relevante'}.
    Especialidades a oferecer (pelo menos uma): {', '.join(especialidades) if especialidades else 'Qualquer uma relevante'}.

    Liste clínicas relevantes dentro do raio, priorizando as que atendem múltiplas condições e especialidades.
    Não limite a um número específico; liste todas as que você souber que se encaixem, mas foque em qualidade.
    Para cada clínica, forneça:
    - Nome
    - Endereço completo
    - Telefone (se souber, senão 'Não disponível')
    - Avaliação (nota média, se souber, senão 'Não disponível')
    - Distância aproximada do centro (em km)
    - Atende: lista com Autismo (TEA): SIM/NÃO, Síndrome de Down: SIM/NÃO, Paralisia Cerebral: SIM/NÃO
    - Especialidades oferecidas: lista das principais
    - Link Google Maps: https://www.google.com/maps/search/?api=1&query=[NOME+DA+CLINICA]+[CIDADE]

    Saída em formato JSON estrito: {{"clinics": [{{"name": "...", "address": "...", "phone": "...", "rating": "...", "dist": number, "atende": {{"autismo": "SIM/NÃO", "down": "SIM/NÃO", "paralisia": "SIM/NÃO"}}, "especialidades": ["...", "..."], "maps_link": "..."}}, ...]}}
    Não inclua texto extra fora do JSON.
    """
    
    response = model.generate_content(prompt)
    try:
        clinics_data = json.loads(response.text.strip())
        clinics = clinics_data.get("clinics", [])
    except Exception as e:
        st.error(f"Erro ao processar resposta da IA: {e}")
        st.stop()
    
    # Cabeçalho obrigatório
    st.markdown(f"📍 **BUSCA REALIZADA EM:** {cidade_bairro.upper()}")
    st.markdown(f"🎯 **RAIO:** {raio}km")
    st.markdown(f"🧩 **CONDIÇÕES:** {', '.join(condicoes) if condicoes else 'Nenhuma selecionada'}")
    st.markdown(f"⚕️ **ESPECIALIDADES:** {', '.join(especialidades) if especialidades else 'Nenhuma selecionada'}")
    st.markdown(f"📊 **TOTAL DE RESULTADOS:** {len(clinics)}")
    
    # Listagem de clínicas
    for clinic in clinics:
        st.markdown("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        st.markdown(f"🏥 **{clinic.get('name', 'Nome não disponível').upper()}**")
        st.markdown(f"📍 {clinic.get('address', 'Endereço não disponível')}")
        st.markdown(f"📞 **TELEFONE:** {clinic.get('phone', 'Não disponível')}")
        st.markdown(f"⭐ **AVALIAÇÃO:** {clinic.get('rating', 'Não disponível')}")
        st.markdown(f"📏 **DISTÂNCIA DO CENTRO:** aproximadamente {clinic.get('dist', 0):.1f}km")
        st.markdown("🧩 **ATENDE:**")
        atende = clinic.get('atende', {})
        st.markdown(f"• Autismo (TEA): {atende.get('autismo', 'NÃO')}")
        st.markdown(f"• Síndrome de Down: {atende.get('down', 'NÃO')}")
        st.markdown(f"• Paralisia Cerebral: {atende.get('paralisia', 'NÃO')}")
        st.markdown("⚕️ **ESPECIALIDADES OFERECIDAS:**")
        for esp in clinic.get('especialidades', []):
            st.markdown(f"• {esp}")
        st.markdown("🔗 **LINK GOOGLE MAPS:**")
        st.markdown(clinic.get('maps_link', 'Link não disponível'))
    
    if not clinics:
        st.info("Nenhum resultado encontrado pela IA dentro do raio e filtros. Tente ampliar o raio ou ajustar os filtros. Lembre-se que a IA usa conhecimento pré-treinado.")
