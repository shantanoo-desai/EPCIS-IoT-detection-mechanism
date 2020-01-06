# EPCIS-IoT-detection-mechanism
Python3.x based automated script to detect changes in MongoDB for incoming EPC documents, obtain IoT information based on meta-data and send relevant data to a Blockchain API.

## System Requirements

- __DocumentDB__: `MongoDB 4.x`
- __SensorDB__: `InfluxDB 1.7.x`
- __Blockchain API__: Standard RESTful service to communicate with Blockchain
- `python3.x`

### System Notes

__DocumentDB__:

- The MongoDB needs to be configured to be a __Replica Set__. A single instance of MongoDB can become the Primary instance. [Reference](https://www.sohamkamani.com/blog/2016/06/30/docker-mongo-replica-set/)
- Once the __Replica Set__ is configured the script will use the __Change Streams__ to detect incoming EPC documents. [Reference](https://www.mongodb.com/blog/post/mongodb-change-streams-with-python)

__SensorDB__:

- For system setup refer to the following libraries:

    1. [EPCIS-IoT-Arduino](https://github.com/iotfablab/EPCIS-IoT-Arduino): Programming Sensor Nodes to send `BME280` Environmental values to an MQTT broker
    2. [EPCIS-IoT-Parser](https://github.com/iotfablab/EPCIS-IoT-Parser): Parsing Script to provision the insertion of meta-data from EPC documents and IoT Data into SensorDB

__Management__:

In order to connect to the DocumentDB for combination of `EPCIS-IoT` Application use the following libraries:

1. [epcis-iot-backend](https://github.com/shantanoo-desai/epcis-iot-backend): GraphQL CRUD Backend to associate EPC data with IoT Data
2. [ng-epcis-iot](https://github.com/shantanoo-desai/ng-epcis-iot): Angular and Apollo Client based Frontend to connect to `epcis-iot-backend`

__Blockchain & Data Validation__:

The solution is part of the [NIMBLE-Project](https://github.com/nimble-platform)

## Development

- Develop using as virtual environment

        python -m venv venv

- Activate the Virtual Environment

    __Windows__
    
        /venv/Scripts/activate.ps1

    __Linux__

        . venv/bin/activate

- Install the dependencies using:

      pip install -r requirements.txt

- Adapt the `config.toml` file with settings for all Databases

- Execute the app using:

      python main.py

### Development using Docker

- Update the image using:

        docker build -t epcis-iot-detection .


## Deployment using Docker

1. Create a `config.production.toml` with your production parameters in it.

2. Execute the following in the Terminal where the `config.production.toml` file exists:

        docker run --name="epcis-iot-detection" -v $(pwd)/config.production.toml:/app/config.toml:ro \
        --net=host --restart=always shantanoodesai/epcis-iot-detection:latest

3. Track the log files using:

        docker logs -f epcis-iot-detection
