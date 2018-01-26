# PubSub Py

A python client for an AMQP-based PubSub system. Specifically designed to work with Django model updates, but can be used with anything.

## Installing

The package can be installed from the GemFury private repo via depot:
```
depot --install pubsubpy
```

## Interface

### Configuratiion

#### `init()`

Exactly one call to the `init()` method is required to configure the global library settings.

Required settings:
* `amqp_url`: The url of the AMQP exchange service.
* `model_exchange`: The exchange name on the service for model events.

This must be called before any other call is made, including `@subscribe`, which means before any function decorated with `@subscribe` is loaded.

For Django services, it is recommended that `init()` is called from `settings.py` files.

### Publishing

#### `publish_model_event()`

Args
* `model_name`: string of model class name, e.g. `mksp.apps.users.models.Booking`
* `event_name`: string event name being published, e.g. `updated`
* `obj`: dictionary payload describing the update, e.g. `{ 'foo': 'bar' }`

`model_name` and `event_name` are used to compose the queue name for this type of message, `obj` is the arbitrary data describing the update.

### Subscribing

#### `@subscribe()`

Args
* `topic`: string of the topic name, e.g. `Booking.*`, `Booking.updated`

Use this decorator to register a function as a handler for model events described by `topic`. It will be registered as a callback and used to process queue events whenever subscription processing occurs (triggered by a call to `drain()`).

#### `drain()`

No Args

Process all outstanding messages with all registered subscription callbacks. Continue pulling from the queues and processing messages until queue is empty. Intended to run asynchronously (e.g. in a periodic celery task) to clear the queues when desired.

## Background

### Publish/subscribe systems
[PubSub pattern - Wikipedia](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)
[RabbitMQ PubSub example](https://www.rabbitmq.com/tutorials/tutorial-three-python.html)

## Contributing

### Setting up your env

1. Install `pyenv` via O/S package manager
1. Install target Python versions (i.e. `pyenv install 2.7.14`)
1. Create project virtualenv (using one of the target pythons)
1. Install `depot`
1. Install all requirements files (i.e. `depot --install -r requirements.txt`)

### Running the testsuite locally

Once your local env is set up, you can run the testsuite with `pytest`.
You can also run the tests on all supported Python configurations with `tox`.

### Packaging

1. Ensure you have incremented the version number in `setup.py`
1. Run `python setup.py bdist_wheel` to build the wheel package
    * builds a universal wheel that works on py2/py3 and all platforms
1. Upload package to gemfury repo

### Future Work / Current Caveats

* There is only one global config, which can only be initialized once and must be initialized before any modules containing subscribers are even loaded.
* Subscribers could unwittingly share a queue if a subscriber is contained in a library that is included in multiple different services. The queue key is not unique across services.
