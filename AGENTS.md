# ha_hytta Project Instructions

- Site-specific files live under the `hytta/`, `brygga/`, and `stua/` directories.
- Each site groups its configuration and programs into `conf/`, a Python source directory, and `scripts/`; `brygga/` currently calls its Python directory `python/`, while `hytta/` and `stua/` use `python-scripts/`.
- Keep shared Python constants in each site's `const.py`; format Python with
  Black using a 70-character target line length.
- Save PHP pages in the `php/` directory.
- SODA PHP pages load `SODAusername`, `SODApassword`, and `sodaURL` from a
  sibling `site.inc` and authenticate to OCI SODA with HTTP Basic Auth.
- IoT stats pages use the existing server-side access-key form gate before
  requesting SODA data; `php/getstatsV3.php` loads `$accessKey` from the
  sibling `site.inc`.
- Production SODA PHP pages load credentials from `site.inc`; standalone test
  utilities may hardcode test configuration only when explicitly requested.
- The standalone Hytta SODA test script uses the shared constants in
  `hytta/python-scripts/const.py` and prints its JSON query response to stdout.
- Existing PHP pages use cURL to call the ORDS REST APIs hosted at `tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com`.
- Keep reusable project conventions here only; do not use this file as a transient change log.
