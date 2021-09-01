import os

import asyncio
from dotenv import load_dotenv

from tracardi_postresql_connector.plugin import PostreSQLConnectorAction

load_dotenv()

init = dict(
    dbname='dev',
    user=os.environ['LOGIN'],
    password=os.environ['PASS'],
    host=os.environ['IP'],
    port=5439,
    query="SELECT * FROM sales LIMIT 10;"
)

payload = {}


async def main():
    plugin = await PostreSQLConnectorAction.build(**init)
    result = await plugin.run(payload)
    print(result)


asyncio.run(main())
