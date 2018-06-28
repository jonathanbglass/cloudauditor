<?php 
include 'common.php';
$dbconn = getdb();
$sql = "SELECT * from al_accounts";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);

if (isset($_GET['output']) && $_GET['output'] == 'json') {
  header("Content-type: application/json");
  header("Content-Disposition: attachment; filename=alertlogic_accounts_and_keys.json");
  header("Pragma: no-cache");
  header("Expires: 0");
  $jsonoutput= "[";
  foreach ($resarray as $key=>$val) {
    $jsonoutput .= "{\"al_account_id\": " . $resarray[$key]['al_account_id'] . "," . 
      "\"aws_account_id\": " . $resarray[$key]['aws_account_id'] . "," .
      "\"al_account_name\": \"" . $resarray[$key]['al_account_name'] . "\"," .
      "\"api_key\": \"" .  $resarray[$key]['api_key'] . "\"},";
  }
  $jsonoutput = substr_replace($jsonoutput, '', -1);
  $jsonoutput .= "]";
  print $jsonoutput;
  die();
}
if (isset($_GET['output']) && $_GET['output'] == 'csv') {
  header("Content-type: text/csv");
  header("Content-Disposition: attachment; filename=alertlogic_accounts_and_keys.csv");
  header("Pragma: no-cache");
  header("Expires: 0");
  foreach ($resarray as $key=>$val) {
    $line = $resarray[$key]['al_account_id'] . ",";
    $line .= sprintf("%'012d", $resarray[$key]['aws_account_id']) . ",";
    $line .= "\"" . $resarray[$key]['al_account_name'] . "\",";
    $line .= $resarray[$key]['api_key'] . "\n";
    print $line;
    }
  die();
} 
$title="ISO - Alert Logic Cloud Defender Accounts";
generate_head($title);
print "
<div style=\"overflow-x:auto;\">
  <table>
    <tr>
      <th>Customer #</th>
      <th>AWS Account #</th>
      <th>Account Name</th>
      <th>API Key - Download as <a href=" . $_SERVER['PHP_SELF'] . "?output=csv>CSV</a> or <a href=" . $_SERVER['PHP_SELF'] . "?output=json>JSON</a></th>
    </tr>\n";
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . $resarray[$key]['al_account_id']  . "</td>\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['al_account_name']  . "</td>\n";
  print '      <td align>' . $resarray[$key]['api_key']  . "</td>\n";
  print "    </tr>\n";
}
?>
   </table>
</div>
<?php generate_footer(); ?>
