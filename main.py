import pika
import pywren_ibm_cloud as pywren
import sys
import json
import random
import os


def slave(nmaps, id):
    rand_list = []
    granted = False
    n_msg = 0

    def send_msg(ch, method_frame, header_frame, body):
        nonlocal nmaps
        nonlocal rand_list
        nonlocal granted
        nonlocal n_msg

        msg = body.decode('ascii')

        if msg == 'permission_granted':
            rand_n = random.randint(0, 1000)
            ch.basic_publish(exchange='fan_logs', routing_key='', body=str(rand_n))
            granted = True
        else:
            rand_list.append(body)
            n_msg += 1

        if n_msg > nmaps-1:
            ch.stop_consuming()

        if not granted:
            channel.basic_publish(exchange='', routing_key='masters_queue', body=str(id))

    pw_config = json.loads(os.environ.get('PYWREN_CONFIG', ''))
    params = pika.URLParameters(pw_config['rabbitmq']['amqp_url'])
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    queue_name = 'slave'+str(id)+'_queue'
    channel.queue_declare(queue=queue_name, auto_delete=True)
    channel.queue_bind(exchange='fan_logs', queue=queue_name)
    channel.basic_publish(exchange='', routing_key='masters_queue', body=str(id))

    channel.basic_consume(send_msg, queue=queue_name, no_ack=True)
    channel.start_consuming()

    connection.close()

    return rand_list


def master(nmaps):
    n_slaves = nmaps

    def listen_slaves(ch, method_frame, header_frame, body):
        nonlocal n_slaves
        nonlocal id_list
        nonlocal slave_req

        id_list.append(body.decode('ascii'))
        slave_req += 1

        if slave_req > n_slaves-1:
            ch.stop_consuming()

    pw_config = json.loads(os.environ.get('PYWREN_CONFIG', ''))
    params = pika.URLParameters(pw_config['rabbitmq']['amqp_url'])
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='masters_queue')
    channel.basic_consume(listen_slaves, queue='masters_queue', no_ack=True)

    id_list = []
    slave_req = 0

    channel.start_consuming()

    while slave_req > 0:
        chosen_slave = random.choice(id_list)
        channel.basic_publish(exchange='', routing_key='slave' + str(chosen_slave) + '_queue',
                              body='permission_granted')
        id_list.remove(chosen_slave)
        slave_req -= 1
    
    channel.queue_delete(queue='masters_queue')
    connection.close()


def main():
    try:
        nmaps = int(sys.argv[1])
    except:
        print('Usage:\n\tpython3 main.py NUM_MAPS\n')
        exit(2)

    if nmaps < 1:
        print('ERROR: the number of maps must be higher than 1\n')
        exit(3)

    pw = pywren.ibm_cf_executor(rabbitmq_monitor=True)

    params = pika.URLParameters(pw.config['rabbitmq']['amqp_url'])
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange='fan_logs', exchange_type='fanout')

    pw.call_async(master, nmaps)

    slave_list = []

    for i in range(nmaps):
        slave_list.append([nmaps, i])

    pw_s = pywren.ibm_cf_executor(rabbitmq_monitor=True)
    pw_s.map(slave, slave_list)

    results = pw_s.get_result()
    i = 0
    equal = len(set(map(tuple, results))) == 1

    for res_list in results:
        print(f'List {i}: {res_list}')
        i += 1

    if equal:
        print('\nIT WORKS!')
    else:
        print('\nThe lists don\'t match...')

    connection.close()


if __name__ == '__main__':
    main()
