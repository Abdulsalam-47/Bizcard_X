import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import mysql.connector
import re

# Database connection function
@st.cache_resource
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port="3306",
        user="root",
        password="root",
        database="bizcardx"
    )

# Function to convert image to text
def img_to_txt(path):
    input_img = Image.open(path)
    img_array = np.array(input_img)
    reader = easyocr.Reader(['en'])
    txt = reader.readtext(img_array, detail=0)
    return txt, input_img

# Function to extract text
def extracted_txt(txts):
    extd_dict = {
        "NAME": [],
        "DESIGNATION": [],
        "COMPANY NAME": [],
        "CONTACT": [],
        "EMAIL": [],
        "WEBSITE": [],
        "ADDRESS": [],
        "STATE": [],
        "PINCODE": []
    }

    if txts:
        extd_dict["NAME"].append(txts[0])
        extd_dict["DESIGNATION"].append(txts[1])

        for i in range(2, len(txts)):
            if txts[i].startswith("+") or (txts[i].replace("-", "").isdigit() and '-' in txts[i]):
                if extd_dict["CONTACT"]:
                    extd_dict["CONTACT"][0] += " & " + txts[i]
                else:
                    extd_dict["CONTACT"].append(txts[i])
            elif "@" in txts[i] and ".com" in txts[i]:
                extd_dict["EMAIL"].append(txts[i])
            elif "www" in txts[i].lower():
                website = txts[i].lower()
                if "www." not in website:
                    website = website.replace("www", "www.")
                extd_dict["WEBSITE"].append(website)
            elif "Tamil Nadu" in txts[i] or "TamilNadu" in txts[i]:
                extd_dict["STATE"].append("Tamil Nadu")
                # Extract pincode if present in the same string
                pincode_match = re.search(r'\b\d{6}\b', txts[i])
                if pincode_match:
                    extd_dict["PINCODE"].append(pincode_match.group())
            elif re.match(r'^\d{6}$', txts[i]):
                extd_dict["PINCODE"].append(txts[i])
            elif re.match(r'^[A-Za-z]', txts[i]):
                extd_dict["COMPANY NAME"].append(txts[i].upper())
            else:
                # Remove unnecessary spaces and replace semicolons with commas
                address = txts[i].strip().replace(';', ',')
                extd_dict["ADDRESS"].append(address)

        for key, value in extd_dict.items():
            extd_dict[key] = [" ".join(value)] if value else ["NA"]

    return extd_dict

# Streamlit app
st.set_page_config(layout="wide")
st.title("EXTRACTING BUSINESS CARD DATA WITH 'OCR'")

# Custom horizontal rule with a gradient
st.markdown('<hr style="border-top: 5px solid black;">', unsafe_allow_html=True)

# Additional markdown with creator's name in a rainbow gradient
st.markdown("""
    <h2 style="font-weight: normal; font-family: 'Arial', sans-serif;">This OCR app is created by 
    <span style="background: linear-gradient(to right, violet, indigo, blue, green, yellow, orange, red); 
    -webkit-background-clip: text; color: purple; font-weight: normal; font-size: 24px; font-family: 'Arial', sans-serif;">ABDUL SALAM</span>!</h2>
    """, unsafe_allow_html=True)


with st.sidebar:
    select = option_menu("Main Menu", ["Home", "Upload Data", "Modify Data", "Delete Data"])

if select == "Home":
    st.markdown("### :blue[Welcome to the Business Card Application!]")
    st.markdown('### Bizcard is a Python application designed to extract information from business cards. It utilizes various technologies such as :blue[Streamlit, Python, EasyOCR, PIL and MySQL] database to achieve this functionality.')
    st.write('### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')

    st.write('### :blue[Technologies Used]')
    st.write('### :white[Python]  :white[Streamlit] :white[EasyOCR]  :white[PIL(Python Imaging Library)]  :white[MySQL]')

elif select == "Upload Data":
    img = st.file_uploader("Upload the Image", type=["png", "jpg", "jpeg"])

    if img is not None:
        st.image(img, width=300)
        with st.spinner('Extracting text from image...'):
            text_image, input_img = img_to_txt(img)
        text_dict = extracted_txt(text_image)

        if text_dict:
            st.success("TEXT IS EXTRACTED SUCCESSFULLY")

        df = pd.DataFrame(text_dict)

        if st.button("Save"):
            try:
                mydb = get_db_connection()
                cursor = mydb.cursor()

                # Table Creation
                create_query = '''
                    CREATE TABLE IF NOT EXISTS bizcard_info (
                        name VARCHAR(225),
                        designation VARCHAR(225),
                        company_name VARCHAR(225),
                        contact VARCHAR(225),
                        email VARCHAR(225),
                        website TEXT,
                        address TEXT,
                        state VARCHAR(225),
                        pincode VARCHAR(225)
                    )
                '''
                cursor.execute(create_query)
                mydb.commit()

                # Insert Query
                insert_query = '''
                    INSERT INTO bizcard_info (
                        name, designation, company_name, contact, email, website, address, state, pincode
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                cursor.execute(insert_query, df.values.tolist()[0])
                mydb.commit()
                st.success("SAVED SUCCESSFULLY")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")
            finally:
                cursor.close()
                mydb.close()

    method = st.radio("Select the Method", ["None", "Preview"])

    if method == "Preview":
        try:
            mydb = get_db_connection()
            cursor = mydb.cursor()

            # Select query
            select_query = "SELECT * FROM bizcard_info"
            cursor.execute(select_query)
            table = cursor.fetchall()
            mydb.commit()

            table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "STATE", "PINCODE"))
            st.dataframe(table_df)
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")
        finally:
            cursor.close()
            mydb.close()

elif select == "Modify Data":
    try:
        mydb = get_db_connection()
        cursor = mydb.cursor()

        # Select query
        select_query = "SELECT * FROM bizcard_info"
        cursor.execute(select_query)
        table = cursor.fetchall()
        mydb.commit()

        table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "STATE", "PINCODE"))

        col1, col2 = st.columns(2)
        with col1:
            selected_name = st.selectbox("Select the name", table_df["NAME"])

        df_3 = table_df[table_df["NAME"] == selected_name]
        df_4 = df_3.copy()

        col1, col2 = st.columns(2)
        with col1:
            mod_name = st.text_input("Name", df_3["NAME"].unique()[0])
            mod_desi = st.text_input("Designation", df_3["DESIGNATION"].unique()[0])
            mod_com_name = st.text_input("Company_name", df_3["COMPANY_NAME"].unique()[0])
            mod_contact = st.text_input("Contact", df_3["CONTACT"].unique()[0])
            mod_email = st.text_input("Email", df_3["EMAIL"].unique()[0])

            df_4["NAME"] = mod_name
            df_4["DESIGNATION"] = mod_desi
            df_4["COMPANY_NAME"] = mod_com_name
            df_4["CONTACT"] = mod_contact
            df_4["EMAIL"] = mod_email

        with col2:
            mod_website = st.text_input("Website", df_3["WEBSITE"].unique()[0])
            mod_addre = st.text_input("Address", df_3["ADDRESS"].unique()[0])
            mod_pincode = st.text_input("Pincode", df_3["PINCODE"].unique()[0])

            df_4["WEBSITE"] = mod_website
            df_4["ADDRESS"] = mod_addre
            df_4["PINCODE"] = mod_pincode

        if st.button("Modify"):
            update_query = '''
                UPDATE bizcard_info
                SET name=%s, designation=%s, company_name=%s, contact=%s, email=%s, website=%s, address=%s, pincode=%s
                WHERE name=%s
            '''
            cursor.execute(update_query, (
                mod_name, mod_desi, mod_com_name, mod_contact, mod_email, mod_website, mod_addre, mod_pincode, selected_name
            ))
            mydb.commit()
            st.success("MODIFIED SUCCESSFULLY")

        # Display modified table
        st.dataframe(df_4)

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
    finally:
        cursor.close()
        mydb.close()

elif select == "Delete Data":
    try:
        mydb = get_db_connection()
        cursor = mydb.cursor()

        # Select query
        select_query = "SELECT * FROM bizcard_info"
        cursor.execute(select_query)
        table = cursor.fetchall()
        mydb.commit()

        table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "STATE", "PINCODE"))
        st.dataframe(table_df)

        col1, col2 = st.columns(2)
        with col1:
            selected_name = st.selectbox("Select the name", table_df["NAME"])

        df_5 = table_df[table_df["NAME"] == selected_name]

        # Display selected record to delete
        st.dataframe(df_5)

        if st.button("Delete"):
            delete_query = "DELETE FROM bizcard_info WHERE name = %s"
            cursor.execute(delete_query, (selected_name,))
            mydb.commit()
            st.warning("DELETED SUCCESSFULLY")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
    finally:
        cursor.close()
        mydb.close()
