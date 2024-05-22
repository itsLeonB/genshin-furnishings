import auth
import streamlit as st
import data_controller as data


client = data.init_connection()
db = client.furnishings

st.title("Genshin Furnishing Helper")
st.write(
    "This app helps to identify needed furnishings to craft/buy and materials required for claiming gift sets."
)

if "user_info" not in st.session_state:
    # col1, col2, col3 = st.columns([1, 2, 1])
    st.divider()
    # Authentication form layout
    do_you_have_an_account = st.selectbox(
        label="Do you have an account?", options=("Yes", "No", "I forgot my password")
    )
    auth_form = st.form(key="Authentication form", clear_on_submit=False)
    email = auth_form.text_input(label="Email")
    password = (
        auth_form.text_input(label="Password", type="password")
        if do_you_have_an_account in {"Yes", "No"}
        else auth_form.empty()
    )
    auth_notification = st.empty()

    # Sign In
    if do_you_have_an_account == "Yes" and auth_form.form_submit_button(
        label="Sign In", use_container_width=True, type="primary"
    ):
        with auth_notification, st.spinner("Signing in"):
            auth.sign_in(email, password)

    # Create Account
    elif do_you_have_an_account == "No" and auth_form.form_submit_button(
        label="Create Account", use_container_width=True, type="primary"
    ):
        with auth_notification, st.spinner("Creating account"):
            auth.create_account(email, password)

    # Password Reset
    elif (
        do_you_have_an_account == "I forgot my password"
        and auth_form.form_submit_button(
            label="Send Password Reset Email", use_container_width=True, type="primary"
        )
    ):
        with auth_notification, st.spinner("Sending password reset link"):
            auth.reset_password(email)

    # Authentication success and warning messages
    if "auth_success" in st.session_state:
        auth_notification.success(st.session_state.auth_success)
        del st.session_state.auth_success
    elif "auth_warning" in st.session_state:
        auth_notification.warning(st.session_state.auth_warning)
        del st.session_state.auth_warning

else:
    st.write("Start by selecting the characters, materials, and furnishings you own.")
    st.write("Then check the gift sets you have claimed rewards for.")
    st.write(
        "Finally, click the 'Calculate requirements' on the Requirements tab to see the needed furnishings and materials."
    )

    char_tab, mat_tab, furn_tab, sets_tab, calc_tab = st.tabs(
        ["Characters", "Materials", "Furnishings", "Sets", "Requirements"]
    )

    (inventory, chars_list, mats_list, furn_list, sets_list) = data.get_data()

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
            if data.update_chars(inventory, char_df):
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
            if data.update_mats(inventory, mat_df):
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
            if data.update_furns(inventory, furn_df):
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
            if data.update_sets(inventory, sets_df):
                st.success("Data successfully updated!")
            else:
                st.error("Data update failed!")

    with calc_tab:
        st.header("Requirements")
        if st.button("Calculate requirements", key="calc", type="primary"):
            reqs = data.calculate_requirements(char_df, sets_df, furn_df, mat_df, db)

            if reqs:
                (needed_furns, buy_furns, needed_mats) = reqs

                cols = st.columns(2)
                with cols[0]:
                    st.subheader("Furnishings to buy:")
                    st.dataframe(
                        buy_furns[["name", "amount"]],
                        hide_index=True,
                    )

                    st.subheader("Materials needed:")
                    st.dataframe(
                        needed_mats[["name", "quantity_diff"]],
                        hide_index=True,
                    )

                with cols[1]:
                    st.subheader("Furnishings to craft:")
                    st.dataframe(
                        needed_furns[["name", "amount"]],
                        hide_index=True,
                    )
            else:
                st.write("There are no gift sets to claim.")
