import streamlit as st
import streamlit_mermaid as stmd

code = """
flowchart TD
    A[Input Layer] -->|Input Data| B[Hidden Layer]
    B -->|Activation Function| C[Output Layer]
"""

try:
    stmd.st_mermaid(code, height=450)
    print("st_mermaid with int height worked without throwing Python exception.")
except Exception as e:
    print(f"Exception: {e}")

try:
    stmd.st_mermaid(code, height="450px")
    print("st_mermaid with str height worked.")
except Exception as e:
    print(f"Exception str: {e}")
