import dash
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import geopandas as gpd
import pandas as pd


WARD = 6
VOTER_LOCATIONS = "/Users/lindseygulden/Desktop/voters.geojson"
STREETS = (
    "/Volumes/T5_External/data/newton/map/GISData/Streets/StreetCenterLines.geojson"
)
voter_gdf = gpd.read_file(VOTER_LOCATIONS)
street_gdf = gpd.read_file(STREETS)

# Add unique ID
voter_df = pd.DataFrame(voter_gdf.drop(columns="geometry"))
voter_df = voter_df.loc[(voter_df.politics != "right") & (voter_df.ward == WARD)]
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
        hover_name="fullname",
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
def export_selected(n_clicks, selected_ids, current_data, exported_ids, export_count):
    if not selected_ids:
        return dash.no_update, dash.no_update, "⚠️ No points to export", export_count

    df = pd.DataFrame(current_data)
    selected_df = df[df["uid"].isin(selected_ids)]

    # Write file
    export_count += 1
    filename = f"~/Desktop/selected_points_{export_count}.csv"
    selected_df.to_csv(filename, index=False)

    # Update list of exported IDs
    updated_exported_ids = list(set(exported_ids + selected_ids))

    return (
        current_data,
        updated_exported_ids,
        f"📁 Exported {len(selected_df)} to selected_points_{export_count}.csv",
        export_count,
    )


if __name__ == "__main__":
    app.run(debug=True)
