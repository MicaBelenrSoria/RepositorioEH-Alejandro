## Requisitos del Sistema

Antes de instalar las dependencias de Python, asegúrate de instalar las dependencias del sistema necesarias.

### Ubuntu/Debian:

```bash
sudo apt update
sudo apt install unixodbc unixodbc-dev 

### Activar entorno
source venv/bin/activate

### Instalar dependencias
pip install -r requirements.txt

### Instalar obdc17
bash install installODBC17.sh
