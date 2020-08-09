import base64
import collections
import functools
import glob
import io
import logging
import ntpath
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from sklearn import preprocessing

from utils.lru_cache import lru_cache

LOG_DIR = os.getenv('LOG_DIR', './examples')
GB = 1024**3

logger = logging.getLogger(__file__)

POWER_SUPPLY_FIELD = 'Ion Beam Source - Process Power Supply: Forward power'
DEFAULT_FILTER_FIELDS = set([
    POWER_SUPPLY_FIELD,
    'Drives - Target Change Drive: Position',
    'Optical Measuring System - OMS5k: Derivative',
    'Optical Measuring System - OMS5k: Intensity',
    'Optical Measuring System - OMS5k: Layer number',
    'Optical Measuring System - OMS5k: Monitor wavelength',
    'Optical Measuring System - OMS5k: Next turning point',
    'Optical Measuring System - OMS5k: Second turning point'
])


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def first_nonzero(arr, axis, invalid_val=-1):
    mask = arr != 0
    return np.where(mask.any(axis=axis), mask.argmax(axis=axis), invalid_val)


def get_fields(df):
    return list(df.columns.values.tolist())


@lru_cache(use_memory_up_to=(1 * GB))
def load_dataframe(filename):
    print(f'Loading dataframe with filename={filename}')
    df = pd.read_csv(filename, index_col=False, low_memory=False)
    df.rename(columns=lambda x: x.strip(), inplace=True)
    fields = get_fields(df)
    df.set_index(fields[0], inplace=True)
    df.index = pd.to_datetime(df.index).strftime("%H:%M:%S%z %Y-%m-%d")
    print(f'Dataframe with filename={filename} loaded')
    return df


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.H1(children='Logly'),

    html.Div(children='''
        Plot large time series data sets.
    '''),

    dcc.Store(id='filtered-output'),
    html.Div(id='output-display'),
    html.Div(id='page-load'),
    dcc.Dropdown(
        id='file-dropdown',
        options=[],
        value=None
    ),
    dcc.Dropdown(
        id='memory-fields',
        options=[],
        multi=True,
        value=[]),
    dcc.Dropdown(
        id='normalized-flag',
        options=[{'label': 'Normalized', 'value': 'Normalized'},
                 {'label': 'Raw', 'value': 'Raw'}],
        value='Raw'),
    dcc.Dropdown(
        id='power-flag',
        options=[{'label': 'Display all', 'value': 'All'},
                 {'label': 'From power on', 'value': 'Power'}],
        value='Power'),
    dcc.Graph(id='example-graph',
              figure={
                  "data": [],
                  "layout": {
                      "title": "Log Data",
                      "height": 450,  # px
                  }
              })
])


@app.callback(Output('file-dropdown', 'options'),
              [Input('page-load', 'children')])
def update_file_dropdown(_):
    return [{'label': path_leaf(path), 'value': path}
            for path in glob.glob(f"{LOG_DIR}/*log*.csv")]


@app.callback(Output('example-graph', 'figure'),
              [Input('memory-fields', 'value'), Input('file-dropdown', 'value'), Input('normalized-flag', 'value'), Input('power-flag', 'value')])
def filter_fields(fields_selected, filename, normalized_flag, power_flag):
    normalized = (normalized_flag == 'Normalized')
    if not fields_selected or not filename:
        # Return all the rows on initial load/no country selected.
        raise PreventUpdate

    df = load_dataframe(filename)

    if power_flag == 'Power' and POWER_SUPPLY_FIELD in df.columns.values.tolist():
        power_supply_values = df[POWER_SUPPLY_FIELD].to_numpy()
        first = first_nonzero(power_supply_values, axis=0, invalid_val=-1)
        starting_point = first.min()
    else:
        starting_point = 0

    df = df[starting_point:]

    filtered = df[[field for field in fields_selected]]

    if normalized:
        x = filtered.values  # returns a numpy array
        min_max_scaler = preprocessing.MinMaxScaler()
        x_scaled = min_max_scaler.fit_transform(x)
        normalized = pd.DataFrame(
            x_scaled, columns=filtered.columns, index=filtered.index)
    else:
        normalized = None

    if normalized_flag == 'Normalized':
        main = normalized
        hover = filtered
    else:
        main = filtered
        hover = filtered

    print(type(main.index))
    response = {
        'data': [
            {
                'name': field,
                'mode': 'lines',
                'y': main[field].values.tolist(),
                'x': main.index.values.tolist(),
                'hovertext': hover[field].values.tolist()
            }
            for field in fields_selected
        ]
    }
    return response


@app.callback(Output('memory-fields', 'options'),
              [Input('file-dropdown', 'value')])
def update_filter_fields(log_file_path):

    if log_file_path is None:
        raise PreventUpdate

    df = load_dataframe(log_file_path)

    if df is not None:
        print('updating filter fields')
        fields = [{'value': field, 'label': field}
                  for field in get_fields(df)]
        print(
            f'updating filter fields with type={type(fields)}, {len(fields)}')
        return fields
    else:
        return []

@app.callback(Output('memory-fields', 'value'),
              [Input('memory-fields', 'options'), Input('file-dropdown', 'value')])
def set_default_filters(options, filename):
    if not options or not filename:
        return []

    defaults = [option['value']
                for option in options if option['value'] in DEFAULT_FILTER_FIELDS]
    print(f'setting filter defaults to defaults={defaults}')
    return defaults


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
