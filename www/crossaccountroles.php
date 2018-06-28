<?php 
include 'common.php';
$title="ISO IAM Auditor - Cross Account Roles";
generate_head($title);
$dbconn = getdb();
$sql = "SELECT *, insert_ts::date as insertdate FROM aws_cross_account_roles order by aws_account_id";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
print "
<div style=\"overflow-x:auto;\">
  <table>
    <tr>
      <th>AWS<br>Account #</th>
      <th>Role ARN</th>
      <th>Role Working?</th>
      <th>Date Inserted</th>
      <th>Last Used</th>
    </tr>\n";
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  //print '    <tr><div class="tooltip"><span class="tooltiptext">' . 
   // $resarray[$key]['aud_iam_user_json'] . '</span>' . "\n";
  // iterate over columns
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td>' . $resarray[$key]['role_arn']  . "</td>\n";
  if ($resarray[$key]['working'] == 't') { $working = "True"; } else { $working = "False"; } 
  print '      <td align=center>' . $working  . "</td>\n";
  print '      <td>' . $resarray[$key]['insertdate'] . "</td>\n";
  $thisdate = explode(" ", $resarray[$key]['last_used_ts']);
  print '      <td>' . $thisdate[0] . "</td>\n";
  print "    </tr>\n";
}
print "   </table>
</div>
";
generate_footer();
