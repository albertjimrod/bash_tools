<think>
Okay, so I need to help the user by converting their technical notes into a clear, educational, and engaging article. They've provided two code snippets related to data preparation for machine learning using Python. 

First, I'll look at what each snippet does. The first part is about preprocessing the dataset: loading it, handling missing values with medians, removing irrelevant variables, replacing outliers, and encoding categorical variables. The second part deals with defining target and predictor variables, normalizing features, scaling them between 0-1, creating matrices for X and y, and splitting into training and test sets using train_test_split.

I need to turn this into an article that's not only clear but also engaging. Maybe I can structure it step by step, explaining each process as if someone is learning data preprocessing for the first time. Including some context about why each step is important will make it educational.

I should start with an introduction about the importance of data preparation in machine learning. Then, break down each step into sections, perhaps using headings and bullet points for clarity. Adding a bit of real-world relevance might help readers see the practical application.

I also need to ensure that the code examples are well-explained, maybe adding comments or explanations next to them if they were part of the article. But since the user provided the code, I can describe what each line does in simple terms.

Thinking about the audience, it's likely someone new to data science who wants to understand the preprocessing steps without getting too bogged down by jargon. So keeping the language conversational and avoiding overly technical terms where possible would be good.

I should also make sure that after explaining all the steps, there's a conclusion that ties everything together, emphasizing how these preprocessing steps are foundational for building effective models.

Maybe adding some tips or common mistakes could add extra value, like why it's important to handle outliers or why scaling is necessary. But since the user didn't ask for that, I'll stick to their provided content unless it's necessary for clarity.

Overall, the key points are: data loading, handling missing values, removing irrelevant features, dealing with outliers, categorical encoding, defining target and predictors, normalization, scaling, creating matrices, and splitting data. Each of these can be a section with a brief explanation and an example code snippet as provided.

I should also ensure that each step flows logically into the next, showing the progression from raw data to preprocessed datasets ready for model training. This will help readers follow along without feeling overwhelmed by the process.
</think>

# Preparación de Datos para el Modelado en Ciencia de Datos

La preparación de datos es una etapa crítica en el proceso de ciencia de datos y machine learning. Un dataset bien preparado no solo mejora el rendimiento de los modelos, sino que también facilita la interpretación y análisis. En este artículo, exploraremos paso a paso cómo preprar un conjunto de datos para su uso en tareas de modelado.

---

## 1. Carga del Dataset

El primer paso es cargar el dataset que se utilizará para entrenar y probar los modelos. Para este ejemplo, utilizaremos el dataset `mpg` de seaborn, que contiene información sobre los combustibles de varios tipos de vehículos:

```python
import seaborn as sns
import numpy as np
import pandas as pd

df = sns.load_dataset('mpg')
```

El dataset `mpg` incluye variables como la potencia del motor (`horsepower`), el año del modelo (`model_year`), el origen del vehículo (`origin`), entre otras.

---

## 2. Manejo de Valores Faltantes

Es posible que el dataset tenga valores faltantes, especialmente en variables numéricas como `horsepower`. Para manejar estos datos, utilizamos la mediana de la variable:

```python
df['horsepower'].fillna(df['horsepower'].median(), inplace=True)
```

La mediana es una buena opción para imputar valores缺失 cuando los datos siguen una distribución normal o cuando hay outliers.

---

## 3. Eliminación de Variables Irrelevantes

Si el dataset incluye variables que no son relevantes para el análisis, debemos eliminarlas:

```python
df = df.drop(['name'], axis=1)
```

En este caso, eliminamos la variable `name`, que no aporta información numérica relevante.

---

## 4. Manejo de Valores Atípicos

Los valores atípicos (outliers) pueden distorsionar los modelos y los resultados. Para mitigar esto, reemplazamos los valores extremadamente altos en la variable `horsepower` por un valor máximo definido arbitrariamente (en este caso, 200):

```python
df['horsepower'] = np.where(df['horsepower'] > 200, 200, df['horsepower'])
```

Esto asegura que los valores de `horsepower` no excedan un rango.reasonable para el análisis.

---

## 5. Codificación Ficticia de Variables Categóricas

Las variables categóricas (como `cylinders`, `model_year` y `origin`) deben codificarse antes de ser utilizadas en los modelos numéricos. Para ello, utilizamos la codificación ficticia:

```python
df = pd.get_dummies(df, columns=['cylinders'], drop_first=True, prefix='Cylinder')
df = pd.get_dummies(df, columns=['model_year'], drop_first=True, prefix='Year')
df = pd.get_dummies(df, columns=['origin'], drop_first=True, prefix='Origin')
```

La función `pd.get_dummies` convierte las variables categóricas en una matriz de dummy variables (0s y 1s), lo que permite su uso en los modelos.

---

## 6. Definición de Variables para el Modelado

Después de la preparación del dataset, definimos la variable objetivo (`target`) y las variables predictoras:

```python
from sklearn.model_selection import train_test_split

target_variable = ['mpg'] 
predictors = list(set(list(df.columns)) - set(target_variable))
```

- `target_variable`: En este caso, `mpg` (miles por galón) es la variable que queremos predecir.
- `predictors`: Son todas las demás variables disponibles en el dataset.

---

## 7. Normalización y Escalado

Muchos algoritmos de machine learning requieren que los datos estén normalizados y escalados para funcionar correctamente. Para ello, dividimos cada variable predictora por su valor máximo:

```python
df[predictors] = df[predictors] / df[predictors].max()
```

Esto asegura que todas las variables se encuentren en el mismo rango (0-1), lo que facilita la convergencia de los algoritmos.

---

## 8. Creación de Matrices para Modelado

Convertimos los datos en matrices numpy, que son el formato requerido por大多数 bibliotecas de machine learning:

```python
X = df[predictors].values
y = df[target_variable].values
```

- `X`: Matriz de features (variables predictoras).
- `y`: Vector de la variable objetivo.

---

## 9. División del Dataset en Train y Test

Finalmente, dividimos el dataset en dos partes: una para entrenar los modelos (`train`) y otra para evaluar su rendimiento (`test`):

```python
# Ejemplo de división:
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

- `test_size=0.2`: 20% del dataset se utiliza para testing.
- `random_state=42`: Asegura que los resultados sean reproducibles.

---

## Conclusión

La preparación de datos es una etapa clave en la ciencia de datos y el machine learning. En este artículo, hemos explorado cómo cargar, limpiar, transformar y dividir un dataset para su uso en tareas de modelado. Una buena preparación de datos no solo mejora el rendimiento de los modelos, sino que también facilita el análisis y la interpretación de los resultados.