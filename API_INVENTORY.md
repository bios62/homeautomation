# Outbound API inventory

This inventory was produced by scanning the project for outbound HTTP clients
(`curl`, `wget`, PHP cURL, Python/CircuitPython `requests`, and browser AJAX)
and raw TCP sockets. It covers PHP, Python, shell scripts, and source-like
backup files (`.orig`, `_new`, and `_2906`). Configuration values are included
where they resolve an endpoint.

`{site}`, `{group}`, `{host}`, `{port}`, and similar placeholders are runtime
values rather than literal URLs.

| API / endpoint pattern | Method | Callers | Notes |
| --- | --- | --- | --- |
| `https://tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com/ords/iot/iotv1/iotstats/{site}` | GET | `php/varmev7.php`, `php/getstatsV2.php` | The PHP dashboard uses `hytta`; the stats page permits `hytta`, `brygga`, or a validated custom site. |
| `https://{ORDS-host}/ords/iot/iotv1/iotstats/` | POST | `python-scripts/collector.py`, `brygga/python/windspeed.py`, `devices/code_saveip.py`, `brygga/scripts/saveip.bash`, `brygga/scripts/saveip.bash_new` | URL comes from `iotstatsURL`. Configured ORDS hosts include the iosp instance and the `myatp-*` placeholders. The legacy `brygga/scripts/saveip_new` hard-codes the iosp host. |
| `https://{ORDS-host}/ords/iot/iotv1/groupconfig/` | GET | `python-scripts/common.py`, `python-scripts/getconfig.py`, `python-scripts/termostat.py`, `python-scripts/updategroupconfig.py`, `termostat.py`, `temp/common.py` | URL comes from `groupConfigURL`. |
| `https://{ORDS-host}/ords/iot/iotv1/groupconfigall` | GET | `php/varmev7.php` | PHP uses the iosp host by default; an older `138.3.241.22` branch remains in the source. |
| `https://{ORDS-host}/ords/iot/iotv1/members/` | GET | `php/varmev7.php`, `python-scripts/common.py`, `python-scripts/getconfig.py`, `python-scripts/termostat.py`, `python-scripts/updategroupconfig.py`, `termostat.py`, `temp/common.py` | URL comes from `membersURL` for Python. |
| `https://{ORDS-host}/ords/iot/iotv1/currentsetting/` | GET | `python-scripts/getconfig.py`, `python-scripts/termostat.py`, `termostat.py` | URL comes from `tempSettingURL`. |
| `https://tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com/ords/iot/iotv1/settempbyname/` | POST | Browser AJAX embedded in `php/varmev7.php` | Changes a named thermostat's temperature state. |
| `https://tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com/ords/iot/iotv1/setrange/` | POST | Browser AJAX embedded in `php/varmev7.php` | Submits group low/high temperature limits. |
| `https://{ORDS-host}/ords/iot/soda/latest/jiotlogs` | POST | `python-scripts/collector.py`, `brygga/python/windspeed.py` | URL comes from `sodaURL`; callers use HTTP Basic authentication. |
| `http://revebaasen.no/php/getpropertyV2.php?siteid={site}&propertyname=ip` | GET | `php/getcurrentip.php` | The commented-out POST code in that file is not active. |
| `https://revebaasen.no/php/saveipV3.php?siteid={site}` | GET | `scripts/saveip.bash`, `brygga/scripts/saveip.bash`, `brygga/scripts/saveip.sh`, and backup variants | `saveipV2.php` is commented out, so it is not an active call. |
| `https://revebaasen.no/php/savetemp.php?temp={temp}` | GET | `brygga/scripts/savetemp.sh` | Legacy temperature submission. |
| `https://{weewxtarget}/php/savepropertyV2.php?siteid=weewx&propertyname=weatherid&propertyvalue={time}` | GET | `scripts/weewx.bash`, `scripts/weewx_upload.sh` | Config default is `https://fox.no/php/savepropertyV2.php`; the upload script hard-codes `revebaasen.no`. |
| `https://api.ipify.org?format=json` | GET | `python-scripts/collector.py`, `devices/code_saveip.py` | Taken from `getmyip1URL`. |
| `http://ip-api.com/json/` | GET | `brygga/scripts/saveip.bash`, `scripts/saveip.bash` | Takes the returned `query` value as the external IP address. |
| `http://checkip.dyndns.org` | GET | `brygga/scripts/saveip_new` | Source-like legacy script; parses its HTML response. |
| `https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month}-{day}_{area}.json` | GET | `python-scripts/getprices.py`, `scripts/getelprice.bash` | The shell script builds the same request from `elPriceURL`; it also has an unused malformed `URL` variable. |
| `http://{hostname-or-ip}:8080/api/savesensorvalues` | POST | `scripts/savesensor.bash`, `scripts/savesensor_njq.bash`, `scripts/savetemp.bash`, `stua/scripts/savesensor.bash`, `devices/code_tempsensor.py` | Local sensor service. `conf/apiserver.json` resolves to `192.168.68.142:8080/api/savesensorvalues`; CircuitPython uses `conf/settings.toml` (`10.0.0.88:8080`). |
| `http://{ip}:8080/isalive` | GET | `scripts/apiserver_monitor.bash` | Local health check for `python-scripts/apiserver.py`. |
| `http://{currentipURL}?siteid=hytta` | GET | `python-scripts/collector.py` | `currentipURL` is referenced in code but has no value in the checked-in site configuration, so its resolved target is unknown. |
| `tcp://{TP-Link-device}:{port}` | Proprietary TCP | `python-scripts/tplink.py`, `python-scripts/tpscan3.py` | Sends TP-Link's encrypted JSON control protocol. The port is configuration/argument supplied (commonly 9999); this is not HTTP. |
| `{ntp_server}` (NTP/UDP) | NTP | `devices/code_tempsensor.py`, `devices/code_saveip.py` | Configured as `no.pool.ntp.org` in `conf/settings.toml`; this is network time synchronization, not an HTTP API. |

## Static third-party browser dependency

`php/varmev7.php` also loads jQuery from
`https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js`. This is a
script dependency, not an application API call.

## Excluded items

* Documentation, SQL notes, and comments that contain example URLs only.
* Local SQLite and MySQL connections, which are database connections rather
  than outbound HTTP APIs.
* `python-scripts/apiserver.py` endpoints such as `/sensordata`, because that
  file serves them; it does not call them remotely.
