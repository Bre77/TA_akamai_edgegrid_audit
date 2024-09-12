import os
import time
import sys
import json
import dateutil.parser
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.modularinput import *
from akamai.edgegrid import EdgeGridAuth


class Input(Script):
    MASK = "<encrypted>"
    LIMIT = 50
    APP = __file__.split(os.sep)[-3]

    def get_scheme(self):
        scheme = Scheme("Akamai Edgegrid")
        scheme.description = "Grab Audit data from the Akamai Edgegrid API"
        scheme.use_external_validation = False
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            Argument(
                name="domain",
                title="Domain",
                data_type=Argument.data_type_string,
                required_on_create=True,
                required_on_edit=False,
            )
        )
        scheme.add_argument(
            Argument(
                name="access_token",
                title="Access Token",
                data_type=Argument.data_type_string,
                required_on_create=True,
                required_on_edit=False,
            )
        )
        scheme.add_argument(
            Argument(
                name="client_token",
                title="Client Token",
                data_type=Argument.data_type_string,
                required_on_create=True,
                required_on_edit=False,
            )
        )
        scheme.add_argument(
            Argument(
                name="client_secret",
                title="Client Secret",
                data_type=Argument.data_type_string,
                required_on_create=True,
                required_on_edit=False,
            )
        )
        scheme.add_argument(
            Argument(
                name="history",
                title="Day of historical data",
                data_type=Argument.data_type_number,
                required_on_create=False,
                required_on_edit=False,
            )
        )
        scheme.add_argument(
            Argument(
                name="proxy",
                title="Optional Proxy URL",
                description="Should start with http:// and end with the port. Include basic auth if required, this field will be encrypted.",
                data_type=Argument.data_type_string,
                required_on_create=False,
                required_on_edit=False,
            )
        )
        return scheme

    def stream_events(self, inputs, ew):
        # Get Variables
        self.service.namespace["app"] = self.APP
        input_name, input_items = inputs.inputs.popitem()
        kind, name = input_name.split("://")
        checkpointfile = os.path.join(
            self._input_definition.metadata["checkpoint_dir"], name + "_v2"
        )
        base = "https://" + input_items["domain"] + "/event-viewer-api/v1/events"
        headers = {"Accept": "application/json"}
        history = int(input_items["history"]) * 86400

        # Password Encryption
        auth = {}
        updates = {}

        for item in ["client_token", "client_secret", "access_token", "proxy"]:
            stored_password = [
                x
                for x in self.service.storage_passwords
                if x.username == item and x.realm == name
            ]
            if input_items[item] == self.MASK:
                if len(stored_password) != 1:
                    ew.log(
                        EventWriter.ERROR,
                        f"Encrypted {item} was not found for {input_name}, reconfigure its value.",
                    )
                    return
                auth[item] = stored_password[0].content.clear_password
            elif input_items[item]:
                if stored_password:
                    ew.log(EventWriter.DEBUG, "Removing Current password")
                    self.service.storage_passwords.delete(username=item, realm=name)
                ew.log(EventWriter.DEBUG, "Storing password and updating Input")
                self.service.storage_passwords.create(input_items[item], item, name)
                updates[item] = self.MASK
                auth[item] = input_items[item]
        if updates:
            self.service.inputs.__getitem__((name, kind)).update(**updates)

        # Checkpoint
        try:
            lastEventId = open(checkpointfile, "r").read()
            params = {"afterEventId": lastEventId}
        except OSError:
            ew.log(EventWriter.WARN, "No Checkpoint found")
            params = {}
            lastEventId = ""

        ew.log(EventWriter.DEBUG, f"Last eventId was {lastEventId}")

        # Web Session
        with requests.Session() as session:
            session.auth = EdgeGridAuth(**auth)
            if input_items.get("proxy", "").startswith("http"):
                session.proxies.update({"https": input_items["proxy"]})
            beforeEventId = None
            more = True
            while more:
                count = 0
                if beforeEventId:
                    params = {"beforeEventId", beforeEventId}
                response = session.get(base, headers=headers, params=params)
                if response.ok:
                    ew.log(EventWriter.DEBUG, response.url)
                    events = response.json()["events"]
                    if len(events) == 0:
                        ew.log(EventWriter.INFO, "No new events.")
                        more = False
                        break
                    if not beforeEventId:  # First event we receive is the most recent, so record its eventID as the checkpoint for next time
                        open(checkpointfile, "w").write(events[0]["eventId"])
                    beforeEventId = events[
                        -1
                    ][
                        "eventId"
                    ]  # Next request should contain events before the last one in this request
                    for event in events:
                        if (event["eventId"]) == lastEventId:
                            ew.log(EventWriter.INFO, "Caught up to last eventId.")
                            more = False
                            break

                        eventtime = dateutil.parser.parse(
                            event["eventTime"]
                        ).timestamp()
                        if eventtime < (time.time() - history):
                            ew.log(EventWriter.INFO, "Hit history limit.")
                            more = False
                            break

                        count += 1

                        # Fix EventData
                        eventData = {}
                        for x in event["eventData"]:
                            eventData[x["key"]] = x["value"]
                        event["eventData"] = eventData

                        # Write Event
                        ew.write_event(
                            Event(
                                time=eventtime,
                                host=input_items["domain"],
                                source="/event-viewer-api/v1/events",
                                data=json.dumps(event, separators=(",", ":")),
                            )
                        )
                    more = count == 50
                    ew.log(EventWriter.INFO, f"Wrote {count} events")
                else:
                    more = False
                    ew.log(
                        EventWriter.ERROR,
                        f"Request returned status {response.status_code}, {response.text}",
                    )
        ew.close()


if __name__ == "__main__":
    exitcode = Input().run(sys.argv)
    sys.exit(exitcode)
