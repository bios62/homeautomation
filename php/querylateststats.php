<?php
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Pragma: no-cache");
header("Expires: 0");

$sodaUsername = "iot";
$sodaPassword = "Mercedes450sl";
$sodaUrl = "https://tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com";
$sodaUrl .= "/ords/iot/soda/latest/jiotlogs";
$errorMessage = "";
$jsonResult = "";
$httpCode = 0;

$queryUrl = $sodaUrl . "?action=query&limit=1&fields=all";
$queryBody = <<<'JSON'
{"$query":{"creationtime":{"$exists":true}},"$orderby":{"creationtime":-1}}
JSON;

$curl = curl_init();
curl_setopt_array(
    $curl,
    array(
        CURLOPT_URL => $queryUrl,
        CURLOPT_POST => true,
        CURLOPT_CUSTOMREQUEST => "POST",
        CURLOPT_POSTFIELDS => $queryBody,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FRESH_CONNECT => true,
        CURLOPT_FORBID_REUSE => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_USERPWD => $sodaUsername . ":" . $sodaPassword,
        CURLOPT_HTTPHEADER => array(
            "Accept: application/json",
            "Content-Type: application/json",
            "Cache-Control: no-cache, no-store, max-age=0",
            "Pragma: no-cache",
        ),
        CURLOPT_USERAGENT => "ha-hytta-querylateststats",
    )
);

$apiResponse = curl_exec($curl);
$curlError = curl_error($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($apiResponse === false || $curlError !== "") {
    $errorMessage = "SODA request failed.";
} elseif ($httpCode < 200 || $httpCode >= 300) {
    $errorMessage = "SODA returned HTTP " . $httpCode . ".";
} else {
    $decodedResponse = json_decode($apiResponse, true);
    $jsonResult = json_last_error() === JSON_ERROR_NONE
        ? json_encode(
            $decodedResponse,
            JSON_PRETTY_PRINT
            | JSON_UNESCAPED_SLASHES
            | JSON_UNESCAPED_UNICODE
        )
        : $apiResponse;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latest IoT SODA Record</title>
    <style>
        body {
            margin: 0;
            background: #f5f7fb;
            color: #1f2937;
            font-family: Arial, Helvetica, sans-serif;
        }

        main {
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 32px 0;
        }

        h1 {
            margin: 0 0 20px;
            font-size: 28px;
        }

        pre, .message {
            overflow-x: auto;
            border: 1px solid #d9e2ef;
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        pre {
            margin: 0;
            padding: 18px;
            font: 14px/1.5 Menlo, Consolas, monospace;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }

        .message {
            padding: 12px 14px;
            border-color: #ffccc7;
            background: #fff1f0;
            color: #b42318;
        }

        .request-meta {
            margin: 0 0 12px;
            color: #64748b;
            font-size: 14px;
            overflow-wrap: anywhere;
        }
    </style>
</head>
<body>
    <main>
        <h1>Latest IoT SODA Record</h1>
        <p class="request-meta">
            Generated: <?php echo gmdate("Y-m-d\\TH:i:s\\Z"); ?>
        </p>
        <?php if ($errorMessage !== "") { ?>
            <div class="message">
                <?php echo htmlspecialchars($errorMessage, ENT_QUOTES, "UTF-8"); ?>
            </div>
        <?php } else { ?>
            <p class="request-meta">
                Request URL:
                <?php echo htmlspecialchars($queryUrl, ENT_QUOTES, "UTF-8"); ?>
            </p>
            <pre><?php echo htmlspecialchars($jsonResult, ENT_QUOTES, "UTF-8"); ?></pre>
        <?php } ?>
    </main>
</body>
</html>
