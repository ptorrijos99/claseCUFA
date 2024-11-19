import streamlit as st

# Configuración de nuestro proyecto
st.set_page_config(layout="wide", page_title="Panel de control de vuelos", page_icon="✈️")

# Para cargar los datos
import pandas as pd

# Para formatear los números
from millify import millify

# Para el mapa
import pydeck as pdk


st.title("Panel de control de vuelos")

# Función que carga los datos, y los guarda en caché para no tener que cargarlos cada vez que se recargue la página
#@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    return df

df = load_data("./data/Global_Air_Transport_Data.csv")
df = df.astype({col: float for col in df.columns[4:]})


# Separamos df en 4 dataframes:
#    - Número de despegues de transportistas aéreos registrados a nivel mundial.
#    - Transporte de carga aérea, medido en millones de toneladas-kilómetro.
#    - Número de pasajeros transportados por el sistema de transporte aéreo
#    - Índice de rendimiento logístico: calidad de la infraestructura de comercio y transporte (de 1 a 5, donde 1 es bajo y 5 es alto).
df_despegues = df[df['Series Name'].isin(['Air transport, registered carrier departures worldwide'])].drop(['Series Name','Series Code'], axis=1)
df_toneladas = df[df['Series Name'].isin(['Air transport, freight (million ton-km)'])].drop(['Series Name','Series Code'], axis=1)
df_pasajeros = df[df['Series Name'].isin(['Air transport, passengers carried'])].drop(['Series Name','Series Code'], axis=1)
df_indice = df[df['Series Name'].isin(['Logistics performance index: Quality of trade and transport-related infrastructure (1=low to 5=high)'])].drop(['Series Name','Series Code'], axis=1).dropna(axis=1, how='all')

g20_countries = ['ARG', 'AUS', 'BRA', 'CAN', 'CHN', 'FRA', 'DEU', 'IND', 'IDN', 'ITA', 'JPN', 'KOR', 'MEX', 'RUS', 'SAU', 'ZAF', 'TUR', 'GBR', 'USA', 'EUU', 'ESP']

def mostrar_indicadores(df, texto):
    st.header(f"Transporte aéreo: {texto}", divider=True)

    # Vamos a dividir el contenido en dos columnas
    col1, col2 = st.columns(2)

    # Número de registros registrados a nivel mundial (Country Name = World)
    df_mundiales = df[df['Country Name'] == 'World']

    # Mostrar las métricas para 2019, variación de 1 año y 2 años
    col1.write(f"Número de {texto} a nivel mundial")
    metric1, metric2, metric3 = col1.columns(3)

    indices = df_mundiales.columns[2:]

    number = millify(df_mundiales[indices[-1]], precision=2)
    metric1.metric(label=indices[-1], value=number)

    number = millify(df_mundiales[indices[-2]], precision=2)
    porcentaje = (((df_mundiales[indices[-1]] - df_mundiales[indices[-2]]) / df_mundiales[indices[-2]]) * 100).iloc[0]
    delta = porcentaje.round(2).astype(str) + "%"
    metric2.metric(label=f"vs {indices[-2]}", value=number, delta=delta)

    number = millify(df_mundiales[indices[-3]], precision=2)
    porcentaje = (((df_mundiales[indices[-1]] - df_mundiales[indices[-3]]) / df_mundiales[indices[-3]]) * 100).iloc[0]
    delta = porcentaje.round(2).astype(str) + "%"
    metric3.metric(label=f"vs {indices[-3]}", value=number, delta=delta)

    # Gráfico de línea con el número de registros mundiales
    col1.line_chart(df_mundiales.iloc[0, 2:], height=300, x_label="Año", y_label=f"{texto} mundial")

    # Variación en el número de registros entre los dos años seleccionados
    col2.write(f"Variación en el número de {texto} entre los años seleccionados")

    # Selección de años para comparar
    year1, year2 = col2.columns(2)
    year1 = year1.selectbox("Año 1", df.columns[2:-1], key=f"year1_selectbox_{texto}")
    opciones_year2 = [col for col in df.columns[2:] if col > year1]
    year2 = year2.selectbox("Año 2", opciones_year2, index=len(opciones_year2) - 1, key=f"year2_selectbox_{texto}")

    # Cálculo de la variación entre los años seleccionados
    df['Variación'] = df[year2] - df[year1]

    # Filtro para los países del G20
    g20 = df[df['Country Code'].isin(g20_countries)]
    g20 = g20.sort_values('Variación', ascending=False).reset_index(drop=True)
    g20['Country Name'] = pd.Categorical(g20['Country Name'], categories=g20['Country Name'], ordered=True)

    # Gráfico de barras con la variación
    col2.bar_chart(g20, x='Country Name', y='Variación', height=400, x_label="País", y_label="Variación", color="Variación")
    
    # Elminar la columna de variación y mostrar el dataset
    df.drop('Variación', axis=1, inplace=True)
    st.header(f"Datos: {texto}", divider=True)
    df

    # Mapa del mundo
    df_latitudes = load_data("./data/countries_codes_and_coordinates.csv")
    df = df.merge(df_latitudes, left_on='Country Code', right_on='Alpha-3 code', how='left')
    df = df.dropna()    

    st.header(f"Mapa del mundo: {texto}", divider=True)

    layer = pdk.Layer(
        "ColumnLayer",  # Tipo de capa
        data=df,
        get_position="[Longitude, Latitude]",  # Coordenadas de los puntos
        get_elevation="2019",  # Altura basada en la columna "2019"
        elevation_scale=100,  # Escala de la altura
        radius=50000,  # Radio de las columnas
        get_fill_color="[255, 140, 0, 200]",  # Color RGBA
        pickable=True,  # Permitir interacción con las columnas
    )
    r = pdk.Deck(layers=[layer], 
                 initial_view_state=pdk.ViewState(pitch=50),
                 tooltip={"text": "{Country Name}: {2019}"})
    st.pydeck_chart(r)


    st.map(df, latitude="Latitude", longitude="Longitude", zoom=1)


# Cuatro pestañas: una para cada df
tab1, tab2, tab3, tab4 = st.tabs(["✈️ Pasajeros", "📦 Vuelos de carga", "📊 Toneladas de carga", "📉 Índice Logístico"])

with tab1:
    mostrar_indicadores(df_pasajeros, "pasajeros")
with tab2:
    mostrar_indicadores(df_despegues, "vuelos de carga")
with tab3:
    mostrar_indicadores(df_toneladas, "toneladas de carga")
with tab4:
    mostrar_indicadores(df_indice, "índice logístico")
