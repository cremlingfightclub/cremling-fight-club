import streamlit as st
import pandas as pd


def calculate_total_threat(party_tier, party_size, enemy_list):
    total_threat = 0
    role_dict = {"Minion": 0.5, "Rival": 1.0, "Boss": 4.0}
    for enemy in enemy_list:
        base_threat = role_dict[enemy["role"]]
        enemy_tier = enemy["tier"]
        tier_delta = int(enemy_tier) - int(party_tier)
        adjusted_threat = base_threat * (2.0**tier_delta)
        if adjusted_threat < 0.25:
            adjusted_threat = 0.0
        total_threat += adjusted_threat
    threat_per_player = total_threat / party_size
    category = ""
    if threat_per_player < 0.75:
        category = "Easy"
    if 0.75 <= threat_per_player < 1.25:
        category = "Average"
    if 1.25 <= threat_per_player < 1.75:
        category = "Hard"
    if threat_per_player >= 1.75:
        category = "Above Hard"
    return threat_per_player, category


# Set page config for wide mode
st.set_page_config(
    layout="wide",
    page_title="Cremling Fight Club",
    page_icon=":crab:",
)

if st.session_state.get("entities_df") is None:
    st.session_state["entities_df"] = pd.read_csv("entities.csv")

if st.session_state.get("current_enemies") is None:
    st.session_state["current_enemies"] = []
# Create a list of columns with 'Add' button first
# Make the second column (index 1) twice as wide as others

st.title("Cremling Fight Club")
st.markdown("A Cosmere RPG Combat Planner")


column_widths = [1] + [1] * len(st.session_state["entities_df"].columns)
column_widths[1] = 2  # Make second column twice as wide
column_widths[5] = 1.5  # Make sixth column 50% wider
columns = st.columns(column_widths)

# Display column headers
# columns[0].write("Add")
selected_values_dict = {}
fcol1, fcol2 = st.columns(2)
with fcol1:
    with st.expander("Filters"):
        # Create multiselect filters for each column (except the first)
        filter_cols = st.columns(
            len(st.session_state["entities_df"].columns) - 1
        )
        for i, col in enumerate(
            st.session_state["entities_df"].columns[1:], start=0
        ):
            unique_values = (
                st.session_state["entities_df"][col].unique().tolist()
            )
            selected_values = st.multiselect(
                f"Filter {col}",
                options=unique_values,
                default=unique_values,
                key=f"filter_{col}",
            )
            selected_values_dict[col] = selected_values

        # Search bar for filtering by name
        search_text = st.text_input(
            "Search by name:",
            placeholder="Name contains...",
            key="name_search",
        )

# Create filtered dataframe based on selected values
filtered_df = st.session_state["entities_df"].copy()

# Apply filters for each column
for col, selected_values in selected_values_dict.items():
    if selected_values:  # Only filter if values are selected
        filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

# Apply name search filter
if search_text and search_text.strip():
    filtered_df = filtered_df[
        filtered_df["Name"].str.contains(search_text, case=False, na=False)
    ]

# Add sorting options
with fcol2:
    sort_option = st.selectbox(
        "Sort by:",
        [
            "No sorting",
            "Tier (ascending)",
            "Tier (descending)",
            "Role (ascending)",
            "Role (descending)",
            "Name (A-Z)",
            "Name (Z-A)",
        ],
        key="sort_option",
    )

# Apply sorting
if sort_option == "Tier (ascending)":
    filtered_df = filtered_df.sort_values("Tier", ascending=True)
elif sort_option == "Tier (descending)":
    filtered_df = filtered_df.sort_values("Tier", ascending=False)
elif sort_option == "Role (ascending)":
    # Define custom order for roles
    role_order = {"Minion": 1, "Rival": 2, "Boss": 3}
    filtered_df["role_order"] = filtered_df["Role"].map(role_order)
    filtered_df = filtered_df.sort_values("role_order", ascending=True)
    filtered_df = filtered_df.drop("role_order", axis=1)
elif sort_option == "Role (descending)":
    # Define custom order for roles
    role_order = {"Minion": 1, "Rival": 2, "Boss": 3}
    filtered_df["role_order"] = filtered_df["Role"].map(role_order)
    filtered_df = filtered_df.sort_values("role_order", ascending=False)
    filtered_df = filtered_df.drop("role_order", axis=1)
elif sort_option == "Name (A-Z)":
    filtered_df = filtered_df.sort_values("Name", ascending=True)
elif sort_option == "Name (Z-A)":
    filtered_df = filtered_df.sort_values("Name", ascending=False)

header_cols = st.columns(column_widths)
for i, col in enumerate(filtered_df.columns, start=1):
    header_cols[i].markdown(
        f"<small><strong>{col}</strong></small>", unsafe_allow_html=True
    )
st.divider()
# Display each row
cols = st.columns(column_widths)

for row in filtered_df.itertuples():

    with cols[0]:
        button_key = f"add_button_{row.Index}"
        button_clicked = st.button("Add", key=button_key)
        if button_clicked:
            enemy = {"name": row.Name, "tier": row.Tier, "role": row.Role}
            st.session_state["current_enemies"].append(enemy)
    for i, val in enumerate(row[1:], start=1):
        display_val = str(val) + "\n\n"
        print(display_val)
        cols[i].markdown(
            f"<small>{display_val}</small>", unsafe_allow_html=True
        )
        cols[i].write("")
if len(filtered_df) == 0:
    st.write("No entries meet filter criteria")
st.divider()
with st.sidebar:

    Party_Tier = st.selectbox("Party Tier", ["1", "2", "3"])
    Party_Size = st.slider("Party Size", min_value=1, max_value=10, value=1)
    added_enemies = {}
    for enemy in st.session_state["current_enemies"]:
        enemy_name = enemy["name"]
        if enemy_name not in added_enemies:
            added_enemies[enemy_name] = {
                "tier": enemy["tier"],
                "role": enemy["role"],
                "name": enemy_name,
                "count": 1,
            }
        else:
            added_enemies[enemy_name]["count"] += 1
    scol1, scol2 = st.columns(2)
    for enemy_dict in added_enemies.values():
        with scol1:
            st.write(f"{enemy_dict['name']} x {enemy_dict['count']}")
        with scol2:
            remove_button_key = f"remove_button_{enemy_dict['name']}"
            remove_button_clicked = st.button("Remove", key=remove_button_key)
            if remove_button_clicked:
                for i, temp_enemy in enumerate(
                    st.session_state["current_enemies"]
                ):
                    if temp_enemy["name"] == enemy_dict["name"]:
                        st.session_state["current_enemies"].pop(i)
                        st.rerun()

                break
    threat_per_player, category = calculate_total_threat(
        Party_Tier, Party_Size, st.session_state["current_enemies"]
    )
    if len(st.session_state["current_enemies"]) > 0:
        st.markdown(f"**Category:** {category}")
        st.markdown(f"Threat per player: {threat_per_player:.2f}")
    else:
        st.markdown("No enemies added")
st.markdown("#### *Hello, would you like to plan some evil today?*")

pcols = st.columns(4)
with pcols[0]:
    with st.expander("Abbreviations"):
        st.write(
            """
        SLWG: Stormlight World Guide
        """
        )
with pcols[1]:
    # Download the default entities.csv file
    with open("entities.csv", "r") as file:
        csv_data = file.read()

    st.download_button(
        label="Download default entities.csv",
        data=csv_data,
        file_name="entities.csv",
        mime="text/csv",
        help="Download the default entities.csv file",
    )

# File upload and download section
with pcols[2]:
    uploaded_file = st.file_uploader(
        "Upload your own enemies CSV file (optional)",
        type=["csv"],
        help=(
            "Upload a CSV file with the same column structure as the default "
            "entities.csv. If your csv is more than 200MB, what the fuck."
        ),
    )

    # Load dataframe from uploaded file or default
    if uploaded_file is not None:
        # Reset session state when new file is uploaded
        if st.session_state.get("uploaded_file_name") != uploaded_file.name:
            st.session_state["entities_df"] = pd.read_csv(uploaded_file)
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.session_state["current_enemies"] = (
                []
            )  # Reset enemies when new file is loaded
            st.rerun()
with pcols[3]:
    with st.expander("Leave Feedback"):
        st.write(
            "If you find this site useful, leave a like by hitting the button below. If I get enough likes, it'll make me feel self-important, which will raise the probability that I update the site with new enemies as books are published."
        )
        like_button = st.button("Leave a Like")
        if like_button:
            with open("likes.txt", "r") as file:
                likes = int(file.read())
            likes += 1
            with open("likes.txt", "w") as file:
                file.write(str(likes))
            st.write(f"{likes} likes so far.")
        st.write(
            "To report a bug, please send a message to cremlingfightclub (at) gmail.com. If enough people ask for a feature, I might even add it."
        )


st.markdown(
    "<small>*This is unofficial fan content, created and shared for non-commercial use. It has not been reviewed by Dragonsteel Entertainment, LLC or Brotherwise Games, LLC.*</small>",
    unsafe_allow_html=True,
)
