__GLOBAL_CONFIG = None

AMQP_URL = 'amqp_url'
MODEL_EXCHANGE = 'model_exchange'
CONNECTION = "__connection"

__REQUIRED_INIT_KWARGS = {AMQP_URL, MODEL_EXCHANGE}
__OPTIONAL_INIT_KWARGS = set()
__ALLOWED_INIT_KWARGS = __REQUIRED_INIT_KWARGS | __OPTIONAL_INIT_KWARGS


def init(**kwargs):
    """Initialize global library parameters.
    """
    import kombu
    global __GLOBAL_CONFIG
    assert not __GLOBAL_CONFIG, 'pubsubpy.init can only be called once'
    if any(k not in __REQUIRED_INIT_KWARGS for k in kwargs.keys()):
        raise KeyError()
    __GLOBAL_CONFIG = {
        k: v
        for k, v in kwargs.items() if k in __ALLOWED_INIT_KWARGS
    }
    __GLOBAL_CONFIG[CONNECTION] = kombu.Connection(get_config_param(AMQP_URL))


def get_config_param(k):
    """Get a parameter from the global config.
    """
    assert __GLOBAL_CONFIG, 'init() needs to have been called by now'
    return __GLOBAL_CONFIG.get(k)


def acquire():
    from kombu.pools import connections
    assert __GLOBAL_CONFIG, 'init() needs to have been called by now'
    connection = get_config_param(CONNECTION)
    return connections[connection].acquire(block=True)


from .pub import publish_model_event  # noqa
from .sub import drain, subscribe  # noqa
