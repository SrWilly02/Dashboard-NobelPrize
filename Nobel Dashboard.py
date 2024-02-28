from dash import Dash, html, dcc, dash_table, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import pycountry

app = Dash(external_stylesheets = [dbc.themes.CERULEAN])

# LECTURA DE DATOS
data = pd.read_csv('./data/nobel.csv')

# LIMPIEZA DE DATOS
data['born'] = data['born'].astype(str)
data = data[~data['born'].str.startswith('00')]
data['born'] = pd.to_datetime(data['born'], format = '%m/%d/%Y')

data['age'] = data['year'] - data['born'].dt.year

def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name = country_name)
        if country:
            return country.alpha_3
        elif country_name == 'USA':
            return 'USA'
    except Exception as e:
        return None
    
data['Country_ISO3'] = data['bornCountry'].apply(get_country_code)

# DASHBOARD

# NAVBAR
navbar = dbc.NavbarSimple(
    brand = 'Premio Nobel Dashboard',
    brand_style= {'marginLeft': 10, 'fontFamily': 'Helvetica'},
    children = [
        html.A('Data Source',
               href = 'https://www.kaggle.com/datasets/thedevastator/a-complete-history-of-nobel-prize-winners?select=nobelTriples.csv',
               target = '_blank')
    ],
    color = 'primary',
    fluid = True
)

# SLIDER
year_min = int(data['year'].min())
year_max = int(data['year'].max())

slider = html.Div([
    html.H4('Año', id = 'title-slider'),
    dcc.RangeSlider(id = 'year-slider',
                    min = year_min,
                    max = year_max,
                    value = [year_min, year_max],
                    marks = {i:str(i) for i in range(year_min, year_max + 1, 10)})

])

# MENU
menu_drop = html.Div([
    dcc.Dropdown(data['category'].unique(), placeholder = 'Selecciona una categoría', id = 'cat-dropdown')
], id = 'menuDrop')

# MAPA
complete_map = html.Div([
    dcc.Graph(id = 'map-graph')
])

# CARTAS
cards = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            html.H4('Hombre'),
            html.H5(id = 'percentage-man')
        ], body = True)),
        dbc.Col(dbc.Card([
            html.H4('Mujer'),
            html.H5(id = 'percentage-woman')
        ], body = True))
    ])
], id = 'cards')

# TABLA DE CATEGORÍAS
table = dash_table.DataTable(
    id = 'table-categories',
    columns = [{'name': 'Category', 'id': 'category'}, {'name' : 'Count', 'id' : 'count'}]
)

# GRÁFICO DE PUNTOS
graph_age = html.Div(
    dcc.Graph(id = 'scatter-graph')
)

@app.callback(
    Output('map-graph', 'figure'),
    Output('scatter-graph', 'figure'),
    Output('percentage-man', 'children'),
    Output('percentage-woman', 'children'),
    Output('table-categories', 'data'),
    Input('year-slider', 'value'),
    Input('cat-dropdown', 'value')
)

def update_dashboard(selected_year, category):

    if category == None:
        # FILTRADO DEL CONJUNTO
        filtered_data = data[(data['year'] >= selected_year[0]) &
                             (data['year'] <= selected_year[1])]
    else:
        filtered_data = data[(data['year'] >= selected_year[0]) &
                             (data['year'] <= selected_year[1]) &
                             (data['category'] == category)]
    
    # MAPA
    winners_country = filtered_data['Country_ISO3'].value_counts().reset_index()
    winners_country.rename(columns = {'Country_ISO3':'country'}, inplace = True)
    map_fig = px.choropleth(winners_country, locations = 'country', color = 'count', title = 'Número de ganadores de Premio Nobel por País')

    # GRÁFICO DE PUNTOS
    scatter_figure = px.scatter(filtered_data, x = 'year', y = 'age', opacity = 0.65,
                                trendline = 'ols', trendline_color_override = 'black',
                                title = 'Edad de los ganadores de Premio Nobel por Año')
    
    # TARJETAS
    total_ganadores = len(filtered_data)
    ganadores_hombres = len(filtered_data[filtered_data['gender'] == 'male'])
    ganadores_mujeres = len(filtered_data[filtered_data['gender'] == 'female'])

    porcentaje_hombres = (ganadores_hombres / total_ganadores) * 100
    porcentaje_mujeres = (ganadores_mujeres / total_ganadores) * 100

    result_man =  f'{round(porcentaje_hombres, 2)} %'
    result_woman = f'{round(porcentaje_mujeres, 2)} %'

    # TABLA
    categories = filtered_data['category'].value_counts().reset_index()

    return map_fig, scatter_figure, result_man, result_woman, categories.to_dict('records')

app.layout = html.Div([
    dbc.Row(navbar),
    dbc.Row(slider),
    dbc.Row([
        dbc.Col(complete_map),
        dbc.Col([
            dbc.Row(menu_drop),
            dbc.Row(cards),
            dbc.Row(table)
        ])
    ]),
    dbc.Row(graph_age)
])

if __name__ == '__main__':
    app.run_server(debug = True)