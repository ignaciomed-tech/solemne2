import requests #Librería para obtener la información.
import pandas as pd #Librería para analizar y manipular datos.
import matplotlib.pyplot as plt #Librería utilizada para crear gráficos.
import streamlit as st #Librería que crea la interfaz gráfica.

#Variable para autentificar las solicitudes API.
usuario = "nurdanetap@correo.uss.cl" 
token = "4424d48d2a5a9fabc5a2a39f"

#Define la función para obtener los datos de la API, retornando un listado con el nombre de la estación climatica y su ID.
def obtener_catalogo(): 

    url = "https://climatologia.meteochile.gob.cl/application/geoservicios/getCatastroEstacionesGeo" 
    params = {"usuario": usuario, "token": token}
    #Se realiza la solicitud http a la URL.
    response = requests.get(url, params=params)
    #El code 200 es para saber que la solicitud fue exitosa.
    if response.status_code == 200:
        
        data = response.json() #La respuesta de la petición debe ser en formato json.
        stations = [] #En la variable "station" se almacenará la información de los codigos y nombres de las estaciones.
      
        features = data.get('features', []) #Se obtiene la propiedad feature.
        for feature in features: #Se itera por cada objeto dentro de feature.
            feature_features = feature.get('features', {}) #A la variable feature_features le asignamos la propiedad features del objeto feature.
            properties = feature_features.get('properties', {}) #A la variable properties le asignamos la propiedad properties del obejto feature_features.
            if properties.get('CodigoNacional') and properties.get('nombreEstacion'): #Si cumple con la condición agrega un objeto al listado stations.
                stations.append({ #Al listado stations agregaremos cada codigo y cada nombre extraído de la itearción. 
                    'codigo': properties.get('CodigoNacional'), #LLamaremos codigo a cada "codigo nacional en la iteración.
                    'nombre': properties.get('nombreEstacion', 'Sin nombre'), #Llamaremos nombre a cada nombre de la estación.
                })
        return stations #Se retorna el objeto station.
    return []

st.title(' Análisis de Temperaturas Históricas - Chile') #Titulo de la interfaz.

catalogo = obtener_catalogo() #Se llama a la función obtener catalogo y se retorna station.

if catalogo:
    st.sidebar.header("Selecciona una Estación") #Agrega un titulo al sidebar
    
    opciones = {} 
    for station in catalogo: #Para las estaciones en el catalogo vamos a mostrar en la interfaz la siguiente estructura
        display_name = f"{station['nombre']}" #La variable display_name obtendrá el nombre de las estaciones dentro del catalogo.
        opciones[display_name] = station['codigo'] 
        
    #Se define el select box con las estaciones disponibles en el sidebar
    selected_station_name = st.sidebar.selectbox(
        "Estación Meteorológica:",
        options=list(opciones.keys()),
        index=0 if opciones else 0
    )
    
    codigo_estacion = opciones.get(selected_station_name, 330020)
    
   #Se busca en el listado catalogo la estación que tenga el codigo estación. La función next itera en el listado 
    #hasta que se cumpla la condición y retorna el station encontrado.
    selected_station = next((station for station in catalogo if station['codigo'] == codigo_estacion), None)
    if selected_station:
        st.sidebar.info(
            f"*Nombre:* {selected_station['nombre']}\n\n"
            f"*Código:* {selected_station['codigo']}\n\n"
        )
else:
    codigo_estacion = 330020
    st.warning("No se pudo cargar el catálogo de estaciones. Usando estación por defecto (330020).")
#En base a la estación escogida la URL cambiará.    
url = f"https://climatologia.meteochile.gob.cl/application/servicios/getTemperaturaHistorica/{codigo_estacion}"
params = {"usuario": usuario, "token": token}

response = requests.get(url, params=params)

if response.status_code == 200:
    data_json = response.json()
  

 
    if 'datosHistoricos' in data_json and 'historico' in data_json['datosHistoricos']:
        historico = data_json['datosHistoricos']['historico']
        
        #Se extraen las variables indicadas como temperatura media, maxima y minima.
        
        temp_max_media = historico['maxima']['media']
        temp_max_abs = historico['maxima']['maxAbs']
        temp_min_media = historico['minima']['media']
        temp_min_abs = historico['minima']['minAbs']

        station_name = "Estación Desconocida"
        
        #Si catalogo y la estación seleccionada son verdadero, se extrae el nombre de la estación.
        
        if catalogo and selected_station:
            station_name = f"{selected_station['nombre']}"
        
        st.subheader(f' {station_name} - Datos obtenidos vía API DMC')

        st.write(f" Temperatura máxima promedio: {temp_max_media:.2f} °C")
        st.write(f" Temperatura máxima registrada: {temp_max_abs} °C")
        st.write(f" Temperatura mínima promedio: {temp_min_media:.2f} °C")
        st.write(f" Temperatura mínima registrada: {temp_min_abs} °C")

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
        st.error(" No se encontraron datos históricos en la respuesta de la API.")
else:
    st.error(f" Error en la solicitud a la API: {response.status_code}")
