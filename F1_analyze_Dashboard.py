# importing libraries
import os
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt 
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd 
from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots

## Enable caching to avoid unnecessary strain on the API
os.makedirs('f1_cache',exist_ok=True)
fastf1.Cache.enable_cache('f1_cache')

# Available GPS Data log

GPS = [
    'Bahrain', 'Saudi Arabia', 'Australia', 'Japan',
    'China','Miami', 'Monaco', 'Canada','Spain','Austria',
    'Britain','Hungary','Belgium','Netherlands','Italia',
    'Azerbaijan','Singapore','United States','Mexico',
    'Brazil','Las Vegas','Qatar','Abu Dhabi'
]

PARAMETERS = {
    'Speed(Km/h)': 'Speed',
    'Throttle(%)': 'Throttle',
    'Brake':       'Brake',
    'Gear':        'nGear',
    'RPM':         'RPM',
    'DRS':         'DRS',
}

Drivers_2024 = [
    'VER','HAM','LEC','NOR','SAI',
    'RUS','PIA','ALO','STR','GAS',
    'OCO','ALB','TSU','HUL','MAG',
    'BOT','ZHO','RIC','LAW','BEA',
    'PER','ANT','LAW'
]

## App Layout 

app = Dash(__name__)

app.layout = html.Div([
    html.Div([ 
        html.H2("F1 Telemetry Dashboard",
            style ={'margin':'0',
                    'color':'#E10600',
                    'fontFamily':'monospace'}),

    html.P("Live driver comparison - powered by fastF1",
           style = {'margin': '4px 0 0',
                    'color':'#888',
                    'fontSize':'13px'})
], style={'padding':'20px 24px 12px',
          'borderBottom': '1px solid #222'}),

html.Div([
    html.Div([
        html.Label('Year',style={'fontSize':'12px',
                                 'color':'#aaa'}),
        dcc.Dropdown(
            id='year-dd',
            options = [{'label':y,'value':y}
                       for y in range(2015,2026)],
            value=2024,
            clearable=False,
            style={'fontSize':'13px'}
        )
    ], style={'flex':'1','minWidth':'80px'}),

    html.Div([
        html.Label("Grand Prix",
                   style={'fontSize':'12px',
                          'color':'#aaa'}),
        dcc.Dropdown(
            id='gp-dd',
            options=[{'label':g,'value':g}
                     for g in GPS],
            value='Las Vegas',
            clearable=False,
            style={'fontSize':'13px'}
        )
    ], style={'flex':'2','minWidth':'140px'}),

    html.Div([
        html.Label("Session",
                   style={'fontSize':'12px',
                          'color':'#aaa'}),
        dcc.Dropdown(
            id='session-dd',
            options=[
                {'label':'Qualifying','value':'Q'},
                {'label':'Race',      'value':'R'},
                {'label':'FP1',      'value':'FP1'},
                {'label':'FP2',      'value':'FP2'},
                {'label':'FP3',      'value':'FP3'},
            ],
            value='Q',
            clearable=False,
            style={'fontSize':'13px'}
        )


    ], style={'flex':'1', 'minWidth':'110px'}),

    html.Div([
        html.Button("Load Session",
                    id='load-btn',
                    n_clicks=0,
                    style={
                        'background':'#E10600',
                        'color':'white',
                        'border':'none',
                        'padding':'8px 18px',
                        'borderRadius': '4px',
                        'cursor':'pointer',
                        'fontSize':'13px',
                        'marginTop':'18px'
                    })
    ]),
], style={
    'display':'flex','gap':'12px',
    'padding':'16px 24px',
    'alignItems':'flex-end',
    'background':'#111',
    'flexWrap':'wrap'
}),

html.Div(id='status-bar',style={
    'padding':'8px 24px',
    'fontSize':'12px',
    'color':'#888',
    'background':'#0a0a0a',
    'borderBottom':'1px solid #222'
}),

html.Div([
    html.Div([
        html.Label("Drivers",
                   style={'fontSize':'12px',
                          'Color':'#aaa',
                          'marginBottom':'6px',
                          'display':'block'}),
        dcc.Checklist(
            id='driver-checklist',
            options=[{'label':d,'value':d}
                     for d in Drivers_2024],
            value=['VER','HAM'],
            labelStyle={
                'display':'block',
                'fontSize':'13px',
                'color':'#ddd',
                'padding':'2px 0',
                'cursor':'pointer'
            }
        )
    ], style={
        'width':'130px',
        'flexShrink':'0',
        'padding':'16px',
        'background':'#111',
        'borderRight':'1px solid #222',
        'overflowY':'auto',
        'maxHeight':'600px'

    }),
    html.Div([
        html.Div([
            html.Label("Parameters",
                       style={'fontSize':'12px',
                              'color':'#aaa'}),
            dcc.Checklist(
                id='param-checklist',
                options=[
                    {'label':k,'value':v}
                    for k,v in PARAMETERS.items()
                ],
                value=['Speed'],
                labelStyle={
                    'display':'inline-block',
                    'fontSize':'13px',
                    'color': '#ddd',
                    'marginRight':'16px',
                    'cursor':'pointer'
                },
                style={'marginBottom':'12px'}
            ),                     
                      
        ],style={'padding':'12px 16px',
                 'borderBottom':'1px solid #222'}),
        html.Div([
            dcc.Graph(
                id='telemetry-graph',
                style={'height':'520px'},
                config={'displayModeBar':True,
                        'scrollZoom':True}
            )
        ], style={'padding':'8px'}),
    ], style={'flex':'1','minWidth':'0'}),

 ], style={'display':'flex',
           'flex':'1',
           'overflow':'hidden'}),
                 
], style={
    'background':'#0d0d0d',
    'minHeight':'100vh',
    'fontFamily':'monospace',
    'display':'flex',
    'flexDirection':'column'

})

# Session Cache
session_cache= {}

# Callback

@callback(
    Output('telemetry-graph','figure'),
    Output('status-bar','children'),
    Input('load-btn','n_clicks'),
    Input('driver-checklist','value'),
    Input('param-checklist','value'),
    Input('year-dd','value'),
    Input('gp-dd','value'),
    Input('session-dd','value'),
    prevent_initial_call=True
)
def update_graph(n_clicks, drivers,params,
                 year,gp, session_type):
    
    if not drivers or not params:
        fig= go.Figure()
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0d0d0d',
            plot_bgcolor='#111',
            title='Select at least one driver and parameter'
        )
        return fig, "Select drivers and parameters"
    cache_key = f"{year}_{gp}_{session_type}"

    if cache_key not in session_cache:
        try:
            sess = fastf1.get_session(year,gp,
                                      session_type)
            sess.load(telemetry=True, weather=False)
            session_cache[cache_key] = sess
            status = (f"Loaded:{year}{gp}"
                      f"{session_type}-"
                      f"{len(sess.laps)} laps")
        except Exception as e:
            fig = go.Figure()
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='#0d0d0d',
                plot_bgcolor='#111',
                title=f'Error loading session: {e}'
            )
            return fig, f"Error: {e}"

    else:
        sess = session_cache[cache_key]
        status = (f"Cached:{year}{gp}"
                  f"{session_type}")

    COLORS = [
        '#E10600','#00D2BE','#FF8700','#DC0000',
        '#0600EF','#005AFF','#006F62','#2B4562',
        '#FFFFFF','#FFF500','#C92D4B','#F596C8',
        '#B6BABD','#C8102E','#F0D787','#37BEDD',
        '#52E252','#FFA500','#FF69B4','#00FFFF'
    ]        
    
    rows = len(params)
        

   
    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=[
            list(PARAMETERS.keys())[
                list(PARAMETERS.values()).index(p)
            ] for p in params
        ]
    )

    for di, driver in enumerate(drivers):
        color = COLORS[di % len(COLORS)]
        try:
            lap = (sess.laps
                   .pick_driver(driver)
                   .pick_fastest())
            tel = lap.get_telemetry().add_distance()
            lap_t = lap['LapTime'].total_seconds()

            for pi, param in enumerate(params):
                if param not in tel.columns:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=tel['Distance'],
                        y=tel[param],
                        name=(f"{driver}"
                              f"{lap_t:.3f}s"
                              if pi ==0
                              else driver),
                        line=dict(color=color,
                                  width=1.8),
                        showlegend=(pi == 0),
                        legendgroup=driver,                             
                    ),
                    row=pi+1, col=1
                )

        except Exception:
            continue

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d0d0d',
        plot_bgcolor='#111',
        font=dict(family='monospace',
                  color='#ddd', size=11),

        legend=dict(
            bgcolor='#1a1a1a',
            bordercolor='#333',
            borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(l=60, r=20, t=40, b=40),
        hovermode='x unified'
    
    )

    fig.update_xaxes(
        title_text='Distance(m)',
        gridcolor='#222',
        row=rows, col=1
    )    
    
    return fig,status
# Run

if __name__ == '__main__':
    print("\n F1 Telemetry Dashboard starting....")
    print("Open browser at : http://127.0.0.1:8050\n")
    app.run(debug=True)    