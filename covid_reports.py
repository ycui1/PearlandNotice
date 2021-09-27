import re
import pandas as pd
import numpy as np
import requests
import streamlit as st
from bs4 import BeautifulSoup
from gsheetsdb import connect
from google.oauth2 import service_account
from gsheetsdb import connect

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)



response = requests.get("https://www.pearlandisd.org/coviddashboard")
document = response.text

soup = BeautifulSoup(document, "lxml")

headings = soup.find_all("h2", text=re.compile(r"(Schools|Facilities)$"))
rows = []
for heading in headings:
    for element in heading.next_siblings:
        if str(element).startswith("<p"):
            rows.append(element.text)
        elif str(element).startswith("<h"):
            break

print(rows)

df = pd.DataFrame(rows)


def _parse_data(row: str):
    parsed = row.split('\xa0')
    is_facility = len(parsed) > 1 and parsed[1].startswith('Staff')
    row_data = ["", np.nan, np.nan]
    if is_facility:
        row_data[0] = parsed[0]
        for item in parsed[1:]:
            if item.startswith("Staff"):
                row_data[1] = int(item[len("Staff:"):])
            if item.startswith("Student"):
                row_data[2] = int(item[len("Student:"):])
    return pd.Series(row_data)

df[["facility", "staff_pos", "student_pos"]] = df[0].apply(_parse_data)

df = df.loc[df["staff_pos"].notna()].reset_index(drop=True).drop([0], axis=1)
