import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

usuario = "nurdanetap@correo.uss.cl"
token = "4424d48d2a5a9fabc5a2a39f"

def obtener_catalogo():

    url = "https://climatologia.meteochile.gob.cl/application/geoservicios/getCatastroEstacionesGeo"
    params = {"usuario": usuario, "token": token}
    
    # intentar obtener el catalogo
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            stations = []
            for feature in data.get('features', []):
                properties = feature['features'].get('properties', {})
                if properties.get('CodigoNacional'):
                    stations.append({
                        'codigo': properties.get('CodigoNacional'),
                        'nombre': properties.get('nombreEstacion', 'Sin nombre'),
                    })
            return stations
    except Exception as e:
        # si hay error, mostrar mensaje de error
        st.error(f"Error al obtener catálogo de estaciones: {e}")
        return []
    
    return []

st.title('🌡️ Análisis de Temperaturas Históricas - Chile')

catalogo = obtener_catalogo()

if catalogo:
    st.sidebar.header("📍 Selecciona una Estación")
    
    opciones = {}
    for station in catalogo:
        display_name = f"{station['nombre']}"
        opciones[display_name] = station['codigo']
    
    selected_station_name = st.sidebar.selectbox(
        "Estación Meteorológica:",
        options=list(opciones.keys()),
        index=0 if opciones else 0
    )
    
    codigo_estacion = opciones.get(selected_station_name, 330020)
    
    # Obtener la estación seleccionada
    selected_station = next((s for s in catalogo if s['codigo'] == codigo_estacion), None)
    if selected_station:
        st.sidebar.info(
            f"*Nombre:* {selected_station['nombre']}\n\n"
            f"*Código:* {selected_station['codigo']}\n\n"
        )
else:
    codigo_estacion = 330020
    st.warning("No se pudo cargar el catálogo de estaciones. Usando estación por defecto (330020).")
url = f"https://climatologia.meteochile.gob.cl/application/servicios/getTemperaturaHistorica/{codigo_estacion}"
params = {"usuario": usuario, "token": token}

response = requests.get(url, params=params)

if response.status_code == 200:
    data_json = response.json()
    # st.write(data_json)

    #  datosHistoricos ---
    if 'datosHistoricos' in data_json and 'historico' in data_json['datosHistoricos']:
        historico = data_json['datosHistoricos']['historico']

        temp_max_media = historico['maxima']['media']
        temp_max_abs = historico['maxima']['maxAbs']
        temp_min_media = historico['minima']['media']
        temp_min_abs = historico['minima']['minAbs']

        station_name = "Estación Desconocida"
        if catalogo and selected_station:
            station_name = f"{selected_station['nombre']}"
        
        st.subheader(f'📊 {station_name} - Datos obtenidos vía API DMC')

        st.write(f"📊 Temperatura máxima promedio: {temp_max_media:.2f} °C")
        st.write(f"🌞 Temperatura máxima registrada: {temp_max_abs} °C")
        st.write(f"📊 Temperatura mínima promedio: {temp_min_media:.2f} °C")
        st.write(f"❄️ Temperatura mínima registrada: {temp_min_abs} °C")

        # mostrar promedios mensuales en tabla y gráfico de barras
        if 'mensualesHistoricos' in data_json['datosHistoricos']:
            mensuales = data_json['datosHistoricos']['mensualesHistoricos']
            # Crear DataFrame con promedios mensuales
            meses = []
            max_medias = []
            min_medias = []
            for mes in mensuales:
                meses.append(mes['mes'])
                max_medias.append(mes['valores']['maxima']['media'])
                min_medias.append(mes['valores']['minima']['media'])
            df_mensual = pd.DataFrame({
                'Mes': meses,
                'Temp Max Promedio': max_medias,
                'Temp Min Promedio': min_medias
            })
            st.subheader("Promedios mensuales")
            st.dataframe(df_mensual)

            # Gráfico de barras
            df_mensual.set_index('Mes')[['Temp Max Promedio', 'Temp Min Promedio']].plot(kind='bar', figsize=(10,5))
            plt.ylabel("Temperatura (°C)")
            plt.title("Temperaturas promedio mensuales")
            st.pyplot(plt)

    else:
        st.error("⚠️ No se encontraron datos históricos en la respuesta de la API.")
else:
    st.error(f"❌ Error en la solicitud a la API: {response.status_code}")
