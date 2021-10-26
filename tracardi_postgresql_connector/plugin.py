import json
import asyncpg
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from tracardi.service.storage.driver import storage
from tracardi_plugin_sdk.domain.register import Plugin, Spec, MetaData, Form, FormGroup, FormField, FormComponent
from tracardi_plugin_sdk.action_runner import ActionRunner
from tracardi_plugin_sdk.domain.result import Result

from tracardi_postgresql_connector.model.configuration import Configuration
from tracardi_postgresql_connector.model.postresql import Connection


def validate(config: dict) -> Configuration:
    return Configuration(**config)


class PostreSQLConnectorAction(ActionRunner):

    @staticmethod
    async def build(**kwargs) -> 'PostreSQLConnectorAction':
        config = validate(kwargs)
        source = await storage.driver.resource.load(config.source.id)
        connection = Connection(**source.config)
        connection = await connection.connect()
        return PostreSQLConnectorAction(connection, config)

    def __init__(self, connection: asyncpg.connection.Connection, config: Configuration):
        self.db = connection
        self.query = config.query
        self.timeout = config.timeout

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
            version='0.6.0',
            license="MIT",
            author="Risto Kowaczewski",
            init={
                "source": {"id": None},
                "query": None,
                "timeout": 20
            },
            form=Form(groups=[
                FormGroup(
                    name="PostreSQL resource",
                    fields=[
                        FormField(
                            id="source",
                            name="PostreSQL resource",
                            description="Select PostreSQL resource. Authentication credentials will be used to "
                                        "connect to PostreSQL server.",
                            component=FormComponent(
                                type="resource",
                                props={"label": "resource"})
                        )
                    ]
                ),
                FormGroup(
                    name="Query settings",
                    fields=[
                        FormField(
                            id="query",
                            name="Query",
                            description="Type SQL Query.",
                            component=FormComponent(type="sql", props={
                                "label": "SQL query"
                            })
                        ),
                        FormField(
                            id="timeout",
                            name="Timeout",
                            description="Type query timeout.",
                            component=FormComponent(type="text", props={
                                "label": "Timeout",

                            })
                        )
                    ])
            ]),

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
