import click
import logging
from math import ceil
import pandas as pd
import warnings
from pathlib import Path
from utils.io import yaml_to_dict

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)


@click.command()
@click.argument("config_path", type=click.Path(exists=True))
def canvass(config_path):

    config = yaml_to_dict(config_path)

    logging.info(f" --- Configuration file read from {config_path}")
    voters_df = pd.read_csv(config["voter_file"])

    df_list = []
    for name, roadlist in config["roads"].items():
        out_list = []
        for s in roadlist:
            if isinstance(s, dict):
                streetname = list(s.keys())[0]
                numbers = list(s.values())[0]
                out_list.append(
                    voters_df.loc[
                        (voters_df[config["street_col"]] == streetname)
                        & (voters_df[config["street_number_col"]] >= numbers[0])
                        & (voters_df[config["street_number_col"]] <= numbers[1])
                    ]
                )
            else:
                out_list.append(voters_df.loc[(voters_df[config["street_col"]] == s)])
        out_df = pd.concat(out_list)
        out_df = out_df[config["write_out_cols"]].sort_values(
            by=config["groupby_cols"], ascending=True
        )
        out_df["canvass_list"] = name
        n = out_df.form_id.nunique()
        out_df.to_csv(
            Path(config["output_dir"]) / Path(name + f"_{n}_addresses.csv"), index=False
        )
        logging.info(f" --- Wrote canvass path {name}")
        df_list.append(out_df.copy())

    pd.concat(df_list).to_csv(
        Path(config["output_dir"]) / Path(config["list_generation_id"] + ".csv"),
        index=False,
    )


if __name__ == "__main__":
    canvass()
