<think>
Okay, so I need to figure out how to display proportions or percentages on each wedge of a pie chart using matplotlib in Python. I remember that pie charts are useful for showing parts of a whole, and having the exact percentages makes them even more informative.

I've heard about the autopct parameter before but I'm not exactly sure how it works. Let me check some documentation. Oh right, autopct stands for "auto percent" and it's used to format the numbers on each slice of the pie chart. But how do I use it?

The example given uses '%.1f%%' as the string for autopct. Hmm, that looks like a Python string formatting code. The '%' sign at the end is to display percentages, right? And before that, '%.1f' means one decimal place. So putting them together gives me one decimal place with a percent sign.

Let me try writing some code. I'll import matplotlib.pyplot as plt first. Then, I need data; maybe I can use pandas for this. Suppose I have a DataFrame called wnba and a column named 'Pos'. I want to count the occurrences of each position.

So, wnba['Pos'].value_counts() gives me the counts. To plot this as a pie chart, I'll call .plot.pie(). Then, I need to set the figure size with figsize=(6,6). Now, for the autopct parameter, I'll use '%.1f%%' here.

Wait, does this automatically calculate the percentages? It should, since each slice's value is divided by the total. So the code would be:

import matplotlib.pyplot as plt
wnba['Pos'].value_counts().plot.pie(figsize=(6,6), autopct='%.1f%%')
plt.show()

This should display a pie chart with each wedge showing its percentage rounded to one decimal place.

I wonder what happens if I change the formatting string. Like, '%.2f%%' would give two decimal places. Or maybe I can remove the percent sign by using just '%.1f'. But usually, percentages are more intuitive with the % symbol.

Also, sometimes the percentages might be cut off or hard to read if there's not enough space. Maybe adjusting the figure size or using labels could help, but for now, autopct seems straightforward.

I think I have a good grasp on how to use autopct now. It's just about formatting the string correctly and including it in the plot.pie() function.
</think>

**Cómo mostrar porcentajes en un gráfico de pastel con Matplotlib**

Cuando trabajas con gráficos de pastel (pie charts) en Python utilizando Matplotlib, es esencial que los datos sean claros y significativos. Para lograrlo, puedes agregar porcentajes a cada sector del gráfico para que los espectadores comprendan rápidamente las proporciones.

### Paso 1: Configurar tu entorno

Antes de empezar, asegúrate de tener instalado Matplotlib:

```bash
pip install matplotlib pandas
```

### Paso 2: Importar las bibliotecas necesarias

Necesitarás importar `matplotlib.pyplot` para crear gráficos y `pandas` si estás trabajando con un DataFrame:

```python
import matplotlib.pyplot as plt
import pandas as pd
```

### Paso 3: Preparar tus datos

Supongamos que tienes un DataFrame llamado `wnba` con una columna denominada 'Pos'. Primero, cuenta las ocurrencias de cada valor en dicha columna:

```python
data = wnba['Pos'].value_counts()
```

### Paso 4: Crear el gráfico de pastel

Ahora, crea un gráfico de pastel y configura los porcentajes con `autopct`:

```python
# Graficar los datos en un pie chart
plt.figure(figsize=(6,6))
data.plot.pie(autopct='%1.1f%%', labels=data.index)
```

### Explicación del código

- **`figsize=(6,6)`**: Define el tamaño de la figura.
- **`data.plot.pie()`**: Crea un gráfico de pastel a partir de los datos.
- **`autopct='%1.1f%%'`**: Formatea los porcentajes con una precisión de una decimal y agrega el símbolo de porcentaje (`%`). 
- **`labels=data.index`**: Etiqueta cada sector con el valor correspondiente de la columna 'Pos'.

### Resultado esperado

Obtendrás un gráfico de pastel donde cada sector muestra su porcentaje redondeado a una decimal, acompañado del símbolo `%`. Por ejemplo:

- 25.0%
- 18.0%
- 30.0%

Esto facilita la comprensión de las proporciones de cada categoría.

### Personalización adicional

Si deseas ajustar el diseño, puedes modificar los colores, agregar sombras o mover las etiquetas:

```python
# Cambiar colores
plt.rcParams['axes.prop_cycle'] = plt.cycler('color', ['#2ecc71', '#3498db', '#e74c3c'])

# Agregar sombra
plt.gca().set_edgecolor('black')

# Mostrar el gráfico
plt.show()
```

### Resumen

Utilizar `autopct` en Matplotlib es una manera sencilla y efectiva de mostrar porcentajes en un gráfico de pastel. Esto no solo mejora la claridad del gráfico, sino que también hace más atractivo el análisis de datos.