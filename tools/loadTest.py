from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from os import environ
from random import randrange, random
from threading import Timer
import asyncio
from concurrent.futures import ThreadPoolExecutor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--threads", type=int, default=10)
parser.add_argument("--queries", type=int, default=5)
args = parser.parse_args()

class Timer:
  def __init__(self, timeout, callback):
    self._timeout = timeout
    self._callback = callback
    self._task = asyncio.ensure_future(self._job())

  async def _job(self):
    await asyncio.sleep(self._timeout)
    await self._callback()

  async def done(self):
    await self._task

  def cancel(self):
    self._task.cancel()


def get_random_element(list):
  return list[randrange(0, len(list) - 1)]

def make_client():
  args = {
    "domain": environ.get("FAUNA_DOMAIN"),
    "scheme": environ.get("FAUNA_SCHEME"),
    "port": environ.get("FAUNA_PORT"),
  }
  # If None, use default instead
  non_null_args = {k: v for k, v in args.items() if v is not None}
  return FaunaClient(secret=environ["FAUNA_ROOT_KEY"], **non_null_args)


client_pool = [make_client() for i in range(10)]

async def run_q():
  client = get_random_element(client_pool)
  random_query = get_random_element([q.paginate(q.collections()), q.sum([1,1])])
  res = await loop.run_in_executor(_executor, client.query, random_query)
  return res

done = 0
def increment_done():
  global done
  done = done + 1

async def tick(idx):
  id = str(random())[2:7]
  print("Running {0} parallel queries for {1}".format(args.queries, id))

  await asyncio.gather(*[run_q() for i in range(args.queries)])

  increment_done()
  print("Done for {0}. Threads {1}/{2}".format(id, done, args.threads))

async def per_thread(idx):
  delay = 0 if idx == args.threads - 1 else randrange(0, 10)
  await Timer(delay, lambda: tick(idx)).done()

async def execute():
  await asyncio.gather(*[per_thread(i) for i in range(args.threads)])


if __name__ == "__main__":
  _executor = ThreadPoolExecutor(args.queries * args.threads)
  loop = asyncio.get_event_loop()
  loop.run_until_complete(execute())
  loop.close()
