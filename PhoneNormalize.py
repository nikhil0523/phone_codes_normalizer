import streamlit as st
import pandas as pd
import io

# ---------------------------
# Load country codes once (adjust the path)
# ---------------------------
@st.cache_data
def load_country_codes(file_path):
    d1 = pd.read_excel(file_path)
    d1["Dialing clean"] = d1["International dialing"].astype(str).str.replace(r"\D", "", regex=True)
    d1["Country_clean"] = d1["Country"].str.strip().str.lower()
    country_to_dialing = dict(zip(d1["Country_clean"], d1["Dialing clean"]))
    all_codes = set(filter(None, d1["Dialing clean"].tolist()))
    return country_to_dialing, all_codes

# Load your country codes Excel file
country_codes_file = "Country_codes.xlsx"
country_to_dialing, all_codes = load_country_codes(country_codes_file)

# ---------------------------
# Normalization function
# ---------------------------
def normalize_number(number: str, country_clean: str):
    correct_code = country_to_dialing.get(country_clean)
    if not correct_code:
        return number, "❌ Unknown country"

    digits = "".join(c for c in str(number) if c.isdigit())

    matched_code = None
    for code in sorted(all_codes, key=lambda x: -len(x)):
        if digits.startswith(code):
            matched_code = code
            digits = digits[len(code):]
            break

    digits = digits.lstrip("0")
    corrected_number = f"+{correct_code}{digits}"

    if matched_code == correct_code:
        verification = "✅ Valid & Matched"
    elif matched_code:
        verification = f"🔄 Corrected from {matched_code} → {correct_code}"
    else:
        verification = f"⚠️ Added country code → {correct_code}"

    return corrected_number, verification

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("Phone Number Normalizer")
st.write("App loaded successfully ✅")  # confirm app is running

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df_numbers = pd.read_csv(uploaded_file)
    else:
        df_numbers = pd.read_excel(uploaded_file)

    # Ensure required columns exist
    if "Phone Number" not in df_numbers.columns or "Country" not in df_numbers.columns:
        st.error("File must contain 'Phone Number' and 'Country' columns.")
    else:
        df_numbers["Country_clean"] = df_numbers["Country"].str.strip().str.lower()

        # ---------------------------
        # Normalization with spinner
        # ---------------------------
        with st.spinner("Normalizing phone numbers, please wait..."):
            df_numbers[["Corrected Number", "Verification"]] = df_numbers.apply(
                lambda x: pd.Series(normalize_number(x["Phone Number"], x["Country_clean"])),
                axis=1
            )

        st.success("Phone numbers normalized!")
        st.dataframe(df_numbers)

        # ---------------------------
        # File download
        # ---------------------------
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data

        def to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download as Excel",
            data=to_excel(df_numbers),
            file_name="normalized_numbers.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="Download as CSV",
            data=to_csv(df_numbers),
            file_name="normalized_numbers.csv",
            mime="text/csv"
        )
