import streamlit as st
import streamlit_mermaid as stmd

code = """
sequenceDiagram
participant "Source" as Source
participant "Machine Learning" as ML
note over Source,ML
"UNIT-II (ARTIFICIAL NEURAL NETWORKS)"
end

activate Source
Source->>ML: Some of Different Activation Functions used in Machine Learning
activate ML
ML->>Note: CONTD..
    note over ML
    "Activation Functions"
    end
ML->>Note: APPLICATIONS OF ARTIFICIAL NEURAL NETWORK
    note over ML
    "ANN learning is well-suited to problems..."
    end
"""
st.write("Rendering...")
stmd.st_mermaid(code)
st.write("Done.")
