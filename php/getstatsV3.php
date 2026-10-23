<?php
$configurationError = "";

if (is_file(__DIR__ . "/site.inc")) {
    require_once __DIR__ . "/site.inc";
} else {
    $configurationError = "missing config";
}

$defaultSiteName = "hytta";
$defaultSites = array("hytta", "brygga");
$accessKey = "Scarab38#";
$keyValue = "";
$selectedSite = $defaultSiteName;
$customSite = "";
$submitted = $_SERVER["REQUEST_METHOD"] === "POST";
$errorMessage = "";
$apiUrl = "";
$latestRecord = array();

function pageValue($value)
{
    if (is_array($value)) {
        return htmlspecialchars(
            json_encode($value, JSON_UNESCAPED_SLASHES),
            ENT_QUOTES,
            "UTF-8"
        );
    }

    return htmlspecialchars((string) $value, ENT_QUOTES, "UTF-8");
}

function displayValue($value)
{
    if ($value === null) {
        return "";
    }

    if (is_bool($value)) {
        return $value ? "Yes" : "No";
    }

    if (is_array($value)) {
        return json_encode(
            $value,
            JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
        );
    }

    return (string) $value;
}

function renderKeyValueRows($values)
{
    foreach ($values as $key => $value) {
        echo "<tr>";
        echo "<th>" . pageValue($key) . "</th>";
        echo "<td>" . pageValue(displayValue($value)) . "</td>";
        echo "</tr>";
    }
}

if ($submitted) {
    $keyValue = (string) ($_POST["key"] ?? "");
    $selectedSite = trim((string) ($_POST["site_select"] ?? ""));
    $customSite = trim((string) ($_POST["site_custom"] ?? ""));
    $siteName = $selectedSite === "" ? $customSite : $selectedSite;

    if (!hash_equals($accessKey, $keyValue)) {
        $errorMessage = "Invalid key.";
    } elseif ($configurationError !== "") {
        $errorMessage = "missing config";
    } elseif ($siteName === "") {
        $errorMessage = "Please enter a site name.";
    } elseif (!preg_match('/^[A-Za-z0-9_-]+$/', $siteName)) {
        $errorMessage = "Site name can only contain letters, numbers, "
            . "underscore and dash.";
    } elseif (
        !isset($SODAusername, $SODApassword, $sodaURL)
        || $SODAusername === ""
        || $SODApassword === ""
        || $sodaURL === ""
    ) {
        $errorMessage = "missing config";
    } else {
        $query = http_build_query(
            array(
                "fields" => "all",
                "limit" => 1,
                "sitename" => $siteName,
            ),
            "",
            "&",
            PHP_QUERY_RFC3986
        );
        $separator = strpos($sodaURL, "?") !== false ? "&" : "?";
        $apiUrl = $sodaURL . $separator . $query;

        $curl = curl_init();
        // 2. Define QBE-payload for sorting
        $jsonPayload = '{
                "$query": {},
                "$orderby": {
                "created_on": -1
                }
        }';
        #$jsonPayload = json_encode($payload);   
        curl_setopt_array(
            $curl,
            array(
                CURLOPT_URL => $apiUrl,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_FOLLOWLOCATION => true,
                CURLOPT_MAXREDIRS => 5,
                CURLOPT_CONNECTTIMEOUT => 10,
                CURLOPT_TIMEOUT => 30,
                CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
                CURLOPT_USERPWD => $SODAusername . ":" . $SODApassword,
                CURLOPT_HTTPHEADER => array('Content-Type: application/json',"Accept: application/json"),
                CURLOPT_USERAGENT => "ha-hytta-getstatsV3",
                CURLOPT_POST => true,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_POSTFIELDS => $jsonPayload,
                
            )
        );
        $apiResponse = curl_exec($curl);
        $curlError = curl_error($curl);
        $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        curl_close($curl);

        if ($apiResponse === false || $curlError !== "") {
            $errorMessage = "SODA request failed: " . $curlError;
        } elseif ($httpCode < 200 || $httpCode >= 300) {
            $errorMessage = "SODA returned HTTP " . $httpCode . ".";
        } else {
            $response = json_decode($apiResponse, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                $errorMessage = "SODA returned invalid JSON.";
            } elseif (!isset($response["items"][0]["value"])) {
                $errorMessage = "SODA returned no record for " . $siteName . ".";
            } elseif (!is_array($response["items"][0]["value"])) {
                $errorMessage = "SODA returned an invalid record.";
            } else {
                $latestRecord = $response["items"][0];
            }
        }
    }
}

$recordValue = $latestRecord["value"] ?? array();
$temperatures = $recordValue["temp"] ?? array();
$sensorStats = $recordValue["sensorstats"] ?? array();
$allSensorStats = $recordValue["allsensorstats"] ?? array();
$sockets = $recordValue["tpSockets"] ?? array();
$ipAddresses = $recordValue["ipaddresses"] ?? array();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT SODA Stats</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --panel: #ffffff;
            --text: #1f2937;
            --muted: #64748b;
            --line: #d9e2ef;
            --accent: #1f7a8c;
            --accent-dark: #14586a;
            --danger: #b42318;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background: var(--bg);
            color: var(--text);
            font-family: Arial, Helvetica, sans-serif;
            font-size: 16px;
        }
        .page {
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 32px 0;
        }

        h1 {
            margin: 0 0 20px;
            font-size: 28px;
            font-weight: 700;
        }

        h2 {
            margin: 26px 0 10px;
            font-size: 20px;
        }

        .search-panel, .table-wrap, .empty {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        .search-panel {
            padding: 18px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            align-items: end;
        }

        label {
            display: block;
            margin-bottom: 6px;
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
        }

        input, select, button {
            width: 100%;
            min-height: 42px;
            border-radius: 6px;
            font: inherit;
        }

        input, select {
            border: 1px solid var(--line);
            background: #fff;
            color: var(--text);
            padding: 8px 10px;
        }

        button {
            border: 0;
            background: var(--accent);
            color: #fff;
            cursor: pointer;
            font-weight: 700;
        }

        button:hover {
            background: var(--accent-dark);
        }

        .message {
            margin: 18px 0 0;
            padding: 12px 14px;
            border: 1px solid #ffccc7;
            border-radius: 6px;
            background: #fff1f0;
            color: var(--danger);
        }

        .result-meta {
            margin: 18px 0 10px;
            color: var(--muted);
            font-size: 14px;
            overflow-wrap: anywhere;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 540px;
        }

        th, td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--line);
            text-align: left;
            vertical-align: top;
        }

        th {
            background: #e8f3f6;
            color: #0f3d4a;
            font-size: 13px;
            text-transform: uppercase;
        }

        tr:nth-child(even) td {
            background: #f9fbfd;
        }

        tr:last-child td {
            border-bottom: 0;
        }

        .empty {
            padding: 18px;
            color: var(--muted);
        }

        @media (max-width: 760px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <main class="page">
        <h1>IoT Stats</h1>
        <section class="search-panel">
            <form method="post" action="">
                <div class="form-grid">
                    <div>
                        <label for="key">Key</label>
                        <input id="key" name="key" type="password"
                            value="" required>
                    </div>
                    <div>
                        <label for="site_select">Site</label>
                        <select id="site_select" name="site_select">
                            <?php foreach ($defaultSites as $siteOption) { ?>
                                <option value="<?php echo pageValue($siteOption); ?>" <?php echo ($selectedSite === $siteOption) ? "selected" : ""; ?>>
                                    <?php echo pageValue($siteOption); ?>
                                </option>
                            <?php } ?>
                            <option value="" <?php echo ($selectedSite === "") ? "selected" : ""; ?>>Blank / typed value</option>
                        </select>
                    </div>
                    <div>
                        <label for="site_custom">Typed site id</label>
                        <input id="site_custom" name="site_custom" type="text"
                            value="<?php echo pageValue($customSite); ?>"
                            placeholder="Only used when blank is selected">
                    </div>
                    <div><button type="submit">Get stats</button></div>
                </div>
            </form>
        </section>

        <?php if ($configurationError !== "" && !$submitted) { ?>
            <div class="message"><?php echo pageValue($configurationError); ?></div>
        <?php } ?>

        <?php if ($errorMessage !== "") { ?>
            <div class="message"><?php echo pageValue($errorMessage); ?></div>
        <?php } ?>

        <?php if ($submitted && $errorMessage === "") { ?>
            <div class="result-meta">
                Latest SODA record for <?php echo pageValue($siteName); ?>.
            </div>

            <h2>Record</h2>
            <div class="table-wrap"><table><tbody>
                <?php renderKeyValueRows(array(
                    "id" => $latestRecord["id"] ?? "",
                    "created" => $latestRecord["created"] ?? "",
                    "lastModified" => $latestRecord["lastModified"] ?? "",
                )); ?>
            </tbody></table></div>

            <?php if (is_array($temperatures) && count($temperatures) > 0) { ?>
                <h2>Temperatures</h2>
                <div class="table-wrap"><table><thead><tr>
                    <th>Room</th><th>Temperature</th><th>Time</th>
                </tr></thead><tbody>
                    <?php foreach ($temperatures as $temperature) { ?>
                        <tr><td><?php echo pageValue($temperature["roomname"] ?? ""); ?></td>
                        <td><?php echo pageValue($temperature["temp"] ?? ""); ?></td>
                        <td><?php echo pageValue($temperature["time"] ?? ""); ?></td></tr>
                    <?php } ?>
                </tbody></table></div>
            <?php } ?>

            <?php if (is_array($sensorStats) && count($sensorStats) > 0) { ?>
                <h2>Sensor Stats</h2>
                <div class="table-wrap"><table><thead><tr>
                    <th>Group</th><th>Temperature</th><th>Source</th>
                </tr></thead><tbody>
                    <?php foreach ($sensorStats as $group => $stat) { ?>
                        <tr><td><?php echo pageValue($group); ?></td>
                        <td><?php echo pageValue($stat["temp"] ?? ""); ?></td>
                        <td><?php echo pageValue($stat["timestamp"] ?? ""); ?></td></tr>
                    <?php } ?>
                </tbody></table></div>
            <?php } ?>

            <?php if (is_array($allSensorStats) && count($allSensorStats) > 0) { ?>
                <h2>All Sensor Stats</h2>
                <div class="table-wrap"><table><thead><tr>
                    <th>Sensor</th><th>Temperature</th><th>Time</th>
                </tr></thead><tbody>
                    <?php foreach ($allSensorStats as $stat) { ?>
                        <tr><td><?php echo pageValue($stat["sensorname"] ?? ""); ?></td>
                        <td><?php echo pageValue($stat["temp"] ?? ""); ?></td>
                        <td><?php echo pageValue($stat["time"] ?? ""); ?></td></tr>
                    <?php } ?>
                </tbody></table></div>
            <?php } ?>

            <?php if (is_array($sockets) && count($sockets) > 0) { ?>
                <h2>TP-Link Sockets</h2>
                <div class="table-wrap"><table><thead><tr>
                    <th>Device</th><th>IP address</th><th>Relay state</th>
                </tr></thead><tbody>
                    <?php foreach ($sockets as $socket) { ?>
                        <tr><td><?php echo pageValue($socket["device"] ?? ""); ?></td>
                        <td><?php echo pageValue($socket["ipAddress"] ?? ""); ?></td>
                        <td><?php echo pageValue($socket["relay_state"] ?? ""); ?></td></tr>
                    <?php } ?>
                </tbody></table></div>
            <?php } ?>

            <?php if (is_array($ipAddresses) && count($ipAddresses) > 0) { ?>
                <h2>IP Addresses</h2>
                <div class="table-wrap"><table><thead><tr>
                    <th>Source</th><th>IP address</th>
                </tr></thead><tbody>
                    <?php foreach ($ipAddresses as $source => $address) { ?>
                        <tr><td><?php echo pageValue($source); ?></td>
                        <td><?php echo pageValue($address["ip"] ?? ""); ?></td></tr>
                    <?php } ?>
                </tbody></table></div>
            <?php } ?>
        <?php } ?>
    </main>
</body>
</html>
