# Copyright (c) 2015 Nicolas JOUANIN
#
# See the file license.txt for copying permission.
import logging

import yaml

logger = logging.getLogger(__name__)


def not_in_dict_or_none(dict, key):
    """
    Check if a key exists in a map and if it's not None
    :param dict: map to look for key
    :param key: key to find
    :return: true if key is in dict and not None
    """
    if key not in dict or dict[key] is None:
        return True
    else:
        return False


def format_client_message(session=None, address=None, port=None):
    if session:
        return "(client id=%s)" % session.client_id
    elif address is not None and port is not None:
        return "(client @=%s:%d)" % (address, port)
    else:
        return "(unknown client)"


def gen_client_id():
    """
    Generates random client ID
    :return:
    """
    import random
    gen_id = 'hbmqtt/'

    for i in range(7, 23):
        gen_id += chr(random.randint(0, 74) + 48)
    return gen_id


def read_yaml_config(config_file):
    config = None
    try:
        with open(config_file, 'r') as stream:
            config = yaml.load(stream)
    except yaml.YAMLError as exc:
        logger.error("Invalid config_file %s: %r", config_file, exc)
    return config


# utility code

import attr
import anyio
from .errors import InvalidStateError

class CancelledError(RuntimeError):
    ## This intentionally does not descend from any toolkit's cancellation exception
    ## (much less from all of them)
    pass


@attr.s
class Future:
    """A waitable value useful for inter-task synchronization,
    inspired by :class:`threading.Event` and :class:`asyncio.Future`.

    An event object manages an internal value, which is initially
    unset, and a task can wait for it to become True.

    Note that the value can only be read once.
    """

    event = attr.ib(factory=anyio.create_event, init=False)
    value = attr.ib(default=None, init=False)

    async def set(self, value):
        """Set the result to return this value, and wake any waiting task.
        """
        if self.event.is_set():
            raise InvalidStateError("Value already set")
        self.value = value
        await self.event.set()

    async def set_error(self, exc):
        """Set the result to raise this exceptio, and wake any waiting task.
        """
        if self.event.is_set():
            raise InvalidStateError("Value already set")
        self.value = exc
        await self.event.set()

    def is_set(self):
        """Check whether the event has occurred.
        """
        return self.value is not None

    async def cancel(self):
        """Send a cancelation to the recipient.
        """
        await self.set_error(CancelledError())

    async def get(self):
        """Block until the value is set.

        If it's already set, then this method returns immediately.

        The value can only be read once.
        """
        await self.event.wait()
        if isinstance(self.value, BaseException):
            raise self.value
        return self.value

    def done(self):
        """Report whether this Future has been set.
        """
        return self.event.is_set()
