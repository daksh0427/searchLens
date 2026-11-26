import streamlit as st

st.markdown("### Test Native Mermaid")
st.markdown("""
```mermaid
graph TD
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```
""")

st.markdown("### Test User's Mermaid")
st.markdown("""
```mermaid
classDiagram
class ArtificialNeuralNetwork {
  +inputLayer
  +hiddenLayer
  +outputLayer
}
class Layer {
  +neurons
  +weightMatrix
}
class Neuron {
  +activationFunction
  +weights
}
ArtificialNeuralNetwork -> inputLayer
inputLayer -> hiddenLayer
hiddenLayer -> outputLayer
Layer -> neurons
neurons -> weightMatrix
```
""")
