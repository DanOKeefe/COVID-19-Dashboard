from flask import Flask, render_template, url_for, redirect, Response
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import math
import json
from bokeh.plotting import figure, show
from bokeh.models import (ColumnDataSource, GeoJSONDataSource, LinearColorMapper, 
                          ColorBar, CDSView, ColorBar, ColumnDataSource,CustomJS, 
                          CustomJSFilter, HoverTool, Slider, LogColorMapper)
from bokeh.layouts import gridplot, row
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar,  SingleIntervalTicker, LinearAxis, FuncTickFormatter
from bokeh.palettes import brewer
from bokeh.io import output_notebook, show, output_file
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models.callbacks import CustomJS
import geopandas as gpd

app = Flask(__name__)


@app.route("/")
def index():
    df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv')
    drop_cols = ['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Lat', 'Long_', 'Combined_Key']
    df.drop(drop_cols, axis=1, inplace=True)
    df=df.melt(id_vars=['Province_State','Country_Region', 'Admin2'] ,value_name='Cases', var_name='Date')
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    # apply filters for recent datd as of yesterday
    df_yesterday = df.loc[df['Date']==datetime.datetime.today().date() - datetime.timedelta(1)]
    tile_provider = get_provider(CARTODBPOSITRON)
    shapefile = 'cb_2018_us_state_20m/cb_2018_us_state_20m.shp'
    usa = gpd.read_file(shapefile)[['NAME', 'STUSPS', 'geometry']]
    usa.columns = ['state', 'state_code', 'geometry']
    cases_by_state_df = df_yesterday.groupby('Province_State')['Cases'].sum().reset_index().sort_values('Cases', ascending=False)
    merged = usa.merge(cases_by_state_df, left_on='state', right_on='Province_State', how='inner')
    merged = merged.loc[-merged['state'].isin(['Alaska', 'Hawaii', 'Puerto Rico'])]
    geosource = GeoJSONDataSource(geojson = merged.to_json())
    # Define color palettes
    #Define a sequential multi-hue color palette.
    palette = brewer['YlGnBu'][8]
    #Reverse color order so that dark blue is highest obesity.
    palette = palette[::-1]

    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LogColorMapper(palette = palette, low = merged.Cases.min(), high = merged.Cases.max())

    # Create figure object.
    p = figure(plot_height = 600, plot_width = 1000, 
               toolbar_location = 'below',
               tools = 'pan, wheel_zoom, box_zoom, reset',)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # Add patch renderer to figure.
    states = p.patches('xs','ys', source = geosource,
                       fill_color = {'field' :'Cases',
                                     'transform' : color_mapper},
                       line_color = '#4a4a4a', 
                       line_width = 0.75, 
                       fill_alpha = 1)

    p.background_fill_color = '#1b1c1b'

    p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    p.xaxis.ticker = []

    p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    p.yaxis.ticker = []

    p.outline_line_color = '#1b1c1b'
    p.border_fill_color = '#1b1c1b'

    # Create hover tool
    p.add_tools(HoverTool(renderers = [states],
                          tooltips = [('State','@state'),
                                    ('Cases','@Cases')]))

    p1_html = file_html(p, CDN, "USA")
    

    return render_template('index.html', p1=p1_html)

@app.route('/florida')
def florida():
    df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv')
    df = df.loc[(df['Country_Region']=='US') & (df['Province_State']=='Florida')]
    drop_cols = ['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Lat', 'Long_', 'Combined_Key']
    df.drop(drop_cols, axis=1, inplace=True)
    df=df.melt(id_vars=['Province_State','Country_Region', 'Admin2'], value_name='Cases', var_name='Date')
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    yesterday_df = df.loc[df['Date']==datetime.datetime.today().date() - datetime.timedelta(1)]
    tile_provider = get_provider(CARTODBPOSITRON)
    shapefile = 'cb_2018_us_county_500k/cb_2018_us_county_500k.shp'
    usa = gpd.read_file(shapefile)
    usa=usa[usa['STATEFP']=='12']
    usa=usa[['NAME', 'GEOID', 'geometry']]
    usa.columns = ['county', 'county_code', 'geometry']
    cases_by_county_df = yesterday_df.groupby('Admin2')['Cases'].sum().reset_index().sort_values('Cases', ascending=False)
    merged = usa.merge(cases_by_county_df, left_on='county', right_on='Admin2', how='inner')
    geosource = GeoJSONDataSource(geojson = merged.to_json())
    # Define color palettes
    #Define a sequential multi-hue color palette.
    palette = brewer['YlGnBu'][8]
    #Reverse color order so that dark blue is highest obesity.
    palette = palette[::-1]
    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LogColorMapper(palette = palette, low = merged.Cases.min(), high = merged.Cases.max())
    # Create figure object.
    p = figure(plot_height = 800, plot_width = 700, 
               toolbar_location = 'below',
               tools = 'pan, wheel_zoom, box_zoom, reset')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # Add patch renderer to figure.
    counties = p.patches('xs','ys', source = geosource,
                         fill_color = {'field' :'Cases',
                                       'transform' : color_mapper},
                         line_color = 'gray', 
                         line_width = 0.75, 
                         fill_alpha = 1,
                         hover_color='#eda1d1')

    p.background_fill_color = '#1b1c1b'

    p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    p.xaxis.ticker = []

    p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    p.yaxis.ticker = []

    p.outline_line_color = '#1b1c1b'
    p.border_fill_color = '#1b1c1b'
    
    code_hover = '''
    if((Bokeh.grabbing == 'undefined') || !Bokeh.grabbing) {
        var elm = document.getElementsByClassName('bk-canvas-events')[0]
        elm.style.cursor = 'context-menu' 
    }
    '''

    # Create hover tool
    p.add_tools(HoverTool(renderers = [counties],
                          tooltips = [('County','@county'),
                                      ('Cases','@Cases')],
                         callback = CustomJS(code = code_hover)))
    #show(p)
    p1_html = file_html(p, CDN, "USA")
    
    days = 21
    date_begin = datetime.datetime.today().date() - datetime.timedelta(1+days)
    date_end = datetime.datetime.today().date() - datetime.timedelta(1)
    df = df.loc[(df['Date']>=date_begin) & (df['Date']<=date_end)]
    cases_by_day_df = df.groupby(['Province_State', 'Date'])['Cases'].sum().reset_index()
    cases_by_day_df['new_cases'] = cases_by_day_df['Cases'].diff().dropna()
    cases_by_day_df.dropna(inplace=True)
    cases_by_day_df['Date'] = cases_by_day_df['Date'].astype(str)
    

    p2 = figure(plot_width=700, plot_height=400, x_range=cases_by_day_df['Date'])

    p2.vbar(
        x=cases_by_day_df['Date'],
        width=1, 
        bottom=0,
        top=cases_by_day_df['new_cases'], 
        color="#ffbe3d", 
        line_color="black",
        hover_fill_color="#ffbe78")
    
    code_hover2 = '''
    if((Bokeh.grabbing == 'undefined') || !Bokeh.grabbing) {
        var elm = document.getElementsByClassName('bk-canvas-events')[0]
        elm.style.cursor = 'context-menu' 
    }
    '''
    
    p2.add_tools(HoverTool(tooltips = [('Date','@x'),
                                      ('New Cases','@top')],
                           callback = CustomJS(code = code_hover2)))

    p2.xaxis.ticker = SingleIntervalTicker(interval=7)

    p2.background_fill_color = '#1b1c1b'

    #p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    #p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    #p.xaxis.ticker = []

    #p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    #p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    #p.yaxis.ticker = []

    p2.outline_line_color = '#1b1c1b'
    p2.border_fill_color = '#1b1c1b'
    p2.xgrid.grid_line_color = None
    p2.ygrid.grid_line_color = '#595959'
    # p.xaxis.major_label_orientation = math.pi/2
    p2.yaxis.major_label_text_color = "#ffde21"
    p2.xaxis.major_label_text_color = "#ffde21"
    
    label_dict = {}
    label_dict[0] = '3 weeks ago'
    label_dict[7] = '2 weeks ago'
    label_dict[14] = '1 week ago'
    label_dict[21] = 'Yesterday'

    p2.xaxis.formatter = FuncTickFormatter(code="""
        var labels = %s;
        return labels[tick];
    """ % label_dict)

    #p.xaxis.ticker = [0,7,14,21]
    #p.xaxis.major_label_overrides = {0:'3 weeks ago', 7:'2 weeks ago', 14:'1 week ago', 21:'Yesterday'}

    p2.title.text = "New Cases by Day: Last 21 Days"
    p2.title.align = "center"
    p2.title.text_color = "#ffde21"
    p2.title.text_font_size = "18px"
    p2.title.background_fill_color = "#1b1c1b"
    
    
    p2_html = file_html(p2, CDN, "home_layout")

    return render_template('florida.html', p1=p1_html, p2=p2_html)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=80)
    #app.run(debug=False)