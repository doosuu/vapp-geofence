# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

import asyncio
import json
import logging
import signal

from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from velocitas_sdk.vdb.reply import DataPointReply
from velocitas_sdk.vehicle_app import VehicleApp

# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)

GET_SPEED_REQUEST_TOPIC = "sampleapp/getSpeed"
GET_SPEED_RESPONSE_TOPIC = "sampleapp/getSpeed/response"
GEOFENCE_TOPIC = "geofence/notification"


class SampleApp(VehicleApp):
    """
    Sample skeleton vehicle app.

    The skeleton subscribes to a getSpeed MQTT topic
    to listen for incoming requests to get
    the current vehicle speed and publishes it to
    a response topic.

    It also subcribes to the VehicleDataBroker
    directly for updates of the
    Vehicle.Speed signal and publishes this
    information via another specific MQTT topic
    """

    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        await self.Vehicle.CurrentLocation.Latitude.join(
            self.Vehicle.CurrentLocation.Longitude
        ).subscribe(self.on_postion_change)

        await self.Vehicle.Cabin.Infotainment.Navigation.DestinationSet.Latitude.set(46)

    async def on_postion_change(self, data: DataPointReply):
        current_lat = data.get(self.Vehicle.CurrentLocation.Latitude).value
        current_lon = data.get(self.Vehicle.CurrentLocation.Longitude).value

        # build a very simple geofence rectangle
        if (
            current_lat > 45
            and current_lat < 47
            and current_lon > 43
            and current_lon < 45
        ):
            await self.publish_event(
                GEOFENCE_TOPIC,
                json.dumps({"message": "Vehicle is within geofence"}),
            )

        # Do anything with the received value.
        # Example:
        # - Publishes current speed to MQTT Topic (i.e. DATABROKER_SUBSCRIPTION_TOPIC).


async def main():
    """Main function"""
    logger.info("Starting SampleApp...")
    # Constructing SampleApp and running it.
    vehicle_app = SampleApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
