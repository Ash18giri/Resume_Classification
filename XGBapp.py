import streamlit as st
import pandas as pd
import re
import nltk
import pickle
import os
import docx
import subprocess
import base64
from pdfminer.high_level import extract_text
import magic
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.preprocessing import OrdinalEncoder
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Function to encode image as base64
def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

background_image = get_base64_of_image("background.jpg")

# Apply custom CSS for better styling with local background image
st.markdown(f"""
    <style>
        .stApp {{
            background: url('data:image/jpg;base64,{background_image}') no-repeat center center fixed;
            background-size: 100% 100%;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            max-width: 800px;
            margin: auto;
        }}
        .stButton>button {{
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px 24px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
        }}
        .stButton>button:hover {{
            background-color: #45a049;
        }}
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("📄 Resume Classifier")
st.write("Upload a file, and the app will classify the resume type.")

# Load trained model and vectorizer
with open("clf.pkl", "rb") as model_file:
    model = pickle.load(model_file)
with open("vectorizer1.pkl", "rb") as vec_file:
    vectorizer = pickle.load(vec_file)
with open("label_encoder.pkl", "rb") as enc_file:
    encoder = pickle.load(enc_file)

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["txt", "csv", "docx", "doc", "pdf"])

import win32com.client

def convert_doc_to_docx(doc_path):
    new_docx_path = doc_path + "x"
    try:
        result = subprocess.run(["soffice", "--headless", "--convert-to", "docx", doc_path], check=True)
        return new_docx_path if os.path.exists(new_docx_path) else None
    except:
        return None

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return " ".join([para.text for para in doc.paragraphs])
    except:
        return ""

def extract_text_from_pdf(pdf_path):
    try:
        return extract_text(pdf_path)
    except:
        return ""

def clean_text(text):
    nltk.download("stopwords")
    nltk.download("wordnet")
    lemma = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))
    text = re.sub("[^a-zA-Z]", " ", text).lower()
    words = [lemma.lemmatize(word) for word in text.split() if word not in stop_words]
    return " ".join(words)

def process_file(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[-1].lower()
    temp_path = os.path.join(os.getcwd(), f"temp{ext}")
    with open(temp_path, "wb") as temp_file:
        temp_file.write(uploaded_file.read())
    file_type = magic.Magic(mime=True).from_file(temp_path)
    content = ""
    if ext == ".doc":
        docx_path = convert_doc_to_docx(temp_path)
        content = extract_text_from_docx(docx_path) if docx_path else ""
    elif ext == ".docx":
        content = extract_text_from_docx(temp_path)
    elif "pdf" in file_type:
        content = extract_text_from_pdf(temp_path)
    os.remove(temp_path)
    return clean_text(content)

if uploaded_file is not None:
    file_content = process_file(uploaded_file)
    if not file_content:
        st.error("File processing failed. Please try another file.")
    else:
        transformed_text = vectorizer.transform([file_content])
        st.write("File processed successfully!")
        if st.button("🔍 Predict Category"):
            prediction = model.predict(transformed_text)
            predicted_category = encoder.inverse_transform([[prediction[0]]])[0][0]
            st.success(f"✅ Predicted Category: {predicted_category}")
