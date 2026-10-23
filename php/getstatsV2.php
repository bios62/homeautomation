<?php
$accessKey = "Scarab38#";
$ordsServer = "tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com";
$defaultSites = array("hytta", "brygga");

$submitted = ($_SERVER["REQUEST_METHOD"] === "POST");
$keyValue = "";
$selectedSite = "hytta";
$customSite = "";
$records = array();
$columns = array();
$errorMessage = "";
$apiUrl = "";

function pageValue($value)
{
    return htmlspecialchars((string) $value, ENT_QUOTES, "UTF-8");
}

function flattenValue($value)
{
    if (is_array($value)) {
        return json_encode($value, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    }

    if ($value === null) {
        return "";
    }

    return (string) $value;
}

if ($submitted) {
    $keyValue = isset($_POST["key"]) ? $_POST["key"] : "";
    $selectedSite = isset($_POST["site_select"]) ? trim($_POST["site_select"]) : "";
    $customSite = isset($_POST["site_custom"]) ? trim($_POST["site_custom"]) : "";
    $siteId = ($selectedSite === "") ? $customSite : $selectedSite;

    if (!hash_equals($accessKey, $keyValue)) {
        $errorMessage = "Invalid key.";
    } elseif ($siteId === "") {
        $errorMessage = "Please select or type a site id.";
    } elseif (!preg_match('/^[A-Za-z0-9_-]+$/', $siteId)) {
        $errorMessage = "Site id can only contain letters, numbers, underscore and dash.";
    } else {
        $apiUrl = "https://" . $ordsServer . "/ords/iot/iotv1/iotstats/" . rawurlencode($siteId);

        $ch = curl_init();
        curl_setopt_array($ch, array(
            CURLOPT_URL => $apiUrl,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_MAXREDIRS => 5,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_HTTPHEADER => array("Accept: application/json"),
            CURLOPT_USERAGENT => "ha-hytta-getstatsV2",
        ));

        $apiResponse = curl_exec($ch);
        $curlError = curl_error($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($apiResponse === false || $curlError !== "") {
            $errorMessage = "REST API call failed: " . $curlError;
        } elseif ($httpCode < 200 || $httpCode >= 300) {
            $errorMessage = "REST API returned HTTP " . $httpCode . ".";
        } else {
            $decodedResponse = json_decode($apiResponse, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                $errorMessage = "REST API returned invalid JSON.";
            } else {
                if (isset($decodedResponse["items"]) && is_array($decodedResponse["items"])) {
                    $records = $decodedResponse["items"];
                } elseif (is_array($decodedResponse)) {
                    $records = $decodedResponse;
                }

                if (isset($records[0]) && is_array($records[0])) {
                    foreach ($records as $record) {
                        if (is_array($record)) {
                            foreach (array_keys($record) as $column) {
                                if (!in_array($column, $columns, true)) {
                                    $columns[] = $column;
                                }
                            }
                        }
                    }
                } elseif (count($records) > 0) {
                    $columns = array("value");
                }
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT Stats</title>
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

        .search-panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
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

        input,
        select,
        button {
            width: 100%;
            min-height: 42px;
            border-radius: 6px;
            font: inherit;
        }

        input,
        select {
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
            border-radius: 6px;
            background: #fff1f0;
            color: var(--danger);
            border: 1px solid #ffccc7;
        }

        .result-meta {
            margin: 18px 0 10px;
            color: var(--muted);
            font-size: 14px;
        }

        .table-wrap {
            margin-top: 16px;
            overflow-x: auto;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 720px;
        }

        th,
        td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--line);
            text-align: left;
            vertical-align: top;
            white-space: nowrap;
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
            margin-top: 16px;
            padding: 18px;
            background: var(--panel);
            border: 1px dashed var(--line);
            border-radius: 8px;
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
                        <input id="key" name="key" type="password" value="" required>
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
                        <input id="site_custom" name="site_custom" type="text" value="<?php echo pageValue($customSite); ?>" placeholder="Only used when blank is selected">
                    </div>

                    <div>
                        <button type="submit">Get stats</button>
                    </div>
                </div>
            </form>
        </section>

        <?php if ($errorMessage !== "") { ?>
            <div class="message"><?php echo pageValue($errorMessage); ?></div>
        <?php } ?>

        <?php if ($submitted && $errorMessage === "") { ?>
            <div class="result-meta">
                Source: <?php echo pageValue($apiUrl); ?> |
                Rows: <?php echo count($records); ?>
            </div>

            <?php if (count($records) === 0) { ?>
                <div class="empty">No rows returned from the REST API.</div>
            <?php } else { ?>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <?php foreach ($columns as $column) { ?>
                                    <th><?php echo pageValue($column); ?></th>
                                <?php } ?>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($records as $record) { ?>
                                <tr>
                                    <?php foreach ($columns as $column) { ?>
                                        <td>
                                            <?php
                                            if (is_array($record)) {
                                                echo pageValue(flattenValue(isset($record[$column]) ? $record[$column] : ""));
                                            } else {
                                                echo pageValue(flattenValue($record));
                                            }
                                            ?>
                                        </td>
                                    <?php } ?>
                                </tr>
                            <?php } ?>
                        </tbody>
                    </table>
                </div>
            <?php } ?>
        <?php } ?>
    </main>
</body>
</html>
