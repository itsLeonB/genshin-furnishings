from typing import Union, Tuple
import pandas as pd
import streamlit as st
import pymongo
import pymongo.database
import pymongo.collection
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient


@st.cache_resource
def init_connection() -> MongoClient:
    return MongoClient(st.secrets["mongo"]["uri"], server_api=ServerApi("1"))


def get_data() -> Tuple[
    pymongo.collection.Collection,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    client = init_connection()
    db = client.furnishings

    characters = pd.DataFrame(db.characters.find({}, {"character_name": 1, "_id": 0}))
    materials = pd.DataFrame(db.materials.find({}, {"name": 1, "_id": 0}))
    furnishings = pd.DataFrame(db.furnishings.find({}, {"name": 1, "_id": 0}))
    sets = pd.DataFrame(db.sets.find({}, {"name": 1, "characters": 1, "_id": 0}))
    sets = sets.explode("characters")
    sets = sets.sort_values("name")

    inventory = db.inventory
    user_inventory = inventory.find_one(
        {"user_id": st.session_state.user_info["localId"]}
    )

    if user_inventory is None:
        user_inventory = {
            "user_id": st.session_state.user_info["localId"],
            "characters": {char: False for char in characters["character_name"]},
            "materials": {mat: 0 for mat in materials["name"]},
            "furnishings": {furn: 0 for furn in furnishings["name"]},
            "sets": [],
        }
        inventory.insert_one(user_inventory)

    owned_chars = pd.DataFrame(
        list(user_inventory["characters"].items()), columns=["character_name", "owned"]
    )
    owned_mats = pd.DataFrame(
        list(user_inventory["materials"].items()), columns=["name", "quantity"]
    )
    owned_furn = pd.DataFrame(
        list(user_inventory["furnishings"].items()), columns=["name", "quantity"]
    )
    owned_sets = user_inventory["sets"]
    set_inv = []
    for set in owned_sets:
        for character, claimed in set["characters"].items():
            set_inv.append([set["name"], character, claimed])
    owned_sets = pd.DataFrame(set_inv, columns=["name", "characters", "claimed"])

    chars_list = pd.merge(characters, owned_chars, on="character_name", how="left")
    chars_list.owned = chars_list.owned.fillna(False).infer_objects(copy=False)
    mats_list = pd.merge(materials, owned_mats, on="name", how="left")
    mats_list.quantity = mats_list.quantity.fillna(0).infer_objects(copy=False)
    furn_list = pd.merge(furnishings, owned_furn, on="name", how="left")
    furn_list.quantity = furn_list.quantity.fillna(0).infer_objects(copy=False)
    sets_list = pd.merge(sets, owned_sets, on=["name", "characters"], how="left")
    sets_list.claimed = sets_list.claimed.fillna(False).infer_objects(copy=False)

    return (inventory, chars_list, mats_list, furn_list, sets_list)


def update_chars(
    inventory: pymongo.collection.Collection, char_df: pd.DataFrame
) -> bool:
    chars = char_df.set_index("character_name")["owned"].to_dict()
    result = inventory.update_one(
        {"user_id": st.session_state.user_info["localId"]},
        {"$set": {"characters": chars}},
    )

    return True if result.matched_count > 0 else False


def update_mats(inventory: pymongo.collection.Collection, mat_df: pd.DataFrame) -> bool:
    mats = mat_df.set_index("name")["quantity"].to_dict()
    result = inventory.update_one(
        {"user_id": st.session_state.user_info["localId"]},
        {"$set": {"materials": mats}},
    )

    return True if result.matched_count > 0 else False


def update_furns(
    inventory: pymongo.collection.Collection, furn_df: pd.DataFrame
) -> bool:
    furn = furn_df.set_index("name")["quantity"].to_dict()
    result = inventory.update_one(
        {"user_id": st.session_state.user_info["localId"]},
        {"$set": {"furnishings": furn}},
    )

    return True if result.matched_count > 0 else False


def update_sets(
    inventory: pymongo.collection.Collection, sets_df: pd.DataFrame
) -> bool:
    # Get unique values of 'name' column
    unique_names = sets_df["name"].unique()

    # Create the array
    sets = []
    for name in unique_names:
        subset_df = sets_df[sets_df["name"] == name]
        character_info = {
            char: claimed
            for char, claimed in zip(subset_df["characters"], subset_df["claimed"])
        }
        sets.append(
            {
                "name": name,
                "characters": character_info,
            }
        )

    result = inventory.update_one(
        {"user_id": st.session_state.user_info["localId"]},
        {"$set": {"sets": sets}},
    )

    return True if result.matched_count > 0 else False


def calculate_requirements(
    char_df: pd.DataFrame,
    sets_df: pd.DataFrame,
    furn_df: pd.DataFrame,
    mat_df: pd.DataFrame,
    db: pymongo.database.Database,
) -> Union[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame], None]:
    owned_chars_true = char_df[char_df["owned"] == True]
    unclaimed_sets = sets_df[sets_df["claimed"] == False]
    unclaimed_sets = unclaimed_sets[
        unclaimed_sets["characters"].isin(owned_chars_true["character_name"])
    ]
    unclaimed_sets = unclaimed_sets.name.unique().tolist()
    gift_sets = pd.DataFrame(db.sets.find({"name": {"$in": unclaimed_sets}}))

    if not gift_sets.empty:
        needed_furns = gift_sets.explode("materials")

        # Extract the 'name', 'recipe', and 'amount' fields from the 'materials' column
        needed_furns["material_name"] = needed_furns["materials"].apply(
            lambda x: x["name"]
        )
        needed_furns["recipe"] = needed_furns["materials"].apply(lambda x: x["recipe"])
        needed_furns["amount"] = needed_furns["materials"].apply(lambda x: x["amount"])

        # Create a new DataFrame with only the 'material_name', 'recipe', and 'amount' columns
        needed_furns = needed_furns[["material_name", "recipe", "amount"]]
        idx = (
            needed_furns.groupby("material_name")["amount"].transform("max")
            == needed_furns["amount"]
        )
        needed_furns = needed_furns[idx]

        # Merge gift_sets and furn_df on 'material_name'
        needed_furns = pd.merge(
            needed_furns,
            furn_df[["name", "quantity"]],
            left_on="material_name",
            right_on="name",
            how="left",
        )

        # Filter rows where 'amount' is >= 'quantity'
        needed_furns = needed_furns[needed_furns["amount"] >= needed_furns["quantity"]]
        needed_furns["amount"] = needed_furns["amount"] - needed_furns["quantity"]
        needed_furns = needed_furns[needed_furns["amount"] > 0]

        mask = needed_furns["recipe"].apply(lambda x: x == [])
        buy_furns = needed_furns[mask]
        needed_furns = needed_furns[~mask]

        # Explode the 'recipe' column and keep the 'amount' column
        needed_mats = needed_furns.explode("recipe").reset_index()

        # Extract the 'name' and 'quantity' fields from the 'recipe' column
        needed_mats["name"] = needed_mats["recipe"].apply(lambda x: x["name"])
        needed_mats["quantity"] = needed_mats["recipe"].apply(lambda x: x["quantity"])

        # Multiply the 'quantity' by the 'amount'
        needed_mats["quantity"] *= needed_mats["amount"]

        # Select only the 'name' and 'quantity' columns
        needed_mats = needed_mats[["name", "quantity"]].groupby("name").sum("quantity")

        needed_mats = needed_mats.merge(mat_df, on="name", suffixes=("_needed", "_mat"))
        needed_mats["quantity_diff"] = (
            needed_mats["quantity_needed"] - needed_mats["quantity_mat"]
        )
        needed_mats = needed_mats[needed_mats["quantity_diff"] > 0]

        return (needed_furns, buy_furns, needed_mats)
    else:
        return None
