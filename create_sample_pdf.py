"""Create a sample PDF for testing."""
import fitz  # PyMuPDF

# Create a PDF with some content
doc = fitz.open()

# Page 1: Introduction to Machine Learning
page1 = doc.new_page()
text1 = """
Introduction to Machine Learning

Machine Learning is a subset of artificial intelligence that enables systems to learn
and improve from experience without being explicitly programmed. It focuses on the
development of computer programs that can access data and use it to learn for themselves.

Types of Machine Learning:
1. Supervised Learning - Learning from labeled data
2. Unsupervised Learning - Finding patterns in unlabeled data
3. Reinforcement Learning - Learning through interaction and feedback

Applications:
- Image recognition and computer vision
- Natural language processing
- Recommendation systems
- Autonomous vehicles
- Medical diagnosis
"""
page1.insert_text((50, 50), text1, fontsize=12)

# Page 2: Neural Networks
page2 = doc.new_page()
text2 = """
Neural Networks

Neural networks are computing systems inspired by biological neural networks that
constitute animal brains. They are a fundamental tool in machine learning and deep learning.

Architecture:
- Input Layer: Receives the initial data
- Hidden Layers: Process the information
- Output Layer: Produces the final result

Key Concepts:
- Neurons: Basic computational units
- Weights: Connection strengths between neurons
- Activation Functions: Introduce non-linearity
- Backpropagation: Algorithm for training networks

Deep Learning is a subset of machine learning that uses neural networks with multiple
hidden layers to learn hierarchical representations of data.
"""
page2.insert_text((50, 50), text2, fontsize=12)

# Page 3: Data Science
page3 = doc.new_page()
text3 = """
Data Science Overview

Data Science is an interdisciplinary field that uses scientific methods, processes,
algorithms, and systems to extract knowledge and insights from structured and
unstructured data.

Core Components:
1. Statistics and Mathematics
2. Computer Science and Programming
3. Domain Expertise
4. Data Visualization

The Data Science Process:
- Data Collection: Gathering relevant data
- Data Cleaning: Removing errors and inconsistencies
- Exploratory Analysis: Understanding patterns and trends
- Modeling: Building predictive models
- Evaluation: Assessing model performance
- Deployment: Implementing solutions in production

Tools and Technologies:
- Python, R, SQL
- Pandas, NumPy, Scikit-learn
- TensorFlow, PyTorch
- Jupyter Notebooks
"""
page3.insert_text((50, 50), text3, fontsize=12)

# Save the PDF
output_path = "data/pdfs/sample_ml_guide.pdf"
doc.save(output_path)
doc.close()

print(f"Sample PDF created: {output_path}")
