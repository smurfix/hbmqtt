MQTTClient API
==============

The :class:`~hbmqtt.client.MQTTClient` class implements the client part of MQTT protocol. It can be used to publish and/or subscribe MQTT message on a broker accessible on the network through TCP or websocket protocol, both secured or unsecured.


Usage examples
--------------

Subscriber
..........

The example below shows how to write a simple MQTT client which subscribes a topic and prints every messages received from the broker :

.. code-block:: python

    import logging
    import anyio

    from hbmqtt.client import open_mqttclient, ClientException
    from hbmqtt.mqtt.constants import QOS_1, QOS_2
    
    logger = logging.getLogger(__name__)

    async def uptime_coro():
        async with open_mqttclient() as C:
            await C.connect('mqtt://test.mosquitto.org/')
            # Subscribe to '$SYS/broker/uptime' with QOS=1
            # Subscribe to '$SYS/broker/load/#' with QOS=2
            await C.subscribe([
                    ('$SYS/broker/uptime', QOS_1),
                    ('$SYS/broker/load/#', QOS_2),
                 ])
            for i in range(1, 100):
                message = await C.deliver_message()
                packet = message.publish_packet
                print("%d:  %s => %s" % (i, packet.variable_header.topic_name, str(packet.payload.data)))
            await C.unsubscribe(['$SYS/broker/uptime', '$SYS/broker/load/#'])

    if __name__ == '__main__':
        formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=formatter)
        anyio.run(uptime_coro)

When executed, this script runs the ``uptime_coro`` until it completes.
``uptime_coro`` starts by opening an async context with :func:`~hbmqtt.client.open_mqttclient`, which returns a
:class:`~hbmqtt.client.MQTTClient` instance.
The coroutine then calls :meth:`~hbmqtt.client.MQTTClient.connect` to connect to the broker, in this case ``test.mosquitto.org``.
Once connected, the coroutine subscribes to some topics, and then waits for 100 messages. Each message received is simply written to output.
Finally, the coroutine unsubscribes from topics and disconnects from the broker.

Publisher
.........

The example below uses the :class:`~hbmqtt.client.MQTTClient` class to implement a publisher.
This test publish 3 messages asynchronously to the broker on a test topic.
For the purposes of the test, each message is published with a different Quality Of Service.
This example also shows to method for publishing message asynchronously.

.. code-block:: python

    import logging
    import anyio

    from hbmqtt.client import MQTTClient
    from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

    logger = logging.getLogger(__name__)
    
    async def test_coro():
        async with open_mqttclient() as C:
            await C.connect('mqtt://test.mosquitto.org/')
            async with anyio.create_task_group() as tg:
                await tg.spawn(C.publish,'a/b', b'TEST MESSAGE WITH QOS_0')
                await tg.spawn(C.publish,'a/b', b'TEST MESSAGE WITH QOS_1', qos=QOS_1)),
                await tg.spawn(C.publish,'a/b', b'TEST MESSAGE WITH QOS_2', qos=QOS_2)),
            logger.info("messages published")


    async def test_coro2():
        try:
            async with open_mqttclient() as C:
               await C.connect('mqtt://test.mosquitto.org:1883/')
               message = await C.publish('a/b', b'TEST MESSAGE WITH QOS_0', qos=QOS_0)
               message = await C.publish('a/b', b'TEST MESSAGE WITH QOS_1', qos=QOS_1)
               message = await C.publish('a/b', b'TEST MESSAGE WITH QOS_2', qos=QOS_2)
               #print(message)
               logger.info("messages published")
        except ConnectException as ce:
            logger.error("Connection failed: %s", ce)


    if __name__ == '__main__':
        formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=formatter)
        anyio.run(test_coro)
        anyio.run(test_coro2)

``test_coro()`` and ``test_coro()`` are executed in sequence.
Both do the same job. ``test_coro()`` publishes 3 messages in sequence. ``test_coro2()`` publishes the same message asynchronously.
The difference appears when looking at the sequence of MQTT messages sent.

``test_coro()`` achieves:
::

    hbmqtt/YDYY;NNRpYQSy3?o -out-> PublishPacket(ts=2015-11-11 21:54:48.843901, fixed=MQTTFixedHeader(length=28, flags=0x0), variable=PublishVariableHeader(topic=a/b, packet_id=None), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_0'"))
    hbmqtt/YDYY;NNRpYQSy3?o -out-> PublishPacket(ts=2015-11-11 21:54:48.844152, fixed=MQTTFixedHeader(length=30, flags=0x2), variable=PublishVariableHeader(topic=a/b, packet_id=1), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_1'"))
    hbmqtt/YDYY;NNRpYQSy3?o <-in-- PubackPacket(ts=2015-11-11 21:54:48.979665, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=1), payload=None)
    hbmqtt/YDYY;NNRpYQSy3?o -out-> PublishPacket(ts=2015-11-11 21:54:48.980886, fixed=MQTTFixedHeader(length=30, flags=0x4), variable=PublishVariableHeader(topic=a/b, packet_id=2), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_2'"))
    hbmqtt/YDYY;NNRpYQSy3?o <-in-- PubrecPacket(ts=2015-11-11 21:54:49.029691, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=2), payload=None)
    hbmqtt/YDYY;NNRpYQSy3?o -out-> PubrelPacket(ts=2015-11-11 21:54:49.030823, fixed=MQTTFixedHeader(length=2, flags=0x2), variable=PacketIdVariableHeader(packet_id=2), payload=None)
    hbmqtt/YDYY;NNRpYQSy3?o <-in-- PubcompPacket(ts=2015-11-11 21:54:49.092514, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=2), payload=None)fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=2), payload=None)

while ``test_coro2()`` runs:
::

    hbmqtt/LYRf52W[56SOjW04 -out-> PublishPacket(ts=2015-11-11 21:54:48.466123, fixed=MQTTFixedHeader(length=28, flags=0x0), variable=PublishVariableHeader(topic=a/b, packet_id=None), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_0'"))
    hbmqtt/LYRf52W[56SOjW04 -out-> PublishPacket(ts=2015-11-11 21:54:48.466432, fixed=MQTTFixedHeader(length=30, flags=0x2), variable=PublishVariableHeader(topic=a/b, packet_id=1), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_1'"))
    hbmqtt/LYRf52W[56SOjW04 -out-> PublishPacket(ts=2015-11-11 21:54:48.466695, fixed=MQTTFixedHeader(length=30, flags=0x4), variable=PublishVariableHeader(topic=a/b, packet_id=2), payload=PublishPayload(data="b'TEST MESSAGE WITH QOS_2'"))
    hbmqtt/LYRf52W[56SOjW04 <-in-- PubackPacket(ts=2015-11-11 21:54:48.613062, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=1), payload=None)
    hbmqtt/LYRf52W[56SOjW04 <-in-- PubrecPacket(ts=2015-11-11 21:54:48.661073, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=2), payload=None)
    hbmqtt/LYRf52W[56SOjW04 -out-> PubrelPacket(ts=2015-11-11 21:54:48.661925, fixed=MQTTFixedHeader(length=2, flags=0x2), variable=PacketIdVariableHeader(packet_id=2), payload=None)
    hbmqtt/LYRf52W[56SOjW04 <-in-- PubcompPacket(ts=2015-11-11 21:54:48.713107, fixed=MQTTFixedHeader(length=2, flags=0x0), variable=PacketIdVariableHeader(packet_id=2), payload=None)

Both coroutines have the same results except that ``test_coro2()`` manages messages flow in parallel which may be more efficient.

Reference
---------

MQTTClient API
..............

.. autofunction:: hbmqtt.client.open_mqttclient

.. automodule:: hbmqtt.client

    .. autoclass:: MQTTClient

        .. automethod:: connect
        .. automethod:: disconnect
        .. automethod:: reconnect
        .. automethod:: ping
        .. automethod:: publish
        .. automethod:: subscribe
        .. automethod:: unsubscribe
        .. automethod:: deliver_message

MQTTClient configuration
........................

Typically, you create a :class:`~hbmqtt.client.MQTTClient` instance by way of ``async with`` :func:`~hbmqtt.client.open_mqttclient`\(). This context manager creates a taskgroup for the client's housekeeping tasks to run in.

:func:`~hbmqtt.client.open_mqttclient` accepts a ``config`` parameter which allows to setup some behaviour and defaults settings. This argument must be a Python dictionary which may contain the following entries:

* ``keep_alive``: keep alive interval (in seconds) to send when connecting to the broker (defaults to ``10`` seconds). :class:`~hbmqtt.client.MQTTClient` will *auto-ping* the broker if no message is sent within the keep-alive interval. This avoids disconnection from the broker.
* ``ping_delay``: *auto-ping* delay before keep-alive times out (defaults to ``1`` seconds). This should be larger than twice the worst-case roundtrip between your client and the broker.
* ``default_qos``: Default QoS (``0``) used by :meth:`~hbmqtt.client.MQTTClient.publish` if ``qos`` argument is not given.
* ``default_retain``: Default retain (``False``) used by :meth:`~hbmqtt.client.MQTTClient.publish` if ``retain`` argument is not given.
* ``auto_reconnect``: enable or disable auto-reconnect feature (defaults to ``True``).
* ``reconnect_max_interval``: maximum interval (in seconds) to wait before two connection retries (defaults to ``10``).
* ``reconnect_retries``: maximum number of connect retries (defaults to ``2``). Negative value will cause client to reconnect infinietly.

Default QoS and default retain can also be overriden by adding a ``topics`` entry with may contain QoS and retain values for specific topics. See the following example:

.. code-block:: python

    config = {
        'keep_alive': 10,
        'ping_delay': 1,
        'default_qos': 0,
        'default_retain': False,
        'auto_reconnect': True,
        'reconnect_max_interval': 5,
        'reconnect_retries': 10,
        'topics': {
            '/test': { 'qos': 1 },
            '/some_topic': { 'qos': 2, 'retain': True }
        }
    }

With this setting any message published will set with QOS_0 and retain flag unset except for

* messages sent to ``/test`` topic will be sent with QOS_1
* messages sent to ``/some_topic`` topic will be sent with QOS_2 and retained

In any case, any ``qos`` and ``retain`` arguments passed to method :meth:`~hbmqtt.client.MQTTClient.publish` will override these settings.
