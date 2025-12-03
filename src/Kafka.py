import sys
import datetime
from confluent_kafka import Consumer, KafkaException, KafkaError, OFFSET_END
from Messages import Messages


class Kafka(object):
    def __init__(self, conf, api):
        # Consumer configuration
        kafkaConf = {
            'bootstrap.servers': conf.getKafkaServer(),
            'group.id': conf.getGroupID(),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'SCRAM-SHA-512',
            'sasl.username': conf.getUsername(),
            'sasl.password': conf.getPassword(),
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True
        }

        # Create Kafka consumer instance
        consumer = Consumer(kafkaConf)

        # Go to last message
        def my_assign(consumer, partitions):
            for p in partitions:
                p.offset = OFFSET_END
            print(f'[{datetime.datetime.now()}][Kafka] assign', partitions)
            consumer.assign(partitions)

        # Subscribe to the topic from latest message
        consumer.subscribe(conf.getTopic(), on_assign=my_assign)
        # Subscribe to the topic normaly
        # consumer.subscribe(conf.getTopic())
        self.consumer = consumer
        self.Messages = Messages(conf, api)

    def consume_messages(self):
        try:
            while True:
                # Poll for messages
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        sys.stderr.write(
                            '%% %s [%d] reached end at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    # Process the message
                    self.Messages.processMessage(msg.value().decode('utf-8'))
        except KeyboardInterrupt:
            print('CTRL+C Pressed, closing properly Kafka consumer')
            # Close down consumer to commit final offsets.
            self.consumer.close()
            exit(0)
        except AttributeError as e:
            print(f"AttributeError excepted:\n{e}")

    def close(self):
        self.consumer.close()
