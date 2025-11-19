import streamlit as st
import pandas as pd

df = pd.read_csv("food2.csv")

df = df[df["data_type"] != "market_acquisition"]
df = df[df["data_type"] != "sub_sample_food"]
df = df[df["data_type"] != "sample_food"]
df = df[df["data_type"] != "agricultural_acquisition"]
df = df.drop(columns = "publication_date")

df.to_csv('food3.csv', index=False)
