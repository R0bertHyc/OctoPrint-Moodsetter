# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import octoprint.plugin
from octoprint.events import Events
import flask

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

class MoodSetterPlugin(
                octoprint.plugin.AssetPlugin,
                octoprint.plugin.StartupPlugin,
                octoprint.plugin.TemplatePlugin,
                octoprint.plugin.SimpleApiPlugin,
                octoprint.plugin.SettingsPlugin,
                octoprint.plugin.EventHandlerPlugin,
                octoprint.plugin.RestartNeedingPlugin
        ):

        light_state = False

        def get_settings_defaults(self):
                return dict(
                        light_pin = 13,
                        brightness_val = 100,
                        inverted_output = False
                )

        def get_template_configs(self):
                return [
                        dict(type="navbar", custom_bindings=True),
                        dict(type="settings", custom_bindings=True)
                ]

        def get_assets(self):
                # Define your plugin's asset files to automatically include in the
                # core UI here.
                return dict(
                        js=["js/moodSetter.js"],
                        css=["css/moodSetter.css"],
                        #less=["less/octolight.less"]
                )

        def on_after_startup(self):
                self.light_state = False
                self._logger.info("--------------------------------------------")
                self._logger.info("MoodSetter started, listening for GET request")
                self._logger.info("Light pin: {}, Brightness: {}, inverted_input: {}".format(
                        self._settings.get(["light_pin"]),
                        self._settings.get(["brightness_val"]),
                        self._settings.get(["inverted_output"])
                ))
                self._logger.info("--------------------------------------------")

                # Setting the default state of pin
                GPIO.setup(int(self._settings.get(["light_pin"])), GPIO.OUT)
                pwm = GPIO.PWM(int(self._settings.get(["light_pin"])), int(self._settings.get(["brightness_val"])))
                pwm.start(0)
                
                if bool(self._settings.get(["inverted_output"])):
                        pwm.ChangeDutyCycle(int(self._settings.get(["brightness_val"])))
                else:
                        GPIO.output(int(self._settings.get(["light_pin"])), GPIO.LOW)

                #Because light is set to ff on startup we don't need to retrieve the current state
                """
                r = self.light_state = GPIO.input(int(self._settings.get(["light_pin"])))
        if r==1:
                self.light_state = False
        else:
                self.light_state = True
        self._logger.info("After Startup. Light state: {}".format(
                self.light_state
        ))
        """

                self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))

        def light_toggle(self):
                # Sets the GPIO every time, if user changed it in the settings.
                GPIO.setup(int(self._settings.get(["light_pin"])), GPIO.OUT)
                pwm = GPIO.PWM(int(self._settings.get(["light_pin"])), int(self._settings.get(["brightness_val"])))
                pwm.start(0)

                self.light_state = not self.light_state

                # Sets the light state depending on the inverted output setting (XOR)
                if self.light_state ^ self._settings.get(["inverted_output"]):
                        pwm.ChangeDutyCycle(int(self._settings.get(["brightness_val"])))
                else:
                        GPIO.output(int(self._settings.get(["light_pin"])), GPIO.LOW)

                self._logger.info("Got request. Light state: {}".format(
                        self.light_state
                ))

                self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))

        def on_api_get(self, request):
                action = request.args.get('action', default="toggle", type=str)

                if action == "toggle":
                        self.light_toggle()

                        return flask.jsonify(state=self.light_state)

                elif action == "getState":
                        return flask.jsonify(state=self.light_state)

                elif action == "turnOn":
                        if not self.light_state:
                                self.light_toggle()

                        return flask.jsonify(state=self.light_state)

                elif action == "turnOff":
                        if self.light_state:
                                self.light_toggle()

                        return flask.jsonify(state=self.light_state)

                else:
                        return flask.jsonify(error="action not recognized")

        def on_event(self, event, payload):
                if event == Events.CLIENT_OPENED:
                        self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))
                        return

        def get_update_information(self):
                return dict(
                        octolight=dict(
                                displayName="OctoPrint-Moodsetter",
                                displayVersion=self._plugin_version,

                                type="github_release",
                                current=self._plugin_version,

                                user="R0bertHyc",
                                repo="OctoPrint-Moodsetter",
                                pip="https://github.com/R0bertHyc/OctoPrint-Moodsetter/archive/master.zip"
                        )
                )

__plugin_name__ = "Mood Setter"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = MoodSetterPlugin()

