import json
import os
import sys

# Ensure backend root is in module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from typing import Any, Dict
from agents.workflow_manager import workflow_manager
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from lib.config_loader import config_loader
from utils.log import logger


class KafkaConsumerWorker:
    """
    OOP Background Kafka Worker Node.
    Consumes support ticket events from Kafka topic 'ticket.incoming'
    and triggers the LangGraph multi-agent orchestration pipeline.
    """

    def __init__(self):
        self.bootstrap_servers = config_loader.get("KAFKA", "bootstrap_servers", "localhost:9092")
        self.topic = config_loader.get("KAFKA", "ticket_topic", "ticket.incoming")
        self.group_id = config_loader.get("KAFKA", "consumer_group", "cs_agent_group")
        self.running = False
        self._ensure_topic_exists()
        self.consumer = self._init_consumer()

    def _ensure_topic_exists(self) -> None:
        """Ensures the target Kafka topic exists on the broker before subscribing."""
        try:
            admin_client = AdminClient({"bootstrap.servers": self.bootstrap_servers})
            topic_metadata = admin_client.list_topics(timeout=5.0)

            if self.topic not in topic_metadata.topics:
                logger.info(f"Topic [{self.topic}] does not exist on Kafka broker. Auto-creating topic...")
                new_topic = NewTopic(self.topic, num_partitions=1, replication_factor=1)
                futures = admin_client.create_topics([new_topic])
                for topic, future in futures.items():
                    try:
                        future.result()
                        logger.info(f"Topic [{topic}] created successfully by Consumer Worker.")
                    except Exception as e:
                        logger.warning(f"Topic creation result: {e}")
            else:
                logger.info(f"Kafka topic [{self.topic}] verified by Consumer Worker.")
        except Exception as e:
            logger.warning(f"Could not verify topic via AdminClient: {e}")

    def _init_consumer(self) -> Consumer:
        """Initializes the confluent-kafka Consumer client."""
        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
        logger.info(f"Initializing Kafka Consumer Worker connected to {self.bootstrap_servers} [Group: {self.group_id}]...")
        return Consumer(conf)

    def process_ticket_event(self, ticket_data: Dict[str, Any]) -> None:
        """
        Processes a consumed ticket event by triggering the LangGraph multi-agent pipeline.
        """
        ticket_id = ticket_data.get("ticket_id")
        subject = ticket_data.get("subject")
        customer_id = ticket_data.get("customer_id")
        customer_name = ticket_data.get("customer_name")
        plan_tier = ticket_data.get("plan_tier")

        logger.info(f"============================================================")
        logger.info(f"🟢 [WORKER EVENT CONSUMED] Ticket ID: {ticket_id}")
        logger.info(f"   Customer: {customer_name} ({customer_id}) | Plan: {plan_tier}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Payload Body: {ticket_data.get('body')}")
        logger.info(f"============================================================")

        # Trigger LangGraph Multi-Agent Orchestration Workflow
        try:
            final_state = workflow_manager.run_workflow(ticket_data)
            logger.info(f"✅ [LangGraph Completed] Ticket [{ticket_id}] Resolution Drafted successfully!")
            logger.info(f"--- DRAFT RESPONSE PREVIEW ---")
            logger.info(f"{final_state.get('draft_response')[:300]}...")
            logger.info(f"--------------------------------")
        except Exception as err:
            logger.error(f"Error during LangGraph multi-agent execution for Ticket [{ticket_id}]: {err}")

    def start_consumer_loop(self) -> None:
        """Starts the infinite Kafka message polling loop."""
        self.consumer.subscribe([self.topic])
        self.running = True
        logger.info(f"🚀 Kafka Consumer Worker active & listening on topic [{self.topic}]...")

        try:
            while self.running:
                # Poll Kafka for incoming messages (timeout: 1 second)
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    err_code = msg.error().code()
                    if err_code == KafkaError._PARTITION_EOF:
                        continue
                    elif err_code == KafkaError._UNKNOWN_TOPIC or err_code == 3:
                        logger.warning(f"Topic [{self.topic}] not yet active on broker. Retrying in 2s...")
                        time.sleep(2.0)
                        continue
                    else:
                        logger.error(f"Kafka Consumer Error: {msg.error()}")
                        time.sleep(1.0)
                        continue

                # Decode message payload
                try:
                    payload_str = msg.value().decode("utf-8")
                    ticket_data = json.loads(payload_str)
                    self.process_ticket_event(ticket_data)
                except Exception as parse_err:
                    logger.error(f"Error parsing consumed Kafka message: {parse_err}")

        except KeyboardInterrupt:
            logger.info("Kafka Consumer Worker interrupted by user.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stops the worker loop and closes the Kafka consumer connection."""
        self.running = False
        logger.info("Closing Kafka Consumer connection...")
        self.consumer.close()


if __name__ == "__main__":
    worker = KafkaConsumerWorker()
    worker.start_consumer_loop()
