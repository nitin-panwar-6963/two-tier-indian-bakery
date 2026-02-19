#download the base image of the python
FROM python:3.9

#create a working directory W
WORKDIR /app

# copy the dependency from the local host
COPY  . .

# dwonload all the dependency
RUN pip install -r requirements.txt

# port number
EXPOSE 5000

#run the code
CMD ["python","app.py"]
