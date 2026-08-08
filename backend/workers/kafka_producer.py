import json
from typing import Any, Dict
from confluent_kafka import KafkaError, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from lib.config_loader import config_loader
from utils.log import logger


class KafkaProducerManager:
    """
    OOP Kafka Producer Manager responsible for creating Kafka topics,
    serializing ticket payloads, and publishing event messages asynchronously.
    """

    def __init__(self):
        self.bootstrap_servers = config_loader.get("KAFKA", "bootstrap_servers", "localhost:9092")
        self.topic = config_loader.get("KAFKA", "ticket_topic", "ticket.incoming")
        self._ensure_topic_exists()
        self.producer = self._init_producer()

    def _ensure_topic_exists(self) -> None:
        """Ensures the target Kafka topic exists on the broker using AdminClient."""
        try:
            admin_client = AdminClient({"bootstrap.servers": self.bootstrap_servers})
            topic_metadata = admin_client.list_topics(timeout=5.0)

            if self.topic not in topic_metadata.topics:
                logger.info(f"Topic [{self.topic}] not found on Kafka broker. Creating topic...")
                new_topic = NewTopic(self.topic, num_partitions=1, replication_factor=1)
                futures = admin_client.create_topics([new_topic])
                for topic, future in futures.items():
                    try:
                        future.result()  # Wait for topic creation result
                        logger.info(f"Topic [{topic}] created successfully on Kafka broker.")
                    except Exception as e:
                        logger.warning(f"Topic creation result for [{topic}]: {e}")
            else:
                logger.info(f"Kafka topic [{self.topic}] verified on broker.")
        except Exception as e:
            logger.warning(f"Could not verify/create Kafka topic via AdminClient: {e}")

    def _init_producer(self) -> Producer:
        """Initializes the confluent-kafka Producer client."""
        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "cs_command_center_producer",
            "acks": "all",  # Ensure all in-sync replicas acknowledge the message
            "retries": 3,
            "retry.backoff.ms": 200,
        }
        logger.info(f"Initializing Kafka Producer connected to {self.bootstrap_servers}...")
        return Producer(conf)

    @staticmethod
    def _delivery_report(err: Any, msg: Any) -> None:
        """Delivery callback invoked by confluent-kafka once the message is written to Kafka."""
        if err is not None:
            logger.error(f"Kafka Delivery Failed for message key {msg.key()}: {err}")
        else:
            logger.info(
                f"Kafka Event Delivered successfully to topic [{msg.topic()}] "
                f"partition [{msg.partition()}] offset [{msg.offset()}]"
            )

    def publish_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Publishes a ticket event dictionary to the ticket.incoming topic.
        
        :param ticket_data: Dictionary containing ticket_id, customer_id, subject, body, etc.
        :return: True if queued successfully.
        """
        ticket_id = ticket_data.get("ticket_id", "unknown")
        try:
            payload_bytes = json.dumps(ticket_data).encode("utf-8")
            
            self.producer.produce(
                topic=self.topic,
                key=ticket_id.encode("utf-8"),
                value=payload_bytes,
                on_delivery=self._delivery_report
            )
            self.producer.poll(0)
            logger.info(f"Queued ticket event [{ticket_id}] to Kafka topic [{self.topic}]")
            return True
        except Exception as e:
            logger.error(f"Failed to publish ticket event [{ticket_id}] to Kafka: {e}")
            return False

    def flush(self, timeout_seconds: float = 5.0) -> None:
        """Flushes remaining pending messages in the producer queue before server shutdown."""
        logger.info("Flushing pending Kafka Producer events...")
        self.producer.flush(timeout=timeout_seconds)


# Global singleton instance of KafkaProducerManager
kafka_producer = KafkaProducerManager()
