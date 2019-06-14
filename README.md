# SDTask2
### Introduction
Contains the files for the Distributed Systems second task. The goal of this task is to implement a synchronization system by using Cloud Serverless technologies. In concrete, by Using IBM-PyWren for running serverless functions and RabbitMQ as a message passing interface.

Unlike Actor models, serverless Functions lack powerful addressing and communication mechanisms between them. In this event-driven model, functions must usually access other distributed services  to communicate , read inputs, write outputs, or even synchronize between them. Examples of these services are Object Stores like S3 or Azure Storage, NoSQL databases like Azure Cosmos DB or Amazon Dynamo DB, and in-memory stores like Azure Redis Cache, Amazon ElastiCache and IBM CloudAMQP. These third-party services will be used for synchronization, fault-tolerance, and consistency in many cases.

First spawn a leader, responsible to receive write requests and decide which function is allowed to write in each moment (mutual exclusion). To receive the write requests you can use a single queue (e.g. Direct Exchange). All the slaves must publish its ID to this queue. To allow a slave to write, you have to randomly chose on of the Ids and then notify the slave(s). Master functions will not return anything.

Slaves functions must generate a random integer number (for example between 0 and 1000). Then synchronize this number with the rest of the functions by putting (append) the number into a list (e.g. Fanout Exchange). At the end, all the slave functions must return the same list.

### Configuration & Execution
This project code has been made using Pyhton 3.6. You will also need the following packages:
```
pip3 install pywren_ibm_cloud
```
Once the packages are installed, run the code using the following line:
```
python3 main.py NMAPS
```
**Note:** the user will need to have a configuration file `.pywren_configuration` to run the code correctly and stablish a connection with the RabbitMQ server.
