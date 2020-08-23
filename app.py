import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from itertools import product

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


col_map = {"retail_and_recreation": "Retail and Recreation", 
           "grocery_and_pharmacy": "Grocery and Pharmacy",
           "parks": "Parks", "transit_stations": "Public Transport Stations",
           "workplaces": "Workplaces", "residential": "Residential"}

    
available_indicators = list(col_map.values())

bins = pd.IntervalIndex.from_tuples(
    [(-1350, -1250), (-1000, -50), (-50, -40), (-40, -30), (-30, -20), 
     (-20, -10), (-10, 10), (10, 20), (20, 30), (30, 40), (40, 50), 
     (50, 1000)]
    )
labels = {"NA": "SlateGrey", "< -50%": "DarkRed", "-50 to -40%": "FireBrick", 
          "-40 to -30%": "LightCoral", "30 to -20%": "LightPink", 
          "-20 to -10%": "MistyRose", "-10 to 10%": "MintCream", 
          "10 to 20%": "PaleGreen", "20 to 30%": "MediumSeaGreen", 
          "30 to 40%": "OliveDrab", "40 to 50%": "Olive", "> 50%": "SeaGreen"}


def import_data():
    # Read in the mobility data
    df = pd.read_csv("Global_Mobility_Report.csv")
    # Filter to just UK data - only sub-regions
    df = df.loc[df.country_region_code=="GB"]
    df = df.loc[~df.sub_region_1.isna()]
    # Remove the suffix on data columns
    df.rename({x:x.replace("_percent_change_from_baseline", "") for x in df.columns}, 
              axis=1, inplace=True)
    
    # For missing data use the sub-region names to match with the geojson fields
    df["iso_3166_2_code"].fillna(df["sub_region_1"], inplace=True)
    # Create a dataframe containing all sub-region / date combinations to fill
    # missing data
    all_rows = pd.DataFrame([list(x[0][1]) + [x[1]] for x in 
                             product(df[["sub_region_1", "iso_3166_2_code"]
                                        ].drop_duplicates().iterrows(),
                                     df["date"].unique())],
                 columns=["sub_region_1", "iso_3166_2_code", "date"])
    df = all_rows.merge(df, how="left")
    
    df = df.rename(col_map, axis=1)
    
    return df

def bin_data(unbinned_df):
    
    plot_df = unbinned_df.copy()

    for old_col in available_indicators:
    
        col = old_col + "_bin"   
        plot_df[col] = plot_df[old_col]
        
        plot_df[col].fillna(-1300, inplace=True)
        
        a = pd.cut(plot_df[col].to_list(), bins)
        a.categories = list(labels.keys())
        plot_df[col] = a.astype("str")
    
    return plot_df

df = import_data()

plot_df = bin_data(df)

geo = "https://raw.githubusercontent.com/jacPeach/covid-movement-map/master/uk_subdivisions.geojson"

slider_map = {i: date for i, date in enumerate(sorted(plot_df["date"].unique()))}

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                "Data Source",
                href="https://www.google.com/covid19/mobility/"
                )
            ),
        dbc.NavItem(
            dbc.NavLink(
                "Source Code",
                href="https://github.com/jacPeach/covid-movement-map"
                )
            )
        ],
    brand="Covid-19: UK Travel Changes",
    brand_href="#",
    color="dark",
    dark=True
)

app_layout = dbc.Container(
    children=[
        dbc.Row(
            dcc.Markdown(
                    f"""
        -----
        ##### Data:
        -----
        This dashboard uses data sourced from the Google Community Mobility Reports
        """
                        )
            ),
        dbc.Row(
            dcc.Dropdown(id="crossfilter-column",
                         options=[{"label": i, "value": i} 
                                 for i in available_indicators],
                         value="Retail and Recreation",
                         style={"width": "50%"})
            ),
        dbc.Row(
            [
                
                dbc.Col(
                    [
                        dcc.Graph(id="choropleth-map",
                                  clickData={"points": [{"hovertext": "Greater London"}]},
                                  )
                        ]
                    
                    )
                ], 
            ),
        dcc.Slider(id="date-slider",
                   min=min(slider_map.keys()),
                   max=max(slider_map.keys()),
                   value=0,
                   step=1,
                   marks={0: min(slider_map.values()),
                          max(slider_map.keys()): max(slider_map.values())}
                   ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id="time-series")
                        ]
                    ),
                ]
            ),
        ],
    style={"marginTop": 20}
    )

app.layout = html.Div([navbar, app_layout])

# app.layout = html.Div(children=[
    
#     html.H1(children="Covid-19: UK Travel Change", style={"textAlign": "center"}),
    
#     html.Div(children="""
#              Visualise the change in movement patterns during the Covid-19 pandemic
#              against a January 2020 baseline.
#              """),
             
#     html.Div([
#         dcc.Dropdown(id="crossfilter-column",
#                      options=[{"label": i, "value": i} for i in available_indicators],
#                      value="Retail and Recreation")
#         ],
#         style={"width": "49%", "display": "inline-block"}),
         
#     html.Div(children=[
#         html.H3("Date : ", style={"display": "inline-block"}),
#         html.H3(id="slider-selected", style={"display": "inline-block"})
#         ], style={"textAlign": "left"}
#         ),
    
#     html.Div([
#         dcc.Graph(id="choropleth-map",
#                   clickData={"points": [{"hovertext": "Greater London"}]})
#         ], style={"display": "inline-block", "width": "48%", "height": "80%"}),
    
#     html.Div([
#          dcc.Graph(id="time-series")
#         ], style={"display": "inline-block", "width": "48%", "height": "80%"}),
    
#     dcc.Slider(id="date-slider",
#                min=min(slider_map.keys()),
#                max=max(slider_map.keys()),
#                value=0,
#                step=1,
#                marks={0: min(slider_map.values()),
#                       max(slider_map.keys()): max(slider_map.values())},
#                updatemode="drag"),
    
#     html.Div(children="Data source: Google Covid-19 Community Mobility Reports")
# ])


@app.callback(
    Output("date-slider", "value"),
    [Input("time-series", "clickData")])
def filter_date(cross_filter_date):
    print(cross_filter_date)
    if cross_filter_date is None:
        return 0
    date = cross_filter_date["points"][0]["x"]
    date_index = {v: k for k, v in slider_map.items()}[date]
    return date_index

@app.callback(
    Output("choropleth-map", "figure"),
    [Input("date-slider", "value"),
     Input("crossfilter-column", "value")])
def update_choropleth(selected_date, selected_col):
    
    col = selected_col + "_bin"
    
    date = slider_map[selected_date]
    columns = ["iso_3166_2_code", "sub_region_1", "date", col, selected_col]
    filtered_df = plot_df.loc[plot_df["date"]==date][columns]
    
    filtered_df = filtered_df.sort_values(by=["sub_region_1", "date"])
    
    # Add blank lines to show in legend
    filtered_df = pd.concat([
        filtered_df,
        pd.DataFrame([
            [
                date if c == "date" else val if c == col else "" 
                for c in filtered_df.columns
             ] for date, val in product(slider_map.values(), labels.keys())], 
            columns=filtered_df.columns
            )
        ], axis=0
    )
    
    title = "<b>{} - Percent Change in Travel to {}</b>".format(date, selected_col)
    
    fig = px.choropleth(filtered_df, 
                        geojson=geo,
                        locations="iso_3166_2_code",
                        featureidkey="properties.iso_3166_2",
                        color=col, 
                        projection="natural earth",
                        hover_name="sub_region_1",
                        color_discrete_map=labels,
                        category_orders={col: list(labels.keys())},
                        hover_data={selected_col:True, "date":False, 
                                    "iso_3166_2_code":False, col:False},
                        title=title,
                        height=800
                       )
    
    
    fig.update_geos(visible=False, fitbounds="locations")
    
    fig.update_layout(legend_title_text="Percent Change")
    
    return fig

@app.callback(
    Output("time-series", "figure"),
    [Input("choropleth-map", "clickData"),
     Input("crossfilter-column", "value")])
def update_time_series(hover_data, selected_col):
    
    region = hover_data["points"][0]["hovertext"]
    filtered_df = plot_df.loc[plot_df["sub_region_1"]==region].sort_values(by="date")
    return create_time_series(filtered_df, selected_col, region)

def create_time_series(df, col, region):
    
    title = "<b>{}</b>".format(region)
    
    df = df.set_index("date")[available_indicators].stack().reset_index()
    df.columns = ["date", "Sector", "Percent Change"]
    
    
    
    fig = px.scatter(df, x="date", y="Percent Change", color="Sector",
                     title=title)
    
    fig.update_traces(mode="lines")
    
    fig.update_yaxes(range=[-100, 100])
    
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)