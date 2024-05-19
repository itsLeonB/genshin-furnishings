import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"], server_api=ServerApi("1"))


client = init_connection()
db = client.furnishings
credentials = list(db.usernames.find())


def transform_users(users):
    result = {"usernames": {}}
    for user in users:
        username = user.pop("username")
        result["usernames"][username] = user
    return result


credentials = transform_users(credentials)

authenticator = stauth.Authenticate(
    credentials,
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
)

authenticator.login()

if st.session_state["authentication_status"]:
    characters = pd.DataFrame(db.characters.find({}, {"character_name": 1, "_id": 0}))
    materials = pd.DataFrame(db.materials.find({}, {"name": 1, "_id": 0}))
    furnishings = pd.DataFrame(db.furnishings.find({}, {"name": 1, "_id": 0}))
    sets = pd.DataFrame(db.sets.find({}, {"name": 1, "characters": 1, "_id": 0}))
    sets = sets.explode("characters")
    sets = sets.sort_values("name")

    inventory = db.inventory
    user_inventory = inventory.find_one({"username": st.session_state["username"]})

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
    chars_list.owned = chars_list.owned.fillna(False)
    mats_list = pd.merge(materials, owned_mats, on="name", how="left")
    mats_list.quantity = mats_list.quantity.fillna(0)
    furn_list = pd.merge(furnishings, owned_furn, on="name", how="left")
    furn_list.quantity = furn_list.quantity.fillna(0)
    sets_list = pd.merge(sets, owned_sets, on=["name", "characters"], how="left")
    sets_list.claimed = sets_list.claimed.fillna(False)

    st.title("Genshin Furnishing Helper")
    st.write(
        "This app helps to identify needed furnishings to craft/buy and materials required for claiming gift sets."
    )
    st.write("Start by selecting the characters, materials, and furnishings you own.")
    st.write("Then check the gift sets you have claimed rewards for.")
    st.write(
        "Finally, click the 'Calculate requirements' on the Requirements tab to see the needed furnishings and materials."
    )

    char_tab, mat_tab, furn_tab, sets_tab, calc_tab = st.tabs(
        ["Characters", "Materials", "Furnishings", "Sets", "Requirements"]
    )

    with char_tab:
        st.header("Characters")
        char_df = st.data_editor(
            chars_list,
            column_config={
                "owned": st.column_config.CheckboxColumn(
                    "Owned?",
                    help="Select your **owned** characters",
                    default=False,
                )
            },
            disabled=["character_name"],
            hide_index=True,
        )

        if st.button("Save changes", key="save_chars", type="primary"):
            chars = char_df.set_index("character_name")["owned"].to_dict()
            result = inventory.update_one(
                {"username": st.session_state["username"]},
                {"$set": {"characters": chars}},
            )

            if result.matched_count > 0:
                st.success("Data successfully updated!")
            else:
                st.error("Data update failed!")

    with mat_tab:
        st.header("Materials")
        mat_df = st.data_editor(
            mats_list,
            column_config={
                "quantity": st.column_config.NumberColumn(
                    "Quantity owned",
                    help="Quantity of the materials you own",
                    min_value=0,
                    max_value=20000,
                    step=1,
                )
            },
            disabled=["name"],
            hide_index=True,
        )

        if st.button("Save changes", key="save_mats", type="primary"):
            mats = mat_df.set_index("name")["quantity"].to_dict()
            result = inventory.update_one(
                {"username": st.session_state["username"]},
                {"$set": {"materials": mats}},
            )

            if result.matched_count > 0:
                st.success("Data successfully updated!")
            else:
                st.error("Data update failed!")

    with furn_tab:
        st.header("Furnishings")
        furn_df = st.data_editor(
            furn_list,
            column_config={
                "quantity": st.column_config.NumberColumn(
                    "Quantity owned",
                    help="Quantity of the furnishings you own",
                    min_value=0,
                    max_value=20000,
                    step=1,
                )
            },
            disabled=["name"],
            hide_index=True,
        )

        if st.button("Save changes", key="save_furn", type="primary"):
            furn = furn_df.set_index("name")["quantity"].to_dict()
            result = inventory.update_one(
                {"username": st.session_state["username"]},
                {"$set": {"furnishings": furn}},
            )

            if result.matched_count > 0:
                st.success("Data successfully updated!")
            else:
                st.error("Data update failed!")

    with sets_tab:
        st.header("Gift Sets")
        sets_df = st.data_editor(
            sets_list,
            column_config={
                "claimed": st.column_config.CheckboxColumn(
                    "Claimed?",
                    help="Check the characters you have claimed rewards for",
                    default=False,
                )
            },
            disabled=["name", "characters"],
            hide_index=True,
        )

        if st.button("Save changes", key="save_sets", type="primary"):
            # Get unique values of 'name' column
            unique_names = sets_df["name"].unique()

            # Create the array
            sets = []
            for name in unique_names:
                subset_df = sets_df[sets_df["name"] == name]
                character_info = {
                    char: claimed
                    for char, claimed in zip(
                        subset_df["characters"], subset_df["claimed"]
                    )
                }
                sets.append(
                    {
                        "name": name,
                        "characters": character_info,
                    }
                )

            result = inventory.update_one(
                {"username": st.session_state["username"]}, {"$set": {"sets": sets}}
            )

            if result.matched_count > 0:
                st.success("Data successfully updated!")
            else:
                st.error("Data update failed!")

    with calc_tab:
        st.header("Requirements")
        if st.button("Calculate requirements", key="calc", type="primary"):
            owned_chars_true = char_df[char_df["owned"] == True]
            unclaimed_sets = sets_df[sets_df["claimed"] == False]
            unclaimed_sets = unclaimed_sets[
                unclaimed_sets["characters"].isin(owned_chars_true["character_name"])
            ]
            unclaimed_sets = unclaimed_sets.name.unique().tolist()
            gift_sets = pd.DataFrame(db.sets.find({"name": {"$in": unclaimed_sets}}))

            needed_furns = gift_sets.explode("materials")

            # Extract the 'name', 'recipe', and 'amount' fields from the 'materials' column
            needed_furns["material_name"] = needed_furns["materials"].apply(
                lambda x: x["name"]
            )
            needed_furns["recipe"] = needed_furns["materials"].apply(
                lambda x: x["recipe"]
            )
            needed_furns["amount"] = needed_furns["materials"].apply(
                lambda x: x["amount"]
            )

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
            needed_furns = needed_furns[
                needed_furns["amount"] >= needed_furns["quantity"]
            ]
            needed_furns["amount"] = needed_furns["amount"] - needed_furns["quantity"]
            needed_furns = needed_furns[needed_furns["amount"] > 0]

            mask = needed_furns["recipe"].apply(lambda x: x == [])
            buy_furns = needed_furns[mask]
            needed_furns = needed_furns[~mask]

            st.subheader("Furnishings to craft:")
            st.dataframe(needed_furns[["name", "amount"]].reset_index(drop=True))

            st.subheader("Furnishings to buy:")
            st.dataframe(buy_furns[["name", "amount"]].reset_index(drop=True))

            # Explode the 'recipe' column and keep the 'amount' column
            needed_mats = needed_furns.explode("recipe").reset_index()

            # Extract the 'name' and 'quantity' fields from the 'recipe' column
            needed_mats["name"] = needed_mats["recipe"].apply(lambda x: x["name"])
            needed_mats["quantity"] = needed_mats["recipe"].apply(
                lambda x: x["quantity"]
            )

            # Multiply the 'quantity' by the 'amount'
            needed_mats["quantity"] *= needed_mats["amount"]

            # Select only the 'name' and 'quantity' columns
            needed_mats = (
                needed_mats[["name", "quantity"]].groupby("name").sum("quantity")
            )

            needed_mats = needed_mats.merge(
                mat_df, on="name", suffixes=("_needed", "_mat")
            )
            needed_mats["quantity_diff"] = (
                needed_mats["quantity_needed"] - needed_mats["quantity_mat"]
            )
            needed_mats = needed_mats[needed_mats["quantity_diff"] > 0]

            st.subheader("Materials needed:")
            st.dataframe(needed_mats[["name", "quantity_diff"]].reset_index(drop=True))


elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
