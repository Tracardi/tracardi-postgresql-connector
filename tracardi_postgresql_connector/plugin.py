import json
import asyncpg
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from tracardi_plugin_sdk.domain.register import Plugin, Spec, MetaData
from tracardi_plugin_sdk.action_runner import ActionRunner
from tracardi_plugin_sdk.domain.result import Result
from tracardi_postgresql_connector.model.postresql import Connection


class PostreSQLConnectorAction(ActionRunner):

    @staticmethod
    async def build(**kwargs) -> 'PostreSQLConnectorAction':
        plugin = PostreSQLConnectorAction(**kwargs)
        connection = Connection(**kwargs)
        plugin.db = await connection.connect()

        return plugin

    def __init__(self, **kwargs):
        self.db = None  # type: Optional[asyncpg.connection.Connection]
        if 'query' not in kwargs:
            raise ValueError("Please define query.")

        self.query = kwargs['query']
        self.timeout = kwargs['timeout'] if 'timeout' in kwargs else None

    async def run(self, payload):
        result = await self.db.fetch(self.query, timeout=self.timeout)
        result = [self.to_dict(record) for record in result]
        return Result(port="result", value={"result": result})

    async def close(self):
        if self.db:
            await self.db.close()

    @staticmethod
    def to_dict(record):

        def json_default(obj):
            """JSON serializer for objects not serializable by default json code"""

            if isinstance(obj, (datetime, date)):
                return obj.isoformat()

            if isinstance(obj, Decimal):
                return float(obj)

            return str(obj)

        j = json.dumps(dict(record), default=json_default)
        return json.loads(j)


def register() -> Plugin:
    return Plugin(
        start=False,
        spec=Spec(
            module='tracardi_postgresql_connector.plugin',
            className='PostreSQLConnectorAction',
            inputs=["payload"],
            outputs=['result'],
            version='0.1.2',
            license="MIT",
            author="Risto Kowaczewski",
            init={
                "host": 'localhost',
                "port": 5439,
                "database": None,
                "user": None,
                "password": None,
                "query": None
            }

        ),
        metadata=MetaData(
            name='PostreSQL connector',
            desc='Connects to postreSQL and reads data.',
            type='flowNode',
            width=200,
            height=100,
            icon='postgres',
            group=["Connectors"]
        )
    )
