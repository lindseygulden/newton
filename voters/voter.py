import dash
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import geopandas as gpd
import pandas as pd
from utils.io import yaml_to_dict
import click
import logging


logging.basicConfig(level=logging.INFO)


@click.command()
@click.argument("config_path", type=click.Path(exists=True))
def voter(config_path):

    config = yaml_to_dict(config_path)

    logging.info(f" --- Configuration file read from {config_path}")
    logging.info(
        f" --- Initializing Dash app using Ward {config['ward']} from voter data at {config['voter_locations']}"
    )

    voter_gdf = gpd.read_file(config["voter_locations"])

    # Add unique ID
    voter_df = pd.DataFrame(voter_gdf.drop(columns="geometry"))

    # get the right ward
    voter_df = voter_df.loc[(voter_df.ward.isin(config["ward"]))]

    # subset the voters to get rid of the exclude politics
    voter_df = voter_df.loc[~voter_df.politics.isin(config["exclude_politics"])]

    # mark the voters to include, starting with politics
    voter_df["includes"] = [
        1 if i in config["include_politics"] else 0 for i in voter_df.politics
    ]

    # also mark the other 'includes'
    for inc in config["include_boolean"]:
        voter_df["includes"] = [
            1 if i == 1 else x for i, x in zip(voter_df[inc], voter_df.includes)
        ]

    # mark the excludes
    voter_df["excludes"] = 0
    for exclude in config["exclude_boolean"]:
        voter_df["excludes"] = [
            1 if e == 1 else x for e, x in zip(voter_df[exclude], voter_df.excludes)
        ]

    # get the includes
    voter_df = voter_df.loc[voter_df.includes == 1]

    # remove the excludes
    voter_df = voter_df.loc[voter_df.excludes == 0]

    # get the UID
    voter_df["uid"] = voter_df.index
    # Initialize Dash app
    app = Dash(__name__)

    app.layout = html.Div(
        [
            html.H3("Lasso-select points on map"),
            # Move the export button and output above the map
            html.Div(
                [
                    html.Button("Export Selected to CSV", id="export-btn", n_clicks=0),
                    html.Div(id="output", style={"marginTop": "10px"}),
                ],
                style={"marginBottom": "20px"},
            ),
            dcc.Graph(id="map", config={"scrollZoom": True}),
            # Hidden data stores
            dcc.Store(id="voter-data", data=voter_df.to_dict("records")),
            dcc.Store(id="selected-ids", data=[]),
            dcc.Store(id="export-count", data=0),
            dcc.Store(id="exported-ids", data=[]),
        ]
    )

    @app.callback(
        Output("map", "figure"),
        Input("voter-data", "data"),
        Input("exported-ids", "data"),
    )
    def update_map(voter_data, exported_ids):
        df = pd.DataFrame(voter_data)
        if exported_ids:
            df = df[~df["uid"].isin(exported_ids)]
        fig = px.scatter_map(
            df,
            lat="lat",
            lon="lon",
            hover_name=config["hover_name"],
            hover_data={"voter_id_number": True, "uid": True, "fullname": False},
            zoom=12,
            height=900,
            color="politics",
        )
        fig.update_layout(mapbox_style="basic")
        fig.update_traces(marker=dict(size=5))
        fig.update_layout(clickmode="event+select", dragmode="lasso")
        return fig

    @app.callback(
        Output("selected-ids", "data"),
        Output("output", "children"),
        Input("map", "selectedData"),
        State("voter-data", "data"),
    )
    def on_select(selected_data, voter_data):
        if not selected_data:
            return [], "No points selected."

        df = pd.DataFrame(voter_data)

        # Extract 'uid' directly from selected points
        selected_ids = [
            p["customdata"][1] if "customdata" in p else p["hoverdata"]["uid"]
            for p in selected_data["points"]
        ]
        selected_df = df[df["uid"].isin(selected_ids)]

        selected_names = selected_df["fullname"].tolist()

        return (
            selected_ids,
            f"✅ Selected {len(selected_ids)} point(s): {', '.join(selected_names)}",
        )

    @app.callback(
        Output("voter-data", "data"),
        Output("exported-ids", "data"),
        Output("export-btn", "children"),
        Output("export-count", "data"),
        Input("export-btn", "n_clicks"),
        State("selected-ids", "data"),
        State("voter-data", "data"),
        State("exported-ids", "data"),
        State("export-count", "data"),
        prevent_initial_call=True,
    )
    def export_selected(
        n_clicks, selected_ids, current_data, exported_ids, export_count
    ):
        if not selected_ids:
            return dash.no_update, dash.no_update, "⚠️ No points to export", export_count

        df = pd.DataFrame(current_data)
        selected_df = df[df["uid"].isin(selected_ids)]

        # Write file
        export_count += 1
        filename = f"{config['output_file_path']}/{config['output_file_prefix']}{export_count}.csv"
        selected_df.to_csv(filename, index=False)
        logging.info(f" --- >>> Wrote voter extract to {filename}")
        # Update list of exported IDs
        updated_exported_ids = list(set(exported_ids + selected_ids))

        return (
            current_data,
            updated_exported_ids,
            f"📁 Exported {len(selected_df)} to selected_points_{export_count}.csv",
            export_count,
        )

    logging.info(
        " --- Newton Voter Dash app is running. To see the Dash app, go to http://127.0.0.1:8050/ in an html browser window"
    )
    app.run(debug=True)


if __name__ == "__main__":
    voter()
