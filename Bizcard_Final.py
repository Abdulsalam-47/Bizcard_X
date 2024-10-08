import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import mysql.connector
import re

# Function to convert image to text
def img_to_txt(path):
    
    #Open the image
    input_img = Image.open(path)
    #converting the image to an array
    img_array = np.array(input_img)
    #initialinzing the OCR
    reader = easyocr.Reader(['en'])
    #Performing text recognition
    txt = reader.readtext(img_array, detail=0)
    #Returning Result
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
        #extd_dict["NAME"].append(txts[0]): Assumes the first text string in the list (txts[0]) is the name and adds it to the "NAME" field.
        extd_dict["NAME"].append(txts[0])
        #extd_dict["DESIGNATION"].append(txts[1]): Assumes the second text string (txts[1]) is the designation and adds it to the "DESIGNATION" field
        extd_dict["DESIGNATION"].append(txts[1])
        
        #for i in range(2, len(txts)):: Loops through the remaining text strings starting from index 2.
        for i in range(2, len(txts)):
            #Checks if the text starts with + or if it contains digits with -, assuming it is a contact number.Combines multiple contact numbers if present.

            if txts[i].startswith("+") or (txts[i].replace("-", "").isdigit() and '-' in txts[i]):
                if extd_dict["CONTACT"]:
                    extd_dict["CONTACT"][0] += " & " + txts[i]
                else:
                    extd_dict["CONTACT"].append(txts[i])
            #Checks if the text contains @ and .com, assuming it is an email address.
            elif "@" in txts[i] and ".com" in txts[i]:
                extd_dict["EMAIL"].append(txts[i])
            #Checks if the text contains "www". If not formatted correctly, it fixes the format and adds it as a website.
            elif "www" in txts[i].lower():
                website = txts[i].lower()
                if "www." not in website:
                    website = website.replace("www", "www.")
                extd_dict["WEBSITE"].append(website)
            #Checks for the presence of "Tamil Nadu" or "TamilNadu" and assigns it as the state
            elif "Tamil Nadu" in txts[i] or "TamilNadu" in txts[i]:
                extd_dict["STATE"].append("Tamil Nadu")
                # Extract pincode if present in the same string
                pincode_match = re.search(r'\b\d{6}\b', txts[i])
                if pincode_match:
                    extd_dict["PINCODE"].append(pincode_match.group())
            elif re.match(r'^\d{6}$', txts[i]):
                extd_dict["PINCODE"].append(txts[i])
            #If the text starts with a letter, it is assumed to be the company name.
            elif re.match(r'^[A-Za-z]', txts[i]):
                extd_dict["COMPANY NAME"].append(txts[i].upper())
            else:
                # All other text is considered as address, Remove unnecessary spaces and replace semicolons with commas
                address = txts[i].strip().replace(';', ',')
                extd_dict["ADDRESS"].append(address)

        #Joins multiple entries for each field into a single string separated by spaces. If a field has no data, it assigns "NA" as the default value.
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
    <h2 style="font-weight: normal; font-family: 'Arial', sans-serif;">This OCR app is created by <span style="background: linear-gradient(to right, violet, indigo, blue, green, yellow, orange, red); -webkit-background-clip: text; color: purple; font-weight: normal; font-size: 24px; font-family: 'Arial', sans-serif;">ABDUL SALAM</span>!</h2>
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
        text_image, input_img = img_to_txt(img)
        text_dict = extracted_txt(text_image)

        if text_dict:
            st.success("TEXT IS EXTRACTED SUCCESSFULLY")

        method = st.radio("Select the Method", ["None", "Preview"])

        # Display DataFrame only if "Preview" is selected
        if method == "Preview":
            df = pd.DataFrame(text_dict)
            st.write("### Preview of Extracted Data")
            st.dataframe(df)
            # Note about modifying data
            st.markdown("**Please note:** If the data is not properly placed or some values are missing, please add or change the missed values in the 'Modify Data' tab.")

        if st.button("Save") and method == "Preview":
            # Connect to the database
            mydb = mysql.connector.connect(
                host="127.0.0.1",
                port="3306",
                user="root",
                password="root",
                database="bizcardx"
            )
            cursor = mydb.cursor()

            # Check if record already exists
            check_query = '''
                SELECT * FROM bizcard_info
                WHERE name = %s AND designation = %s AND company_name = %s
            '''
            cursor.execute(check_query, (text_dict["NAME"][0], text_dict["DESIGNATION"][0], text_dict["COMPANY NAME"][0]))
            result = cursor.fetchone()

            if result:
                st.warning("A record with the same name, designation, and company name already exists. No new record was added.")
            else:
                # Table Creation
                create_query = '''
                    CREATE TABLE IF NOT EXISTS bizcard_info (
                        id INT AUTO_INCREMENT PRIMARY KEY,
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



elif select == "Modify Data":
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        port="3306",
        user="root",
        password="root",
        database="bizcardx"
    )
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

    st.dataframe(df_4)

    if st.button("Modify"):
        cursor.execute(f"DELETE FROM bizcard_info WHERE NAME = '{selected_name}'")
        mydb.commit()

        # Insert Query
        insert_query = '''
            INSERT INTO bizcard_info (
                name, designation, company_name, contact, email, website, address, state, pincode
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(insert_query, df_4.values.tolist()[0])
        mydb.commit()
        st.success("MODIFIED SUCCESSFULLY")

elif select == "Delete Data":
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        port="3306",
        user="root",
        password="root",
        database="bizcardx"
    )
    cursor = mydb.cursor()

    # Select query
    select_query = "SELECT * FROM bizcard_info"
    cursor.execute(select_query)
    table = cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "STATE", "PINCODE"))

    selected_name = st.selectbox("Select the name to delete", table_df["NAME"])

    # Create a unique key for the checkbox using the selected name
    delete_confirmation_key = f"delete_confirmation_{selected_name}"
    delete_confirmation = st.checkbox(f"Are you sure you want to delete {selected_name}? This action cannot be undone.", key=delete_confirmation_key)

    # Create a form to handle deletion
    if delete_confirmation:
        form_delete = st.form(key='form_delete')
        submit_delete = form_delete.form_submit_button(label='Confirm Deletion', help='Please confirm deletion.')

        if submit_delete:
            # Perform the deletion
            cursor.execute(f"DELETE FROM bizcard_info WHERE NAME = '{selected_name}'")
            mydb.commit()
            st.success(f"{selected_name} has been deleted successfully.")
    else:
        st.warning("Please confirm the deletion.")


