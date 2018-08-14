# PubSub Py

A python client for an AMQP-based PubSub system. Specifically designed to work with Django model updates, but can be used with anything.

## Installing

The package can be installed from PyPI:
```
pip install pubsubpy
```

The underlying kombu library can be used with both `librabbitmq` and the pure Python `amqp` libraries, and will prefer `librabbitmq` if present. We recommend `librabbitmq` for production use if it is available for your platform. Other AMQP transports are also available and may work, but have not been tested. See here for more details on potential AMQP transports: http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html#amqp-transports

## Interface

### Configuration

#### `PubSub`

Subscribers and publishers are managed by the `PubSub` class. Initialize a `PubSub` object with an amqp_url and model_exchange name, and the object exposes three main methods for managing pubsub:

- `subscribe()`, a decorator around subscriber functions;
- `drain()`, a method which will consume all registered queues and process with subscribers;
- `publish_model_event()`, which will publish a new event to the exchange.

##### Required settings
* `amqp_url`: The url of the AMQP exchange service.
* `model_exchange`: The exchange name on the service for model events.

##### Example
```
from pubsub import PubSub
if settings.PUBSUB_AMQP_URL and settings.PUBSUB_MODEL_EXCHANGE:
	pubsub_app = PubSub(settings.PUBSUB_AMQP_URL, settings.PUBSUB_MODEL_EXCHANGE)
```

### Publishing

#### `publish_model_event(model_name, event_name, obj)`

`model_name` and `event_name` are used to compose the queue name for this type of message, `obj` is the arbitrary data describing the update.

##### Args
* `model_name`: string of model class name, e.g. `booking`
* `event_name`: string event name being published, e.g. `updated`
* `obj`: dictionary payload describing the update, e.g. `{ 'foo': 'bar' }`

##### Example
```
pubsub_app.publish_model_event('booking','saved', instance.to_service_model())
```

### Subscribing

#### `@subscribe(topic)`

Use this decorator to register a function as a handler for model events described by `topic`. It will be registered as a callback and used to process queue events whenever subscription processing occurs (triggered by a call to `drain()`).

The decorated function should take two positional arguments, for instance:
```
@pubsub_app.subscribe('booking.*')
def process_booking_event(body, message):
    ...
```

##### Args
* `topic`: string of the topic name, e.g. `booking.*`, `booking.updated`

##### Decorated Function Args
* `body`: dict which is the payload of the message, currently the format is `{"object": obj}` where `obj` is the value of the `obj` parameter passed into the call to `publish_model_event()` that created this update
* `message`: the entire message object (headers, metadata, body, etc) from the underlying `kombu` library

In most cases, the `body` argument should be sufficient to process events, as message acking is done by the pubsub library.

##### Example
```
@pubsub_app.subscribe('booking.*')
def update_booking(body, message):
    print(body, message)
```

#### `drain()`

Process all outstanding messages with all registered subscription callbacks. Continue pulling from the queues and processing messages until queue is empty. Intended to run asynchronously (e.g. in a periodic celery task) to clear the queues when desired.

##### Args
none

##### Example
As a periodic celery task:
```
from my_app.pubsub import pubsub_app
@scheduled(minute='*')
@app.task
def pubsub_listen():
    pubsub_app.drain()
```

## Background

### Publish/subscribe systems

[PubSub pattern - Wikipedia](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)

[RabbitMQ PubSub example](https://www.rabbitmq.com/tutorials/tutorial-three-python.html)

## Contributing

### Setting up your env

1. Install `pyenv` via O/S package manager
1. Install target Python versions (i.e. `pyenv install 2.7.14`)
1. Create project virtualenv (using one of the target pythons)
1. Install all requirements files (`pip install -r requirements.txt`, etc)

### Running the testsuite locally

Once your local env is set up, you can run the testsuite with `pytest`.
You can also run the tests on all supported Python configurations with `tox`.

### Future Work / Current Caveats

* Subscribers could unwittingly share a queue if a subscriber is contained in a library that is included in multiple different services. The queue key is not unique across services.
