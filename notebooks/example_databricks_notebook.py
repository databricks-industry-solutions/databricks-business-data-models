# Databricks notebook source
# MAGIC %md
# MAGIC # Example Databricks Notebook
# MAGIC
# MAGIC This is a template Databricks notebook in .py format.
# MAGIC Replace this with your actual notebook content.
# MAGIC
# MAGIC ## Features
# MAGIC
# MAGIC - Markdown cells using `# MAGIC %md`
# MAGIC - Code cells get syntax highlighting
# MAGIC - Renders consistently with .ipynb notebooks

# COMMAND ----------

# MAGIC %md
# MAGIC ## Code Example

# COMMAND ----------

# This is example Python code for Databricks
import pandas as pd
import numpy as np

# Create sample data
df = pd.DataFrame({
    'column1': np.random.randn(10),
    'column2': np.random.randn(10)
})

print("Sample DataFrame:")
print(df.head())

# COMMAND ----------

# MAGIC %md
# MAGIC ## SQL Example

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Example SQL query
# MAGIC SELECT 'Hello' as greeting, 'World' as target
