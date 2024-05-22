# Genshin Impact Furnishings Gift Set Helper

This app helps to identify needed furnishings to craft/buy and materials required for claiming gift sets.

## Prerequisites

This project is built using:

- Python 3.9.13
- Pandas
- MongoDB
- Streamlit
- Firebase (for authentication)

## Local Deployment

1. Clone the project
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Make a new directory `.streamlit` and move `secrets.example.toml` there
4. Rename the file to `secrets.toml`, and edit the values inside to your own values
5. Make sure your Firebase project has the Authentication enabled
6. Start the Streamlit server:
   ```sh
   streamlit run main.py
   ```
