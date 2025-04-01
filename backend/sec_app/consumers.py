import json
from channels.generic.websocket import AsyncWebsocketConsumer
from sec_app.models.metric import FinancialMetric
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

class RevenueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_revenue_data()
    async def send_revenue_data(self):
        revenue_data = await sync_to_async(list)(
            FinancialMetric.objects.filter(
                metric_name="Revenue", company__ticker="AAPL"
            ).order_by("period__period").values("period__period", "value")
        )

        profit_data = await sync_to_async(list)(
            FinancialMetric.objects.filter(
                metric_name="Profit", company__ticker="AAPL"
            ).order_by("period__period").values("period__period", "value")
        )

        # Log the query results
        logger.info(f"Revenue data: {revenue_data}")
        logger.info(f"Profit data: {profit_data}")

        data = {
            "revenue": revenue_data,
            "profit": profit_data,
        }

        await self.send(json.dumps(data))

    async def receive(self, text_data):
        await self.send_revenue_data()
