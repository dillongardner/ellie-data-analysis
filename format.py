import re

import polars as pl
import constants


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
        pl.col("Line Number"),
        "terminal_level",
        "full_pattern",
        pl.col("selection").str.replace("  ", " ").alias("selection"),
    ).filter(
        pl.col("full_pattern").is_not_null()
    ).with_columns(
        str_length=pl.col("full_pattern").str.len_chars()
    ).with_columns(
        menu_pattern=pl.col("full_pattern").str.slice(0, pl.col("str_length") - 1),
        button=pl.col("full_pattern").str.slice(-1)
    ).select(
        "Line Number",
        "full_pattern",
        "menu_pattern",
        "button",
        "selection",
    )
    return _add_board_columns(df)


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


def _add_board_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Expects a dataframe with columns
    full_pattern
    menu_pattern
    button
    selection
    :param df:
    :return:
    full_pattern
    menu_pattern
    button
    selection
    menu_title
    is_menu
    """
    menus = df.select(
        "full_pattern",
        "selection"
    ).join(
        df.select("menu_pattern", pl.col("full_pattern").alias("TMP")),
        how="semi",
        left_on="full_pattern",
        right_on="menu_pattern"
    ).select(
        "full_pattern",
        pl.lit(True).alias("is_menu"),
        pl.col("full_pattern").len().over("selection").alias("menu_multiplicity")
    )

    result = (df.join(
        df.select(
            "full_pattern", pl.col("selection").alias("menu_title")
        ),
        how="left",
        left_on="menu_pattern",
        right_on="full_pattern"
    ).with_columns(
        menu_title=pl.when(pl.col("menu_title").is_not_null()).then(pl.col("menu_title")).when(
            pl.col("full_pattern").str.len_chars() == 1).then(pl.lit("MAIN MENU")).otherwise(pl.lit("UNKNOWN"))
    ).join(
        menus, how="left", on="full_pattern"
    ).with_columns(
        pl.col("is_menu").fill_null(value=pl.lit(False)).alias("is_menu"),
    ).with_columns(
        pl.col("full_pattern").len().over("selection", "is_menu").alias("multiplicity")
    )
    )
    return result


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
        pl.col("Location path code").alias("full_pattern"),
        terminal_level.str.to_uppercase().alias("selection")
    ).filter(
        pl.col("full_pattern").is_not_null()
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
    return _add_board_columns(df)


def format_selections(df: pl.DataFrame) -> pl.DataFrame:
    """

    :param df: requires column "Word/Phrase" and "Menu"
    :return: dataframe with column "selection" and "row_number"
    """
    if "Destination Word" in df.columns:
        # Column name for selection of board 1
        df = df.rename({"Destination Word": "Word/Phrase"})
    terminal_press = pl.coalesce(pl.col("Word/Phrase"), pl.col("Menu"))
    source = pl.when(pl.col("Word/Phrase").is_not_null()).then(pl.lit("FINAL")).otherwise(pl.lit("MENU"))
    result = df.with_columns(
        terminal_press.str.to_uppercase().alias("selection"),
        source.alias("source"),
    ).filter(
        pl.col("selection").is_not_null()
    ).select(pl.col("Line Number"),
             pl.col("Location path code"),
             (pl.col("selection").str.strip_chars()
              .str.replace("  ", " ")
              .str.replace("BEETHOVEN AND DVORAK", "BEETHOVEN & DVORAK")
              .alias("selection")),
             "source",
             pl.col("Word/Phrase").alias("word"),
             pl.col("Menu").str.to_uppercase().alias("menu"),
             pl.col("Menu").forward_fill().str.to_uppercase().alias("menu_ff"),
             )
    return result


def combine(selections: pl.DataFrame, board: pl.DataFrame) -> pl.DataFrame:
    """
    Joins the selection to the board
    This is done by
    1. if there is a manual inputted pattern in "Location path code" - called CODE_MATCH
    2. if selection type (meaning is a MENU or FINAL) has a multiplicity of 1 - called UNIQUE_MATCH
    3. if selection type is final and last pressed menu by Ellie uniquely defines - called FORWARD_FILL
    """
    code_match = (
            pl.col("Location path code") == pl.col("full_pattern")
    )
    unique_match = (
            (pl.col("selection") == pl.col("selection_right"))
            & (pl.col("multiplicity") == 1)
            & (
                    (
                            (pl.col("source") == pl.lit("MENU")) & (pl.col("is_menu"))
                    )
                    | (
                            (pl.col("source") == pl.lit("FINAL")) & (~pl.col("is_menu"))
                    )
            )
    )
    forward_fill = (
            (pl.col("source") == pl.lit("FINAL"))
            & (~pl.col("is_menu"))
            & (pl.col("selection") == pl.col("selection_right"))
            & (pl.col("menu_ff") == pl.col("menu_title"))
            & (pl.col("menu_multiplicity") == 1)
    )

    df: pl.LazyFrame = selections.lazy().join(
        board.lazy(), how="cross"
    ).with_columns(
        (code_match | unique_match | forward_fill).alias("is_match"),
        (pl.when(code_match).then(pl.lit("CODE_MATCH"))
         .when(unique_match).then(pl.lit("UNIQUE_MATCH"))
         .when(forward_fill).then(pl.lit("FORWARD_FILL"))
         .otherwise(pl.lit("NONE")).alias("match_type")),
    )
    matches = df.filter((pl.col("is_match"))
                        ).collect().select(constants.FULL_SELECTIONS_COLS
                                           )
    unmatched = selections.join(
        matches.select("Line Number"), how="anti", on="Line Number"
    ).with_columns(
        *[pl.lit(None).alias(c) for c in constants.FULL_SELECTIONS_COLS if c not in constants.FORMATTED_SELECTIONS_COL]
    )
    print(f"matched length is {len(matches)}")
    print(f"unmatched length is {len(unmatched)}")
    print(f"selection length is {len(selections)}")
    result = matches.vstack(
        unmatched
    ).with_columns(
        pl.col("is_match").fill_null(pl.lit(False)).alias("is_match"),
    ).sort(
        "Line Number"
    )
    if (len(result) != len(selections)) or (not (result["Line Number"] == selections["Line Number"]).all()):
        print("WARNING: LINE NUMBERS DO NOT MATCH")
    return result
