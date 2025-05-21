import re

import polars as pl


def format_selections(df: pl.DataFrame) -> pl.DataFrame:
    """

    :param df: requires column "Word/Phrase" and "Menu"
    :return: dataframe with column "selection" and "row_number"
    """
    if "Destination Word" in df.columns:
        terminal_press = pl.coalesce(pl.col("Destination Word"), pl.col("Menu"))
    else:
        terminal_press = pl.coalesce(pl.col("Word/Phrase"), pl.col("Menu"))
    result = df.with_columns(
        terminal_press.str.to_uppercase().alias("selection")
    ).filter(
        pl.col("selection").is_not_null()
    ).select(pl.arange(0,pl.count()).alias("row_number"),
             (pl.col("selection").str.strip_chars()
              .str.replace("  ", " ")
              .str.replace("BEETHOVEN AND DVORAK", "BEETHOVEN & DVORAK")
              .alias("selection"))
             )
    return result


def format_boards(df: pl.DataFrame) -> pl.DataFrame:
    """
    Format the Board spreadsheet data.
    Expects each level column to be of the form "<full_pattern> <phrase>"
    :param df:
    :return dataframe with columns
    full_pattern
    menu_pattern
    button
    selection
    menu_title
    """
    terminal_level = create_level_coalesce(df)
    df = df.with_columns(
        terminal_level.alias("terminal_level")
    ).with_columns(
        pl.col("terminal_level").str.replace("\xa0", " ", n=-1).str.splitn(" ", 2).alias("splits")
    ).with_columns(
        pl.col("splits").struct.field("field_0").alias("full_pattern"),
        pl.col("splits").struct.field("field_1").str.strip_chars().str.to_uppercase().alias("selection"),
    ).select(
        "terminal_level",
        "full_pattern",
        pl.col("selection").str.replace("  ", " ").alias("selection"),
    ).with_columns(
        str_length=pl.col("full_pattern").str.len_chars()
    ).with_columns(
        menu_pattern=pl.col("full_pattern").str.slice(0, pl.col("str_length") - 1),
        button=pl.col("full_pattern").str.slice(-1)
    ).select(
        "full_pattern",
        "menu_pattern",
        "button",
        "selection",
    )
    result = df.join(
        df.select(
            "full_pattern", pl.col("selection").alias("menu_title")
        ),
        how="left",
        left_on="menu_pattern",
        right_on="full_pattern"
    ).with_columns(
        menu_title=pl.col("menu_title").fill_null(value="MAIN MENU")
    )

    return result


def create_level_coalesce(df):
    l_cols = [
        col for col in df.columns
        if re.fullmatch(r"L\d+", col)
    ]
    l_cols_sorted = sorted(
        l_cols,
        key=lambda x: int(x[1:]),
        reverse=True
    )
    terminal_level = pl.coalesce(*[pl.col(c) for c in l_cols_sorted])
    return terminal_level


def format_board_v1(df: pl.DataFrame) -> pl.DataFrame:
    """
    Expects a "lookup code" column and each level column to consist of just the phrase
    :param df:
    :return dataframe with columns
    full_pattern
    menu_pattern
    button
    selection
    menu_title
    """
    terminal_level = create_level_coalesce(df)
    df = df.select(
        pl.col("Lookup code").alias("full_pattern"),
        terminal_level.alias("selection")
    ).with_columns(
        str_length=pl.col("full_pattern").str.len_chars()
    ).with_columns(
        menu_pattern=pl.col("full_pattern").str.slice(0, pl.col("str_length") - 1),
        button=pl.col("full_pattern").str.slice(-1)
    ).select(
        "full_pattern",
        "menu_pattern",
        "button",
        "selection",
    )
    result = df.join(
        df.select(
            "full_pattern", pl.col("selection").alias("menu_title")
        ),
        how="left",
        left_on="menu_pattern",
        right_on="full_pattern"
    ).with_columns(
        menu_title=pl.col("menu_title").fill_null(value="MAIN MENU")
    )
    return result
