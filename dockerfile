
#Create container with python 3.13
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install the libraries needed
RUN pip install xarray numpy matplotlib cartopy cdsapi netCDF4 h5netcdf
RUN pip install python-telegram-bot

#Create an application directory named code
WORKDIR /code

#Copy inside code, the application file. I have to write "." because the dockerfile is inside the folder. If I had a folder for environment (ENV) > ./env/read_netcdf.py . 
COPY main.py .
COPY cdsapi.txt /root/.cdsapirc

#CMD [ "main.py" ]

ENTRYPOINT [ "python", "bot.py" ]
#CMD [ "sleep", "infinity" ]