# bash_tools <img src="https://github.com/odb/official-bash-logo/raw/master/assets/Logos/Icons/PNG/64x64.png" alt="bash" width="40" height="40" style="max-width: 100%;">

This repository contains scripts designed to automate **Conda environment** management tasks, which I have found essential for my workflow.

The most important functionalities include:

### Exporting Conda environments: 

- **export_conda_envs:** This allows me to save the current state of a Conda environment in every independent file, so it can be easily transferred.

```bash

     4 -rw-rw-r--  1 i  i         83 ene 22 07:42  StableDif.yml
    12 -rw-rw-r--  1 i  i       9579 ene 22 07:42  bigquery.yml
     4 -rw-rw-r--  1 i  i       1419 ene 22 07:42  blablacar.yml
     4 -rw-rw-r--  1 i  i         77 ene 22 07:42  crewai.yml
     4 -rw-rw-r--  1 i  i        992 ene 22 07:42  django.yml
    12 -rw-rw-r--  1 i  i      10837 ene 22 07:42  docker_jupyterlab.yml
    12 -rw-rw-r--  1 i  i      10910 ene 22 07:42  eda.yml
    12 -rw-rw-r--  1 i  i       8598 ene 22 07:42  eda_dataprep.yml
     8 -rw-rw-r--  1 i  i       6865 ene 22 07:42  hispasonic.yml
     8 -rw-rw-r--  1 i  i       5101 ene 22 07:42  jupyterbook.yml
    12 -rw-rw-r--  1 i  i      10633 ene 22 07:42  kaggle.yml
     8 -rw-rw-r--  1 i  i       6566 ene 22 07:42  praisonai.yml
     8 -rw-rw-r--  1 i  i       4545 ene 22 07:42  rstudio.yml
     8 -rw-rw-r--  1 i  i       4865 ene 22 07:42  sonus.yml
     4 -rw-rw-r--  1 i  i       2449 ene 22 07:42  sqlite.yml
     4 -rw-rw-r--  1 i  i         85 ene 22 07:42  synth_data.yml
     8 -rw-rw-r--  1 i  i       5495 ene 22 07:42  tf_env.yml
     4 -rw-rw-r--  1 i  i         87 ene 22 07:42  time_series.yml
```


- **import_conda_envs:** This script allows me to load Conda environments from the same folder, ensuring consistent development and production setups.


- **check_conda_package.sh:** This script asks which package to search for within each Conda environment that is installed. For example, if I want to know in which environments 'jupyterlab' is installed, I simply need to run the script and tell it what I am searching for within the environments.

```bash

(base) i@R7:$ ./check_conda_package.sh 
¿Qué paquete de Conda estás buscando? jupyterlab
Verificando en el entorno: base
❌ jupyterlab no está instalado en el entorno base
Verificando en el entorno: StableDif
❌ jupyterlab no está instalado en el entorno StableDif
Verificando en el entorno: bigquery
✅ jupyterlab está instalado en el entorno bigquery
Verificando en el entorno: blablacar
❌ jupyterlab no está instalado en el entorno blablacar
Verificando en el entorno: time_series
❌ jupyterlab no está instalado en el entorno time_series
.
.
.
```

<br>

These scripts help streamline my workflow by reducing the time spent on manual setup and configuration tasks.
