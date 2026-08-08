import json
import redis
from typing import Any, Dict
from lib.config_loader import config_loader
from utils.log import logger
import redis.asyncio as aioredis


class RedisPubSubManager:
    """
    OOP Redis Pub/Sub Manager responsible for publishing live agent telemetry events
    from background Kafka worker nodes to Redis pub/sub channels, bridging worker events to WebSockets.
    """

    def __init__(self):
        self.redis_host = config_loader.get("REDIS", "redis_host", "localhost")
        self.redis_port = config_loader.get_int("REDIS", "redis_port", 6379)
        self.channel_name = "telemetry:events"

    def publish_event_sync(self, event_data: Dict[str, Any]) -> bool:
        """
        Synchronously publishes a telemetry event dictionary to Redis (used by background workers).
        """
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            payload_str = json.dumps(event_data)
            r.publish(self.channel_name, payload_str)
            r.close()
            logger.info(f"[RedisPubSub] Live Telemetry Event Published for Ticket [{event_data.get('ticket_id')}] - Node: {event_data.get('node_name')}")
            return True
        except Exception as e:
            logger.warning(f"[RedisPubSub] Failed to publish event to Redis: {e}")
            return False

    async def subscribe_channel(self):
        """
        Subscribes asynchronously to the Redis telemetry channel (used by FastAPI WebSockets).
        """
        client = aioredis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe(self.channel_name)
        logger.info(f"[RedisPubSub] FastAPI WebSocket subscribed to Redis channel [{self.channel_name}]")

        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    yield message.get("data")
        except Exception as e:
            logger.error(f"[RedisPubSub] Channel subscription error: {e}")
        finally:
            await pubsub.unsubscribe(self.channel_name)
            await client.close()


# Global singleton instance of RedisPubSubManager
redis_pubsub = RedisPubSubManager()
